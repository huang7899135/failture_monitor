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

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()
    # monitor = DevicesMonitor()
    # monitor.run()

    baishan = Baishan()
    baishan.rack_auto_perform_stress_test(2717, "ipv4")
    baishan.rack_auto_perform_stress_test(2717, "ipv6")
    msg = WeChatTemplateMessage()
    msg.send_network_recovery_notification("ozoJjv3QyBLlDf-PzkxfrRA5aPHk", "http://www.baidu.com", "压测成功了",
                                           "ipv4", "ipv6", "remark")

