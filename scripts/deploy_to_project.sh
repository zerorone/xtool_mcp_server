#!/bin/bash
# Zen MCP Server - 跨项目部署脚本
# 将优化后的 Zen MCP Server 部署到其他项目中

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
🚀 Zen MCP Server 跨项目部署工具

用法: $0 [选项] <目标项目路径>

选项:
  -h, --help              显示此帮助信息
  -m, --mode MODE         部署模式 (docker|compose|standalone) [默认: compose]
  -p, --profile PROFILE   部署配置 (dev|prod|minimal) [默认: prod]
  -e, --env-file FILE     环境变量文件路径 [可选]
  -n, --name NAME         容器/服务名称 [默认: zen-mcp-\$PROJECT_NAME]
  --skip-build           跳过 Docker 镜像构建
  --skip-health-check    跳过健康检查
  --dry-run              仅显示要执行的操作，不实际执行

部署模式:
  docker      - 单独的 Docker 容器部署
  compose     - Docker Compose 部署（推荐）
  standalone  - 复制源代码并本地运行

配置档案:
  dev         - 开发环境（启用调试、详细日志）
  prod        - 生产环境（优化性能、安全加固）
  minimal     - 最小配置（基础功能）

示例:
  $0 /path/to/my-project                    # 使用默认配置部署
  $0 -m docker -p dev /path/to/my-project   # Docker 开发模式部署
  $0 -e my.env --name my-zen /path/to/proj  # 使用自定义环境文件

EOF
}

# 默认配置
DEPLOY_MODE="compose"
DEPLOY_PROFILE="prod"
ENV_FILE=""
CONTAINER_NAME=""
SKIP_BUILD=false
SKIP_HEALTH_CHECK=false
DRY_RUN=false
ZEN_SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -m|--mode)
            DEPLOY_MODE="$2"
            shift 2
            ;;
        -p|--profile)
            DEPLOY_PROFILE="$2"
            shift 2
            ;;
        -e|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-health-check)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -*)
            error "未知选项: $1"
            ;;
        *)
            TARGET_PROJECT_PATH="$1"
            shift
            ;;
    esac
done

# 检查必要参数
if [[ -z "${TARGET_PROJECT_PATH:-}" ]]; then
    error "请指定目标项目路径"
fi

# 验证部署模式
case $DEPLOY_MODE in
    docker|compose|standalone)
        ;;
    *)
        error "无效的部署模式: $DEPLOY_MODE（支持: docker, compose, standalone）"
        ;;
esac

# 验证部署配置
case $DEPLOY_PROFILE in
    dev|prod|minimal)
        ;;
    *)
        error "无效的部署配置: $DEPLOY_PROFILE（支持: dev, prod, minimal）"
        ;;
esac

# 规范化路径
TARGET_PROJECT_PATH="$(realpath "$TARGET_PROJECT_PATH")"
PROJECT_NAME="$(basename "$TARGET_PROJECT_PATH")"

# 设置默认容器名
if [[ -z "$CONTAINER_NAME" ]]; then
    CONTAINER_NAME="zen-mcp-${PROJECT_NAME}"
fi

# 验证目标路径
if [[ ! -d "$TARGET_PROJECT_PATH" ]]; then
    error "目标项目路径不存在: $TARGET_PROJECT_PATH"
fi

if [[ ! -w "$TARGET_PROJECT_PATH" ]]; then
    error "目标项目路径不可写: $TARGET_PROJECT_PATH"
fi

# 验证 Zen 源码目录
if [[ ! -f "$ZEN_SOURCE_DIR/server.py" ]]; then
    error "Zen MCP Server 源码目录无效: $ZEN_SOURCE_DIR"
fi

log "🎯 准备部署 Zen MCP Server"
info "源码目录: $ZEN_SOURCE_DIR"
info "目标项目: $TARGET_PROJECT_PATH"
info "项目名称: $PROJECT_NAME"
info "部署模式: $DEPLOY_MODE"
info "部署配置: $DEPLOY_PROFILE"
info "容器名称: $CONTAINER_NAME"

# 创建部署目录
ZEN_DEPLOY_DIR="$TARGET_PROJECT_PATH/zen-mcp-server"

if [[ "$DRY_RUN" == "true" ]]; then
    info "🧪 DRY RUN 模式 - 仅显示操作，不实际执行"
    echo
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

# 创建部署目录
log "📁 创建部署目录"
run_command "mkdir -p '$ZEN_DEPLOY_DIR'"

# 复制必要文件
log "📋 复制部署文件"

