#!/bin/bash
# Zen MCP Server - Docker 镜像构建和发布脚本

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"; exit 1; }
info() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }

# 默认配置
REGISTRY="docker.io"
NAMESPACE="zenserver"
IMAGE_NAME="zen-mcp-server"
VERSION=$(grep -E '^__version__' config.py | cut -d'"' -f2 || echo "latest")
PLATFORMS="linux/amd64,linux/arm64"
BUILD_ARGS=""
PUSH_REGISTRY=false
BUILD_CACHE=true
DRY_RUN=false

show_help() {
    cat << EOF
🐳 Zen MCP Server Docker 构建和发布工具

用法: $0 [选项]

选项:
  -h, --help                显示此帮助信息
  -r, --registry REGISTRY   Docker 镜像仓库 [默认: docker.io]
  -n, --namespace NAMESPACE 命名空间 [默认: zenserver]
  -t, --tag TAG             镜像标签 [默认: 从 config.py 读取]
  -p, --platforms PLATFORMS 目标平台 [默认: linux/amd64,linux/arm64]
  --push                    推送到镜像仓库
  --no-cache                禁用构建缓存
  --dry-run                 仅显示操作，不实际执行
  --build-arg ARG=VALUE     传递构建参数

示例:
  $0                                           # 本地构建
  $0 --push                                   # 构建并推送
  $0 -t v2.0.0 --push                        # 指定版本并推送
  $0 -r ghcr.io -n myorg --push              # 推送到 GitHub Container Registry

EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -t|--tag)
            VERSION="$2"
            shift 2
            ;;
        -p|--platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --push)
            PUSH_REGISTRY=true
            shift
            ;;
        --no-cache)
            BUILD_CACHE=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --build-arg)
            BUILD_ARGS="$BUILD_ARGS --build-arg $2"
            shift 2
            ;;
        -*)
            error "未知选项: $1"
            ;;
        *)
            error "意外参数: $1"
            ;;
    esac
done

# 构建完整镜像名
FULL_IMAGE_NAME="$REGISTRY/$NAMESPACE/$IMAGE_NAME"

# 验证环境
command -v docker >/dev/null 2>&1 || error "Docker 未安装"

if [[ "$PUSH_REGISTRY" == "true" ]]; then
    if ! docker buildx version >/dev/null 2>&1; then
        error "Docker Buildx 未安装，多平台构建需要 Buildx"
    fi
fi

# 检查 Dockerfile
if [[ ! -f "Dockerfile" ]]; then
    error "未找到 Dockerfile"
fi

log "🐳 准备构建 Zen MCP Server Docker 镜像"
info "镜像名称: $FULL_IMAGE_NAME:$VERSION"
info "构建平台: $PLATFORMS"
info "推送仓库: $([ "$PUSH_REGISTRY" == "true" ] && echo "是" || echo "否")"
info "使用缓存: $([ "$BUILD_CACHE" == "true" ] && echo "是" || echo "否")"

if [[ "$DRY_RUN" == "true" ]]; then
    info "🧪 DRY RUN 模式 - 仅显示操作"
fi

# 执行命令的包装函数
run_command() {
    local cmd="$1"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  $ $cmd"
    else
        eval "$cmd"
    fi
}

# 创建 buildx builder（如果需要）
if [[ "$PUSH_REGISTRY" == "true" ]]; then
    log "🔧 设置 Docker Buildx"
    
    BUILDER_NAME="zen-builder"
    if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
        run_command "docker buildx create --name $BUILDER_NAME --driver docker-container --use"
    else
        run_command "docker buildx use $BUILDER_NAME"
    fi
    
    run_command "docker buildx inspect --bootstrap"
fi

# 构建参数
BUILD_CMD="docker"
if [[ "$PUSH_REGISTRY" == "true" ]]; then
    BUILD_CMD="$BUILD_CMD buildx build --platform $PLATFORMS"
    if [[ "$PUSH_REGISTRY" == "true" ]]; then
        BUILD_CMD="$BUILD_CMD --push"
    fi
else
    BUILD_CMD="$BUILD_CMD build"
fi

