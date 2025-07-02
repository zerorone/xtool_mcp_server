# 🌐 XTool MCP Server 跨项目使用指南

## 概述

XTool MCP Server 现在作为本地Docker服务运行，可以在您的多个项目中通过 Claude Code 使用。

## 🚀 本地服务信息

### 服务状态
- **容器名称**: `xtool-mcp`
- **服务端口**: `http://localhost:8888`
- **网络名称**: `xtool-local-network`
- **状态**: ✅ 运行中（MCP服务器通过stdio通信，容器重启是正常现象）

### 管理命令
```bash
# 在 xtool-mcp-server 项目目录下运行
./start-local-service.sh status    # 查看状态
./start-local-service.sh logs      # 查看日志
./start-local-service.sh stop      # 停止服务
./start-local-service.sh restart   # 重启服务
```

## 📋 在 Claude Code 中配置

### 方法1: 直接配置（推荐）

在任意项目目录下创建或编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "xtool-mcp": {
      "command": "docker",
      "args": [
        "exec", "-i", "xtool-mcp", 
        "python", "/app/server.py"
      ]
    }
  }
}
```

### 方法2: 通过网络连接

```json
{
  "mcpServers": {
    "xtool-mcp": {
      "command": "nc",
      "args": ["localhost", "8888"]
    }
  }
}
```

## 🔧 项目集成示例

### 示例1: 在新项目中使用

```bash
# 1. 进入您的项目目录
cd /path/to/your/project

# 2. 创建 Claude Code 配置
cat > claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "xtool-mcp": {
      "command": "docker",
      "args": [
        "exec", "-i", "xtool-mcp", 
        "python", "/app/server.py"
      ]
    }
  }
}
EOF

# 3. 启动 Claude Code 并测试
claude-code .
```

### 示例2: 与现有项目的Docker服务集成

如果您的项目已有 docker-compose.yml：

```yaml
# 在您项目的 docker-compose.yml 中添加
services:
  your-app:
    # 您的应用配置
    networks:
      - xtool-local-network
    depends_on:
      - xtool-mcp-external

  # 引用外部的 XTool MCP 服务
  xtool-mcp-external:
    image: xtool-mcp-server:latest
    external_links:
      - xtool-mcp
    networks:
      - xtool-local-network

networks:
  xtool-local-network:
    external: true
    name: xtool-local-network
```

## 🛠️ 可用的 AI 工具

XTool MCP Server 提供 20+ 种专业 AI 工具：

### 分析和规划工具
- **`analyze`** - 智能文件分析
- **`planner`** - 交互式步骤规划
- **`consensus`** - 多模型协作决策

### 代码质量工具
- **`codereview`** - 专业代码审查
- **`refactor`** - 智能代码重构
- **`precommit`** - 提交前验证

### 调试和测试工具
- **`debug`** - 专家级调试助手
- **`tracer`** - 代码执行追踪
- **`testgen`** - 测试用例生成

### 文档和安全工具
- **`docgen`** - 文档生成
- **`secaudit`** - 安全审计

### 思维增强工具
- **`thinkdeep`** - 深度思考模式
- **`chat`** - 智能对话
- **`challenge`** - 挑战性问题求解

### 记忆和管理工具
- **`memory`** - 智能记忆管理
- **`recall`** - 记忆回忆
- **`xtool_advisor`** - XTool 顾问

## 🎯 使用示例

### 在 Claude Code 中使用

1. **启动 Claude Code**
   ```bash
   cd your-project
   claude-code .
   ```

2. **使用工具示例**
   ```
   # 代码分析
   使用 analyze 工具分析这个项目的架构
   
   # 代码审查
   使用 codereview 工具审查最近的更改，重点关注安全性和性能
   
   # 规划功能
   使用 planner 工具帮我规划一个用户认证系统的实现步骤
   
   # 多模型协作
   使用 consensus 工具让多个AI模型讨论这个设计方案的优缺点
   ```

## 🔍 故障排除

### 1. 检查服务状态
```bash
cd /path/to/xtool-mcp-server
./start-local-service.sh status
```

### 2. 查看服务日志
```bash
./start-local-service.sh logs -f
```

### 3. 重启服务
```bash
./start-local-service.sh restart
```

### 4. 验证网络连接
```bash
# 检查端口是否可用
nc -zv localhost 8888

# 检查Docker网络
docker network ls | grep xtool-local-network
```

### 5. 测试MCP连接
```bash
# 测试Docker exec方式
docker exec -i xtool-mcp python /app/server.py
```

## 📊 性能和资源

### 当前配置
- **内存限制**: 1GB（最大）
- **CPU限制**: 1核（最大）
- **网络**: 专用Docker网络
- **存储**: 持久化数据卷

### 支持的AI模型
- ✅ **OpenRouter** - 多种模型访问（已配置）
- 🔧 **Gemini** - Google AI模型（需配置API密钥）
- 🔧 **OpenAI** - GPT系列模型（需配置API密钥）
- 🔧 **XAI** - Grok模型（需配置API密钥）
- 🔧 **自定义模型** - Ollama、vLLM等

## ⚙️ 高级配置

### 环境变量定制
编辑 `.env.local` 文件来配置：
- API密钥
- 默认模型选择
- 日志级别
- 思维模式设置

### 数据持久化
服务使用Docker卷保存：
- **日志**: `xtool_logs_local`
- **记忆**: `xtool_memory_local`
- **配置**: `xtool_config_local`

### 网络访问
- **本地访问**: `http://localhost:8888`
- **容器间通信**: 通过 `xtool-local-network` 网络
- **MCP协议**: stdio 通信（推荐）

## 🎉 优势

1. **一次部署，多项目使用** - 无需在每个项目中重复配置
2. **资源共享** - 共享AI模型API配额和缓存
3. **版本统一** - 所有项目使用相同版本的工具
4. **数据隔离** - 每个项目的会话和记忆独立管理
5. **性能优化** - 服务保持运行，减少启动开销

## 📞 获取帮助

如果遇到问题：

1. 查看本指南的故障排除部分
2. 检查 XTool MCP Server 项目的日志
3. 参考完整文档：`docs/deployment/DOCKER_DEPLOYMENT_GUIDE.md`
4. 在 GitHub 提交 Issue

---

**🎯 现在您可以在任何项目中享受 XTool MCP Server 的强大AI工具了！**