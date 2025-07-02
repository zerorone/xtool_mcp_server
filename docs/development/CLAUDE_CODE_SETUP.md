# 🚀 xtool MCP Server - Claude Code 集成配置指南 (macOS)

## 📋 前提条件

1. ✅ Docker 已安装并运行
2. ✅ xtool MCP Server Docker 容器已启动
3. ✅ Claude Code 已安装

## 🔧 配置步骤

### 1. 确保 Docker 服务运行

```bash
# 启动 xtool MCP Server
cd /Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool_mcp_server
./docker-production.sh start

# 验证容器运行
docker ps | grep xtool-mcp-production
```

### 2. 创建 Claude Code MCP 配置

在你的**其他项目**目录中创建 `claude_desktop_config.json` 文件：

**配置文件路径**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**配置内容**:
```json
{
  "mcpServers": {
    "xtool_mcp_server": {
      "command": "/Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool_mcp_server/scripts/xtool-mcp-docker.sh",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 3. 如果已有其他 MCP 服务器配置

将 xtool_mcp_server 添加到现有配置中：

```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
    "xtool_mcp_server": {
      "command": "/Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool_mcp_server/scripts/xtool-mcp-docker.sh",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 🎯 使用方法

### 1. 重启 Claude Code

配置完成后，需要重启 Claude Code 使配置生效。

### 2. 验证连接

在 Claude Code 中输入：

```
请使用 xtool_mcp_server 的 listmodels 工具列出可用的 AI 模型
```

### 3. 使用 Xtool 工具

Claude Code 现在可以使用所有 xtool MCP Server 工具：

```
# 聊天工具
使用 zen 的 chat 工具帮我分析这段 Python 代码

# 深度思考
使用 zen 的 thinkdeep 工具进行系统性分析

# 记忆管理
使用 zen 的 memory 工具保存这个重要的架构决策

# 代码审查
使用 zen 的 codereview 工具审查我的代码

# 调试工具
使用 zen 的 debug 工具帮我排查问题

# 文档生成
使用 zen 的 docgen 工具为我的项目生成文档
```

## 🔍 可用工具列表

xtool MCP Server 提供以下工具：

- **chat** - 通用开发聊天和协作思考
- **thinkdeep** - 系统化深度分析
- **planner** - 项目规划和任务管理
- **consensus** - 多角度决策分析
- **codereview** - 代码审查
- **precommit** - 提交前代码检查
- **debug** - 调试助手
- **secaudit** - 安全审计
- **docgen** - 文档生成
- **analyze** - 代码分析
- **refactor** - 重构建议
- **tracer** - 问题追踪
- **testgen** - 测试生成
- **challenge** - 挑战和练习
- **memory** - 记忆管理
- **recall** - 记忆回忆
- **thinkboost** - 增强思维模式
- **listmodels** - 模型列表
- **version** - 版本信息

## 🛠️ 故障排除

### 问题 1: "xtool-mcp-production 容器未运行"

**解决方案**:
```bash
cd /Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool_mcp_server
./docker-production.sh start
```

### 问题 2: "权限被拒绝"

**解决方案**:
```bash
chmod +x /Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool_mcp_server/scripts/xtool-mcp-docker.sh
```

### 问题 3: Claude Code 无法连接

**解决方案**:
1. 检查配置文件路径是否正确
2. 重启 Claude Code
3. 检查 Docker 容器状态：`docker ps | grep zen-mcp`

### 问题 4: 工具调用失败

**解决方案**:
```bash
# 查看容器日志
docker logs xtool-mcp-production --tail 20

# 手动测试连接
/Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool_mcp_server/scripts/xtool-mcp-docker.sh
```

## 📝 注意事项

1. **Docker 必须运行**: 确保 Docker Desktop 正在运行
2. **容器持续运行**: xtool MCP Server 容器需要保持运行状态
3. **配置文件路径**: 确保 `claude_desktop_config.json` 在正确位置
4. **重启生效**: 配置更改后需要重启 Claude Code

## 🎉 完成！

现在你可以在任何项目的 Claude Code 中使用 xtool MCP Server 的所有强大功能了！