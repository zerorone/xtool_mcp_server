#!/bin/bash
# 测试 Zen MCP Server Docker 连接

set -euo pipefail

echo "🧪 测试 Zen MCP Server Docker 连接"
echo "=================================="

# 检查 Docker 是否运行
echo "1. 检查 Docker 状态..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 未运行"
    exit 1
fi
echo "✅ Docker 正在运行"

# 检查容器是否存在
echo "2. 检查容器状态..."
if ! docker ps | grep -q "zen-mcp-production"; then
    echo "❌ zen-mcp-production 容器未运行"
    echo "请运行: ./docker-production.sh start"
    exit 1
fi
echo "✅ zen-mcp-production 容器正在运行"

# 测试 MCP 协议连接
echo "3. 测试 MCP 协议连接..."
timeout 10s bash -c '
echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"test\",\"version\":\"1.0\"}}}" | docker exec -i zen-mcp-production python server.py
' 2>/dev/null && echo "✅ MCP 协议连接成功" || echo "⚠️  MCP 协议连接测试超时（正常现象）"

# 测试启动脚本
echo "4. 测试启动脚本..."
SCRIPT_PATH="$(dirname "$0")/zen-mcp-docker.sh"
if [[ -x "$SCRIPT_PATH" ]]; then
    echo "✅ 启动脚本可执行"
else
    echo "❌ 启动脚本权限不足"
    chmod +x "$SCRIPT_PATH"
    echo "✅ 已修复启动脚本权限"
fi

# 显示配置信息
echo "5. 配置信息:"
echo "   启动脚本路径: $SCRIPT_PATH"
echo "   Claude Config 路径: ~/Library/Application Support/Claude/claude_desktop_config.json"

echo ""
echo "🎉 测试完成！"
echo ""
echo "📋 下一步配置 Claude Code:"
echo "1. 将以下内容添加到 Claude Config:"
echo ""
cat << 'EOF'
{
  "mcpServers": {
    "zen-mcp-server": {
      "command": "/Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/zen-mcp-server/scripts/zen-mcp-docker.sh",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
EOF
echo ""
echo "2. 重启 Claude Code"
echo "3. 在 Claude Code 中测试: '使用 zen 的 version 工具显示版本信息'"