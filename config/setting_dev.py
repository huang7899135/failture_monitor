from datetime import time
import netifaces as ni

# 监控对象数据来源
MONITOR_OBJECTS_DATA_SOURCE = "yaml"
# 监控对象数据路径
MONITOR_OBJECTS_DATA_YAML_PATH = "datasource/monitor_objects.yaml"

# 通知起始时间段
NOTICE_START_TIME = time(0, 0, 0)
NOTICE_END_TIME = time(23, 59, 0)

###############数据库配置################
DATABASE_CONFIG = {
    'dialect': 'mysql+pymysql',
    'user': 'root',
    'password': 'xs123456',
    'host': '127.0.0.1',
    'port': '3306',
    'database': 'failure_monitor'
}

DATABASE_URL = f"{DATABASE_CONFIG['dialect']}://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

###############render_url################
# 查询本机eno 对应的ip地址


def get_ipv4_address(interface='en0'):
    try:
        interface_addresses = ni.ifaddresses(interface)
        ipv4_info = interface_addresses[ni.AF_INET][0]  # First IPv4 address
        return ipv4_info['addr']
    except (ValueError, KeyError):
        return "No IPv4 address found for the interface."


NETLOC = f'{get_ipv4_address()}:8090'
