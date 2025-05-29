import os

env = os.getenv('APP_ENV', 'prod')  # 使用 APP_ENV 环境变量，与 docker-compose.yml 保持一致

if env == 'prod':
    from config.setting_prod import *
else:
    from config.setting_dev import *

DEVICE_ONLINE_MONITOR_INTERVAL = 600  # 设备在线监控间隔,单位秒
