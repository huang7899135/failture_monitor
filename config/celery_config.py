"""celery配置文件"""
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'
beat_schedule = {
    'test': {
        'task': 'tasks.devices_check_tasks.device_checker',
        'schedule': 120,  # 单位秒
        'args': ()  # 替换为你要爬取的 URL
    },
}
