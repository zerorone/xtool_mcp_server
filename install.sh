#!/bin/bash

# ===========================================
# XTool MCP Server 安装脚本
# ===========================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 XTool MCP Server 安装程序${NC}"
echo ""

# 检查 Docker
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未安装或未运行${NC}"
    echo "请先安装并启动 Docker Desktop"
    exit 1
fi

# 获取当前目录
XTOOL_DIR="$(pwd)"

# 创建符号链接到 /usr/local/bin
echo -e "${YELLOW}需要管理员权限来创建全局命令...${NC}"
sudo ln -sf "$XTOOL_DIR/xtool" /usr/local/bin/xtool

echo -e "${GREEN}✅ 安装完成！${NC}"
echo ""
echo -e "${BLUE}📋 使用方法：${NC}"
echo ""
echo "1. 在任意项目目录创建 mcp.json 文件："
echo ""
cat << 'EOF'
{
  "mcpServers": {
    "xtool": {
      "command": "xtool"
    }
  }
}
EOF
echo ""
echo "2. 在该目录启动 Claude Code："
echo "   claude ."
echo ""
echo "3. 使用 xtool 命令："
echo "   - xtool listmodels"
echo "   - xtool chat"
echo "   - xtool thinkdeep"
echo "   - xtool codereview"
echo "   等等..."
echo ""
echo -e "${GREEN}提示：XTool 会在首次使用时自动启动 Docker 容器${NC}"