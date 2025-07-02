#!/bin/bash
# Zen MCP Server - 生产环境 Docker 构建脚本

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

log "开始构建 Zen MCP Server 生产环境 Docker 镜像..."

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    error "Docker 未运行，请启动 Docker"
fi

# 检查必要文件
if [[ ! -f "Dockerfile" ]]; then
    error "Dockerfile 不存在"
fi

if [[ ! -f "requirements.txt" ]]; then
    error "requirements.txt 不存在"
fi

# 检查API密钥配置
if [[ ! -f ".env" ]]; then
    warn "未找到 .env 文件，确保在启动时提供 API 密钥"
else
    log "发现 .env 文件"
fi

# 验证 .dockerignore 文件
if [[ ! -f ".dockerignore" ]]; then
    log "创建 .dockerignore 文件..."
    cat > .dockerignore << 'EOF'
.git
.venv
.zen_venv
.zen_memory
logs
*.log
*.pyc
__pycache__
.pytest_cache
.ruff_cache
tests
simulator_tests
docs
*.md
.env.example
.github
scripts
patch
examples
test_simulation_files
.claude
.DS_Store
.coveragerc
.desktop_configured
.docker_cleaned
EOF
    log "✅ 已创建 .dockerignore 文件"
fi

# 构建 Docker 镜像
log "构建生产环境镜像..."

if docker build -t zen-mcp-server:production .; then
    log "✅ 生产镜像构建成功"
    
    # 创建版本标签
    VERSION=$(date +"%Y%m%d-%H%M%S")
    docker tag zen-mcp-server:production zen-mcp-server:v${VERSION}
    log "✅ 已创建版本标签: v${VERSION}"
    
    # 创建latest标签
    docker tag zen-mcp-server:production zen-mcp-server:latest
    log "✅ 已创建 latest 标签"
    
else
    error "Docker 镜像构建失败"
fi

# 验证镜像
log "验证 Docker 镜像..."
docker images | grep zen-mcp-server

# 显示镜像信息
IMAGE_SIZE=$(docker images zen-mcp-server:production --format "table {{.Size}}" | tail -n 1)
log "🎉 生产环境 Docker 镜像构建完成！"
info "镜像名称: zen-mcp-server:production"
info "镜像大小: $IMAGE_SIZE"
info "版本标签: v${VERSION}"

echo
log "📋 下一步操作："
echo "1. 配置环境变量: cp .env.example .env && 编辑 .env"
echo "2. 启动服务: docker-compose -f docker-compose.production.yml up -d"
echo "3. 查看日志: docker-compose -f docker-compose.production.yml logs -f zen-mcp-server"
echo "4. 健康检查: docker-compose -f docker-compose.production.yml exec zen-mcp-server python /usr/local/bin/healthcheck.py"
echo "5. 启动监控: docker-compose -f docker-compose.production.yml --profile monitoring up -d"

exit 0