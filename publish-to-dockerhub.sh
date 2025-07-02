#!/bin/bash

# ===========================================
# 发布 XTool MCP Server 到 Docker Hub
# Publish to Docker Hub for easier access
# ===========================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Docker Hub 配置
DOCKER_USERNAME="xiaocodepro"
IMAGE_NAME="xtool-mcp-server"
VERSION=$(git describe --tags --always 2>/dev/null || echo "latest")

echo -e "${BLUE}🚀 发布 XTool MCP Server 到 Docker Hub${NC}"
echo ""

# 1. 检查是否登录
echo -e "${YELLOW}1. 检查 Docker Hub 登录状态...${NC}"
if ! docker info 2>/dev/null | grep -q "Username: ${DOCKER_USERNAME}"; then
    echo -e "${YELLOW}需要登录 Docker Hub${NC}"
    docker login -u ${DOCKER_USERNAME}
fi

# 2. 构建多平台镜像
echo -e "${YELLOW}2. 构建多平台镜像...${NC}"
docker buildx create --use --name xtool-builder 2>/dev/null || true
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DOCKER_USERNAME}/${IMAGE_NAME}:latest \
    -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} \
    --push \
    .

# 3. 显示结果
echo -e "${GREEN}✅ 发布成功！${NC}"
echo ""
echo -e "${BLUE}用户现在可以使用：${NC}"
echo ""
echo "1. 在 mcp.json 中配置："
cat << EOF
{
  "mcpServers": {
    "xtool": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "OPENROUTER_API_KEY=\${OPENROUTER_API_KEY}",
        "-v", "\${HOME}/.xtool_memory:/app/.xtool_memory",
        "${DOCKER_USERNAME}/${IMAGE_NAME}:latest",
        "python", "/app/server.py"
      ]
    }
  }
}
EOF
echo ""
echo "2. 或使用一键安装："
echo "   curl -fsSL https://raw.githubusercontent.com/xiaocodepro/xtool-mcp-server/main/quick-setup.sh | bash"
echo ""
echo -e "${GREEN}镜像信息：${NC}"
echo "- Docker Hub: https://hub.docker.com/r/${DOCKER_USERNAME}/${IMAGE_NAME}"
echo "- 支持平台: linux/amd64, linux/arm64"
echo "- 版本标签: latest, ${VERSION}"