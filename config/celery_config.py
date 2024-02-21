from celery.schedules import crontab
from config.setting import DEVICE_ONLINE_MONITOR_INTERVAL


"""celery配置文件"""
timezone = 'Asia/Shanghai'
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'
beat_schedule = {
    # 'device_online_monitor': {
    #     'task': 'tasks.monitor_tasks.device_online_monitor',
    #     'schedule': DEVICE_ONLINE_MONITOR_INTERVAL,  # 每隔10分钟
    #     'args': ()
    # },
    "baishan_yicheng_auto_recover_accounts_every_hour": {
        "task": "tasks.monitor_tasks.yicheng_auto_recover_accounts",
        "schedule": crontab(minute="0", hour='9-19'),  # 每天9点到19点,每隔一个小时
        "args": ()
    },
    "baishan_vision_blue_auto_recover_accounts_every_hour": {
        "task": "tasks.monitor_tasks.vision_blue_auto_recover_accounts",
        "schedule": crontab(minute="0", hour='9-19'),  # 每天9点到19点,每隔一个小时
        "args": ()
    },
    "baishan_yicheng_auto_recover_nodes_every_hour": {
        "task": "tasks.monitor_tasks.yicheng_auto_recover_nodes",
        "schedule": 60 * 60,
        "args": ()
    },
    "baishan_vision_blue_auto_recover_nodes_every_hour": {
        "task": "tasks.monitor_tasks.vision_blue_auto_recover_nodes",
        "schedule": 60 * 60,
        "args": ()
    },
}
