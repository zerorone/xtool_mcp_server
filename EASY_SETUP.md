# 🚀 XTool MCP Server - 极简配置指南

## 方式一：直接使用（推荐）

在您的任意项目中创建 `.mcp.json` 或 `mcp.json` 文件：

```json
{
  "mcpServers": {
    "xtool": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--name", "xtool-mcp-temp",
        "-e", "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}",
        "-e", "GEMINI_API_KEY=${GEMINI_API_KEY}",
        "-e", "OPENAI_API_KEY=${OPENAI_API_KEY}",
        "-e", "XAI_API_KEY=${XAI_API_KEY}",
        "-e", "CUSTOM_API_URL=${CUSTOM_API_URL}",
        "-v", "${HOME}/.xtool_memory:/app/.xtool_memory",
        "ghcr.io/xiaocodepro/xtool-mcp-server:latest",
        "python", "/app/server.py"
      ]
    }
  }
}
```

然后启动 Claude Code：
```bash
claude .
```

## 方式二：使用本地 Docker 服务

如果您已经在本地运行了 xtool-mcp 容器：

```json
{
  "mcpServers": {
    "xtool": {
      "command": "docker",
      "args": [
        "exec", "-i", "xtool-mcp", 
        "python", "/app/server.py"
      ]
    }
  }
}
```

## 环境变量配置

在您的 shell 配置文件（如 `~/.zshrc` 或 `~/.bashrc`）中添加：

```bash
# 至少配置一个 API Key
export GEMINI_API_KEY="your_gemini_api_key"      # 推荐，免费额度高
export OPENAI_API_KEY="your_openai_api_key"      # OpenAI API
export OPENROUTER_API_KEY="your_openrouter_key"  # 多模型访问
export XAI_API_KEY="your_xai_api_key"           # Grok 模型
export CUSTOM_API_URL="http://localhost:11434"   # Ollama 等本地模型
```

## 使用示例

配置完成后，在 Claude Code 中：

```
# 列出可用模型
xtool listmodels

# AI 对话
xtool chat 帮我分析这段代码的性能问题

# 深度思考
xtool thinkdeep 如何设计一个高性能的缓存系统

# 代码审查
xtool codereview 审查最近的代码更改

# 更多工具...
```

## 优势

✅ **无需本地安装** - 直接通过 Docker 运行  
✅ **全局可用** - 在任何项目中都能使用  
✅ **自动更新** - 始终使用最新版本  
✅ **数据持久化** - 记忆和配置保存在本地  
✅ **多模型支持** - 根据 API Key 自动启用对应模型

## 注意事项

1. 确保 Docker Desktop 已安装并运行
2. 至少配置一个 API Key
3. 首次运行会自动拉取镜像（约需1-2分钟）
4. 记忆数据保存在 `~/.xtool_memory` 目录