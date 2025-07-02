#!/bin/bash
# 自动配置 Claude Code MCP 集成

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

CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/zen-mcp-docker.sh"

log "配置 Claude Code MCP 集成"
echo "=========================="

# 检查 Claude 配置目录
if [[ ! -d "$CLAUDE_CONFIG_DIR" ]]; then
    warn "Claude 配置目录不存在，正在创建..."
    mkdir -p "$CLAUDE_CONFIG_DIR"
fi

# 备份现有配置
if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
    warn "发现现有配置，正在备份..."
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d-%H%M%S)"
    info "备份已保存: $CLAUDE_CONFIG_FILE.backup.*"
fi

# 创建或更新配置
if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
    # 更新现有配置
    log "更新现有 Claude 配置..."
    
    # 使用 jq 如果可用，否则手动处理
    if command -v jq >/dev/null 2>&1; then
        # 使用 jq 更新配置
        tmp_file=$(mktemp)
        jq --arg script_path "$SCRIPT_PATH" '
        .mcpServers["zen-mcp-server"] = {
          "command": $script_path,
          "env": {
            "LOG_LEVEL": "INFO"
          }
        }' "$CLAUDE_CONFIG_FILE" > "$tmp_file"
        mv "$tmp_file" "$CLAUDE_CONFIG_FILE"
    else
        # 手动处理 JSON
        warn "未找到 jq，使用备用方法..."
        
        # 简单的 JSON 合并（假设现有配置格式正确）
        if grep -q '"mcpServers"' "$CLAUDE_CONFIG_FILE"; then
            # 已有 mcpServers 节点，需要添加
            sed -i.tmp 's/"mcpServers": {/"mcpServers": {\
    "zen-mcp-server": {\
      "command": "'"$SCRIPT_PATH"'",\
      "env": {\
        "LOG_LEVEL": "INFO"\
      }\
    },/' "$CLAUDE_CONFIG_FILE"
            rm -f "$CLAUDE_CONFIG_FILE.tmp"
        else
            # 没有 mcpServers 节点，需要创建
            sed -i.tmp 's/{/{\
  "mcpServers": {\
    "zen-mcp-server": {\
      "command": "'"$SCRIPT_PATH"'",\
      "env": {\
        "LOG_LEVEL": "INFO"\
      }\
    }\
  },/' "$CLAUDE_CONFIG_FILE"
            rm -f "$CLAUDE_CONFIG_FILE.tmp"
        fi
    fi
else
    # 创建新配置
    log "创建新的 Claude 配置..."
    cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "zen-mcp-server": {
      "command": "$SCRIPT_PATH",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
EOF
fi

# 验证配置文件
log "验证配置文件..."
if python3 -m json.tool "$CLAUDE_CONFIG_FILE" >/dev/null 2>&1; then
    info "✅ 配置文件格式正确"
else
    error "配置文件格式错误"
fi

# 显示配置内容
log "当前配置内容:"
echo "------------------------"
cat "$CLAUDE_CONFIG_FILE"
echo "------------------------"

# 检查启动脚本
log "验证启动脚本..."
if [[ -x "$SCRIPT_PATH" ]]; then
    info "✅ 启动脚本可执行"
else
    warn "启动脚本权限不足，正在修复..."
    chmod +x "$SCRIPT_PATH"
    info "✅ 已修复启动脚本权限"
fi

# 检查 Docker 容器
log "检查 Docker 容器状态..."
if docker ps | grep -q "zen-mcp-production"; then
    info "✅ zen-mcp-production 容器正在运行"
else
    warn "zen-mcp-production 容器未运行"
    echo "请运行以下命令启动容器:"
    echo "cd $(dirname "$SCRIPT_PATH")/.."
    echo "./docker-production.sh start"
fi

echo ""
log "🎉 配置完成！"
echo ""
info "📋 下一步操作:"
echo "1. 重启 Claude Code"
echo "2. 在 Claude Code 中测试: '使用 zen 的 version 工具显示版本信息'"
echo "3. 在 Claude Code 中测试: '使用 zen 的 listmodels 工具列出可用模型'"
echo ""
info "📂 配置文件位置: $CLAUDE_CONFIG_FILE"
info "📂 启动脚本位置: $SCRIPT_PATH"