# 添加缓存参数
if [[ "$BUILD_CACHE" == "false" ]]; then
    BUILD_CMD="$BUILD_CMD --no-cache"
fi

# 添加构建参数
if [[ -n "$BUILD_ARGS" ]]; then
    BUILD_CMD="$BUILD_CMD $BUILD_ARGS"
fi

# 添加标签
BUILD_CMD="$BUILD_CMD -t $FULL_IMAGE_NAME:$VERSION"
BUILD_CMD="$BUILD_CMD -t $FULL_IMAGE_NAME:latest"

# 添加构建上下文
BUILD_CMD="$BUILD_CMD ."

# 执行构建
log "🏗️ 开始构建 Docker 镜像"
run_command "$BUILD_CMD"

# 如果是本地构建，显示镜像信息
if [[ "$PUSH_REGISTRY" == "false" && "$DRY_RUN" == "false" ]]; then
    log "📋 构建完成的镜像"
    docker images | grep "$NAMESPACE/$IMAGE_NAME" | head -5
    
    echo
    info "🚀 使用以下命令运行容器："
    echo "docker run -d --name zen-mcp-server \\"
    echo "  --env-file .env \\"
    echo "  -v \$(pwd)/logs:/app/logs \\"
    echo "  $FULL_IMAGE_NAME:$VERSION"
fi

# 推送到仓库的后续操作
if [[ "$PUSH_REGISTRY" == "true" && "$DRY_RUN" == "false" ]]; then
    log "✅ 镜像已推送到仓库"
    echo
    info "🌐 镜像地址:"
    echo "  $FULL_IMAGE_NAME:$VERSION"
    echo "  $FULL_IMAGE_NAME:latest"
    
    echo
    info "📥 使用以下命令拉取镜像："
    echo "docker pull $FULL_IMAGE_NAME:$VERSION"
    
    echo
    info "🚀 使用以下命令运行容器："
    echo "docker run -d --name zen-mcp-server \\"
    echo "  --env-file .env \\"
    echo "  -v \$(pwd)/logs:/app/logs \\"
    echo "  $FULL_IMAGE_NAME:$VERSION"
fi

# 生成部署模板
if [[ "$DRY_RUN" == "false" ]]; then
    DEPLOY_TEMPLATE="docker-deploy-template.yml"
    cat > "$DEPLOY_TEMPLATE" << EOF
# Zen MCP Server 部署模板
# 镜像: $FULL_IMAGE_NAME:$VERSION
# 生成时间: $(date)

version: '3.8'

services:
  zen-mcp-server:
    image: $FULL_IMAGE_NAME:$VERSION
    container_name: zen-mcp-server
    
    environment:
      # 基本配置
      - DEFAULT_MODEL=auto
      - LOG_LEVEL=INFO
      - PYTHONUNBUFFERED=1
      
      # API 密钥 (请填入您的密钥)
      - GEMINI_API_KEY=\${GEMINI_API_KEY}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
      - XAI_API_KEY=\${XAI_API_KEY}
      - OPENROUTER_API_KEY=\${OPENROUTER_API_KEY}
      
      # 优化功能配置
      - ZEN_FILE_OPTIMIZATION_ENABLED=true
      - ZEN_FILE_CACHE_MEMORY_MB=100
      - ZEN_FILE_CACHE_DISK_MB=500
      - ZEN_WORKFLOW_PERSISTENCE_ENABLED=true
      - ZEN_MONITORING_ENABLED=true
    
    volumes:
      - ./logs:/app/logs
      - zen-memory:/app/.zen_memory
      - zen-config:/app/conf
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "python", "/usr/local/bin/healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  zen-memory:
  zen-config:
EOF

    log "📄 已生成部署模板: $DEPLOY_TEMPLATE"
fi

log "🎉 Docker 镜像构建完成！"

if [[ "$DRY_RUN" == "false" ]]; then
    echo
    warn "💡 接下来的步骤："
    echo "1. 编辑 .env 文件并填入 API 密钥"
    echo "2. 使用生成的部署模板启动容器"
    echo "3. 执行健康检查验证部署"
    echo "4. 配置 Claude Desktop 连接到 MCP 服务器"
fi

exit 0