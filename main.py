from monitor.device_monitor import DevicesOnlineMonitor
from checker.webpage_checker.sites.baishan import Baishan
from checker.webpage_checker.sites.openfog import Openfog
from checker.webpage_checker.sites.haidian import Haidian
from notifier.wechat_template_message import WeChatTemplateMessage
from utils.logger import setup_logger
import os

# 设置当前目录为工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# logger = setup_logger()


def test_node_recover():
    client = Baishan("vision_blue")
    # client = Baishan("yicheng")
    client.init()
    fault_nodes = client.query_faulty_nodes()
    for node in fault_nodes:
        node_id = node.get("id")

        # 查询故障节点的故障服务器
        faulty_servers = client.query_faulty_servers_in_node_failure(node_id)
        # 从故障服务器中提取故障服务器的id
        faulty_server_ids = list(map(lambda x: x.get("id"), faulty_servers))

        # pprint(faulty_servers)

        # 执行故障节点的故障服务器的联通性检测
        # res = client.perform_connectivity_check_in_node_failure(faulty_server_ids)
        # pprint(res)

        # # 执行故障节点的故障服务器的硬件检测
        # res = client.perform_hardware_checking_in_node_failure(faulty_server_ids)
        # pprint(res)
        # # 执行故障节点的故障服务器的拨测
        # res = client.perform_dialing_in_node_failure(faulty_server_ids, node_id)
        # pprint(res)

        # 执行故障节点的故障服务器的压测
        # res = client.perform_stress_test_in_node_failure(node_id)
        # pprint(res)

        # res = client.submit_node_recovery_application(node_id, faulty_server_ids)

        faulty_servers_status = client.query_faulty_servers_in_node_failure(node_id)
        pprint(faulty_servers_status)


def test_rack_mounting():
    # baishan = Baishan("vision_blue")
    baishan = Baishan("yicheng")
    baishan.auto_recover_accounts_in_account_failure()
    baishan.perform_server_stress_test_in_server_rack_mounting(2763, "ipv4")
    baishan.perform_stress_test_in_server_rack_mounting(2763, "ipv6")
    msg = WeChatTemplateMessage()
    msg.send_network_recovery_notification("ozoJjv3QyBLlDf-PzkxfrRA5aPHk", "http://www.baidu.com", "压测成功了",
                                           "ipv4", "ipv6", "remark")


def test_haidian():
    haidian = Haidian()
    haidian.init()
    ret = haidian.query_server_status()
    pprint(ret)


def test_openfog():
    openfog = Openfog()
    openfog.init()
    bills = openfog.query_historical_income()
    pprint(bills)


def test_device_online_monitor():
    monitor = DevicesOnlineMonitor()
    monitor.run()


if __name__ == "__main__":
    import os
    from utils.logger import setup_logger
    from pprint import pprint

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()

    # test_openfog()
    # test_node_recover()
    # test_rack_mounting()
    # test_haidian()
    test_device_online_monitor()
