#!/bin/bash
# 生产环境部署脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker和Docker Compose
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或不在PATH中"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装或不在PATH中"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 检查环境变量文件
check_env_file() {
    log_info "检查环境变量文件..."
    
    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，从模板创建..."
        cp .env.example .env
        log_warning "请编辑 .env 文件设置正确的配置值"
        read -p "是否现在编辑 .env 文件? (y/n): " edit_env
        if [ "$edit_env" = "y" ]; then
            ${EDITOR:-nano} .env
        fi
    fi
    
    log_success "环境变量文件检查完成"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    docker compose -f docker-compose.prod.yml build --no-cache
    log_success "镜像构建完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 启动数据库服务
    docker compose -f docker-compose.prod.yml up -d db redis
    
    # 等待数据库准备就绪
    log_info "等待数据库启动..."
    sleep 30
    
    # 运行数据库初始化
    docker compose -f docker-compose.prod.yml run --rm app python init_db.py --action=sync
    
    log_success "数据库初始化完成"
}

# 启动服务
start_services() {
    log_info "启动所有服务..."
    
    case "$1" in
        "with-nginx")
            docker compose -f docker-compose.prod.yml --profile nginx up -d
            ;;
        *)
            docker compose -f docker-compose.prod.yml up -d
            ;;
    esac
    
    log_success "服务启动完成"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    docker compose -f docker-compose.prod.yml ps
    
    # 检查应用健康状态
    log_info "等待应用启动..."
    sleep 10
    
    if curl -f http://localhost:8090/health > /dev/null 2>&1; then
        log_success "应用健康检查通过"
    else
        log_warning "应用健康检查失败，请检查日志"
    fi
}

# 查看日志
view_logs() {
    log_info "查看服务日志..."
    docker compose -f docker-compose.prod.yml logs -f
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    docker compose -f docker-compose.prod.yml down
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    docker compose -f docker-compose.prod.yml restart
    log_success "服务重启完成"
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="backup_${timestamp}.sql"
    
    docker compose -f docker-compose.prod.yml exec db mysqldump -u root -p${MYSQL_ROOT_PASSWORD:-xs123456} failure_monitor > "$backup_file"
    
    log_success "数据库备份完成: $backup_file"
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    # 停止并删除容器
    docker compose -f docker-compose.prod.yml down
    
    # 删除未使用的镜像
    docker image prune -f
    
    # 删除未使用的卷（谨慎使用）
    read -p "是否删除未使用的Docker卷? 这将删除所有数据! (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        docker volume prune -f
        log_warning "所有未使用的卷已删除"
    fi
    
    log_success "清理完成"
}

# 更新应用
update_app() {
    log_info "更新应用..."
    
    # 拉取最新代码
    git pull
    
    # 重新构建镜像
    build_images
    
    # 重启服务
    restart_services
    
    log_success "应用更新完成"
}

# 显示帮助信息
show_help() {
    echo "生产环境部署脚本"
    echo ""
    echo "使用方法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  deploy          完整部署（构建、初始化、启动）"
    echo "  deploy-nginx    完整部署（包含Nginx）"
    echo "  start           启动服务"
    echo "  start-nginx     启动服务（包含Nginx）"
    echo "  stop            停止服务"
    echo "  restart         重启服务"
    echo "  build           构建镜像"
    echo "  init-db         初始化数据库"
    echo "  status          查看服务状态"
    echo "  logs            查看日志"
    echo "  backup          备份数据库"
    echo "  update          更新应用"
    echo "  cleanup         清理Docker资源"
    echo "  help            显示帮助信息"
    echo ""
}

# 主函数
main() {
    case "$1" in
        "deploy")
            check_dependencies
            check_env_file
            build_images
            init_database
            start_services
            check_services
            log_success "部署完成！应用已在 http://localhost:8090 运行"
            ;;
        "deploy-nginx")
            check_dependencies
            check_env_file
            build_images
            init_database
            start_services "with-nginx"
            check_services
            log_success "部署完成！应用已在 http://localhost 运行（通过Nginx代理）"
            ;;
        "start")
            start_services
            ;;
        "start-nginx")
            start_services "with-nginx"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "build")
            build_images
            ;;
        "init-db")
            init_database
            ;;
        "status")
            check_services
            ;;
        "logs")
            view_logs
            ;;
        "backup")
            backup_database
            ;;
        "update")
            update_app
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
