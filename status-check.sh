#!/bin/bash
# 快速状态检查脚本

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== 故障监控系统状态检查 ==="
echo ""

# 检查Docker服务
echo "🐳 Docker 服务状态:"
if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Docker 服务运行正常${NC}"
else
    echo -e "${RED}✗ Docker 服务异常${NC}"
fi

# 检查应用健康状态
echo ""
echo "🌐 应用健康检查:"
if curl -s -f http://localhost:8090/health > /dev/null; then
    echo -e "${GREEN}✓ 应用响应正常${NC}"
    curl -s http://localhost:8090/health | python3 -m json.tool
else
    echo -e "${RED}✗ 应用无响应${NC}"
fi

# 检查数据库连接
echo ""
echo "🗄️ 数据库状态:"
if docker compose -f docker-compose.prod.yml exec -T db mysqladmin ping -h localhost -u root --password=${MYSQL_ROOT_PASSWORD:-xs123456} > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 数据库连接正常${NC}"
else
    echo -e "${RED}✗ 数据库连接失败${NC}"
fi

# 检查Redis连接
echo ""
echo "📦 Redis 状态:"
if docker compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis 连接正常${NC}"
else
    echo -e "${RED}✗ Redis 连接失败${NC}"
fi

# 检查Celery状态
echo ""
echo "⚙️ Celery 状态:"
if docker compose -f docker-compose.prod.yml exec -T celery celery -A tasks.monitor_tasks.app inspect ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Celery 工作正常${NC}"
else
    echo -e "${RED}✗ Celery 工作异常${NC}"
fi

# 显示系统资源使用情况
echo ""
echo "📊 系统资源使用:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "=== 检查完成 ==="
