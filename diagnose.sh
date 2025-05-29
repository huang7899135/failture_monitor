#!/bin/bash

# 故障监控系统诊断脚本

echo "==================================================="
echo "         故障监控系统诊断脚本"
echo "==================================================="

# 检查容器状态
echo "1. 检查容器状态"
echo "---------------------------------------------------"
docker-compose ps

echo ""
echo "2. 检查容器健康状态"
echo "---------------------------------------------------"
echo "数据库健康状态:"
docker-compose ps -q db | xargs docker inspect -f '{{.State.Health.Status}}' 2>/dev/null || echo "无法获取数据库健康状态"

echo "Redis健康状态:"
docker-compose ps -q redis | xargs docker inspect -f '{{.State.Health.Status}}' 2>/dev/null || echo "无法获取Redis健康状态"

echo ""
echo "3. 网络连接测试"
echo "---------------------------------------------------"
echo "测试应用到数据库的连接:"
docker-compose exec -T app python -c "
import os
import pymysql
try:
    conn = pymysql.connect(
        host=os.getenv('DATABASE_HOST', 'db'),
        user='root',
        password='xs123456',
        database='failure_monitor'
    )
    print('✓ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
" 2>/dev/null || echo "无法测试数据库连接"

echo ""
echo "测试应用到Redis的连接:"
docker-compose exec -T app python -c "
import os
import redis
try:
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=0)
    r.ping()
    print('✓ Redis连接成功')
except Exception as e:
    print(f'❌ Redis连接失败: {e}')
" 2>/dev/null || echo "无法测试Redis连接"

echo ""
echo "4. 检查应用配置"
echo "---------------------------------------------------"
docker-compose exec -T app python check_config.py 2>/dev/null || echo "无法运行配置检查"

echo ""
echo "5. 最近的错误日志 (最后20行)"
echo "---------------------------------------------------"
echo "应用日志:"
docker-compose logs --tail=10 app 2>/dev/null || echo "无法获取应用日志"

echo ""
echo "数据库日志:"
docker-compose logs --tail=10 db 2>/dev/null || echo "无法获取数据库日志"

echo ""
echo "Redis日志:"
docker-compose logs --tail=10 redis 2>/dev/null || echo "无法获取Redis日志"

echo ""
echo "Celery日志:"
docker-compose logs --tail=10 celery 2>/dev/null || echo "无法获取Celery日志"

echo ""
echo "==================================================="
echo "诊断完成"
echo "==================================================="
