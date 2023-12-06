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
def yicheng_auto_recover_accounts():
    """白山自动恢复账号故障"""
    yicheng = Baishan("yicheng")
    yicheng.auto_recover_accounts()


@app.task
def vision_blue_auto_recover_accounts():
    vision_blue = Baishan("vision_blue")
    vision_blue.auto_recover_accounts()