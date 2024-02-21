from celery import Celery
from monitor.device_online_monitor import DevicesOnlineMonitor
from checker.webpage_checker.sites.baishan import Baishan

app = Celery('pcdn_monitor')
app.config_from_object('config.celery_config')


@app.task
def device_online_monitor():
    """设备检测"""
    with DevicesOnlineMonitor() as monitor:
        monitor.run()


@app.task
def yicheng_auto_recover_accounts():
    """白山自动恢复账号故障"""
    with Baishan("yicheng") as yicheng:
        yicheng.auto_recover_accounts_in_account_failure()


@app.task
def vision_blue_auto_recover_accounts():
    with Baishan("vision_blue") as vision_blue:
        vision_blue.auto_recover_accounts_in_account_failure()


@app.task
def yicheng_auto_recover_nodes():
    """白山自动恢复节点故障"""
    with Baishan("yicheng") as yicheng:
        yicheng.auto_recover_node_in_node_failure()


@app.task
def vision_blue_auto_recover_nodes():
    with Baishan("vision_blue") as vision_blue:
        vision_blue.auto_recover_node_in_node_failure()
