from celery import Celery
from monitor.base import DevicesMonitor

app = Celery('pcdn_monitor')
app.config_from_object('config.celery_config')


@app.task
def device_checker():
    """设备检测"""
    monitor = DevicesMonitor()
    monitor.run()



