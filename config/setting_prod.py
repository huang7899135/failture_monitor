import os
from datetime import time

# 监控对象数据来源
MONITOR_OBJECTS_DATA_SOURCE = "yaml"
# 监控对象数据路径
MONITOR_OBJECTS_DATA_YAML_PATH = "datasource/monitor_objects.yaml"

# 通知起始时间段
NOTICE_START_TIME = time(7, 0, 0)
NOTICE_END_TIME = time(18, 0, 0)

###############数据库配置################
DATABASE_CONFIG = {
    'dialect': 'mysql+pymysql',
    'user': 'root',
    'password': 'xs123456',
    'host': os.getenv('DATABASE_HOST', 'db'),  # 默认使用Docker服务名
    'port': '3306',
    'database': 'failure_monitor'
}

DATABASE_URL = f"{DATABASE_CONFIG['dialect']}://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

###############render_url################

NETLOC = 'monitor.visionblue.cloud:8090'