case $DEPLOY_MODE in
    docker)
        run_command "cp '$ZEN_SOURCE_DIR/Dockerfile' '$ZEN_DEPLOY_DIR/'"
        run_command "cp '$ZEN_SOURCE_DIR/requirements.txt' '$ZEN_DEPLOY_DIR/'"
        run_command "cp -r '$ZEN_SOURCE_DIR/docker' '$ZEN_DEPLOY_DIR/'"
        ;;
    compose)
        run_command "cp '$ZEN_SOURCE_DIR/Dockerfile' '$ZEN_DEPLOY_DIR/'"
        run_command "cp '$ZEN_SOURCE_DIR/docker-compose.enhanced.yml' '$ZEN_DEPLOY_DIR/docker-compose.yml'"
        run_command "cp '$ZEN_SOURCE_DIR/requirements.txt' '$ZEN_DEPLOY_DIR/'"
        run_command "cp -r '$ZEN_SOURCE_DIR/docker' '$ZEN_DEPLOY_DIR/'"
        ;;
    standalone)
        # 复制完整源码
        run_command "cp -r '$ZEN_SOURCE_DIR'/* '$ZEN_DEPLOY_DIR/'"
        # 移除不必要的文件
        run_command "rm -rf '$ZEN_DEPLOY_DIR'/.git '$ZEN_DEPLOY_DIR'/tests '$ZEN_DEPLOY_DIR'/simulator_tests"
        ;;
esac

# 创建环境配置文件
log "⚙️  创建环境配置"

ENV_FILE_PATH="$ZEN_DEPLOY_DIR/.env"

if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
    run_command "cp '$ENV_FILE' '$ENV_FILE_PATH'"
else
    # 生成默认环境文件
    # 根据配置档案设置值
    if [[ "$DEPLOY_PROFILE" == "dev" ]]; then
        LOG_LEVEL_VAL="DEBUG"
        CACHE_MEMORY_MB="100"
        CACHE_DISK_MB="500" 
        PARALLEL_READS="5"
        MAX_STEPS="50"
        MEMORY_LIMIT="512M"
        CPU_LIMIT="0.5"
    elif [[ "$DEPLOY_PROFILE" == "minimal" ]]; then
        LOG_LEVEL_VAL="INFO"
        CACHE_MEMORY_MB="50"
        CACHE_DISK_MB="200"
        PARALLEL_READS="10"
        MAX_STEPS="25"
        MEMORY_LIMIT="256M"
        CPU_LIMIT="0.25"
    else
        LOG_LEVEL_VAL="INFO"
        CACHE_MEMORY_MB="100"
        CACHE_DISK_MB="500"
        PARALLEL_READS="10"
        MAX_STEPS="50"
        MEMORY_LIMIT="1G"
        CPU_LIMIT="1.0"
    fi

    cat > "$ENV_FILE_PATH" << EOF
# Zen MCP Server 环境配置
# 项目: $PROJECT_NAME
# 生成时间: $(date)

# 基本配置
DEFAULT_MODEL=auto
LOG_LEVEL=$LOG_LEVEL_VAL
TZ=$(date +%Z)

# API 密钥（请填入您的密钥）
# GEMINI_API_KEY=your_gemini_key_here
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
# XAI_API_KEY=your_xai_key_here
# OPENROUTER_API_KEY=your_openrouter_key_here

# 增强功能配置
ZEN_FILE_OPTIMIZATION_ENABLED=true
ZEN_FILE_CACHE_MEMORY_MB=$CACHE_MEMORY_MB
ZEN_FILE_CACHE_DISK_MB=$CACHE_DISK_MB
ZEN_PARALLEL_FILE_READS=$PARALLEL_READS

# 工作流配置
ZEN_WORKFLOW_PERSISTENCE_ENABLED=true
ZEN_WORKFLOW_MAX_STEPS=$MAX_STEPS
ZEN_WORKFLOW_CLEANUP_INTERVAL=300

# 监控配置
ZEN_MONITORING_ENABLED=true
ZEN_HEALTH_CHECK_INTERVAL=30

# 资源限制
ZEN_MEMORY_LIMIT=$MEMORY_LIMIT
ZEN_CPU_LIMIT=$CPU_LIMIT

# 容器配置
ZEN_HTTP_PORT=8080
ZEN_PROMETHEUS_PORT=9090

