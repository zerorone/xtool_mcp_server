#!/bin/bash

# ===========================================
# XTool MCP Server 快速启动脚本
# Quick Start Script for XTool MCP Server
# ===========================================

# 这是一个便捷脚本，调用重新组织后的实际启动脚本
# This is a convenience script that calls the reorganized actual startup script

echo "🚀 XTool MCP Server - 快速启动"
echo "📂 项目结构已重新整理，脚本位置已更新"
echo ""

# 检查脚本是否存在
SCRIPT_PATH="build/scripts/run-server.sh"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 错误: 找不到启动脚本 $SCRIPT_PATH"
    echo "   请确保项目结构完整"
    exit 1
fi

# 使脚本可执行
chmod +x "$SCRIPT_PATH"

# 调用实际的启动脚本，传递所有参数
echo "📍 调用: $SCRIPT_PATH $@"
echo ""
exec "$SCRIPT_PATH" "$@"