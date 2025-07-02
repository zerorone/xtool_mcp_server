#!/bin/bash
# Zen MCP Server - 一键快速部署脚本
# 适用于新项目的快速集成

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

show_help() {
    cat << EOF
🚀 Zen MCP Server 一键部署工具

这个脚本将帮助您在几分钟内将 Zen MCP Server 部署到您的项目中。

用法: $0 [目标目录] [选项]

选项:
  -h, --help              显示此帮助信息
  --dev                   开发模式部署
  --minimal               最小化部署
  --with-monitoring       包含监控组件
  --api-key KEY           预设 API 密钥

示例:
  $0                                    # 在当前目录部署
  $0 /path/to/my-project               # 部署到指定目录
  $0 --dev                             # 开发模式部署
  $0 --minimal                         # 最小化部署
  $0 --api-key "your-key-here"         # 预设 API 密钥

支持的 API 提供商:
  - Google Gemini (推荐)
  - OpenAI GPT-4/O3
  - Anthropic Claude
  - xAI Grok
  - OpenRouter (多模型访问)
  - 自定义本地模型 (Ollama, vLLM 等)

EOF
}

# 默认配置
TARGET_DIR="${1:-$(pwd)/zen-mcp-server}"
DEPLOY_MODE="prod"
WITH_MONITORING=false
PRESET_API_KEY=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --dev)
            DEPLOY_MODE="dev"
            shift
            ;;
        --minimal)
            DEPLOY_MODE="minimal"
            shift
            ;;
        --with-monitoring)
            WITH_MONITORING=true
            shift
            ;;
        --api-key)
            PRESET_API_KEY="$2"
            shift 2
            ;;
        -*)
            warn "未知选项: $1"
            shift
            ;;
        *)
            if [[ ! "$1" =~ ^-- ]]; then
                TARGET_DIR="$1"
            fi
            shift
            ;;
    esac
done

# 规范化路径
TARGET_DIR="$(realpath "$TARGET_DIR" 2>/dev/null || echo "$TARGET_DIR")"

log "开始一键部署 Zen MCP Server"
echo "════════════════════════════════════════════════"
info "目标目录: $TARGET_DIR"
info "部署模式: $DEPLOY_MODE"
info "包含监控: $([ "$WITH_MONITORING" == "true" ] && echo "是" || echo "否")"
echo

# 步骤 1: 环境检查
log "步骤 1/6 - 环境检查"

# 检查 Docker
if command -v docker >/dev/null 2>&1; then
    info "✅ Docker 已安装"
    if docker info >/dev/null 2>&1; then
        info "✅ Docker 服务运行正常"
    else
        warn "Docker 服务未运行，请启动 Docker"
    fi
else
    warn "Docker 未安装，将使用 standalone 模式"
    DEPLOY_MODE="standalone"
fi

# 检查 Python (standalone 模式需要)
if [[ "$DEPLOY_MODE" == "standalone" ]]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        info "✅ Python $PYTHON_VERSION 已安装"
    else
        error "Python 3 未安装，请先安装 Python 3.9+"
    fi
fi

echo

# 步骤 2: 创建部署目录
log "步骤 2/6 - 创建部署目录"

if [[ -d "$TARGET_DIR" ]]; then
    warn "目标目录已存在: $TARGET_DIR"
    read -p "是否继续？现有文件可能被覆盖 (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "部署已取消"
        exit 0
    fi
fi

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"
info "✅ 目标目录已创建"

echo

# 步骤 3: 下载/复制 Zen MCP Server
log "步骤 3/6 - 获取 Zen MCP Server"

