# 🔑 API 密钥设置指南

本指南将帮助您获取和配置各个 AI 提供商的 API 密钥。

## 目录

1. [快速开始](#快速开始)
2. [Google Gemini](#google-gemini-推荐)
3. [OpenRouter](#openrouter-多模型访问)
4. [OpenAI](#openai)
5. [X.AI (Grok)](#xai-grok)
6. [自定义/本地模型](#自定义本地模型)
7. [API 密钥管理最佳实践](#api-密钥管理最佳实践)
8. [故障排除](#故障排除)

## 快速开始

### 1. 创建 `.env` 文件

在项目根目录创建 `.env` 文件：
```bash
cp .env.example .env
```

### 2. 添加您的 API 密钥

编辑 `.env` 文件，添加您获得的 API 密钥：
```env
# 至少配置一个
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
XAI_API_KEY=your_key_here
```

### 3. 验证配置

运行以下命令验证：
```bash
source .env
python -c "import os; print('✓ 配置成功' if any([os.getenv('GEMINI_API_KEY'), os.getenv('OPENROUTER_API_KEY')]) else '✗ 未找到 API 密钥')"
```

## Google Gemini (推荐)

### 为什么推荐 Gemini？
- ✅ 慷慨的免费额度
- ✅ 支持超长上下文（100万+ tokens）
- ✅ 优秀的代码理解能力
- ✅ 快速响应

### 获取步骤

1. **访问 Google AI Studio**
   - 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
   - 使用您的 Google 账号登录

2. **创建 API 密钥**
   - 点击 "Create API Key"
   - 选择或创建一个项目
   - 复制生成的 API 密钥

3. **配置密钥**
   ```env
   GEMINI_API_KEY=AIza...你的密钥...
   ```

### 可用模型
- `gemini-2.5-flash` - 快速，适合日常任务
- `gemini-2.5-pro` - 强大，支持深度推理
- `gemini-2.0-flash` - 最新的快速模型

### 使用限制
- 免费层：每分钟 60 次请求
- 每日配额取决于您的账户类型

## OpenRouter (多模型访问)

### 为什么选择 OpenRouter？
- ✅ 一个 API 访问多个提供商
- ✅ 包括 Claude、GPT-4、Llama 等
- ✅ 灵活的付费模式
- ✅ 自动故障转移

### 获取步骤

1. **注册账户**
   - 访问 [OpenRouter](https://openrouter.ai/)
   - 创建账户并登录

2. **获取 API 密钥**
   - 进入 [API Keys](https://openrouter.ai/keys) 页面
   - 点击 "Create Key"
   - 保存生成的密钥

3. **添加信用额度**
   - 访问 [Credits](https://openrouter.ai/credits) 页面
   - 添加信用额度（支持多种支付方式）

4. **配置密钥**
   ```env
   OPENROUTER_API_KEY=sk-or-...你的密钥...
   ```

### 可用模型示例
- `anthropic/claude-opus-4` - Claude 最强模型
- `google/gemini-2.5-pro` - 通过 OpenRouter 访问 Gemini
- `openai/o3` - OpenAI 的推理模型
- `meta-llama/llama-3-70b` - 开源 Llama 模型

### 费用说明
- 按使用量付费
- 不同模型价格不同
- 可设置花费限制

## OpenAI

### 获取步骤

1. **创建 OpenAI 账户**
   - 访问 [OpenAI Platform](https://platform.openai.com/)
   - 注册或登录

2. **生成 API 密钥**
   - 访问 [API Keys](https://platform.openai.com/api-keys) 页面
   - 点击 "Create new secret key"
   - 命名并创建密钥
   - **立即复制保存**（只显示一次）

3. **配置密钥**
   ```env
   OPENAI_API_KEY=sk-...你的密钥...
   ```

### 可用模型
- `gpt-4o` - 最新的 GPT-4 模型
- `gpt-4o-mini` - 成本效益高的模型
- `o3` - 深度推理模型（如果有权限）

### 计费说明
- 需要绑定支付方式
- 按 token 使用量计费
- 可设置使用限制

## X.AI (Grok)

### 获取步骤

1. **申请访问权限**
   - 访问 [X.AI](https://x.ai/)
   - 申请 API 访问权限
   - 等待批准

2. **获取 API 密钥**
   - 批准后，登录开发者控制台
   - 生成 API 密钥

3. **配置密钥**
   ```env
   XAI_API_KEY=xai-...你的密钥...
   ```

### 可用模型
- `grok-2` - 最新的 Grok 模型
- `grok-2-vision` - 支持图像理解

## 自定义/本地模型

### Ollama (推荐用于本地测试)

1. **安装 Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **下载模型**
   ```bash
   ollama pull llama3.2
   ollama pull codellama
   ```

3. **配置连接**
   ```env
   CUSTOM_API_URL=http://localhost:11434
   ```

### vLLM

1. **启动 vLLM 服务器**
   ```bash
   python -m vllm.entrypoints.openai.api_server \
     --model your-model-name \
     --port 8000
   ```

2. **配置连接**
   ```env
   CUSTOM_API_URL=http://localhost:8000
   ```

### LM Studio

1. **下载并安装 LM Studio**
   - 访问 [LM Studio](https://lmstudio.ai/)

2. **启动本地服务器**
   - 在 LM Studio 中加载模型
   - 启动服务器（通常在端口 1234）

3. **配置连接**
   ```env
   CUSTOM_API_URL=http://localhost:1234/v1
   ```

## API 密钥管理最佳实践

### 1. 安全存储

❌ **不要做**：
- 将 API 密钥提交到 Git
- 在代码中硬编码密钥
- 分享包含密钥的截图

✅ **应该做**：
- 使用 `.env` 文件（已在 `.gitignore` 中）
- 使用环境变量
- 定期轮换密钥

### 2. 权限控制

- 为不同项目使用不同的密钥
- 设置 API 使用限制
- 监控使用情况

### 3. 备份策略

```bash
# 安全备份您的密钥
cp .env .env.backup
# 加密存储
gpg -c .env.backup
```

## 故障排除

### 常见问题

#### "No API keys configured"
```bash
# 检查环境变量
echo $GEMINI_API_KEY
echo $OPENROUTER_API_KEY

# 重新加载环境变量
source .env
```

#### "Invalid API key"
- 确认密钥没有多余的空格
- 检查密钥是否已过期
- 验证密钥格式正确

#### "Rate limit exceeded"
- 等待几分钟再试
- 考虑升级到付费计划
- 使用不同的 API 密钥

### 验证 API 密钥

使用 Zen 的 `listmodels` 工具验证配置：
```
使用 listmodels 工具查看可用模型
```

如果看到模型列表，说明 API 密钥配置成功。

### 获取帮助

1. **查看日志**
   ```bash
   tail -f logs/mcp_server.log
   ```

2. **测试连接**
   ```bash
   curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     https://generativelanguage.googleapis.com/v1beta/models
   ```

3. **社区支持**
   - 查看 [GitHub Issues](https://github.com/gptopencn/xtool_mcp_server/issues)
   - 加入讨论社区

## 推荐配置

### 个人开发者
```env
# 主要使用 Gemini（免费额度充足）
GEMINI_API_KEY=your_gemini_key

# 备选：本地模型
CUSTOM_API_URL=http://localhost:11434
```

### 专业用户
```env
# 多模型配置，获得最佳体验
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=your_openai_key
```

### 企业用户
```env
# 完整配置，包含所有提供商
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=your_openai_key
XAI_API_KEY=your_xai_key
CUSTOM_API_URL=your_private_endpoint
```

## 下一步

配置好 API 密钥后：
1. 运行 `./run-server.sh` 启动服务器
2. 重启 Claude Desktop
3. 使用 `listmodels` 工具验证配置
4. 开始使用 xtool MCP Server！

有问题？查看 [用户指南](USER_GUIDE.md) 或 [故障排除](troubleshooting.md)。