# 数据目录
ZEN_LOGS_PATH=./docker-data/logs
ZEN_MEMORY_PATH=./docker-data/memory
ZEN_CONFIG_PATH=./docker-data/config
ZEN_WORKFLOWS_PATH=./docker-data/workflows
ZEN_FILE_CACHE_PATH=./docker-data/file-cache
EOF

    if [[ "$DRY_RUN" != "true" ]]; then
        log "📄 已创建默认环境配置文件: $ENV_FILE_PATH"
        warn "请编辑 $ENV_FILE_PATH 并填入您的 API 密钥"
    fi
fi

# 创建数据目录
log "📂 创建数据目录"
case $DEPLOY_MODE in
    docker|compose)
        run_command "mkdir -p '$ZEN_DEPLOY_DIR/docker-data/{logs,memory,config,workflows,file-cache}'"
        ;;
    standalone)
        run_command "mkdir -p '$ZEN_DEPLOY_DIR/{logs,.zen_memory,.zen_memory/file_cache,.zen_memory/workflow_states}'"
        ;;
esac

# 创建部署脚本
log "📜 创建部署脚本"

DEPLOY_SCRIPT="$ZEN_DEPLOY_DIR/deploy.sh"
cat > "$DEPLOY_SCRIPT" << EOF
#!/bin/bash
# Zen MCP Server 部署脚本 - $PROJECT_NAME
# 生成时间: $(date)

set -euo pipefail

cd "\$(dirname "\${BASH_SOURCE[0]}")"

case \${1:-start} in
    start|up)
        echo "🚀 启动 Zen MCP Server..."
        $(case $DEPLOY_MODE in
            docker)
                echo "docker build -t zen-mcp-server:latest ."
                echo "docker run -d --name $CONTAINER_NAME --env-file .env -v \$(pwd)/docker-data/logs:/app/logs zen-mcp-server:latest"
                ;;
            compose)
                echo "docker-compose up -d"
                ;;
            standalone)
                echo "python -m venv .venv"
                echo "source .venv/bin/activate"
                echo "pip install -r requirements.txt"
                echo "python server.py"
                ;;
        esac)
        ;;
    stop|down)
        echo "🛑 停止 Zen MCP Server..."
        $(case $DEPLOY_MODE in
            docker)
                echo "docker stop $CONTAINER_NAME || true"
                echo "docker rm $CONTAINER_NAME || true"
                ;;
            compose)
                echo "docker-compose down"
                ;;
            standalone)
                echo "pkill -f server.py || true"
                ;;
        esac)
        ;;
    restart)
        echo "🔄 重启 Zen MCP Server..."
        \$0 stop
        sleep 2
        \$0 start
        ;;
    status)
        echo "📊 检查 Zen MCP Server 状态..."
        $(case $DEPLOY_MODE in
            docker)
                echo "docker ps | grep $CONTAINER_NAME"
                echo "docker logs --tail 20 $CONTAINER_NAME"
                ;;
            compose)
                echo "docker-compose ps"
                echo "docker-compose logs --tail 20"
                ;;
            standalone)
                echo "pgrep -f server.py || echo 'Not running'"
                echo "tail -n 20 logs/mcp_server.log || echo 'No logs found'"
                ;;
        esac)
        ;;
    logs)
        echo "📋 查看日志..."
        $(case $DEPLOY_MODE in
            docker)
                echo "docker logs -f $CONTAINER_NAME"
                ;;
            compose)
                echo "docker-compose logs -f"
                ;;
            standalone)
                echo "tail -f logs/mcp_server.log"
                ;;
        esac)
        ;;
    health)
        echo "🏥 执行健康检查..."
        $(case $DEPLOY_MODE in
            docker)
                echo "docker exec $CONTAINER_NAME python /usr/local/bin/enhanced_healthcheck.py --enhanced"
                ;;
            compose)
                echo "docker-compose exec zen-mcp-server python /usr/local/bin/enhanced_healthcheck.py --enhanced"
                ;;
            standalone)
                echo "python docker/scripts/enhanced_healthcheck.py --enhanced"
                ;;
        esac)
        ;;
    *)
        echo "用法: \$0 {start|stop|restart|status|logs|health}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  logs    - 查看日志"
        echo "  health  - 健康检查"
        exit 1
        ;;
esac
EOF

run_command "chmod +x '$DEPLOY_SCRIPT'"

# 创建 Claude 配置文件
log "🧠 创建 Claude 配置文件"
CLAUDE_CONFIG="$ZEN_DEPLOY_DIR/claude_mcp_config.json"

