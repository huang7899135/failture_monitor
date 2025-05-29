#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Output commands being executed
# set -x

echo "==================================================="
echo "         故障监控系统部署脚本"
echo "==================================================="

# 检查Docker和Docker Compose是否安装
echo "检查 Docker 和 Docker Compose..."
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "✓ Docker 和 Docker Compose 已安装"

# 停止并清理已存在的容器（如果有）
echo "清理已存在的容器..."
docker-compose down -v 2>/dev/null || true

echo "构建并启动所有服务 (app, db, redis, celery)..."
docker-compose up -d --build

echo "等待数据库服务初始化..."
echo "正在检查数据库健康状态..."

# 使用健康检查等待数据库就绪
max_attempts=30
attempt_num=1
until [ "$(docker-compose ps -q db | xargs docker inspect -f '{{.State.Health.Status}}')" == "healthy" ]; do
    if [ "$attempt_num" -eq "$max_attempts" ]; then
        echo "❌ 数据库健康检查失败，尝试次数已达 $max_attempts 次"
        echo "查看数据库日志："
        docker-compose logs db
        exit 1
    fi
    echo "等待数据库健康检查通过 (尝试 $attempt_num/$max_attempts)..."
    sleep 2
    attempt_num=$((attempt_num+1))
done

echo "✓ 数据库服务已就绪"

# 等待Redis服务就绪
echo "等待 Redis 服务初始化..."
max_attempts=30
attempt_num=1
until [ "$(docker-compose ps -q redis | xargs docker inspect -f '{{.State.Health.Status}}')" == "healthy" ]; do
    if [ "$attempt_num" -eq "$max_attempts" ]; then
        echo "❌ Redis 健康检查失败，尝试次数已达 $max_attempts 次"
        echo "查看Redis日志："
        docker-compose logs redis
        exit 1
    fi
    echo "等待 Redis 健康检查通过 (尝试 $attempt_num/$max_attempts)..."
    sleep 2
    attempt_num=$((attempt_num+1))
done

echo "✓ Redis 服务已就绪"

echo "正在初始化数据库模式..."
if docker-compose exec app python init_db.py; then
    echo "✓ 数据库初始化完成"
else
    echo "❌ 数据库初始化失败"
    echo "查看应用日志："
    docker-compose logs app
    exit 1
fi

echo ""
echo "==================================================="
echo "              部署完成！"
echo "==================================================="
echo "📱 Web应用访问地址: http://localhost:8090"
echo "🗄️  MySQL数据库: 仅在Docker内部网络可访问 (service: db:3306)"
echo "🔴 Redis缓存: 仅在Docker内部网络可访问 (service: redis:6379)"
echo "⚙️  Celery任务调度器: 正在 'celery' 服务中运行"
echo ""
echo "常用命令："
echo "  查看所有服务状态: docker-compose ps"
echo "  查看实时日志: docker-compose logs -f"
echo "  查看特定服务日志: docker-compose logs -f [service_name]"
echo "  停止所有服务: docker-compose down"
echo "  完全清理: docker-compose down -v"
echo "==================================================="
