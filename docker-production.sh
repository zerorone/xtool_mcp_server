#!/bin/bash
# Zen MCP Server - 生产环境管理脚本

set -euo pipefail

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}🚀 $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

cd "$(dirname "${BASH_SOURCE[0]}")"

COMPOSE_FILE="docker-compose.production.yml"

show_help() {
    echo "Zen MCP Server 生产环境管理脚本"
    echo
    echo "用法: $0 [操作]"
    echo
    echo "操作:"
    echo "  build       构建 Docker 镜像"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      查看状态"
    echo "  logs        查看日志"
    echo "  health      健康检查"
    echo "  shell       进入容器 shell"
    echo "  clean       清理资源"
    echo "  monitoring  启动监控服务"
    echo "  backup      备份数据"
    echo "  help        显示帮助"
    echo
}

check_requirements() {
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker 未安装"
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        error "Docker Compose 未安装"
    fi
    
    if ! docker info >/dev/null 2>&1; then
        error "Docker 未运行"
    fi
    
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose 文件不存在: $COMPOSE_FILE"
    fi
}

build_image() {
    log "构建生产环境镜像..."
    ./docker-build-production.sh
}

start_services() {
    log "启动 Zen MCP Server 生产服务..."
    
    # 检查环境配置
    if [[ ! -f ".env" ]]; then
        warn "未找到 .env 文件，使用示例配置"
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            warn "请编辑 .env 文件设置 API 密钥"
        fi
    fi
    
    docker-compose -f "$COMPOSE_FILE" up -d zen-mcp-server
    
    log "✅ 服务启动完成"
    info "等待 30 秒进行健康检查..."
    sleep 30
    show_status
}

stop_services() {
    log "停止 Zen MCP Server 服务..."
    docker-compose -f "$COMPOSE_FILE" down
    log "✅ 服务已停止"
}

restart_services() {
    log "重启 Zen MCP Server 服务..."
    docker-compose -f "$COMPOSE_FILE" restart zen-mcp-server
    log "✅ 服务已重启"
}

show_status() {
    log "服务状态:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo
    log "容器健康状态:"
    docker ps --filter "name=zen-mcp-production" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # 健康检查
    echo
    if docker ps --filter "name=zen-mcp-production" --filter "health=healthy" | grep -q zen-mcp-production; then
        log "✅ 服务健康状态: 正常"
    elif docker ps --filter "name=zen-mcp-production" --filter "health=unhealthy" | grep -q zen-mcp-production; then
        warn "⚠️ 服务健康状态: 不健康"
    else
        info "ℹ️ 服务健康状态: 检查中..."
    fi
}

show_logs() {
    log "显示服务日志 (Ctrl+C 退出):"
    docker-compose -f "$COMPOSE_FILE" logs -f zen-mcp-server
}

health_check() {
    log "执行健康检查..."
    
    if docker ps --filter "name=zen-mcp-production" | grep -q zen-mcp-production; then
        log "容器运行状态: ✅ 运行中"
        
        # 执行内部健康检查
        if docker exec zen-mcp-production python /usr/local/bin/healthcheck.py; then
            log "✅ 健康检查通过"
        else
            error "❌ 健康检查失败"
        fi
        
        # 显示服务统计
        echo
        log "服务统计:"
        docker exec zen-mcp-production ls -la /app/logs/ 2>/dev/null || true
        
    else
        error "容器未运行"
    fi
}

enter_shell() {
    log "进入容器 shell..."
    docker exec -it zen-mcp-production /bin/bash
}

clean_resources() {
    log "清理 Docker 资源..."
    
    # 停止服务
    docker-compose -f "$COMPOSE_FILE" down
    
    # 清理未使用的镜像
    docker image prune -f
    
    # 清理未使用的卷
    docker volume prune -f
    
    log "✅ 资源清理完成"
}

start_monitoring() {
    log "启动监控服务..."
    docker-compose -f "$COMPOSE_FILE" --profile monitoring up -d
    log "✅ 监控服务已启动"
    info "Prometheus: http://localhost:9090"
}

backup_data() {
    log "备份数据..."
    
    BACKUP_DIR="./backups/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份日志
    if docker volume ls | grep -q zen-logs; then
        docker run --rm -v zen-logs:/source -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/logs.tar.gz -C /source .
        log "✅ 日志备份完成: $BACKUP_DIR/logs.tar.gz"
    fi
    
    # 备份内存数据
    if docker volume ls | grep -q zen-memory; then
        docker run --rm -v zen-memory:/source -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/memory.tar.gz -C /source .
        log "✅ 内存数据备份完成: $BACKUP_DIR/memory.tar.gz"
    fi
    
    # 备份配置
    if docker volume ls | grep -q zen-config; then
        docker run --rm -v zen-config:/source -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/config.tar.gz -C /source .
        log "✅ 配置备份完成: $BACKUP_DIR/config.tar.gz"
    fi
    
    log "✅ 完整备份完成: $BACKUP_DIR"
}

# 主逻辑
case "${1:-help}" in
    build)
        check_requirements
        build_image
        ;;
    start)
        check_requirements
        start_services
        ;;
    stop)
        check_requirements
        stop_services
        ;;
    restart)
        check_requirements
        restart_services
        ;;
    status)
        check_requirements
        show_status
        ;;
    logs)
        check_requirements
        show_logs
        ;;
    health)
        check_requirements
        health_check
        ;;
    shell)
        check_requirements
        enter_shell
        ;;
    clean)
        check_requirements
        clean_resources
        ;;
    monitoring)
        check_requirements
        start_monitoring
        ;;
    backup)
        check_requirements
        backup_data
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "未知操作: $1\n$(show_help)"
        ;;
esac