#!/usr/bin/env python3
"""
配置检查脚本
验证所有配置是否正确设置
"""

import os
import sys
import time
from config.setting import DATABASE_CONFIG, DATABASE_URL
from config.celery_config import broker_url, result_backend


def check_environment():
    """检查环境变量"""
    print("=== 环境变量检查 ===")
    
    required_env_vars = [
        'DATABASE_HOST',
        'REDIS_HOST',
        'FLASK_APP',
        'APP_ENV'
    ]
    
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var} = {value}")
        else:
            print(f"❌ {var} 未设置")
    
    print()


def check_database_config():
    """检查数据库配置"""
    print("=== 数据库配置检查 ===")
    print(f"数据库主机: {DATABASE_CONFIG['host']}")
    print(f"数据库端口: {DATABASE_CONFIG['port']}")
    print(f"数据库名称: {DATABASE_CONFIG['database']}")
    print(f"数据库用户: {DATABASE_CONFIG['user']}")
    print(f"连接字符串: {DATABASE_URL}")
    print()


def check_redis_config():
    """检查Redis配置"""
    print("=== Redis 配置检查 ===")
    print(f"Broker URL: {broker_url}")
    print(f"Result Backend: {result_backend}")
    print()


def test_database_connection():
    """测试数据库连接"""
    print("=== 数据库连接测试 ===")
    try:
        from model.session import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        result = db.execute(text("SELECT 1")).fetchone()
        if result:
            print("✓ 数据库连接成功")
        else:
            print("❌ 数据库连接失败")
    except Exception as e:
        print(f"❌ 数据库连接异常: {e}")
    print()


def test_redis_connection():
    """测试Redis连接"""
    print("=== Redis 连接测试 ===")
    try:
        import redis
        redis_host = os.getenv('REDIS_HOST', 'redis')
        r = redis.Redis(host=redis_host, port=6379, db=0)
        r.ping()
        print("✓ Redis连接成功")
    except Exception as e:
        print(f"❌ Redis连接异常: {e}")
    print()


def check_celery_tasks():
    """检查Celery任务配置"""
    print("=== Celery 任务配置检查 ===")
    try:
        from config.celery_config import beat_schedule
        print(f"配置的定时任务数量: {len(beat_schedule)}")
        for task_name, task_config in beat_schedule.items():
            print(f"  - {task_name}: {task_config['task']}")
        print("✓ Celery任务配置正常")
    except Exception as e:
        print(f"❌ Celery任务配置异常: {e}")
    print()


def main():
    """主函数"""
    print("故障监控系统配置检查")
    print("=" * 50)
    
    check_environment()
    check_database_config()
    check_redis_config()
    check_celery_tasks()
    
    # 连接测试（可能需要服务已启动）
    if '--test-connections' in sys.argv:
        test_database_connection()
        test_redis_connection()
    else:
        print("提示: 使用 --test-connections 参数来测试数据库和Redis连接")
    
    print("配置检查完成")


if __name__ == "__main__":
    main()
