# 故障监控系统 - 生产环境部署指南

## 概述

本文档介绍如何在生产环境中部署故障监控系统。系统采用 Docker Compose 进行容器化部署，包含以下组件：

- **Flask Web应用**: 故障监控的主要应用
- **MySQL**: 数据存储
- **Redis**: 缓存和消息队列
- **Celery**: 异步任务处理
- **Nginx**: 反向代理（可选）

## 系统要求

### 硬件要求
- CPU: 2核心或以上
- 内存: 4GB或以上
- 磁盘: 20GB可用空间

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- Git

## 部署步骤

### 1. 获取代码
```bash
git clone <your-repository-url>
cd failure_monitor
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
nano .env
```

**重要配置项:**
- `MYSQL_ROOT_PASSWORD`: MySQL根密码（必须修改）
- `APP_DOMAIN`: 应用域名
- 其他配置根据需要修改

### 3. 一键部署

#### 基础部署（不包含Nginx）
```bash
./deploy-prod.sh deploy
```

#### 完整部署（包含Nginx反向代理）
```bash
./deploy-prod.sh deploy-nginx
```

### 4. 验证部署
```bash
# 检查服务状态
./deploy-prod.sh status

# 查看日志
./deploy-prod.sh logs
```

## 服务管理

### 启动服务
```bash
# 启动基础服务
./deploy-prod.sh start

# 启动包含Nginx的服务
./deploy-prod.sh start-nginx
```

### 停止服务
```bash
./deploy-prod.sh stop
```

### 重启服务
```bash
./deploy-prod.sh restart
```

### 查看日志
```bash
# 查看所有服务日志
./deploy-prod.sh logs

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f app
docker compose -f docker-compose.prod.yml logs -f celery
```

## 数据库管理

### 初始化数据库
```bash
./deploy-prod.sh init-db
```

### 备份数据库
```bash
./deploy-prod.sh backup
```

### 手动备份
```bash
# 创建备份
docker compose -f docker-compose.prod.yml exec db mysqldump -u root -p failure_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复备份
docker compose -f docker-compose.prod.yml exec -T db mysql -u root -p failure_monitor < backup_file.sql
```

## 应用更新

### 自动更新
```bash
./deploy-prod.sh update
```

### 手动更新
```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
./deploy-prod.sh build

# 3. 重启服务
./deploy-prod.sh restart
```

## 监控和维护

### 健康检查
系统提供健康检查端点：
- HTTP: `http://your-domain:8090/health`
- 通过Nginx: `http://your-domain/health`

### 日志管理
日志文件位置：
- 应用日志: Docker卷 `app_logs`
- Nginx日志: 容器内 `/var/log/nginx/`
- MySQL日志: 容器内 `/var/lib/mysql/`

### 性能监控
```bash
# 查看资源使用情况
docker stats

# 查看系统负载
docker compose -f docker-compose.prod.yml top
```

## 安全配置

### 1. 防火墙设置
```bash
# 只开放必要端口
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 22    # SSH
```

### 2. SSL证书配置（可选）
如果使用HTTPS，需要配置SSL证书：

1. 将证书文件放在 `ssl/` 目录下
2. 编辑 `nginx/conf.d/app.conf`，取消注释HTTPS配置
3. 重启Nginx服务

### 3. 数据库安全
- 修改默认密码
- 限制数据库访问权限
- 定期备份数据

## 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看错误日志
docker-compose -f docker-compose.prod.yml logs
```

#### 2. 数据库连接失败
```bash
# 检查数据库服务
docker-compose -f docker-compose.prod.yml exec db mysql -u root -p

# 检查网络连接
docker-compose -f docker-compose.prod.yml exec app ping db
```

#### 3. 应用无响应
```bash
# 检查应用健康状态
curl http://localhost:8090/health

# 重启应用服务
docker-compose -f docker-compose.prod.yml restart app
```

#### 4. Celery任务不执行
```bash
# 检查Celery状态
docker-compose -f docker-compose.prod.yml exec celery celery -A tasks.monitor_tasks.app inspect active

# 重启Celery服务
docker-compose -f docker-compose.prod.yml restart celery
```

### 清理和重置

#### 清理Docker资源
```bash
./deploy-prod.sh cleanup
```

#### 完全重置（谨慎使用）
```bash
# 停止所有服务
./deploy-prod.sh stop

# 删除所有容器和卷
docker-compose -f docker-compose.prod.yml down -v

# 删除镜像
docker rmi $(docker images -q)

# 重新部署
./deploy-prod.sh deploy
```

## 配置文件说明

### docker-compose.prod.yml
生产环境的Docker Compose配置文件，包含所有服务的定义。

### .env
环境变量配置文件，包含敏感信息和环境相关配置。

### nginx/
Nginx配置文件目录，包含反向代理和SSL配置。

### mysql/conf.d/
MySQL配置文件目录，包含性能优化配置。

### redis/
Redis配置文件目录，包含持久化和性能配置。

## 联系支持

如果遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查系统日志
3. 联系系统管理员

---

**注意**: 在生产环境中部署前，请确保：
- 所有密码已修改为安全值
- 网络配置正确
- 备份策略已制定
- 监控系统已配置
