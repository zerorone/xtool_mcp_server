#!/bin/bash

# ===========================================
# XTool MCP Server 直接运行方式配置脚本
# Direct Setup Script for Local Development
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
XTOOL_DIR="$(dirname "$SCRIPT_DIR")"

# 显示 Logo
show_logo() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════╗"
    echo "║      XTool MCP Server Setup           ║"
    echo "║      直接运行方式 - 记忆隔离           ║"
    echo "╚═══════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查Python环境
check_python() {
    echo -e "${YELLOW}检查Python环境...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        echo "请安装 Python 3.10 或更高版本"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 10 ]; then
        echo -e "${RED}❌ Python版本过低: $PYTHON_VERSION${NC}"
        echo "需要 Python 3.10 或更高版本"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"
}

# 创建虚拟环境
setup_virtual_env() {
    echo -e "${YELLOW}设置Python虚拟环境...${NC}"
    
    if [ -d "$XTOOL_DIR/xtool_venv" ]; then
        echo -e "${YELLOW}虚拟环境已存在，是否重新创建？ (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$XTOOL_DIR/xtool_venv"
        else
            echo -e "${GREEN}✅ 使用现有虚拟环境${NC}"
            return
        fi
    fi
    
    python3 -m venv "$XTOOL_DIR/xtool_venv"
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}安装依赖包...${NC}"
    
    # 激活虚拟环境
    source "$XTOOL_DIR/xtool_venv/bin/activate"
    
    # 升级pip
    pip install --upgrade pip --quiet
    
    # 安装依赖
    if [ -f "$XTOOL_DIR/requirements.txt" ]; then
        pip install -r "$XTOOL_DIR/requirements.txt" --quiet
    else
        echo -e "${RED}❌ requirements.txt 文件未找到${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
}

# 检测API Keys
detect_api_keys() {
    echo -e "${YELLOW}检测API Keys...${NC}"
    
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
    
    if [ ! -z "$DIAL_API_KEY" ]; then
        echo -e "${GREEN}✅ DIAL API Key 已配置${NC}"
        ((found_keys++))
    fi
    
    if [ $found_keys -eq 0 ]; then
        echo -e "${YELLOW}⚠️  未检测到API Key${NC}"
        echo -e "请至少配置一个API Key："
        echo -e "  ${YELLOW}export OPENROUTER_API_KEY='your_key'${NC}"
        echo -e "  ${YELLOW}export GEMINI_API_KEY='your_key'${NC}"
        echo -e "  ${YELLOW}export OPENAI_API_KEY='your_key'${NC}"
        echo -e "  ${YELLOW}export XAI_API_KEY='your_key'${NC}"
        echo ""
        echo -e "是否继续配置？(Y/n)"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            echo "配置已取消"
            exit 0
        fi
    fi
    
    return $found_keys
}

# 生成配置模板
generate_config_template() {
    echo -e "${YELLOW}生成配置模板...${NC}"
    
    # 确定Python可执行文件路径
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        PYTHON_PATH="$XTOOL_DIR/xtool_venv/Scripts/python.exe"
    else
        PYTHON_PATH="$XTOOL_DIR/xtool_venv/bin/python"
    fi
    
    # 生成配置模板
    cat > "$XTOOL_DIR/mcp-config-template.json" << EOF
{
  "mcpServers": {
    "xtool-mcp": {
      "command": "$PYTHON_PATH",
      "args": [
        "$XTOOL_DIR/server.py"
      ],
      "env": {
        "PYTHONPATH": "$XTOOL_DIR",
        "LOG_LEVEL": "INFO",
        "DEFAULT_MODEL": "google/gemini-2.5-flash",
        "MEMORY_TOOL_MODEL": "google/gemini-2.5-flash"
      }
    }
  }
}
EOF
    
    echo -e "${GREEN}✅ 配置模板已生成: mcp-config-template.json${NC}"
}

