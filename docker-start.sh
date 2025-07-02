#!/bin/bash

# xtool MCP Server Docker 启动脚本
# 提供便捷的 Docker 服务启动方式

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 帮助信息
show_help() {
    echo -e "${BLUE}xtool MCP Server Docker 管理脚本${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start     启动 Docker 服务"
    echo "  stop      停止 Docker 服务"
    echo "  restart   重启 Docker 服务"
    echo "  build     构建 Docker 镜像"
    echo "  logs      查看服务日志"
    echo "  status    查看服务状态"
    echo "  clean     清理 Docker 资源"
    echo "  dev       开发模式启动 (挂载本地代码)"
    echo "  prod      生产模式启动"
    echo "  shell     进入容器 shell"
    echo "  help      显示此帮助信息"
    echo ""
    echo "环境变量配置："
    echo "  可以通过 .env 文件或环境变量设置 API 密钥"
    echo "  支持的 API 密钥: OPENROUTER_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY 等"
}

# 检查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ docker-compose 未安装${NC}"
        exit 1
    fi
}

# 检查 .env 文件
check_env() {
    if [[ ! -f .env ]]; then
        echo -e "${YELLOW}⚠️  .env 文件不存在，将从示例创建${NC}"
        if [[ -f .env.example ]]; then
            cp .env.example .env
            echo -e "${GREEN}✅ 已创建 .env 文件，请配置 API 密钥${NC}"
        else
            echo -e "${RED}❌ .env.example 文件不存在${NC}"
            exit 1
        fi
    fi
    
    # 检查是否有配置的 API 密钥
    if ! grep -q "^[^#]*API_KEY=" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠️  未检测到配置的 API 密钥，服务可能无法正常工作${NC}"
        echo -e "${YELLOW}   请在 .env 文件中配置至少一个 API 密钥${NC}"
    fi
}

# 启动服务
start_service() {
    local mode=${1:-"prod"}
    
    echo -e "${BLUE}🚀 启动 xtool MCP Server ($mode 模式)${NC}"
    check_docker
    check_env
    
    if [[ "$mode" == "dev" ]]; then
        echo -e "${YELLOW}📝 开发模式：挂载本地代码目录${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.enhanced.yml up -d --build
    else
        echo -e "${GREEN}🏭 生产模式：使用容器内代码${NC}"
        docker-compose up -d --build
    fi
    
    echo -e "${GREEN}✅ 服务启动完成${NC}"
    echo -e "${BLUE}📊 查看状态: $0 status${NC}"
    echo -e "${BLUE}📋 查看日志: $0 logs${NC}"
}

# 停止服务
stop_service() {
    echo -e "${YELLOW}🛑 停止 xtool MCP Server${NC}"
    docker-compose down
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 重启服务
restart_service() {
    echo -e "${BLUE}🔄 重启 xtool MCP Server${NC}"
    stop_service
    sleep 2
    start_service
}

# 构建镜像
build_image() {
    echo -e "${BLUE}🔨 构建 Docker 镜像${NC}"
    check_docker
    docker-compose build --no-cache
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

# 查看日志
show_logs() {
    echo -e "${BLUE}📋 查看服务日志 (Ctrl+C 退出)${NC}"
    docker-compose logs -f
}

# 查看状态
show_status() {
    echo -e "${BLUE}📊 xtool MCP Server 状态${NC}"
    echo ""
    
    # 容器状态
    echo -e "${YELLOW}容器状态:${NC}"
    docker-compose ps
    echo ""
    
    # 健康检查
    echo -e "${YELLOW}健康检查:${NC}"
    container_id=$(docker-compose ps -q xtool-mcp 2>/dev/null || echo "")
    if [[ -n "$container_id" ]]; then
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "unknown")
        case "$health_status" in
            "healthy")
                echo -e "${GREEN}✅ 健康${NC}"
                ;;
            "unhealthy")
                echo -e "${RED}❌ 不健康${NC}"
                ;;
            "starting")
                echo -e "${YELLOW}🔄 启动中${NC}"
                ;;
            *)
                echo -e "${YELLOW}❓ 未知状态${NC}"
                ;;
        esac
    else
        echo -e "${RED}❌ 容器未运行${NC}"
    fi
    echo ""
    
    # 资源使用
    echo -e "${YELLOW}资源使用:${NC}"
    if [[ -n "$container_id" ]]; then
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "$container_id" 2>/dev/null || echo "无法获取资源信息"
    fi
}

# 清理资源
clean_resources() {
    echo -e "${YELLOW}🧹 清理 Docker 资源${NC}"
    echo -e "${RED}⚠️  这将删除容器、镜像和未使用的卷${NC}"
    read -p "确认继续? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down --rmi all --volumes --remove-orphans
        docker system prune -f
        echo -e "${GREEN}✅ 清理完成${NC}"
    else
        echo -e "${BLUE}❌ 已取消${NC}"
    fi
}

# 进入容器 shell
enter_shell() {
    echo -e "${BLUE}🖥️  进入容器 shell${NC}"
    container_id=$(docker-compose ps -q xtool-mcp 2>/dev/null || echo "")
    if [[ -n "$container_id" ]]; then
        docker exec -it "$container_id" /bin/bash
    else
        echo -e "${RED}❌ 容器未运行，请先启动服务${NC}"
        exit 1
    fi
}

# 主逻辑
case "${1:-help}" in
    "start")
        start_service "prod"
        ;;
    "dev")
        start_service "dev"
        ;;
    "prod")
        start_service "prod"
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "build")
        build_image
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "clean")
        clean_resources
        ;;
    "shell")
        enter_shell
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo -e "${RED}❌ 未知选项: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac