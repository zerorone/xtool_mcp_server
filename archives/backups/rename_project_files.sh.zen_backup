#!/bin/bash

echo "🔄 重命名项目文件：从 zen 更新为 xtool"
echo "=================================================="

# 定义重命名映射数组
declare -a old_files=(
    "docs/zen_development_usage_guide.md"
    "docs/zen_self_development_plan.md"
    "docs/zen_usage_guide.md"
    "docs/zen_advisor_guide.md"
    "docs/TODO_zen_development.md"
    "scripts/zen-mcp-docker.cmd"
    "scripts/zen-mcp-docker.sh"
    "test_zen_advisor_production.py"
    "systemprompts/zen_advisor.md"
    "tools/zen_advisor.py"
)

declare -a new_files=(
    "docs/xtool_development_usage_guide.md"
    "docs/xtool_self_development_plan.md"
    "docs/xtool_usage_guide.md"
    "docs/xtool_advisor_guide.md"
    "docs/TODO_xtool_development.md"
    "scripts/xtool-mcp-docker.cmd"
    "scripts/xtool-mcp-docker.sh"
    "test_xtool_advisor_production.py"
    "systemprompts/xtool_advisor.md"
    "tools/xtool_advisor.py"
)

echo "📋 将要重命名的文件："
for i in "${!old_files[@]}"; do
    old_file="${old_files[$i]}"
    new_file="${new_files[$i]}"
    if [ -f "$old_file" ]; then
        echo "  ✅ $old_file → $new_file"
    else
        echo "  ❌ $old_file (文件不存在)"
    fi
done

read -p "🤔 确认执行重命名操作？(y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "❌ 取消操作"
    exit 0
fi

echo ""
echo "🚀 开始重命名操作..."

# 执行重命名
for i in "${!old_files[@]}"; do
    old_file="${old_files[$i]}"
    new_file="${new_files[$i]}"
    if [ -f "$old_file" ]; then
        echo "📝 重命名: $old_file → $new_file"
        
        # 创建目标目录（如果不存在）
        mkdir -p "$(dirname "$new_file")"
        
        # 执行重命名
        git mv "$old_file" "$new_file" 2>/dev/null || mv "$old_file" "$new_file"
        
        if [ $? -eq 0 ]; then
            echo "  ✅ 成功"
        else
            echo "  ❌ 失败"
        fi
    else
        echo "⚠️  跳过不存在的文件: $old_file"
    fi
done

echo ""
echo "🔍 更新文件内容中的引用..."

# 更新文件内容中的zen相关引用
echo "📝 更新导入语句和引用..."

# 更新 tools/__init__.py 中的导入
if [ -f "tools/__init__.py" ]; then
    sed -i.bak 's/from \.zen_advisor import ZenAdvisorTool/from .xtool_advisor import XtoolAdvisorTool/g' tools/__init__.py
    sed -i.bak 's/"ZenAdvisorTool"/"XtoolAdvisorTool"/g' tools/__init__.py
    echo "  ✅ 更新 tools/__init__.py"
fi

# 更新 server.py 中的引用
if [ -f "server.py" ]; then
    sed -i.bak 's/ZenAdvisorTool/XtoolAdvisorTool/g' server.py
    echo "  ✅ 更新 server.py"
fi

# 更新所有Python文件中的类名引用
find . -name "*.py" -not -path "./.zen_venv/*" -not -path "./__pycache__/*" -exec sed -i.bak 's/ZenAdvisorTool/XtoolAdvisorTool/g' {} \;
echo "  ✅ 更新所有Python文件中的类名引用"

# 更新重命名后的工具文件内部的类名
if [ -f "tools/xtool_advisor.py" ]; then
    sed -i.bak 's/class ZenAdvisorTool/class XtoolAdvisorTool/g' tools/xtool_advisor.py
    sed -i.bak 's/ZenAdvisor/XtoolAdvisor/g' tools/xtool_advisor.py
    echo "  ✅ 更新 xtool_advisor.py 内部类名"
fi

# 更新文档中的工具引用
find docs/ -name "*.md" -exec sed -i.bak 's/zen_advisor/xtool_advisor/g' {} \;
find docs/ -name "*.md" -exec sed -i.bak 's/ZenAdvisor/XtoolAdvisor/g' {} \;
echo "  ✅ 更新文档中的工具引用"

# 清理备份文件
echo "🧹 清理备份文件..."
find . -name "*.bak" -type f -delete

echo ""
echo "✅ 文件重命名完成！"
echo ""
echo "📋 重命名总结："
echo "  🔄 重命名了 $total_files 个文件"
echo "  📝 更新了相关引用和导入语句"
echo "  🧹 清理了临时备份文件"
echo ""
echo "🎯 接下来的步骤："
echo "1. 检查重命名结果: git status"
echo "2. 测试功能是否正常: python test_xtool_advisor_production.py"
echo "3. 提交更改: git add . && git commit -m 'Rename: 项目文件从 zen 更新为 xtool'"
echo "4. 推送更改: git push"

total_files=${#old_files[@]}
echo ""
echo "📊 重命名统计："
echo "  📁 总文件数: $total_files"