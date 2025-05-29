#!/bin/bash

echo "==================================================="
echo "         数据库连接调试脚本"
echo "==================================================="

echo "1. 检查容器状态："
docker compose ps

echo ""
echo "2. 检查数据库容器健康状态："
db_container=$(docker compose ps -q db)
if [ -n "$db_container" ]; then
    echo "容器ID: $db_container"
    health_status=$(docker inspect -f '{{.State.Health.Status}}' $db_container 2>/dev/null || echo "无健康检查")
    echo "健康状态: $health_status"
    
    echo ""
    echo "3. 尝试从应用容器连接数据库："
    docker compose exec app ping -c 3 db || echo "无法ping通数据库容器"
    
    echo ""
    echo "4. 检查数据库端口："
    docker compose exec db netstat -ln | grep 3306 || echo "数据库端口检查失败"
    
    echo ""
    echo "5. 尝试MySQL连接测试："
    docker compose exec db mysql -u root -pxs123456 -e "SELECT 1;" 2>/dev/null && echo "✓ MySQL内部连接成功" || echo "❌ MySQL内部连接失败"
    
    echo ""
    echo "6. 从应用容器测试数据库连接："
    docker compose exec app python -c "
import os
import pymysql
try:
    conn = pymysql.connect(
        host='db',
        user='root', 
        password='xs123456',
        database='failure_monitor'
    )
    print('✓ Python MySQL连接成功')
    conn.close()
except Exception as e:
    print(f'❌ Python MySQL连接失败: {e}')
" 2>/dev/null || echo "Python连接测试失败"
    
else
    echo "❌ 数据库容器未运行"
fi

echo ""
echo "7. 查看最近的数据库日志："
docker compose logs --tail=20 db

echo ""
echo "8. 查看最近的应用日志："
docker compose logs --tail=20 app
