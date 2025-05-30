import time

import requests.exceptions

from .BasePlatform import Platform
from celery.utils.log import get_task_logger
from utils.crypto import encrypt_data_with_public_key
import os

logger = get_task_logger(__name__)


# logger = logging.getLogger(__name__)


class Baishan(Platform):
    def __init__(self, supplier: str = ""):
        assert supplier in ["vision_blue", "yicheng"], "只有vision_blue or yicheng "
        logger.info(f"白山:{supplier}初始化中...")
        self.login_supplier = supplier
        super().__init__()
        self.session_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                              f"sessions/baishan_{supplier}")
        self.query_url = "https://service-luohan.bs58i.baishancloud.com/agent/graphql/query"
        self.suppliers = self.login_info["suppliers"]

    def perform_login(self, supplier_id: int = 1355) -> None:
        """因为白山有2个公司主体,所以需要登录2次,分别获取2个公司的token"""
        self.before_login()
        login_url = "https://service-luohan-auth.bs58i.baishancdnx.com/login"

        login_data = {
            "client_id": "luohan",
            "phone": self.username,
            "password": self.password,
            "supplier_id": supplier_id
        }
        data = {
            "secret": encrypt_data_with_public_key(self._get_pub_key(), login_data)
        }
        login_resp = self.session.post(url=login_url, json=data, verify=False)
        # logger.debug(login_resp.json())
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
            logger.error(f"白山<{self.login_supplier}>:{login_resp.json()['msg']}")
            raise Exception(login_resp.json()['msg'])

    def _login(self):
        supplier_id = self.suppliers.get(self.login_supplier).get("supplier_id")
        self.perform_login(supplier_id)

    def _logout(self):
        data = {
            "query": "{logout {result}}\n"
        }
        self._fetch(self.query_url, json=data)

    def _get_pub_key(self) -> str:
        url = f"https://service-luohan-auth.bs58i.baishancdnx.com/publicKey"
        resp = self.session.get(url)
        if resp.json()['code'] == 200:
            pub_key_str = resp.json()['data']
            logger.debug(f"白山<{self.login_supplier}>:获取公钥成功,")
            return pub_key_str

    def session_is_unexpected(self, resp):
        super().session_is_unexpected(resp)
        # print(resp.status_code)
        # print(resp.text)
        try:
            if resp.json()['code'] == 401:
                logger.warning(f"白山<{self.login_supplier}>:登录过期,重新登录")
                return True
        except requests.exceptions.JSONDecodeError:
            return False

    def query_faulty_accounts(self) -> dict:
        """查询故障账号,默认1000条"""
        query_data = {
            "query": "\n    query(\n        $id: String $node_name: String,\n        $pagination: commonPageType,"
                     "\n        $fault_type: [Int],\n        $supplier_name: String,\n        $wechat_group_name: "
                     "String,\n        $start_time: String,\n        $node_type: [Int],\n        "
                     "$pressure_test_status: [Int],\n        $dial_status: [Int],\n        $flow_user_id: [Int],"
                     "\n        $account_status: [Int],\n        $fault_status: [Int],\n        $claim_status: [Int] "
                     "$host_name: String,\n        $multi_search: String,\n        $multi_search_way: String,"
                     "\n    ) {\n        accountFaultList(\n            id: $id,\n            pagination: "
                     "$pagination,\n            flow_user_id: $flow_user_id,\n            supplier_name: "
                     "$supplier_name,\n            wechat_group_name: $wechat_group_name,\n            host_name: "
                     "$host_name,\n            pressure_test_status: $pressure_test_status,\n            dial_status: "
                     "$dial_status,\n            node_name: $node_name,\n            fault_type: $fault_type,"
                     "\n            start_time: $start_time,\n            node_type: $node_type,\n            status: "
                     "$account_status,\n            fault_status: $fault_status,\n            claim_status: "
                     "$claim_status,\n            multi_search: $multi_search,\n            multi_search_way: "
                     "$multi_search_way\n        ) {\n            id\n            account_id\n            svr_id\n    "
                     "        svr_name\n            node_name\n            ipv4_type\n            ipv6_type\n         "
                     "   net_type\n            ipv6\n            ipv6_pressure_test_status\n            "
                     "ipv6_retransmission\n            ipv6_tcp_in_bw\n            ipv6_pressure_test_log\n           "
                     " wechat_group_name\n            supplier_name\n            dial_status\n            "
                     "fault_type\n            recover_status\n            fault_start_time\n            "
                     "fault_end_time\n            level\n            username\n            pwd\n            vlan_id\n "
                     "           pressure_test_status\n            dial_log\n            pressure_test_log\n          "
                     "  rtns_rate\n            tcp_in_bw\n            mac\n            ACname\n            SCname\n   "
                     "         follower\n            max_limit\n            account_ip\n            claim_status\n    "
                     "        planning_type\n            gateway\n            netmask\n            remark\n           "
                     " push_remark\n            fault_status\n            fault_status_text\n        }\n    }\n    \n",
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 1000
                },
                "multi_search_way": "1",
                "id": "",
                "account_status": [
                    0,
                    1,
                    3
                ]
            }
        }

        resp = self._fetch(url=self.query_url, json=query_data)
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

    def _identify_account_status(self, data: list) -> dict:
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

        planning_type 网络类型
        "static"/"pppoe"
        """
        result = {
            "accounts_id_for_dialing": [],
            "accounts_id_for_stress_test": [],
            "dialing_accounts": [],
            "stress_test_accounts": []
        }
        logger.debug(f"白山<{self.login_supplier}>:故障记录数量{len(data)}")
        for item in data:
            logger.debug(item)
            if item['planning_type'] == "static":
                result['accounts_id_for_stress_test'].append(item['id'])
            else:
                if (item['dial_status'] == 1 and item['account_ip'] and item['pressure_test_status'] in [0, 3]):
                    result['accounts_id_for_stress_test'].append(item['id'])
                elif item['dial_status'] in [2, 3] or (item['dial_status'] == 1 and not item['account_ip']):
                    result['accounts_id_for_dialing'].append(item['id'])
                elif item['dial_status'] == 0:
                    result['dialing_accounts'].append(item)
                elif item['pressure_test_status'] == 1:
                    result['stress_test_accounts'].append(item)

        return result

    @staticmethod
    def _filter_account_ids_for_ipv4_pressure_test(data: list) -> list:
        """
        遍历data中的账号,如果dial_status为2,就将符合条件的账号组成一个账号列表返回
        :param data: 节点下的故障账号
        :return: 状态为压测成功的账号
        """
        # return [item['id'] for item in data if item['dial_status'] == 2]
        rest = []
        for item in data:
            if item['dial_status'] == 2 and item['pressure_test_status'] in [0, 3]:
                rest.append(item['id'])
        return rest

    @staticmethod
    def _filter_account_ids_for_ipv6_pressure_test(data: list) -> list:
        return [item['id'] for item in data if item['ipv6'] and item['ipv6_pressure_test_status'] in [0, 3]]

    def _query_and_category_fault_accounts(self):
        """查询并分类故障账号"""
        fault_accounts_ticket = self.query_faulty_accounts()
        # 整理故障单的账号,区分各种状态
        return self._identify_account_status(fault_accounts_ticket['account_fault_list'])

    def perform_accounts_stress_test_in_account_failure(self, account_list: list, ip_type: str = "ipv4") -> dict:
        """执行宽带压测"""
        if not account_list:
            logger.info(f"白山<{self.login_supplier}>:没有可以执行压测的账号")
            return {}
        
        # 如果是IPv6压测，需要先过滤掉不支持IPv6的账户
        if ip_type == "ipv6":
            # 获取当前故障账户的详细信息
            current_fault_accounts = self.query_faulty_accounts()['account_fault_list']
            # 创建id到账户详情的映射
            account_detail_map = {item['id']: item for item in current_fault_accounts}
            # 过滤掉没有IPv6地址或IPv6压测状态不可用的账户
            filtered_account_list = []
            for account_id in account_list:
                if account_id in account_detail_map:
                    account_detail = account_detail_map[account_id]
                    # 检查账户是否有IPv6地址且IPv6压测状态可用
                    if (account_detail.get('ipv6') and 
                        account_detail.get('ipv6_pressure_test_status') in [0, 3]):
                        filtered_account_list.append(account_id)
                    else:
                        logger.warning(f"白山<{self.login_supplier}>:账号{account_id}无IPv6地址或IPv6压测状态不可用，跳过IPv6压测")
                else:
                    logger.warning(f"白山<{self.login_supplier}>:账号{account_id}未找到详细信息，跳过IPv6压测")
            
            account_list = filtered_account_list
            if not account_list:
                logger.warning(f"白山<{self.login_supplier}>:过滤后没有可以执行IPv6压测的账号")
                return {}
        
        query_data = {
            "query": "mutation _ ($ids: [Int] !, $pressure_type: Int) {\n        accountPressureTest(ids: $ids, "
                     "pressure_type:$pressure_type) {\n            result\n        }\n    }\n",
            "variables": {
                "ids": account_list,
                "pressure_type": 0 if ip_type == "ipv4" else 1
            }
        }
        logger.info(f"白山<{self.login_supplier}>:执行{ip_type}压测共计账号{len(account_list)}个")
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            logger.info(f"白山<{self.login_supplier}>:{ip_type}宽带测速提交成功")
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def perform_accounts_dialing_in_account_failure(self, account_list: list) -> dict:
        """执行拨号"""
        if not account_list:
            logger.warning(f"白山<{self.login_supplier}>:没有可以执行拨号的账号")
            return {}
        query_data = {
            "variables": {
                "fault_account_ids": account_list
            },
            "query": "mutation _ ($fault_account_ids: [Int!]) {accountDial(fault_account_ids: $fault_account_ids) {"
                     "result}}"
        }
        logger.info(f"白山<{self.login_supplier}>:执行拨号共计账号{len(account_list)}个")
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            logger.info(f"白山<{self.login_supplier}>:执行拨号成功")
            return resp.json()
        else:
            raise Exception({"accounts": account_list, "msg": resp.json()['msg']})

    def query_faulty_servers(self) -> list:
        """查询故障服务器"""
        logger.info("查询故障服务器")
        query_data = {
            "query": "query($id: String $node_name: String,$push_fault_type: [Int],$hostname: String,$start_time: "
                     "String,$end_time: String,$pagination: commonPageType,$supplier_name: String,$wechat_group_name: "
                     "String,$server_status: [Int],$check_status: [Int],$follower: [Int],$claim_status: [Int],"
                     "$multi_search: String,$multi_search_way: String) {faultSvrList(id: $id node_name: $node_name,"
                     "push_fault_type: $push_fault_type,hostname: $hostname,start_time: $start_time,end_time: "
                     "$end_time,supplier_name: $supplier_name,wechat_group_name: $wechat_group_name,"
                     "status: $server_status,check_status: $check_status,follower: $follower,pagination: $pagination,"
                     "claim_status: $claim_status,multi_search: $multi_search,multi_search_way: $multi_search_way) {"
                     "id svr_id node_id  hostname account_num  node_name  priority push_fault_type fault_desc "
                     "follower_name accountability fault_start_time fault_end_time claim_status status check_status "
                     "bandwidth  port ip  sn  wechat_group_name supplier_name  is_power_off is_reinstall "
                     "is_can_recover  is_baishan_server is_replace_hard_disk recover_apply_remark recover_remark "
                     "small_check feed_log_op_user log_create_at  log  check {  id name  ename check_status  "
                     "check_log } } }",
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
        resp = self._fetch(url=self.query_url, json=query_data)
        # logger.debug(resp.json())
        if resp.json()['code'] == 0:
            return resp.json()['data']['faultSvrList']
            # return self.filter_servers_that_can_be_handle(fault_servers)
        else:
            raise Exception(resp.json()['msg'])

    def query_faulty_nodes(self) -> dict:
        """查询故障节点,主要查询字段为故障节点的id,即node_feedback_id"""
        query_data = {
            "query": "\n    query(\n        $id: String $node_name: String,\n        $fault_type: [Int],\n        "
                     "$wechat_group_name: String,\n        $supplier_name: String,\n        $fault_granularity: Int,"
                     "\n        $start_time: String,\n        $start_time_end: String,\n        $end_time: String,"
                     "\n        $end_time_end: String,\n        $node_type: [Int],\n        $node_status: [Int],"
                     "\n        $flow_user_id: [Int],\n        $pagination: commonPageType,\n    ) {\n        "
                     "faultNodeList(\n            id: $id,\n            wechat_group_name: $wechat_group_name,"
                     "\n            supplier_name: $supplier_name,\n            node_name: $node_name,\n            "
                     "flow_user_id: $flow_user_id,\n            fault_type: $fault_type,\n            "
                     "fault_granularity: $fault_granularity,\n            start_time: $start_time,\n            "
                     "start_time_end: $start_time_end,\n            end_time: $end_time,\n            end_time_end: "
                     "$end_time_end,\n            node_type: $node_type,\n            status: $node_status,"
                     "\n            pagination: $pagination\n        ) {\n            id\n            name\n          "
                     "  node_type\n            fault_type\n            fault_reason\n            status\n            "
                     "fault_time\n            wechat_group_name\n            fault_owner\n            flow_user_id\n  "
                     "          flow_user_name\n            supplier_id\n            supplier_name\n            "
                     "priority\n            describe\n            claim_status\n            create_time\n            "
                     "end_time\n            cutover_id\n            isp_names\n            cutover_way_text\n         "
                     "   cutover_way\n            fault_type_text\n            countSvr\n            checkSvr\n       "
                     "     account_count\n            feed_log_op_user\n            log_create_at\n            log\n  "
                     "          apply_fault_reason\n            apply_fault_remark\n            "
                     "apply_recover_remark\n        }\n    }\n    \n",
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 20
                },
                "node_status": [0, 3, 4],
                "id": ""
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()['data']['faultNodeList']
        else:
            raise Exception(resp.json()['msg'])

    def query_faulty_servers_in_node_failure(self, node_feedback_id: int) -> list:
        # TODO: 如果有状态为...之中的,需要提出,说明当时的情况是在手工修复
        """查询故障节点下的故障服务器"""
        query_data = {
            "query": "\n    query (\n        $fault_receipt_id: Int\n        $check_status: [Int]\n        $status: ["
                     "Int]\n        $fault_status: [Int]\n        $multi_search: String\n        $multi_search_way: "
                     "Int\n        $pagination: commonPageType\n    ) {\n        faultNodeSvrList(\n            "
                     "fault_receipt_id: $fault_receipt_id\n            check_status: $check_status\n            "
                     "status: $status\n            multi_search: $multi_search\n            multi_search_way: "
                     "$multi_search_way\n            fault_status: $fault_status\n            pagination: "
                     "$pagination\n        ) {\n            id\n            svr_id\n            node_id\n            "
                     "hostname\n            node_feedback_id\n            account_num\n            node_name\n        "
                     "    priority\n            push_fault_type\n            fault_desc\n            follower_name\n  "
                     "          accountability\n            fault_start_time\n            fault_end_time\n            "
                     "claim_status\n            status\n            check_status\n            bandwidth\n            "
                     "port\n            ip\n            sn\n            wechat_group_name\n            "
                     "supplier_name\n            check_log\n            is_power_off\n            is_reinstall\n      "
                     "      is_can_recover\n            is_baishan_server\n            is_replace_hard_disk\n         "
                     "   recover_apply_remark\n            recover_remark\n            fault_status\n            "
                     "fault_status_text\n            small_check\n            feed_log_op_user\n            "
                     "log_create_at\n            log\n            check {\n                id\n                name\n "
                     "               ename\n            }\n        }\n    }\n    \n    \n",
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 30
                },
                "fault_receipt_id": node_feedback_id,
                "multi_search_way": 1
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()['data']['faultNodeSvrList']
        else:
            raise Exception(resp.json()['msg'])

    @staticmethod
    def evaluate_recovery_conditions_in_node_failure(data: list) -> bool:
        """
        检查list的item里面的check_status是否等于1,如果等于1就是检测合格了,如果主要item的check_status等于1的数量大于list的60%,就满足恢复条件
        :param data:
        :return:
        """
        is_checked_servers = list(filter(lambda x: x['check_status'] == 1, data))
        return len(is_checked_servers) / len(data) >= 0.6

    def perform_server_connectivity_checking(self, fault_ids: list) -> dict:
        """执行连通性检测"""
        query_data = {
            "query": "mutation _ (\n        $ids: [Int]\n    ) {\n        faultSvrDetective(\n            ids: $ids\n "
                     "       )\n    }\n",
            "variables": {
                "ids": fault_ids
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def perform_server_hardware_checking(self, fault_ids: list) -> dict:
        """执行硬件检测"""
        query_data = {
            "query": "mutation _ (\n    $fault_order_ids:[Int]!\n){\n    faultSvrHardwareDetection(\n        "
                     "fault_order_ids:$fault_order_ids\n    )\n}\n",
            "variables": {
                "fault_order_ids": fault_ids
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def perform_dialing_in_node_failure(self, faulty_server_id_list: list, node_feedback_id: int) -> dict:
        """执行拨号"""
        query_data = {
            "query": "mutation _ (\n        $fault_receipt_id: Int\n        $fault_svr_order_ids: [Int]\n        "
                     "$fault_account_ids: [Int]\n        $is_all: Boolean\n    ) {\n        faultNodeDial(\n          "
                     "  is_all: $is_all\n            fault_receipt_id: $fault_receipt_id\n            "
                     "fault_svr_order_ids: $fault_svr_order_ids\n            fault_account_ids: $fault_account_ids\n  "
                     "          \n        ) {\n            result\n        }\n    }\n",
            "variables": {
                "fault_receipt_id": node_feedback_id,
                "is_all": False,
                "fault_svr_order_ids": faulty_server_id_list
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def perform_stress_test_in_node_failure(self, node_feedback_id: int, ip_type: str = "ipv4") -> dict:
        """
        查询节点下面可以进行压测的账号,然后执行压测
        :param node_feedback_id: 故障id
        :param ip_type:ipv4 or ipv6
        :return: 返回的压测提交是否成功结果
        """
        if ip_type == 'ipv4':
            pressure_type = 0
        elif ip_type == 'ipv6':
            pressure_type = 1
        else:
            raise ValueError("Invalid test type provided. Use 'ipv4' or 'ipv6'")
            # 1,先查询节点下的故障账号的状态
        account_status = self.query_account_status_in_node_failure(node_feedback_id)
        # 2,整理可以压测的账号
        accounts_id_for_stress_test = self._filter_account_ids_for_ipv4_pressure_test(account_status)
        query_data = {
            "query": "mutation _ (\n        $fault_receipt_id: Int,\n        $fault_svr_order_ids: [Int],\n        "
                     "$fault_account_ids: [Int],\n        $is_all: Boolean,\n        $pressure_type: Int\n    ) {\n   "
                     "     faultNodePressTest(\n            fault_receipt_id: $fault_receipt_id,\n            "
                     "fault_svr_order_ids: $fault_svr_order_ids,\n            fault_account_ids: $fault_account_ids,"
                     "\n            is_all: $is_all,\n            pressure_type:$pressure_type\n        )\n    }\n",
            "variables": {
                "fault_receipt_id": node_feedback_id,
                "is_all": False,
                "fault_account_ids": accounts_id_for_stress_test,
                "pressure_type": pressure_type
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def query_account_status_in_node_failure(self, node_feedback_id: int) -> list:
        query_data = {
            "query": "\n    query(\n        $fault_receipt_id: Int,\n        $pressure_test_status: [Int],\n        "
                     "$dial_status: [Int],\n        $pagination: commonPageType,\n        $account_id: Int "
                     "$multi_search: String\n    ) {\n        faultNodeAccountList(\n            fault_receipt_id: "
                     "$fault_receipt_id,\n            pagination: $pagination,\n            pressure_test_status: "
                     "$pressure_test_status,\n            dial_status: $dial_status,\n            account_id: "
                     "$account_id,\n            multi_search: $multi_search\n        ) {\n            id\n            "
                     "account_id\n            dial_status\n            p_type\n            svr_order_id\n            "
                     "fault_start_time\n            ipv4_type\n            ipv6_type\n            net_type\n          "
                     "  ipv6\n            ipv6_pressure_test_status\n            ipv6_retransmission\n            "
                     "ipv6_tcp_in_bw\n            ipv6_pressure_test_log\n            fault_end_time\n            "
                     "retransmission\n            username\n            pwd\n            vlan_id\n            "
                     "pressure_test_status\n            tcp_in_bw\n            mac\n            dial_log\n            "
                     "remark\n            pressure_test_log\n            ACname\n            SCname\n            ip\n "
                     "           plan_bw\n            gateway\n            netmask\n            consume_time\n        "
                     "    hostname\n            svr_order_status\n        }\n    }\n    \n",
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 500
                },
                "fault_receipt_id": node_feedback_id
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()['data']['faultNodeAccountList']
        else:
            raise Exception(resp.json()['msg'])

    def submit_node_recovery_application(self, node_feedback_id: int, faulty_server_id_list: list) -> dict:
        """提交节点恢复申请"""

        server_application_template = {
            "accountability": 0,
            "is_reinstall": 0,
            "is_power_off": 0,
            "is_baishan_server": 0,
            "is_replace_hard_disk": 0,
            "comment": "电力故障"
        }
        query_data = {
            "query": "mutation _ (\n        $fault_receipt_id: Int\n        $accountability: Int\n        "
                     "$node_fault_desc_id: Int\n        $fault_reason: String\n        $fault_svr_order_applies:["
                     "faultNodeSvrApplyType]\n        $supplier_name: String\n    ) {\n        faultNodeRecovery(\n   "
                     "         fault_receipt_id: $fault_receipt_id\n            accountability: $accountability\n     "
                     "       node_fault_desc_id: $node_fault_desc_id\n            fault_reason: $fault_reason\n       "
                     "     fault_svr_order_applies: $fault_svr_order_applies\n            supplier_name: "
                     "$supplier_name\n        ) {\n            result\n        }\n    }\n",
            "variables": {
                "fault_receipt_id": node_feedback_id,
                "accountability": 0,
                "node_fault_desc_id": 341,
                "fault_reason": "电力故障",
                "fault_svr_order_applies": list(
                    map(lambda x: {**server_application_template, **{"fault_id": x}}, faulty_server_id_list)),
                "supplier_name": "数云-视觉蓝-技术群-ruby"
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def auto_recover_nodes(self) -> None:
        """
        自动恢复节点
        :return:
        """
        # 1,查询故障节点
        faulty_nodes = self.query_faulty_nodes()
        # 2,遍历故障节点
        for node in faulty_nodes:
            # 3,查询故障节点下的故障服务器
            faulty_servers = self.query_faulty_servers_in_node_failure(node['id'])
            faulty_server_ids = list(map(lambda x: x.get("id"), faulty_servers))
            # 4,执行连通性检测
            self.perform_server_connectivity_checking(faulty_server_ids)
            # 5,执行硬件检测
            self.perform_server_hardware_checking(faulty_server_ids)
            # 6,执行拨号
            self.perform_dialing_in_node_failure(faulty_server_ids, node['id'])
            # 7,执行压测
            time.sleep(60 * 5)
            self.perform_stress_test_in_node_failure(node['id'])
            time.sleep(60 * 10)
            self.perform_stress_test_in_node_failure(node['id'], "ipv6")
            time.sleep(60 * 10)
            # 8,查询是否满足恢复条件
            server_status = self.query_faulty_servers_in_node_failure(node['id'])
            # FIXME: 下面有异常,需要处理
            # File "/Users/a.huang/DEV/failure_monitor/checker/webpage_checker/sites/baishan.py", line 362, in <lambda>
            #     is_checked_servers = list(filter(lambda x: x['check_status'] == 1, data))
            # KeyError: 'check_status'
            if self.evaluate_recovery_conditions_in_node_failure(server_status):
                # 9,提交恢复申请
                self.submit_node_recovery_application(node['id'], faulty_server_ids)
                logger.info(f"白山<{self.login_supplier}>:节点{node['id']}提交恢复申请成功")
            else:
                logger.info(f"白山<{self.login_supplier}>:节点{node['id']}不满足恢复条件")

    def perform_server_stress_test_in_server_rack_mounting(self, p_id: int, ip_type: str = "ipv4") -> dict:
        """执行机柜ipv6压测"""
        query_data = {
            "query": "mutation _ ($p_id: Int!, $type: Int!, $ip_type: [String],$servers: ["
                     "BSCResourceMachineMutationType]) {bscResourceTestScan(p_id: $p_id,type: $type,"
                     "ip_type: $ip_type,servers: $servers){result}}",
            "variables": {
                "p_id": p_id,
                "type": 1,
                "ip_type": [
                    ip_type
                ],
                "servers": []
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        try:
            logger.info(resp.json())
        except requests.exceptions.JSONDecodeError:
            return {}

        if resp.json()['code'] == 0:
            logger.info(f"白山<{self.login_supplier}>:机柜{ip_type}压测提交成功")
            return resp.json()
        elif resp.json()['code'] == 102001:
            logger.info(f"白山<{self.login_supplier}>:机柜{ip_type}压测中,请勿重复提交")
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def query_server_stress_result_in_server_rack_mounting(self, p_id: int):
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
            "query": "\n   query( \n    $p_id: Int!,  \n    $status: Int!,\n    $error_status: String,"
                     "\n    $env_status: Int,\n    $scanning_status: Int,\n    $dial_status: Int,"
                     "\n    $stress_test_status: Int,\n    $next_status: Int\n    $orderBy:String\n    $pagination: "
                     "commonPageType\n  ) {\n    bscResourceMachineInfoQuery(\n      p_id: $p_id,\n      status: "
                     "$status,\n      error_status: $error_status,\n      env_status: $env_status,"
                     "\n      scanning_status: $scanning_status,\n      dial_status: $dial_status,"
                     "\n      stress_test_status: $stress_test_status,\n      next_status: $next_status\n      "
                     "orderBy: $orderBy\n      pagination: $pagination\n    ) {\n      id,\n      p_id,\n      p_no,"
                     "\n      sn,\n      re_sn,\n      cabinet,\n      cpus,\n      memorys,\n      networks,"
                     "\n      SSD,\n      HDD,\n      public_net_addr,\n      private_net_addr,"
                     "\n      dial_up_network_card,\n      deliver_status,\n      deliver_unicom_status,"
                     "\n      tcp_in_upper_limit,\n      tcp_in_upper_v6_limit\n      tcp_out_lower_limit,"
                     "\n      tcp_out_lower_v6_limit\n      map_port_22,\n      map_port_10022,"
                     "\n      map_port_17251,\n      all_account,\n      account_status_suc,"
                     "\n      account_status_v6_suc\n      account_status_error,\n      account_status_v6_error\n     "
                     " status,\n      next_status,\n      env_status,\n      env_error_log\n      scanning_status,"
                     "\n      scanning_remark,\n      owner,\n      dial_status,\n      stress_test_status,"
                     "\n      stress_test_v6_status\n      restore_status\n      account_dial_status_suc\n      "
                     "account_dial_status_error\n      restore_log\n      bandwidth\n      is_hardware_match\n      "
                     "hardware_match_remark\n      idcs {\n        p_no,\n        server_id,\n        ip,"
                     "\n        type,\n        cname,\n        key,\n      },\n      accounts {\n        id,"
                     "\n        p_id,\n        p_no,\n        pppoe_type,\n        server_id,\n        account,"
                     "\n        passwd,\n        vlan_id,\n        mask,\n        gateway,\n        "
                     "tcp_in_upper_limit,\n        tcp_in_upper_v6_limit\n        tcp_out_lower_limit,"
                     "\n        tcp_out_lower_v6_limit\n        retransmission_ratio,\n        "
                     "retransmission_v6_ratio\n        packet_loss_v6_rate\n        packet_loss_rate,"
                     "\n        created_at,\n        updated_at,\n        dial_status,\n        dial_ip,"
                     "\n        dial_ip_v6,\n        account_network_name,\n        dial_status,\n        "
                     "stress_test_status,\n        stress_test_v6_status\n        dial_error_log,\n        "
                     "stress_test_remark,\n        stress_test_v6_remark\n        dial_remark,\n        mac,"
                     "\n        ppp_servicename,\n        ppp_acname\n      },\n      detail {\n        cpu {\n       "
                     "   model,\n          cpu_thread,\n        },\n        memory {\n          size,\n        },"
                     "\n        network {\n          id,\n          name,\n          mac,\n          bandwidth,"
                     "\n          ips,\n          adapter_status\n        },\n        ssd {\n          sys_path,     "
                     "\n          standard_capacity,\n          type,\n        },\n        hdd {\n          sys_path, "
                     "     \n          standard_capacity,\n          type,\n        },\n      }\n    }\n  }\n  \n",
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
        resp = self._fetch(url=self.query_url, json=query_data)
        logger.info(resp.json())
        if resp.json()['code'] == 0:
            return resp.json()
        elif resp.json()['code'] == 102001:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def perform_stress_test_in_server_rack_mounting(self, p_id: int, ip_type: str = "ipv4"):
        """上架流程:自动提交压测"""
        wait_time = 60
        for times in range(1000):
            result = self.query_server_stress_result_in_server_rack_mounting(p_id)
            if result == {}:
                time.sleep(wait_time)
                continue
            # 提取所有的ipv6压测信息为一个列表
            if ip_type == "ipv4":
                stress_test_info = [server['stress_test_status'] for server in
                                    result['data']['bscResourceMachineInfoQuery']]
            else:
                stress_test_info = [server['stress_test_v6_status'] for server in
                                    result['data']['bscResourceMachineInfoQuery']]
            # 如果有机柜正在压测中,则等待
            # if 320018 in stress_test_info:
            if 320018 in stress_test_info:
                logger.info(f"<{self.suppliers}>机柜{ip_type}压测中")
                time.sleep(wait_time)
            # 如果有机柜压测失败,则提交压测,并等待
            elif 320020 in stress_test_info or 0 in stress_test_info:
                logger.info(f"白山<{self.login_supplier}>:机柜{ip_type}压测失败,提交压测")
                self.perform_server_stress_test_in_server_rack_mounting(p_id, ip_type=ip_type)
                time.sleep(wait_time)
            # 如果所有机柜压测成功,则退出
            elif all([item == 320019 for item in stress_test_info]):
                logger.info(f"白山<{self.login_supplier}>:机柜{ip_type}压测成功,共计执行了{times}次")
                return
            else:
                logger.error(f"白山压测状态码为:{stress_test_info}")
        logger.error(f"白山<{self.login_supplier}>:机柜{ip_type}压测失败")

    def auto_recover_accounts(self):
        """
        自动恢复账号
        :return:
        """
        # fault_account_for_processing = self._query_and_category_fault_accounts()
        fault_account_for_processing = []
        account_ids = [item['id'] for item in self.query_faulty_accounts()["account_fault_list"]]
        # accounts_id_for_dialing = fault_account_for_processing['accounts_id_for_dialing']
        # 执行拨号
        self.perform_accounts_dialing_in_account_failure(account_ids)
        # 等待10分钟,查看是否还有拨号中的号码,没有后,就进入压测环节
        time.sleep(5* 60)

        fault_account_for_processing = self._query_and_category_fault_accounts()
        dialing_accounts = fault_account_for_processing['dialing_accounts']
        if not dialing_accounts:
            logger.info(f"白山<{self.login_supplier}>:拨号完成,开始ipv4压测")

        # IPv4压测
        self.perform_accounts_stress_test_in_account_failure(
            fault_account_for_processing['accounts_id_for_stress_test'])

        time.sleep(10 * 60)

        # IPv6压测 - 获取最新的故障账户信息并执行IPv6压测
        try:
            self.perform_accounts_stress_test_in_account_failure(
                fault_account_for_processing['accounts_id_for_stress_test'], ip_type="ipv6")
        except Exception as e:
            logger.error(f"白山<{self.login_supplier}>:IPv6压测执行失败: {str(e)}")
            # 继续执行，不中断整个流程
        
        time.sleep(10 * 60)

        # fault_account_for_processing = self._query_and_category_fault_accounts()
        # stress_test_accounts = fault_account_for_processing['stress_test_accounts']

        logger.info(f"白山<{self.login_supplier}>:压测完成")

        return self.query_faulty_accounts()['account_fault_list']

    def query_account_status_in_server_failure(self, fault_id: int, server_id: int) -> list:
        """
        dial_status: 拨号状态
            0: 没有拨号
            1: 拨号中
            2: 拨号成功
            3: 拨号失败
        pressure_test_status: ipv4 压测
            0: 待压测
            1: 压测中
            2: 压测成功
            3: 压测失败

        ipv6_pressure_test_status: ipv6 压测
            0: 待压测
            1: 压测中
            2: 压测成功
            3: 压测失败

        """
        query_data = {
            "query": "\n    query(\n        $id: Int,\n        $svr_id: Int,\n        $pressure_test_status: [Int],"
                     "\n        $dial_status: [Int],\n        $pagination: commonPageType,\n        $account_id: "
                     "Int\n    ) {\n        faultSvrAccountList(\n            id: $id,\n            pagination: "
                     "$pagination,\n            svr_id: $svr_id,\n            pressure_test_status: "
                     "$pressure_test_status,\n            dial_status: $dial_status,\n            account_id: "
                     "$account_id\n        ) {\n            id\n            account_id\n            dial_status\n     "
                     "       p_type\n            fault_start_time\n            fault_end_time\n            "
                     "retransmission\n            username\n            ipv4_type\n            ipv6_type\n            "
                     "ipv6\n            net_type\n            ipv6_pressure_test_status\n            "
                     "ipv6_retransmission\n            ipv6_tcp_in_bw\n            ipv6_pressure_test_log\n           "
                     " pwd\n            remark\n            vlan_id\n            pressure_test_status\n            "
                     "tcp_in_bw\n            mac\n            dial_log\n            pressure_test_log\n            "
                     "acname\n            scname\n            ip\n            plan_bw\n            gateway\n          "
                     "  netmask\n            consume_time\n            \n        }\n    }\n    \n",
            "variables": {
                "pagination": {
                    "current_page": 1,
                    "page_size": 50
                },
                "id": fault_id,
                "svr_id": server_id,
                "dial_status": None,
                "pressure_test_status": None,
                "account_id": None
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()['data']['faultSvrAccountList']
        else:
            raise Exception(resp.json()['msg'])

    @staticmethod
    def extract_ids(data_list: list) -> tuple:
        # 使用列表推导式分别提取account_id和id
        account_ids = [item['account_id'] for item in data_list]
        ids = [item['id'] for item in data_list]
        return ids, account_ids

    def perform_dialing_in_server_failure(self, account_ids: list, ids: list) -> dict:
        query_data = {
            "query": "mutation _ (\n        $fault_order_account_ids: [Int],\n        $account_ids: [Int]\n    ) {\n  "
                     "      faultSvrStep(\n            fault_order_account_ids: $fault_order_account_ids,\n           "
                     " account_ids: $account_ids\n        )\n    }\n",
            "variables": {
                "account_ids": account_ids,
                "fault_order_account_ids": ids
            }
        }
        """执行拨号"""

        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            logger.warning(resp.json()['msg'])

    def perform_pressure_test_in_server_failure(self, fault_id: int, fault_account_ids: list,
                                                ip_type: str = "ipv4") -> dict:
        """执行压测"""
        pressure_type = 0 if ip_type == "ipv4" else 1
        query_data = {
            "query": "mutation _ ($pressure_test_params: [svrPressureTestType!],$pressure_type:Int) {\n        "
                     "svrPressureTest(pressure_test_params: $pressure_test_params,pressure_type:$pressure_type) {\n   "
                     "         result\n        }\n    }\n",
            "variables": {
                "pressure_test_params": [
                    {
                        "fault_id": fault_id,
                        "fault_account_ids": fault_account_ids
                    }
                ],
                "pressure_type": pressure_type
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    @staticmethod
    def filter_servers_that_can_be_recovered(servers_info: list) -> list:
        result = []
        for item in servers_info:
            # Check if all 'check_status' in 'check' are 3
            status_all_three = all(check['check_status'] == 3 for check in item['check'])
            result.append(item['id']) if status_all_three else None
        return result

    @staticmethod
    def filter_servers_that_can_be_handle(servers_info: list) -> list:
        """
        check_status:
            0: 未检测
            1: 检测中
            2: 检测不通过
            3: 检测通过
        """
        result = []
        for item in servers_info:
            # 跳过检测中的服务器
            if any(check['check_status'] == 1 for check in item['check']):
                pass
            result.append(item)
        return result

    def commit_recovery_application_in_server_failure(self, fault_id: int) -> dict:
        """提交恢复申请"""
        query_data = {
            "query": "mutation _ (\n        $fault_id: Int!\n        $is_can_recover: Int!\n        $is_reinstall: Int\n        $is_power_off: Int\n        $is_baishan_server: Int\n        $is_replace_hard_disk: Int\n        $accountability: Int\n        $is_replace_new_svr: Int\n        $comment: String\n        $supplier_name: String\n    ) {\n        svrRecoverApply(\n            fault_id: $fault_id\n            is_can_recover: $is_can_recover\n            is_reinstall: $is_reinstall\n            is_power_off: $is_power_off\n            is_baishan_server: $is_baishan_server\n            is_replace_hard_disk: $is_replace_hard_disk\n            accountability: $accountability\n            is_replace_new_svr:$is_replace_new_svr\n            comment: $comment\n            supplier_name: $supplier_name\n        ) {\n            result\n        }\n    }\n",
            "variables": {
                "fault_id": fault_id,
                "is_can_recover": 1,
                "is_baishan_server": 1,
                "accountability": 0,
                "is_reinstall": 0,
                "is_power_off": 0,
                "is_replace_hard_disk": 0,
                "comment": "电源故障",
                "supplier_name": "视觉蓝-技术群-ruby"
            }
        }
        resp = self._fetch(url=self.query_url, json=query_data)
        if resp.json()['code'] == 0:
            return resp.json()
        else:
            raise Exception(resp.json()['msg'])

    def auto_recover_servers(self):
        """自动恢复故障"""
        logger.info("自动恢复服务器开始")
        faulty_servers = self.query_faulty_servers()
        logger.debug(f"故障服务器数量{len(faulty_servers)}")
        server_info_list = []
        for server in faulty_servers:
            fault_id = server['id']
            server_id = server['svr_id']
            server_name = server['hostname']
            is_pending = server['status']
            if is_pending == 1:
                logger.debug(f"{server_name}正在处理中")
                continue
            server_info_list.append((fault_id, server_id, server_name))
            logger.debug(f"当前hostname：{server['hostname']}")
            if server['check'][2]['check_status'] in [0, 2]:  # 未检测0或检测不通过2, 执行连通性检测,检测中1 和 检测成功3 跳过
                self.perform_server_connectivity_checking(fault_id)
                logger.debug(f"{server['hostname']}执行联通性检查")
            if server['check'][0]['check_status'] in [0, 2]:
                self.perform_server_hardware_checking(fault_id)
                logger.debug(f"{server['hostname']}执行硬件检查")

            if server['check'][1]['check_status'] in [0, 2]:
                # 执行拨号
                ret = self.query_account_status_in_server_failure(fault_id, server_id)
                logger.debug(f"{server['hostname']}查询账号状态")

                ids, account_ids = self.extract_ids(ret)
                if account_ids:
                    self.perform_dialing_in_server_failure(account_ids, ids)
                    logger.debug(f"{server['hostname']}执行拨号")
        logger.debug("等待拨号结果，将耗时5分钟")
        time.sleep(5 * 60)

        # 执行ipv4压测
        for fault_id, server_id, server_name in server_info_list:
            logger.debug(f"{server_name}查询账号状态")
            accounts = self.query_account_status_in_server_failure(fault_id, server_id)
            account_ids_of_dialed = self._filter_account_ids_for_ipv4_pressure_test(accounts)
            if account_ids_of_dialed:
                self.perform_pressure_test_in_server_failure(fault_id, account_ids_of_dialed)
                logger.debug(f"{server_name}执行ipv4压测")
        logger.debug("等待ipv4压测结果，将耗时10分钟")
        time.sleep(10 * 60)

        # 判断是否有ipv6，执行ipv6压测
        ipv6_test_flag = False
        for fault_id, server_id, server_name in server_info_list:
            # 检查拨号结果
            logger.debug(f"{server_name}查询账号状态")
            accounts = self.query_account_status_in_server_failure(fault_id, server_id)
            account_ids_with_ipv6 = self._filter_account_ids_for_ipv6_pressure_test(accounts)
            if account_ids_with_ipv6:
                self.perform_pressure_test_in_server_failure(fault_id, account_ids_with_ipv6, ip_type="ipv6")
                logger.debug(f"{server_name}执行ipv6压测")
                ipv6_test_flag = True
        if ipv6_test_flag:
            logger.debug("等待ipv6压测结果，将耗时10分钟")
            time.sleep(10 * 60)

        final_servers_status = self.query_faulty_servers()
        recover_server_ids = self.filter_servers_that_can_be_recovered(final_servers_status)
        logger.debug(f"当前可恢复的服务器数量为{len(recover_server_ids)}")
        # print(recover_server_ids)
        for server_id in recover_server_ids:
            logger.debug(f"开始提交服务器恢复")
            self.commit_recovery_application_in_server_failure(server_id)


if __name__ == "__main__":
    import os
    from utils.logger import setup_logger
    from pprint import pprint

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()

    # baishan = Baishan("yicheng")
    # baishan.init()
    # baishan = Baishan("vision_blue")
    # 自动拨号
    # baishan.auto_recover_accounts_in_account_failure()
    # baishan.rack_auto_perform_stress_test(2765, ip_type="ipv4")
    with Baishan("yicheng") as baishan:
        pass
# servers = baishan.query_faulty_servers()
# server_info_list = []
# for server in servers:
#     fault_id = server['id']
#     server_id = server['svr_id']
#     server_info_list.append((fault_id, server_id))
#     baishan.perform_server_connectivity_checking(fault_id)
#     baishan.perform_server_hardware_checking(fault_id)
#     ret = baishan.query_account_status_in_server_failure(fault_id, server_id)
#     accounts = baishan.extract_ids(ret)
#     pprint(accounts)
#     ret = baishan.perform_dialing_in_server_failure(*accounts)
#     pprint(ret)
# time.sleep(5 * 60)
# for fault_id, server_id in server_info_list:
#     accounts = baishan.query_account_status_in_server_failure(fault_id, server_id)
#     dialed_accounts = baishan._filter_account_for_stress_test(accounts)
#     baishan.perform_stress_test_in_server_failure(fault_id, dialed_accounts)
# time.sleep(10 * 60)
