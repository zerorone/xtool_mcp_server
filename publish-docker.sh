#!/bin/bash

# ===========================================
# 发布 XTool MCP Server Docker 镜像
# ===========================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 配置
REGISTRY="ghcr.io"
NAMESPACE="xiaocodepro"
IMAGE_NAME="xtool-mcp-server"
VERSION="latest"

echo -e "${BLUE}🚀 开始发布 XTool MCP Server Docker 镜像${NC}"
echo ""

# 1. 构建镜像
echo -e "${YELLOW}1. 构建 Docker 镜像...${NC}"
docker build -t ${IMAGE_NAME}:${VERSION} .

# 2. 标记镜像
echo -e "${YELLOW}2. 标记镜像...${NC}"
docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}

# 3. 登录 GitHub Container Registry
echo -e "${YELLOW}3. 登录 GitHub Container Registry...${NC}"
echo -e "${RED}请确保已经设置了 GITHUB_TOKEN 环境变量${NC}"
echo $GITHUB_TOKEN | docker login ${REGISTRY} -u ${GITHUB_USERNAME} --password-stdin

# 4. 推送镜像
echo -e "${YELLOW}4. 推送镜像到 ${REGISTRY}...${NC}"
docker push ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}

echo -e "${GREEN}✅ 发布完成！${NC}"
echo ""
echo -e "用户现在可以直接使用："
echo -e "${BLUE}${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}${NC}"
echo ""
echo -e "在 mcp.json 中配置："
cat << EOF
{
  "mcpServers": {
    "xtool": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "OPENROUTER_API_KEY=\${OPENROUTER_API_KEY}",
        "${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}",
        "python", "/app/server.py"
      ]
    }
  }
}
EOF