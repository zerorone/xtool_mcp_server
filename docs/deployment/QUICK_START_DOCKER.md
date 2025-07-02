# 🚀 XTool MCP Server - 5分钟快速开始

## 什么是 XTool MCP Server？

XTool MCP Server 是一个强大的AI工具服务器，提供20+种专业AI工具：
- 🔧 **代码分析和重构**
- 🐛 **调试和故障排除** 
- 🔒 **安全审计**
- 📝 **文档生成**
- 🧠 **深度思考和规划**
- 🤝 **多模型协作**

## 最快 30 秒启动

### 1. 准备API密钥

至少准备以下一种API密钥：
- **Gemini API**: 在 [Google AI Studio](https://aistudio.google.com/) 获取
- **OpenAI API**: 在 [OpenAI Platform](https://platform.openai.com/) 获取  
- **OpenRouter API**: 在 [OpenRouter](https://openrouter.ai/) 获取

### 2. 一键启动

```bash
# 使用 Gemini API（推荐，免费额度高）
docker run -d \
  --name xtool-mcp \
  -e GEMINI_API_KEY=your_gemini_api_key_here \
  xtoolteam/xtool-mcp-server:latest

# 或使用 OpenAI API
docker run -d \
  --name xtool-mcp \
  -e OPENAI_API_KEY=your_openai_api_key_here \
  xtoolteam/xtool-mcp-server:latest
```

### 3. 验证运行

```bash
# 查看日志
docker logs xtool-mcp

# 应该看到类似输出：
# [INFO] XTool MCP Server started successfully
# [INFO] Available tools: 20+
# [INFO] Supported models: Gemini Pro, GPT-4, etc.
```

## 在您的项目中使用

### 方法1: 添加到现有项目

在您的 `docker-compose.yml` 中添加：

```yaml
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./xtool-data:/app/.xtool_memory
    restart: unless-stopped

  # 您的其他服务...
```

### 方法2: 独立服务

```bash
# 创建数据目录
mkdir -p ./xtool-data/{logs,memory}

# 启动完整配置
docker run -d \
  --name xtool-mcp \
  --restart unless-stopped \
  -e GEMINI_API_KEY=your_api_key \
  -e LOG_LEVEL=INFO \
  -v ./xtool-data/logs:/app/logs \
  -v ./xtool-data/memory:/app/.xtool_memory \
  xtoolteam/xtool-mcp-server:latest
```

## 快速测试可用工具

```bash
# 进入容器
docker exec -it xtool-mcp python -c "
from server import list_available_tools
tools = list_available_tools()
print(f'可用工具数量: {len(tools)}')
for tool in tools[:5]:
    print(f'- {tool}')
print('...')
"
```

## 常用配置示例

### 最小配置（只需API密钥）
```yaml
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

### 推荐配置（持久化数据）
```yaml
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}  # 多模型支持
      - LOG_LEVEL=INFO
    volumes:
      - xtool-memory:/app/.xtool_memory
      - xtool-logs:/app/logs
    restart: unless-stopped

volumes:
  xtool-memory:
  xtool-logs:
```

### 生产配置（安全加固）
```yaml
services:
  xtool-mcp:
    image: xtoolteam/xtool-mcp-server:latest
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - LOG_LEVEL=INFO
      - PRODUCTION=true
    volumes:
      - xtool-memory:/app/.xtool_memory
      - xtool-logs:/app/logs
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m

volumes:
  xtool-memory:
  xtool-logs:
```

## 环境变量快速参考

| 必需变量 | 描述 | 获取地址 |
|----------|------|----------|
| `GEMINI_API_KEY` | Google Gemini API | [AI Studio](https://aistudio.google.com/) |
| `OPENAI_API_KEY` | OpenAI API | [OpenAI Platform](https://platform.openai.com/) |
| `OPENROUTER_API_KEY` | OpenRouter API | [OpenRouter](https://openrouter.ai/) |

| 可选变量 | 默认值 | 说明 |
|----------|--------|------|
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DEFAULT_MODEL` | `auto` | 默认AI模型 |
| `PRODUCTION` | `false` | 生产模式 |

## 故障排除

### 问题1: 容器无法启动
```bash
# 检查日志
docker logs xtool-mcp

# 常见原因：API密钥未设置或无效
```

### 问题2: API密钥错误
```bash
# 验证密钥是否正确设置
docker exec xtool-mcp env | grep API_KEY

# 测试API连接
docker exec xtool-mcp python -c "
import os
from providers.gemini import GeminiProvider
if os.getenv('GEMINI_API_KEY'):
    provider = GeminiProvider()
    print('Gemini API:', provider.is_available())
"
```

### 问题3: 内存不足
```bash
# 检查容器资源使用
docker stats xtool-mcp

# 增加内存限制
docker update --memory 2g xtool-mcp
```

## 下一步

1. **查看完整文档**: [DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md)
2. **了解所有工具**: 查看 `systemprompts/` 目录
3. **配置多模型**: 添加多个API密钥以支持更多模型
4. **性能优化**: 根据使用情况调整资源限制

## 获取帮助

- 🐛 **问题反馈**: [GitHub Issues](https://github.com/xtoolteam/xtool-mcp-server/issues)
- 📖 **完整文档**: [项目README](./README.md)
- 💬 **社区讨论**: GitHub Discussions

---

**🎉 祝您使用愉快！XTool MCP Server 让AI协作更简单！**