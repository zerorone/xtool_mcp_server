#!/bin/bash

# ===========================================
# XTool MCP Wrapper for Claude Desktop
# ===========================================

# 确保容器在运行
if ! docker ps | grep -q "xtool-mcp"; then
    # 启动容器
    cd "$(dirname "$0")"
    ./start-local-service.sh start >/dev/null 2>&1
    
    # 等待容器启动
    sleep 2
fi

# 执行 MCP 服务器
exec docker exec -i xtool-mcp python /app/server.py