"""celery配置文件"""
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'
beat_schedule = {
    'baishan_auto_recover_accounts_every_hour': {
        'task': 'tasks.crawler_tasks.baishan_auto_recover_accounts',
        'schedule': 3660,  # 每隔一个小时
        'args': ()  # 替换为你要爬取的 URL
    },
}
