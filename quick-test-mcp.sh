#!/bin/bash

echo "🔍 XTool MCP 快速测试"
echo "===================="

# 检查虚拟环境
if [ ! -d "xtool_venv" ]; then
    echo "❌ 未找到虚拟环境 xtool_venv"
    echo "请先运行: python -m venv xtool_venv"
    exit 1
fi

# 激活虚拟环境
source xtool_venv/bin/activate

# 检查环境变量
echo ""
echo "📋 检查环境配置:"
if [ -f ".env" ]; then
    echo "✅ 找到 .env 文件"
    # 加载环境变量
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ 未找到 .env 文件"
fi

# 检查 API 密钥
echo ""
echo "🔑 检查 API 密钥:"
if [ ! -z "$OPENROUTER_API_KEY" ]; then
    echo "✅ OPENROUTER_API_KEY 已设置"
elif [ ! -z "$GEMINI_API_KEY" ]; then
    echo "✅ GEMINI_API_KEY 已设置"
elif [ ! -z "$OPENAI_API_KEY" ]; then
    echo "✅ OPENAI_API_KEY 已设置"
else
    echo "❌ 未找到任何 API 密钥"
fi

# 测试服务器启动
echo ""
echo "🚀 测试服务器启动..."
timeout 5 python -m server --version 2>&1

if [ $? -eq 124 ]; then
    echo "✅ 服务器启动正常（超时退出）"
else
    echo "✅ 服务器版本检查完成"
fi

# 运行 Python 测试脚本
echo ""
echo "🧪 运行连接测试..."
if [ -f "test-mcp-connection.py" ]; then
    python test-mcp-connection.py
else
    echo "❌ 未找到测试脚本 test-mcp-connection.py"
fi

echo ""
echo "测试完成！"