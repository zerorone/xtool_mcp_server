#!/bin/bash
# Zen MCP Server Docker 启动脚本
# 用于 Claude Code MCP 集成

set -euo pipefail

# 检查 Docker 容器是否运行
if ! docker ps | grep -q "zen-mcp-production"; then
    echo "错误: zen-mcp-production 容器未运行" >&2
    echo "请先启动容器: docker-compose -f docker-compose.production.yml up -d" >&2
    exit 1
fi

# 执行 MCP 服务器
exec docker exec -i zen-mcp-production python server.py