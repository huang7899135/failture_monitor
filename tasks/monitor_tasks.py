from celery import Celery
from monitor.device_monitor import DevicesMonitor
from checker.platform_spider.sites.baishan import Baishan


app = Celery('pcdn_monitor')
app.config_from_object('config.celery_config')


@app.task
def device_checker():
    """设备检测"""
    monitor = DevicesMonitor()
    monitor.run()


@app.task
def baishan_auto_recover_accounts():
    """白山自动恢复账号故障"""
    baishan = Baishan()
    return baishan.auto_recover_accounts()