# 检查是否在 Zen 源码目录中运行
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/server.py" ]]; then
    info "从本地源码复制..."
    
    # 复制必要文件
    cp "$SCRIPT_DIR/Dockerfile" . 2>/dev/null || true
    cp "$SCRIPT_DIR/docker-compose.enhanced.yml" ./docker-compose.yml 2>/dev/null || true
    cp "$SCRIPT_DIR/requirements.txt" . 2>/dev/null || true
    cp -r "$SCRIPT_DIR/docker" . 2>/dev/null || true
    
    if [[ "$DEPLOY_MODE" == "standalone" ]]; then
        # Standalone 模式需要完整源码
        cp -r "$SCRIPT_DIR"/* . 2>/dev/null || true
        rm -rf .git tests simulator_tests 2>/dev/null || true
    fi
    
    info "✅ 已从本地源码复制文件"
else
    # 从 GitHub 下载（如果有 git 或 curl）
    if command -v git >/dev/null 2>&1; then
        info "从 GitHub 克隆..."
        git clone https://github.com/BeehiveInnovations/zen-mcp-server.git temp-zen
        mv temp-zen/* . 2>/dev/null || true
        mv temp-zen/.* . 2>/dev/null || true
        rm -rf temp-zen .git
        info "✅ 已从 GitHub 下载"
    else
        error "无法获取 Zen MCP Server 源码，请确保在源码目录中运行此脚本"
    fi
fi

echo

# 步骤 4: 配置环境
log "步骤 4/6 - 配置环境"

# 创建 .env 文件
cat > .env << EOF
# Zen MCP Server 环境配置
# 部署时间: $(date)
# 部署模式: $DEPLOY_MODE

# 基本配置
DEFAULT_MODEL=auto
LOG_LEVEL=$([ "$DEPLOY_MODE" == "dev" ] && echo "DEBUG" || echo "INFO")
TZ=$(date +%Z 2>/dev/null || echo "UTC")

# API 密钥配置
$(if [[ -n "$PRESET_API_KEY" ]]; then
    echo "GEMINI_API_KEY=$PRESET_API_KEY"
else
    echo "# GEMINI_API_KEY=your_gemini_key_here"
fi)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
# XAI_API_KEY=your_xai_key_here
# OPENROUTER_API_KEY=your_openrouter_key_here
# CUSTOM_API_URL=http://localhost:11434/v1  # Ollama 本地
# CUSTOM_API_KEY=not-needed                 # 本地模型通常不需要

# 增强功能配置
ZEN_FILE_OPTIMIZATION_ENABLED=true
ZEN_FILE_CACHE_MEMORY_MB=$([ "$DEPLOY_MODE" == "minimal" ] && echo "25" || echo "100")
ZEN_FILE_CACHE_DISK_MB=$([ "$DEPLOY_MODE" == "minimal" ] && echo "100" || echo "500")
ZEN_PARALLEL_FILE_READS=$([ "$DEPLOY_MODE" == "dev" ] && echo "5" || echo "10")

# 工作流配置
ZEN_WORKFLOW_PERSISTENCE_ENABLED=true
ZEN_WORKFLOW_MAX_STEPS=$([ "$DEPLOY_MODE" == "minimal" ] && echo "25" || echo "50")
ZEN_WORKFLOW_CLEANUP_INTERVAL=300

# 监控配置
ZEN_MONITORING_ENABLED=$([ "$WITH_MONITORING" == "true" ] && echo "true" || echo "false")
ZEN_HEALTH_CHECK_INTERVAL=30

# 资源限制
ZEN_MEMORY_LIMIT=$([ "$DEPLOY_MODE" == "minimal" ] && echo "256M" || [ "$DEPLOY_MODE" == "dev" ] && echo "512M" || echo "1G")
ZEN_CPU_LIMIT=$([ "$DEPLOY_MODE" == "minimal" ] && echo "0.25" || [ "$DEPLOY_MODE" == "dev" ] && echo "0.5" || echo "1.0")

# 端口配置
ZEN_HTTP_PORT=8080
$([ "$WITH_MONITORING" == "true" ] && echo "ZEN_PROMETHEUS_PORT=9090")

# 数据目录
ZEN_LOGS_PATH=./docker-data/logs
ZEN_MEMORY_PATH=./docker-data/memory
ZEN_CONFIG_PATH=./docker-data/config
ZEN_WORKFLOWS_PATH=./docker-data/workflows
ZEN_FILE_CACHE_PATH=./docker-data/file-cache
EOF

# 创建数据目录
mkdir -p docker-data/{logs,memory,config,workflows,file-cache}

info "✅ 环境配置已创建"

echo

# 步骤 5: 部署服务
log "步骤 5/6 - 部署服务"

case $DEPLOY_MODE in
    standalone)
        info "配置 Standalone 模式..."
        
        # 创建虚拟环境
        python3 -m venv .venv
        source .venv/bin/activate
        
        # 安装依赖
        pip install --upgrade pip
        pip install -r requirements.txt
        
        info "✅ Standalone 环境配置完成"
        ;;
    *)
        info "配置 Docker 模式..."
        
        # 构建镜像
        docker build -t zen-mcp-server:latest .
        
        info "✅ Docker 镜像构建完成"
        ;;
esac

echo

# 步骤 6: 创建启动脚本
log "步骤 6/6 - 创建管理脚本"

cat > manage.sh << 'EOF'
#!/bin/bash
# Zen MCP Server 管理脚本

set -euo pipefail

DEPLOY_MODE="__DEPLOY_MODE__"
WITH_MONITORING="__WITH_MONITORING__"

case ${1:-help} in
    start)
        echo "🚀 启动 Zen MCP Server..."
        if [[ "$DEPLOY_MODE" == "standalone" ]]; then
            source .venv/bin/activate
            nohup python server.py > logs/server.log 2>&1 &
            echo $! > .zen_pid
            echo "服务已在后台启动，PID: $(cat .zen_pid)"
        else
            if [[ "$WITH_MONITORING" == "true" ]]; then
                docker-compose up -d
            else
                docker run -d --name zen-mcp-server \
                    --env-file .env \
                    -v $(pwd)/docker-data/logs:/app/logs \
                    -v $(pwd)/docker-data/memory:/app/.zen_memory \
                    zen-mcp-server:latest
            fi
            echo "Docker 容器已启动"
        fi
        ;;
    stop)
        echo "🛑 停止 Zen MCP Server..."
        if [[ "$DEPLOY_MODE" == "standalone" ]]; then
            if [[ -f .zen_pid ]]; then
                kill $(cat .zen_pid) 2>/dev/null || true
                rm -f .zen_pid
            fi
            pkill -f "python server.py" 2>/dev/null || true
        else
            if [[ "$WITH_MONITORING" == "true" ]]; then
                docker-compose down
            else
                docker stop zen-mcp-server 2>/dev/null || true
                docker rm zen-mcp-server 2>/dev/null || true
            fi
        fi
        echo "服务已停止"
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        echo "📊 Zen MCP Server 状态:"
        if [[ "$DEPLOY_MODE" == "standalone" ]]; then
            if [[ -f .zen_pid ]] && kill -0 $(cat .zen_pid) 2>/dev/null; then
                echo "✅ 服务运行中，PID: $(cat .zen_pid)"
            else
                echo "❌ 服务未运行"
            fi
        else
            if docker ps | grep -q zen-mcp-server; then
                echo "✅ Docker 容器运行中"
                docker ps | grep zen-mcp-server
            else
                echo "❌ Docker 容器未运行"
            fi
        fi
        ;;
    logs)
        echo "📋 查看日志..."
        if [[ "$DEPLOY_MODE" == "standalone" ]]; then
            tail -f logs/mcp_server.log 2>/dev/null || echo "日志文件不存在"
        else
            if [[ "$WITH_MONITORING" == "true" ]]; then
                docker-compose logs -f zen-mcp-server
            else
                docker logs -f zen-mcp-server 2>/dev/null || echo "容器不存在"
            fi
        fi
        ;;
    health)
        echo "🏥 执行健康检查..."
        if [[ "$DEPLOY_MODE" == "standalone" ]]; then
            source .venv/bin/activate
            python docker/scripts/enhanced_healthcheck.py --enhanced 2>/dev/null || \
            python docker/scripts/healthcheck.py 2>/dev/null || \
            echo "健康检查脚本不可用"
        else
            if [[ "$WITH_MONITORING" == "true" ]]; then
                docker-compose exec zen-mcp-server python /usr/local/bin/enhanced_healthcheck.py --enhanced
            else
                docker exec zen-mcp-server python /usr/local/bin/enhanced_healthcheck.py --enhanced 2>/dev/null || \
                docker exec zen-mcp-server python /usr/local/bin/healthcheck.py 2>/dev/null || \
                echo "容器不可用或健康检查失败"
            fi
        fi
        ;;
    config)
        echo "⚙️ 编辑配置文件..."
        ${EDITOR:-nano} .env
        echo "配置文件已更新，请重启服务以应用更改"
        ;;
    *)
        echo "Zen MCP Server 管理工具"
        echo ""
        echo "用法: $0 {start|stop|restart|status|logs|health|config}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  logs    - 查看日志"
        echo "  health  - 健康检查"
        echo "  config  - 编辑配置"
        echo ""
        echo "部署模式: $DEPLOY_MODE"
        echo "监控功能: $([ "$WITH_MONITORING" == "true" ] && echo "启用" || echo "禁用")"
        ;;
esac
EOF

# 替换占位符
sed -i.bak "s/__DEPLOY_MODE__/$DEPLOY_MODE/g" manage.sh
sed -i.bak "s/__WITH_MONITORING__/$WITH_MONITORING/g" manage.sh
rm -f manage.sh.bak
chmod +x manage.sh

# 创建 Claude 配置
cat > claude_mcp_config.json << EOF
{
  "mcpServers": {
    "zen-mcp-server": {
      "command": "docker",
      "args": ["exec", "-i", "zen-mcp-server", "python", "server.py"],
      "env": {}
    }
  }
}
EOF

info "✅ 管理脚本已创建"

echo

# 完成部署
log "🎉 部署完成！"
echo "════════════════════════════════════════════════"
echo
info "📁 部署目录: $TARGET_DIR"
info "🚀 启动服务: ./manage.sh start"
info "📊 查看状态: ./manage.sh status"
info "🏥 健康检查: ./manage.sh health"
info "📋 查看日志: ./manage.sh logs"
info "⚙️ 编辑配置: ./manage.sh config"

echo
warn "⚠️  接下来的步骤："
echo "1. 编辑 .env 文件并填入至少一个 API 密钥"
echo "2. 运行 ./manage.sh start 启动服务"
echo "3. 运行 ./manage.sh health 验证部署"
echo "4. 将 claude_mcp_config.json 内容添加到 Claude 配置中"

echo
if [[ -z "$PRESET_API_KEY" ]]; then
    warn "🔑 没有 API 密钥？获取方式："
    echo "• Google Gemini: https://ai.google.dev/"
    echo "• OpenAI: https://platform.openai.com/"
    echo "• OpenRouter: https://openrouter.ai/ (一个账号访问多个模型)"
fi

echo
info "📚 需要帮助？查看文档:"
echo "• README.md - 基本使用说明"
echo "• ./manage.sh - 查看所有管理命令"

echo
log "✨ Zen MCP Server 已准备就绪！享受 AI 驱动的开发体验吧！"

exit 0