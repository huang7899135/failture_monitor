from monitor.device_monitor import DevicesMonitor
from checker.platform_spider.sites.baishan import Baishan
from notifier.wechat_template_message import WeChatTemplateMessage
from utils.logger import setup_logger
import os

# 设置当前目录为工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# logger = setup_logger()

if __name__ == "__main__":
    import os
    from utils.logger import setup_logger
    from pprint import pprint

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()
    # monitor = DevicesMonitor()
    # monitor.run()

    # yicheng = Baishan("yicheng")
    # yicheng.auto_recover_accounts()
    # vision_blue = Baishan("vision_blue")
    client = Baishan("vision_blue")
    client.init()
    fault_nodes = client.query_faulty_nodes()
    for node in fault_nodes:
        node_id = node.get("id")
        res = client.perform_stress_test_in_node_failure(node_id)
        print(res)

        # faulty_servers = client.query_faulty_servers_in_node_failure(node_id)
        # pprint(faulty_servers)
        # faulty_server_ids = list(map(lambda x: x.get("id"), faulty_servers))
        # res = client.perform_connectivity_check_in_node_failure(faulty_server_ids)
        # pprint(res)
        # res = client.perform_hardware_checking_in_node_failure(faulty_server_ids)
        # pprint(res)
        #
        # res = client.perform_dialing_in_node_failure(faulty_server_ids, node_id)
        # pprint(res)

        # res = client.query_account_status_in_node_failure(node_id)
        # for item in res:
        #     pprint(item)

        # res = client.perform_stress_test_in_node_failure(faulty_server_ids, node_id)
        # pprint(res)

        # pprint(res)

    # vision_blue.auto_recover_accounts()

    # baishan = Baishan("vision_blue")
    # baishan = Baishan("yicheng")
    # baishan.auto_recover_accounts()
    # baishan.rack_auto_perform_stress_test(2763, "ipv4")
    # baishan.rack_auto_perform_stress_test(2763, "ipv6")
    # msg = WeChatTemplateMessage()
    # msg.send_network_recovery_notification("ozoJjv3QyBLlDf-PzkxfrRA5aPHk", "http://www.baidu.com", "压测成功了",
    #                                        "ipv4", "ipv6", "remark")
