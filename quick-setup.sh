#!/bin/bash

# ===========================================
# XTool MCP Server 快速设置脚本
# Quick Setup Script for Any Project
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 显示 Logo
show_logo() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════╗"
    echo "║      XTool MCP Server Setup           ║"
    echo "║      快速配置 AI 开发工具              ║"
    echo "╚═══════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查系统依赖...${NC}"
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装${NC}"
        echo "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    # 检查 Docker 是否运行
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker 未运行${NC}"
        echo "请启动 Docker Desktop"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 依赖检查通过${NC}"
}

# 检测已配置的 API Keys
detect_api_keys() {
    echo -e "\n${YELLOW}检测 API Keys...${NC}"
    
    local found_keys=0
    
    if [ ! -z "$OPENROUTER_API_KEY" ]; then
        echo -e "${GREEN}✅ OpenRouter API Key 已配置${NC}"
        ((found_keys++))
    fi
    
    if [ ! -z "$GEMINI_API_KEY" ]; then
        echo -e "${GREEN}✅ Gemini API Key 已配置${NC}"
        ((found_keys++))
    fi
    
    if [ ! -z "$OPENAI_API_KEY" ]; then
        echo -e "${GREEN}✅ OpenAI API Key 已配置${NC}"
        ((found_keys++))
    fi
    
    if [ ! -z "$XAI_API_KEY" ]; then
        echo -e "${GREEN}✅ X.AI API Key 已配置${NC}"
        ((found_keys++))
    fi
    
    if [ $found_keys -eq 0 ]; then
        echo -e "${YELLOW}⚠️  未检测到 API Key${NC}"
        echo -e "请至少配置一个 API Key："
        echo -e "  export OPENROUTER_API_KEY='your_key'"
        echo -e "  export GEMINI_API_KEY='your_key'"
        echo -e "  export OPENAI_API_KEY='your_key'"
    fi
    
    return $found_keys
}

# 创建 mcp.json
create_mcp_config() {
    echo -e "\n${YELLOW}创建配置文件...${NC}"
    
    if [ -f "mcp.json" ]; then
        echo -e "${YELLOW}mcp.json 已存在，是否覆盖？ (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "跳过创建配置文件"
            return
        fi
    fi
    
    cat > mcp.json << 'EOF'
{
  "mcpServers": {
    "xtool": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--name", "xtool-mcp-${USER}-$$",
        "-e", "GEMINI_API_KEY=${GEMINI_API_KEY}",
        "-e", "OPENAI_API_KEY=${OPENAI_API_KEY}",
        "-e", "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}",
        "-e", "XAI_API_KEY=${XAI_API_KEY}",
        "-e", "DIAL_API_KEY=${DIAL_API_KEY}",
        "-e", "CUSTOM_API_URL=${CUSTOM_API_URL}",
        "-v", "${HOME}/.xtool_memory:/app/.xtool_memory",
        "-v", "${PWD}:/workspace:ro",
        "ghcr.io/xiaocodepro/xtool-mcp-server:latest",
        "python", "/app/server.py"
      ]
    }
  }
}
EOF
    
    echo -e "${GREEN}✅ 配置文件创建成功${NC}"
}

# 显示使用说明
show_usage() {
    echo -e "\n${GREEN}🎉 设置完成！${NC}"
    echo -e "\n${BLUE}使用方法：${NC}"
    echo -e "1. 启动 Claude Code："
    echo -e "   ${YELLOW}claude .${NC}"
    echo -e ""
    echo -e "2. 使用 XTool 命令："
    echo -e "   ${YELLOW}xtool listmodels${NC}     - 查看可用模型"
    echo -e "   ${YELLOW}xtool chat${NC}           - AI 对话"
    echo -e "   ${YELLOW}xtool codereview${NC}     - 代码审查"
    echo -e "   ${YELLOW}xtool debug${NC}          - 智能调试"
    echo -e "   ${YELLOW}xtool planner${NC}        - 项目规划"
    echo -e ""
    echo -e "${BLUE}提示：${NC}"
    echo -e "- 首次使用会自动下载 Docker 镜像"
    echo -e "- 记忆数据保存在 ~/.xtool_memory"
    echo -e "- 查看更多工具：xtool listmodels"
}

# 主函数
main() {
    show_logo
    check_dependencies
    
    # 检测 API Keys
    detect_api_keys
    local has_keys=$?
    
    if [ $has_keys -eq 0 ]; then
        echo -e "\n${YELLOW}是否继续？(Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            echo "安装已取消"
            exit 0
        fi
    fi
    
    create_mcp_config
    show_usage
    
    # 拉取镜像（可选）
    echo -e "\n${YELLOW}是否现在拉取 Docker 镜像？(y/N)${NC}"
    echo "（也可以在首次使用时自动拉取）"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}正在拉取镜像...${NC}"
        docker pull ghcr.io/xiaocodepro/xtool-mcp-server:latest
        echo -e "${GREEN}✅ 镜像拉取完成${NC}"
    fi
}

# 运行主函数
main