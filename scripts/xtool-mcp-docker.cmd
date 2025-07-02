@echo off
REM Zen MCP Server Docker 启动脚本 (Windows)
REM 用于 Claude Code MCP 集成

REM 检查 Docker 容器是否运行
docker ps | findstr "zen-mcp-production" >nul
if %errorlevel% neq 0 (
    echo 错误: zen-mcp-production 容器未运行 >&2
    echo 请先启动容器: docker-compose -f docker-compose.production.yml up -d >&2
    exit /b 1
)

REM 执行 MCP 服务器
docker exec -i zen-mcp-production python server.py