# 测试配置
test_setup() {
    echo -e "${YELLOW}测试服务器配置...${NC}"
    
    # 激活虚拟环境
    source "$XTOOL_DIR/xtool_venv/bin/activate"
    
    # 设置Python路径
    export PYTHONPATH="$XTOOL_DIR"
    
    # 测试导入
    if python3 -c "import server; print('✅ 服务器模块导入成功')" 2>/dev/null; then
        echo -e "${GREEN}✅ 服务器配置测试通过${NC}"
    else
        echo -e "${RED}❌ 服务器配置测试失败${NC}"
        echo "请检查依赖是否正确安装"
        exit 1
    fi
}

# 创建便捷脚本
create_helper_scripts() {
    echo -e "${YELLOW}创建便捷脚本...${NC}"
    
    # 创建启动脚本
    cat > "$XTOOL_DIR/start-server.sh" << EOF
#!/bin/bash
# XTool MCP Server 启动脚本
cd "$XTOOL_DIR"
source xtool_venv/bin/activate
export PYTHONPATH="$XTOOL_DIR"
python server.py
EOF
    
    chmod +x "$XTOOL_DIR/start-server.sh"
    
    # 创建测试脚本
    cat > "$XTOOL_DIR/test-server.sh" << EOF
#!/bin/bash
# XTool MCP Server 测试脚本
cd "$XTOOL_DIR"
source xtool_venv/bin/activate
export PYTHONPATH="$XTOOL_DIR"
python -c "
import server
print('✅ 服务器启动正常')
print('✅ 所有依赖已安装')
"
EOF
    
    chmod +x "$XTOOL_DIR/test-server.sh"
    
    echo -e "${GREEN}✅ 便捷脚本创建完成${NC}"
}

# 显示使用说明
show_usage() {
    echo -e "\n${GREEN}🎉 直接运行方式配置完成！${NC}"
    echo -e "\n${BLUE}配置信息：${NC}"
    echo -e "- XTool安装目录: ${YELLOW}$XTOOL_DIR${NC}"
    echo -e "- Python虚拟环境: ${YELLOW}$XTOOL_DIR/xtool_venv${NC}"
    echo -e "- 配置模板: ${YELLOW}$XTOOL_DIR/mcp-config-template.json${NC}"
    
    echo -e "\n${BLUE}使用步骤：${NC}"
    echo -e "1. ${YELLOW}配置API Key${NC}（如果还未配置）："
    echo -e "   export OPENROUTER_API_KEY='your_key'"
    echo -e ""
    echo -e "2. ${YELLOW}复制配置到目标项目${NC}："
    echo -e "   cp $XTOOL_DIR/mcp-config-template.json /path/to/your/project/.mcp.json"
    echo -e ""
    echo -e "3. ${YELLOW}在目标项目中启动Claude Code${NC}："
    echo -e "   cd /path/to/your/project"
    echo -e "   claude ."
    echo -e ""
    echo -e "${BLUE}便捷脚本：${NC}"
    echo -e "- 启动服务器: ${YELLOW}$XTOOL_DIR/start-server.sh${NC}"
    echo -e "- 测试服务器: ${YELLOW}$XTOOL_DIR/test-server.sh${NC}"
    
    echo -e "\n${BLUE}⭐ 记忆隔离特性：${NC}"
    echo -e "- 项目记忆: ${YELLOW}{项目目录}/.xtool_memory/${NC} （每个项目独立）"
    echo -e "- 全局记忆: ${YELLOW}~/.xtool_global_memory/${NC}"
    echo -e "- ${GREEN}✅ 多项目并行使用，记忆数据完全隔离${NC}"
    
    echo -e "\n${BLUE}验证安装：${NC}"
    echo -e "运行测试脚本: ${YELLOW}$XTOOL_DIR/test-server.sh${NC}"
}

# 主函数
main() {
    show_logo
    
    echo -e "${BLUE}开始配置 XTool MCP Server 直接运行方式...${NC}\n"
    
    # 检查环境
    check_python
    
    # 设置虚拟环境
    setup_virtual_env
    
    # 安装依赖
    install_dependencies
    
    # 检测API Keys
    detect_api_keys
    
    # 生成配置模板
    generate_config_template
    
    # 测试配置
    test_setup
    
    # 创建便捷脚本
    create_helper_scripts
    
    # 显示使用说明
    show_usage
    
    echo -e "\n${GREEN}✅ 所有配置已完成！${NC}"
}

# 运行主函数
main "$@"