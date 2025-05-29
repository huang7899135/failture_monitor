# 故障监控系统部署指南

## 系统架构

本系统采用Docker Compose进行容器化部署，包含以下服务：

- **app**: Flask Web应用 (端口8090)
- **db**: MySQL数据库 (内部网络)
- **redis**: Redis缓存 (内部网络)
- **celery**: Celery任务调度器 (内部网络)

## 快速部署

### 1. 一键部署

```bash
./deploy.sh
```

此脚本会自动：
- 检查Docker环境
- 清理旧容器
- 构建并启动所有服务
- 等待数据库和Redis就绪
- 初始化数据库
- 显示访问信息

### 2. 访问应用

部署完成后，访问：http://localhost:8090

## 配置说明

### 环境配置

系统通过环境变量自动配置：

- `APP_ENV=dev`: 开发环境配置
- `DATABASE_HOST=db`: 数据库主机（Docker服务名）
- `REDIS_HOST=redis`: Redis主机（Docker服务名）

### 网络配置

- 所有服务都在内部Docker网络中通信
- 只有Web应用的8090端口暴露给主机
- 数据库和Redis不暴露端口，避免与主机服务冲突

## 诊断和维护

### 系统诊断

```bash
./diagnose.sh
```

此脚本会检查：
- 容器运行状态
- 健康检查状态
- 网络连接
- 配置文件
- 错误日志

### 配置检查

```bash
# 在容器内运行
docker-compose exec app python check_config.py

# 包含连接测试
docker-compose exec app python check_config.py --test-connections
```

### 常用命令

```bash
# 查看所有服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f redis
docker-compose logs -f celery

# 重启服务
docker-compose restart [service_name]

# 停止所有服务
docker-compose down

# 完全清理（包括数据卷）
docker-compose down -v

# 重新构建并启动
docker-compose up -d --build
```

## 故障排除

### 常见问题

1. **端口冲突**
   - 检查8090端口是否被占用
   - 数据库和Redis现在只在内部网络运行，不会有端口冲突

2. **数据库连接失败**
   ```bash
   # 检查数据库健康状态
   docker-compose ps
   ./diagnose.sh
   ```

3. **Celery任务不执行**
   ```bash
   # 查看Celery日志
   docker-compose logs -f celery
   ```

4. **配置问题**
   ```bash
   # 运行配置检查
   docker-compose exec app python check_config.py
   ```

### 重新部署

如果遇到问题，可以完全重新部署：

```bash
# 清理所有容器和数据
docker-compose down -v

# 重新部署
./deploy.sh
```

## 开发调试

### 进入容器

```bash
# 进入应用容器
docker-compose exec app bash

# 进入数据库容器
docker-compose exec db bash

# 进入Redis容器
docker-compose exec redis sh
```

### 数据库操作

```bash
# 在数据库容器中连接MySQL
docker-compose exec db mysql -u root -pxs123456 failure_monitor
```

### 手动运行任务

```bash
# 在应用容器中手动执行任务
docker-compose exec app python -c "from tasks.monitor_tasks import device_online_monitor; device_online_monitor()"
```

## 监控和日志

### 日志位置

- 应用日志：`log/debug.log`
- Docker日志：`docker-compose logs`

### 性能监控

```bash
# 查看容器资源使用情况
docker stats
```

## 安全注意事项

1. 数据库密码已设置为`xs123456`，生产环境请修改
2. 所有敏感服务都在内部网络中，不对外暴露端口
3. 定期更新Docker镜像版本
4. 备份重要数据
