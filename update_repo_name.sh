#!/bin/bash

echo "🔄 更新仓库名称从 zen-mcp-server 到 xtool_mcp_server"
echo "========================================================"

# 1. 更新 docker-compose.enhanced.yml
echo "📝 更新 docker-compose.enhanced.yml..."
sed -i.bak 's/zen-mcp-server/xtool_mcp_server/g' docker-compose.enhanced.yml

# 2. 更新 server.py 中的描述
echo "📝 更新 server.py..."
sed -i.bak 's/zen-mcp-server/xtool_mcp_server/g' server.py

# 3. 更新 tools/version.py 中的 GitHub URL
echo "📝 更新 tools/version.py..."
sed -i.bak 's/zen-mcp-server/xtool_mcp_server/g' tools/version.py

# 4. 更新 docker/README.md
echo "📝 更新 docker/README.md..."
sed -i.bak 's/zen-mcp-server/xtool_mcp_server/g' docker/README.md

# 5. 查找并更新其他可能的文件
echo "🔍 查找其他包含旧名称的文件..."
grep -r "zen-mcp-server" . --exclude-dir=.git --exclude-dir=.zen_memory --exclude-dir=__pycache__ --include="*.md" --include="*.py" --include="*.json" --include="*.yml" --include="*.yaml" -l | while read file; do
    echo "  更新文件: $file"
    sed -i.bak 's/zen-mcp-server/xtool_mcp_server/g' "$file"
done

# 6. 清理备份文件
echo "🧹 清理备份文件..."
find . -name "*.bak" -type f -delete

echo "✅ 文件更新完成！"
echo ""
echo "📋 接下来的步骤："
echo "1. 在 GitHub 上将仓库改名为 xtool_mcp_server"
echo "2. 运行以下命令更新本地 remote URL:"
echo "   git remote set-url origin https://github.com/zerorone/xtool_mcp_server.git"
echo "3. 验证更新: git remote -v"
echo "4. 推送更改: git add . && git commit -m 'Update: 仓库名称更新为 xtool_mcp_server' && git push"