cat > "$CLAUDE_CONFIG" << EOF
{
  "mcpServers": {
    "zen-mcp-${PROJECT_NAME}": {
      "command": "docker",
      "args": ["exec", "-i", "$CONTAINER_NAME", "python", "server.py"],
      "env": {}
    }
  }
}
EOF

if [[ "$DRY_RUN" != "true" ]]; then
    log "📄 已创建 Claude 配置文件: $CLAUDE_CONFIG"
fi

# 构建 Docker 镜像（如果需要）
if [[ "$DEPLOY_MODE" != "standalone" && "$SKIP_BUILD" != "true" ]]; then
    log "🏗️  构建 Docker 镜像"
    run_command "cd '$ZEN_DEPLOY_DIR' && docker build -t zen-mcp-server:${PROJECT_NAME} ."
fi

# 创建使用说明
README_FILE="$ZEN_DEPLOY_DIR/README.md"
cat > "$README_FILE" << EOF
# Zen MCP Server - $PROJECT_NAME

这是为项目 **$PROJECT_NAME** 部署的 Zen MCP Server 实例。

## 🚀 快速开始

### 1. 配置 API 密钥
编辑 \`.env\` 文件，填入您的 API 密钥：
\`\`\`bash
nano .env
\`\`\`

### 2. 启动服务
\`\`\`bash
./deploy.sh start
\`\`\`

### 3. 验证部署
\`\`\`bash
./deploy.sh health
\`\`\`

## 📋 可用命令

- \`./deploy.sh start\` - 启动服务
- \`./deploy.sh stop\` - 停止服务
- \`./deploy.sh restart\` - 重启服务
- \`./deploy.sh status\` - 查看状态
- \`./deploy.sh logs\` - 查看日志
- \`./deploy.sh health\` - 健康检查

## 🧠 Claude 集成

1. 复制 \`claude_mcp_config.json\` 的内容
2. 添加到您的 Claude 配置文件中
3. 重启 Claude Desktop

## 📊 监控面板

$(if [[ "$DEPLOY_MODE" == "compose" ]]; then
    echo "- Prometheus: http://localhost:9090"
    echo "- Zen HTTP API: http://localhost:8080"
fi)

## ⚙️ 配置信息

- **部署模式**: $DEPLOY_MODE
- **配置档案**: $DEPLOY_PROFILE
- **容器名称**: $CONTAINER_NAME
- **生成时间**: $(date)

## 🔧 高级功能

### 文件处理优化
- ✅ 智能文件缓存
- ✅ 异步并行读取
- ✅ 大文件自动摘要
- ✅ 令牌预算优化

### 工作流管理
- ✅ 状态持久化
- ✅ 线程安全处理
- ✅ 资源限制保护
- ✅ 自动清理机制

### 监控和度量
- ✅ 实时健康检查
- ✅ 性能统计
- ✅ 缓存监控
- ✅ 工作流追踪

## 📞 支持

如需帮助，请查看：
- [Zen MCP Server 文档](https://github.com/BeehiveInnovations/zen-mcp-server)
- [问题报告](https://github.com/BeehiveInnovations/zen-mcp-server/issues)

---
*此部署由 Zen MCP Server 部署工具自动生成*
EOF

if [[ "$DRY_RUN" != "true" ]]; then
    log "📚 已创建使用说明: $README_FILE"
fi

# 执行健康检查（如果不跳过）
if [[ "$SKIP_HEALTH_CHECK" != "true" && "$DRY_RUN" != "true" ]]; then
    log "🏥 执行部署后健康检查"
    
    if [[ "$DEPLOY_MODE" == "standalone" ]]; then
        if [[ -f "$ZEN_DEPLOY_DIR/docker/scripts/enhanced_healthcheck.py" ]]; then
            cd "$ZEN_DEPLOY_DIR"
            if python docker/scripts/enhanced_healthcheck.py; then
                log "✅ 健康检查通过"
            else
                warn "⚠️ 健康检查未完全通过，请检查配置"
            fi
        fi
    fi
fi

# 部署完成
echo
log "🎉 Zen MCP Server 部署完成！"
echo
info "📁 部署目录: $ZEN_DEPLOY_DIR"
info "🚀 启动服务: cd '$ZEN_DEPLOY_DIR' && ./deploy.sh start"
info "📋 查看日志: cd '$ZEN_DEPLOY_DIR' && ./deploy.sh logs"
info "🏥 健康检查: cd '$ZEN_DEPLOY_DIR' && ./deploy.sh health"
echo
warn "⚠️ 请记得编辑 $ZEN_DEPLOY_DIR/.env 文件并填入您的 API 密钥！"
echo

exit 0