from monitor.device_online_monitor import DevicesOnlineMonitor
from monitor.server_income_monitor import ServerIncomeMonitor
from checker.webpage_checker.sites.baishan import Baishan
from checker.webpage_checker.sites.openfog import Openfog
from checker.webpage_checker.sites.haidian import HaiDian
from notifier.wechat_template_message import WeChatTemplateMessage
from utils.logger import setup_logger
import os

# 设置当前目录为工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# logger = setup_logger()

def test_baishan_account():
    client = Baishan("vision_blue")
    # client = Baishan("yicheng")
    client.init()
    client.auto_recover_accounts_in_account_failure()


def test_node_recover():
    # client = Baishan("vision_blue")
    client = Baishan("yicheng")
    client.init()
    client.auto_recover_node_in_node_failure()


def test_rack_mounting():
    # baishan = Baishan("vision_blue")
    baishan = Baishan("yicheng")
    baishan.auto_recover_accounts_in_account_failure()
    baishan.perform_server_stress_test_in_server_rack_mounting(2763, "ipv4")
    baishan.perform_stress_test_in_server_rack_mounting(2763, "ipv6")
    msg = WeChatTemplateMessage()
    msg.send_network_recovery_notification("ozoJjv3QyBLlDf-PzkxfrRA5aPHk", "http://www.baidu.com", "压测成功了",
                                           "ipv4", "ipv6", "remark")


# def test_haidian():
#     with HaiDian() as haidian:
#         ret = haidian.perform_income_check()
#         pprint(ret)


def test_openfog():
    openfog = Openfog()
    openfog.init()
    bills = openfog.query_historical_income()
    pprint(bills)


def test_device_online_monitor():
    while True:
        with DevicesOnlineMonitor() as monitor:
            monitor.run()
        time.sleep(10)


def test_bug():
    client = Baishan("yicheng")
    client.init()
    faulty_nodes = client.query_faulty_nodes()
    # 2,遍历故障节点
    for node in faulty_nodes:
        faulty_servers = client.query_faulty_servers_in_node_failure(node['id'])
        faulty_server_ids = list(map(lambda x: x.get("id"), faulty_servers))
        # server_status = client.query_faulty_servers_in_node_failure(node['id'])

        if client.check_recovery_conditions_in_node_failure(faulty_servers):
            client.submit_node_recovery_application(node['id'], faulty_server_ids)


def server_income_monitor():
    with ServerIncomeMonitor() as monitor:
        monitor.run()


if __name__ == "__main__":
    import os
    import time
    from pprint import pprint

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()

    # test_baishan_account()

    # server_income_monitor()
    # test_openfog()
    # test_node_recover()
    # test_rack_mounting()
    # test_haidian()
    # test_device_online_monitor()
    # test_bug()

    server_income_monitor()

