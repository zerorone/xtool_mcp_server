#!/bin/bash

# ===========================================
# XTool MCP Server 构建脚本
# Build Script for XTool MCP Server
# ===========================================

# Docker 构建快捷脚本
BUILD_CONTEXT="."
DOCKERFILE_PATH="build/docker/Dockerfile.lightweight"
IMAGE_NAME="xtool-mcp-server"
TAG="${1:-latest}"

echo "🔨 XTool MCP Server - Docker 构建"
echo "📂 Dockerfile: $DOCKERFILE_PATH"
echo "🏷️  镜像标签: $IMAGE_NAME:$TAG"
echo ""

# 检查 Dockerfile 是否存在
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo "❌ 错误: 找不到 Dockerfile: $DOCKERFILE_PATH"
    echo "   请确保项目结构完整"
    exit 1
fi

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装或不可用"
    exit 1
fi

# 构建镜像
echo "🚀 开始构建镜像..."
if docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_NAME:$TAG" "$BUILD_CONTEXT"; then
    echo ""
    echo "✅ 构建成功!"
    echo "📊 镜像信息:"
    docker images "$IMAGE_NAME:$TAG"
    echo ""
    echo "🎯 快速启动:"
    echo "   docker run -d --name xtool-mcp -e GEMINI_API_KEY=your_key $IMAGE_NAME:$TAG"
    echo ""
    echo "📝 完整文档: docs/deployment/DOCKER_DEPLOYMENT_GUIDE.md"
else
    echo ""
    echo "❌ 构建失败"
    exit 1
fi