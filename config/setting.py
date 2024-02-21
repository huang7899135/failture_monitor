import os

env = os.getenv('ENV', 'prod')

if env == 'prod':
    from config.setting_prod import *
else:
    from config.setting_dev import *

DEVICE_ONLINE_MONITOR_INTERVAL = 600  # 设备在线监控间隔,单位秒
