# 🚀 XTool MCP Server - 快速开始指南

## 📋 选择您的使用方式

### 方式 1：直接使用 Docker（推荐）

适合：想要立即使用，无需安装任何东西

1. **创建配置文件**  
   在您的项目目录创建 `mcp.json`：

   ```json
   {
     "mcpServers": {
       "xtool": {
         "command": "docker",
         "args": [
           "run", "--rm", "-i",
           "-e", "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}",
           "-v", "${HOME}/.xtool_memory:/app/.xtool_memory",
           "ghcr.io/xiaocodepro/xtool-mcp-server:latest",
           "python", "/app/server.py"
         ]
       }
     }
   }
   ```

2. **设置 API Key**（至少一个）
   ```bash
   export OPENROUTER_API_KEY="your_key"
   # 或其他：GEMINI_API_KEY, OPENAI_API_KEY, XAI_API_KEY
   ```

3. **启动 Claude Code**
   ```bash
   claude .
   ```

### 方式 2：使用本地 Docker 服务

适合：需要更多控制，或多个项目共享

1. **启动本地服务**
   ```bash
   # 克隆项目
   git clone https://github.com/xiaocodepro/xtool-mcp-server.git
   cd xtool-mcp-server
   
   # 配置 API Keys
   cp .env.example .env.local
   # 编辑 .env.local 添加您的 API Keys
   
   # 启动服务
   ./start-local-service.sh start
   ```

2. **在项目中配置**  
   创建 `mcp.json`：
   ```json
   {
     "mcpServers": {
       "xtool": {
         "command": "docker",
         "args": ["exec", "-i", "xtool-mcp", "python", "/app/server.py"]
       }
     }
   }
   ```

3. **启动 Claude Code**
   ```bash
   claude .
   ```

## 🔑 API Key 配置

### 支持的 AI 提供商

| 提供商 | 环境变量 | 获取地址 | 说明 |
|--------|----------|----------|------|
| OpenRouter | `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai/) | 一个 Key 访问多种模型 |
| Gemini | `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/) | 免费额度高，推荐 |
| OpenAI | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/) | GPT-4, O3 等模型 |
| X.AI | `XAI_API_KEY` | [x.ai](https://x.ai/) | Grok 模型 |
| DIAL | `DIAL_API_KEY` | 企业内部 | 企业 AI 平台 |
| 本地模型 | `CUSTOM_API_URL` | - | Ollama 等本地模型 |

### 配置方法

**方法 1：环境变量（推荐）**
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
export OPENROUTER_API_KEY="your_key_here"
export GEMINI_API_KEY="your_key_here"
```

**方法 2：.env 文件（本地服务）**
```bash
# .env.local
OPENROUTER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

## 🎯 使用示例

### 基础命令

```bash
# 列出可用模型
xtool listmodels

# AI 对话
xtool chat 帮我分析这个函数的性能问题

# 深度思考
xtool thinkdeep 如何设计一个高并发的消息队列
```

### 工作流工具

```bash
# 代码审查
xtool codereview 审查 src/ 目录的代码质量

# 智能调试
xtool debug 帮我解决这个内存泄漏问题

# 项目规划
xtool planner 设计一个用户认证系统

# 代码重构
xtool refactor 优化这个模块的结构
```

### 高级用法

```bash
# 多模型协作
xtool consensus 用 Gemini 和 O3 一起评估这个架构设计

# 指定模型
xtool chat --model=gemini-pro 分析这个算法的时间复杂度

# 记忆管理
xtool memory save 这是项目的核心架构决策
xtool recall 查找关于认证系统的设计决策
```

## 🛠️ 故障排除

### Docker 未安装
```bash
# macOS
brew install --cask docker

# Linux
curl -fsSL https://get.docker.com | sh
```

### 镜像拉取失败
```bash
# 使用 Docker Hub 镜像
docker pull xiaocodepro/xtool-mcp-server:latest

# 或手动构建
git clone https://github.com/xiaocodepro/xtool-mcp-server.git
cd xtool-mcp-server
docker build -t xtool-mcp-server:latest .
```

### API Key 未配置
```bash
# 检查环境变量
echo $OPENROUTER_API_KEY

# 查看可用模型（会显示哪些提供商已配置）
xtool listmodels
```

## 📚 更多资源

- [完整文档](./README.md)
- [工具列表](./docs/TOOLS.md)
- [API 配置指南](./docs/API_KEY_SETUP.md)
- [Docker 部署指南](./docs/deployment/DOCKER_DEPLOYMENT_GUIDE.md)

## 💡 提示

1. **首次使用**会自动拉取 Docker 镜像（约 500MB）
2. **记忆持久化**：数据保存在 `~/.xtool_memory`
3. **性能优化**：容器会在后台持续运行，减少启动时间
4. **多项目共享**：一个容器可服务多个项目

---

需要帮助？查看 [故障排除指南](./docs/troubleshooting.md) 或提交 [Issue](https://github.com/xiaocodepro/xtool-mcp-server/issues)