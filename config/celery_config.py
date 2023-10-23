from celery.schedules import crontab

"""celery配置文件"""
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'
beat_schedule = {
    'test': {
        'task': 'tasks.devices_check_tasks.device_checker',
        'schedule': 600,  # 每隔10分钟
        'args': ()
    },
    "baishan_auto_recover_accounts_every_hour": {
        "task": "tasks.crawler_tasks.baishan_auto_recover_accounts",
        "schedule": crontab(minute="0", hour='9-19'),  # 每天9点到19点,每隔一个小时
        "args": ()
    }
}
