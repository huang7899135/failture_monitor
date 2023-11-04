import logging
import time
import os
from .BasePlatform import Platform

logger = logging.getLogger(__name__)


class Baishan(Platform):
    def __init__(self, supplier: str = ""):
        assert supplier in ["vision_blue", "yicheng"], "只有vision_blue or yicheng "
        self.login_supplier = supplier
        self.session_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                              f"sessions/baishan_{supplier}")
        super().__init__()
        self.query_url = "https://service-luohan.bs58i.baishancloud.com/agent/graphql/query"
        self.suppliers = self.login_info["suppliers"]

    def _login(self, supplier_id: int = 1355) -> None:
        """因为白山有2个公司主体,所以需要登录2次,分别获取2个公司的token"""
        self.before_login()
        login_url = "https://service-luohan-auth.bs58i.baishancdnx.com/login"
        login_data = {
            "client_id": "luohan",
            "phone": self.username,
            "password": self.password,
            "supplier_id": supplier_id
        }
        login_resp = self.session.post(url=login_url, json=login_data, verify=False)
        logger.debug(login_resp.json())
        if login_resp.json()['code'] == 200:
            # 保存token
            token = login_resp.json()['data']['jwt_token']
            test_data = {
                "query": f"""
                    {{
                        SsoValidateQuery(
                            token: "{token}"
                        ) {{
                            id
                            phone
                            supplier_name
                        }}
                    }}
                """
            }
            resp = self.session.post(url=self.query_url, json=test_data, verify=False)
            if resp.json()['code'] == 0:
                self.after_login()
                logger.info(f"白山:{self.suppliers[self.login_supplier]['supplier_name']}登录成功")
            else:
                logger.critical(resp.json()['msg'])
                raise Exception(login_resp.json()['msg'])

        else:
            logger.error(f"白山:{login_resp.json()['msg']}")
            raise Exception(login_resp.json()['msg'])

    def login(self):
        supplier_id = self.suppliers.get(self.login_supplier).get("supplier_id")
        self._login(supplier_id)

    def logout(self):
        data = {
            "query": "{logout {result}}\n"
        }
        self.fetch(self.query_url, json=data)

    def session_is_unexpected(self, resp):
        super().session_is_unexpected(resp)
        if resp.json()['code'] == 401:
            logger.warning("白山:登录过期,重新登录")
            return True

    def query_fault_accounts(self) -> dict:
        """查询故障账号,默认1000条"""

        query_data = {
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 1000
                },
                "multi_search_way": "1",
                "id": "",
                "account_status": [0, 1, 3]
            },
            "query": "query(\n$id:String\n$node_name:String,\n$pagination: commonPageType,\n$fault_type:[Int],\n$supplier_name:String,\n$wechat_group_name:String,\n$start_time:String,\n$node_type:[Int],\n$pressure_test_status:[Int],\n$dial_status:[Int],\n$flow_user_id:[Int],\n$account_status:[Int],\n$fault_status:[Int],\n$claim_status:[Int]\n$host_name:String,\n$multi_search:String,\n$multi_search_way:String,\n){accountFaultList(\nid:$id,\npagination:$pagination,\nflow_user_id:$flow_user_id,\nsupplier_name:$supplier_name,\nwechat_group_name:$wechat_group_name,\nhost_name:$host_name,\npressure_test_status:$pressure_test_status,\ndial_status:$dial_status,\nnode_name:$node_name,\nfault_type:$fault_type,\nstart_time:$start_time,\nnode_type:$node_type,\nstatus:$account_status,\nfault_status:$fault_status\nclaim_status:$claim_status\nmulti_search:$multi_search\nmulti_search_way:$multi_search_way\n){\nid\naccount_id\nsvr_id\nsvr_name\nnode_name\nwechat_group_name\nsupplier_name\ndial_status\nfault_type\nrecover_status\nfault_start_time\nfault_end_time\nlevel\nusername\npwd\nvlan_id\npressure_test_status\ndial_log\npressure_test_log\nrtns_rate\ntcp_in_bw\nmac\nACname\nSCname\nfollower\nmax_limit\naccount_ip\nclaim_status\nplanning_type\ngateway\nnetmask\npush_remark\nfault_status\nfault_status_text\n}\n}\n    \n"
        }
        resp = self.fetch(url=self.query_url, json=query_data)
        total_count = resp.headers['x-pagination-total-count']
        current_page = resp.headers['x-pagination-current-page']
        page_count = resp.headers['x-pagination-page-count']
        per_page = resp.headers['x-pagination-per-page']
        account_fault_list = resp.json()['data']['accountFaultList']
        data = {
            "total_count": total_count,
            "current_page": current_page,
            "page_count": page_count,
            "per_page": per_page,
            "account_fault_list": account_fault_list
        }
        # logger.debug(account_fault_list)
        return data

    @staticmethod
    def identify_account_status(data: list) -> dict:
        """整理可以拨号和压测的账号
        dial_status拨号状态:
        0 -->拨号中
        1 -->拨号成功
        2 -->拨号失败
        3 -->待拨号

        pressure_test_status压测状态:
        0 -->待压测
        1 -->压测中
        2 -->压测成功
        3 -->压测失败

        recover_status恢复状态
        0 -->待恢复
        1 -->恢复中
        2 -->已完成
        """
        result = {
            "accounts_id_for_dialing": [],
            "accounts_id_for_stress_test": [],
            "dialing_accounts": [],
            "stress_test_accounts": []
        }
        logger.debug(f"白山:故障记录数量{len(data)}")
        for item in data:
            logger.debug(item)
            if item['dial_status'] == 1 and item['account_ip'] != "" and item['pressure_test_status'] in [0, 3]:
                result['accounts_id_for_stress_test'].append(item['id'])
            elif item['dial_status'] in [2, 3] or (item['dial_status'] == 1 and not item['account_ip']):
                result['accounts_id_for_dialing'].append(item['id'])
            elif item['dial_status'] == 0:
                result['dialing_accounts'].append(item)
            elif item['pressure_test_status'] == 1:
                result['stress_test_accounts'].append(item)

        return result

    def query_category_fault_account(self):
        """查询并分类故障账号"""
        fault_accounts_ticket = self.query_fault_accounts()
        # 整理故障单的账号,区分各种状态
        return self.identify_account_status(fault_accounts_ticket['account_fault_list'])

    def perform_accounts_stress_test(self, account_list: list) -> dict:
        """执行宽带压测"""
        if not account_list:
            logger.info("白山:没有可以执行压测的账号")
            return {}
        query_data = {
            "variables": {
                "ids": account_list
            },
            "query": """mutation _ ($ids: [Int] !, $pressure_type: Int) {accountPressureTest(ids: $ids, pressure_type:$pressure_type) {result}}"""
        }
        logger.info(f"白山:执行压测共计账号{len(account_list)}个")
        resp = self.fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            logger.info("白山:宽带测速提交成功")
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def perform_accounts_dialing(self, account_list: list) -> dict:
        """执行拨号"""
        if not account_list:
            logger.warning("白山:没有可以执行拨号的账号")
            return {}
        query_data = {
            "variables": {
                "fault_account_ids": account_list
            },
            "query": "mutation _ ($fault_account_ids: [Int!]) {accountDial(fault_account_ids: $fault_account_ids) {result}}"
        }
        logger.info(f"白山:执行拨号共计账号{len(account_list)}个")
        resp = self.fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            logger.info("白山:执行拨号成功")
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def query_fault_server(self) -> dict:
        """查询故障服务器"""
        query_data = {
            "query": "query($id: String $node_name: String,$push_fault_type: [Int],$hostname: String,$start_time: String,$end_time: String,$pagination: commonPageType,$supplier_name: String,$wechat_group_name: String,$server_status: [Int],$check_status: [Int],$follower: [Int],$claim_status: [Int],$multi_search: String,$multi_search_way: String) {faultSvrList(id: $id node_name: $node_name,push_fault_type: $push_fault_type,hostname: $hostname,start_time: $start_time,end_time: $end_time,supplier_name: $supplier_name,wechat_group_name: $wechat_group_name,status: $server_status,check_status: $check_status,follower: $follower,pagination: $pagination,claim_status: $claim_status,multi_search: $multi_search,multi_search_way: $multi_search_way) {id svr_id node_id  hostname account_num  node_name  priority push_fault_type fault_desc follower_name accountability fault_start_time fault_end_time claim_status status check_status bandwidth  port ip  sn  wechat_group_name supplier_name  is_power_off is_reinstall is_can_recover  is_baishan_server is_replace_hard_disk recover_apply_remark recover_remark small_check feed_log_op_user log_create_at  log  check {  id name  ename check_status  check_log } } }",
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 200
                },
                "multi_search_way": "1",
                "id": "",
                "server_status": [0, 1, 3]
            }
        }
        resp = self.fetch(url=self.query_url, json=query_data)
        logger.debug(resp.json())
        if resp.json()['code'] == 0:
            return resp.json()['data']['faultSvrList']
        else:
            raise Exception(resp.json()['msg'])

    def query_fault_node(self) -> dict:
        query_data = {
            "query": "\n    query(\n        $id: String $node_name: String,\n        $fault_type: [Int],\n        $wechat_group_name: String,\n        $supplier_name: String,\n        $fault_granularity: Int,\n        $start_time: String,\n        $start_time_end: String,\n        $end_time: String,\n        $end_time_end: String,\n        $node_type: [Int],\n        $node_status: [Int],\n        $flow_user_id: [Int],\n        $pagination: commonPageType,\n    ) {\n        faultNodeList(\n            id: $id,\n            wechat_group_name: $wechat_group_name,\n            supplier_name: $supplier_name,\n            node_name: $node_name,\n            flow_user_id: $flow_user_id,\n            fault_type: $fault_type,\n            fault_granularity: $fault_granularity,\n            start_time: $start_time,\n            start_time_end: $start_time_end,\n            end_time: $end_time,\n            end_time_end: $end_time_end,\n            node_type: $node_type,\n            status: $node_status,\n            pagination: $pagination\n        ) {\n            id\n            name\n            node_type\n            fault_type\n            fault_reason\n            status\n            fault_time\n            wechat_group_name\n            fault_owner\n            flow_user_id\n            flow_user_name\n            supplier_id\n            supplier_name\n            priority\n            describe\n            claim_status\n            create_time\n            end_time\n            cutover_id\n            isp_names\n            cutover_way_text\n            cutover_way\n            fault_type_text\n            countSvr\n            checkSvr\n            account_count\n            feed_log_op_user\n            log_create_at\n            log\n            apply_fault_reason\n            apply_fault_remark\n            apply_recover_remark\n        }\n    }\n    \n",
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 20
                },
                "node_status": [0, 3, 4],
                "id": ""
            }
        }
        resp = self.fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()['data']['faultNodeList']
        else:
            raise Exception(resp.json()['msg'])

    def auto_recover_accounts(self):
        """自动恢复故障"""
        fault_account_for_processing = self.query_category_fault_account()
        accounts_id_for_dialing = fault_account_for_processing['accounts_id_for_dialing']
        # 执行拨号
        self.perform_accounts_dialing(accounts_id_for_dialing)
        # 等待10分钟,查看是否还有拨号中的号码,没有后,就进入压测环节
        for _ in range(20):
            time.sleep(30)
            fault_account_for_processing = self.query_category_fault_account()
            dialing_accounts = fault_account_for_processing['dialing_accounts']
            if not dialing_accounts:
                logger.info("白山:拨号完成,开始压测")
                break
            logger.debug("白山:等待拨号完成")

        self.perform_accounts_stress_test(fault_account_for_processing['accounts_id_for_stress_test'])
        for _ in range(20):
            time.sleep(30)
            fault_account_for_processing = self.query_category_fault_account()
            stress_test_accounts = fault_account_for_processing['stress_test_accounts']

            if not stress_test_accounts:
                logger.info("白山:压测完成")
                break
            logger.debug("白山:等待压测完成")

        return self.query_fault_accounts()['account_fault_list']

    def perform_server_rack_stress_test(self, p_id: int, ip_type: str = "ipv4") -> dict:
        """执行机柜ipv6压测"""
        query_data = {
            "query": "mutation _ ($p_id: Int!, $type: Int!, $ip_type: [String],$servers: [BSCResourceMachineMutationType]) {bscResourceTestScan(p_id: $p_id,type: $type,ip_type: $ip_type,servers: $servers){result}}",
            "variables": {
                "p_id": p_id,
                "type": 1,
                "ip_type": [
                    ip_type
                ],
                "servers": []
            }

        }
        resp = self.fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            logger.info(f"白山:机柜{ip_type}压测提交成功")
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def query_server_rack_stress_result(self, p_id: int):
        """
        p_id,即为上架的id,获取方式为url链接:https://luohan.portal.baishancloud.com/#/resources_mng/detail/2717,最后的2717就是p_id
        查询机柜ipv6压测结果
        code对应含义
        0: 待压测
        320018: 压测中
        320019: 压测成功
        320020: 压测失败
        :return:
        """
        query_data = {
            "query": "\n   query( \n    $p_id: Int!,  \n    $status: Int!,\n    $error_status: String,\n    $env_status: Int,\n    $scanning_status: Int,\n    $dial_status: Int,\n    $stress_test_status: Int,\n    $next_status: Int\n    $orderBy:String\n    $pagination: commonPageType\n  ) {\n    bscResourceMachineInfoQuery(\n      p_id: $p_id,\n      status: $status,\n      error_status: $error_status,\n      env_status: $env_status,\n      scanning_status: $scanning_status,\n      dial_status: $dial_status,\n      stress_test_status: $stress_test_status,\n      next_status: $next_status\n      orderBy: $orderBy\n      pagination: $pagination\n    ) {\n      id,\n      p_id,\n      p_no,\n      sn,\n      re_sn,\n      cabinet,\n      cpus,\n      memorys,\n      networks,\n      SSD,\n      HDD,\n      public_net_addr,\n      private_net_addr,\n      dial_up_network_card,\n      deliver_status,\n      deliver_unicom_status,\n      tcp_in_upper_limit,\n      tcp_in_upper_v6_limit\n      tcp_out_lower_limit,\n      tcp_out_lower_v6_limit\n      map_port_22,\n      map_port_10022,\n      map_port_17251,\n      all_account,\n      account_status_suc,\n      account_status_v6_suc\n      account_status_error,\n      account_status_v6_error\n      status,\n      next_status,\n      env_status,\n      env_error_log\n      scanning_status,\n      scanning_remark,\n      owner,\n      dial_status,\n      stress_test_status,\n      stress_test_v6_status\n      restore_status\n      account_dial_status_suc\n      account_dial_status_error\n      restore_log\n      bandwidth\n      is_hardware_match\n      hardware_match_remark\n      idcs {\n        p_no,\n        server_id,\n        ip,\n        type,\n        cname,\n        key,\n      },\n      accounts {\n        id,\n        p_id,\n        p_no,\n        pppoe_type,\n        server_id,\n        account,\n        passwd,\n        vlan_id,\n        mask,\n        gateway,\n        tcp_in_upper_limit,\n        tcp_in_upper_v6_limit\n        tcp_out_lower_limit,\n        tcp_out_lower_v6_limit\n        retransmission_ratio,\n        retransmission_v6_ratio\n        packet_loss_v6_rate\n        packet_loss_rate,\n        created_at,\n        updated_at,\n        dial_status,\n        dial_ip,\n        dial_ip_v6,\n        account_network_name,\n        dial_status,\n        stress_test_status,\n        stress_test_v6_status\n        dial_error_log,\n        stress_test_remark,\n        stress_test_v6_remark\n        dial_remark,\n        mac,\n        ppp_servicename,\n        ppp_acname\n      },\n      detail {\n        cpu {\n          model,\n          cpu_thread,\n        },\n        memory {\n          size,\n        },\n        network {\n          id,\n          name,\n          mac,\n          bandwidth,\n          ips,\n          adapter_status\n        },\n        ssd {\n          sys_path,     \n          standard_capacity,\n          type,\n        },\n        hdd {\n          sys_path,      \n          standard_capacity,\n          type,\n        },\n      }\n    }\n  }\n  \n",
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 15
                },
                "p_id": p_id,
                "status": 1,
                "next_status": 0
            }
        }
        resp = self.fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def rack_auto_perform_stress_test(self, p_id: int, ip_type: str = "ipv4"):
        """上架流程:自动提交压测"""
        wait_time = 30
        for times in range(1000):
            result = self.query_server_rack_stress_result(p_id)
            # 提取所有的ipv6压测信息为一个列表
            if ip_type == "ipv4":
                stress_test_info = [server['stress_test_status'] for server in
                                    result['data']['bscResourceMachineInfoQuery']]
            else:
                stress_test_info = [server['stress_test_v6_status'] for server in
                                    result['data']['bscResourceMachineInfoQuery']]
            # 如果有机柜正在压测中,则等待
            if 320018 in stress_test_info:
                logger.info(f"白山:机柜{ip_type}压测中")
                time.sleep(wait_time)
            # 如果有机柜压测失败,则提交压测,并等待
            elif 320020 in stress_test_info or 0 in stress_test_info:
                logger.info(f"白山:机柜{ip_type}压测失败,提交压测")
                self.perform_server_rack_stress_test(p_id, ip_type=ip_type)
                time.sleep(wait_time)
            # 如果所有机柜压测成功,则退出
            elif all([item == 320019 for item in stress_test_info]):
                logger.info(f"白山:机柜{ip_type}压测成功,共计执行了{times}次")
                return
            else:
                logger.error(f"白山压测状态码为:{stress_test_info}")
        logger.error(f"白山:机柜{ip_type}压测失败")


if __name__ == "__main__":
    import os
    from utils.logger import setup_logger
    from pprint import pprint

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()

    baishan = Baishan("yicheng")
    baishan.rack_auto_perform_stress_test(2765,ip_type="ipv4")
