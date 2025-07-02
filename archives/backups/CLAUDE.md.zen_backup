# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 快速命令参考

### 快速启动
```bash
# 设置服务器（自动处理所有配置）
./run-server.sh

# 实时查看日志
./run-server.sh -f

# 查看配置说明
./run-server.sh -c
```

### 代码质量和测试
```bash
# 提交前必须运行 - 包括代码检查、格式化、单元测试
./code_quality_checks.sh

# 运行集成测试（需要 API 密钥）
./run_integration_tests.sh

# 快速测试模式（6个核心测试，约2分钟）
python communication_simulator_test.py --quick

# 运行特定的模拟器测试
python communication_simulator_test.py --individual <test_name>

# 列出所有可用的模拟器测试
python communication_simulator_test.py --list-tests
```

### 开发工作流程

#### 修改代码前
1. 激活虚拟环境：`source .zen_venv/bin/activate`
2. 运行质量检查：`./code_quality_checks.sh`
3. 检查服务器状态：`tail -n 50 logs/mcp_server.log`

#### 修改代码后
1. 运行质量检查：`./code_quality_checks.sh`
2. 运行集成测试：`./run_integration_tests.sh`
3. 运行快速测试：`python communication_simulator_test.py --quick`
4. 检查日志：`tail -n 100 logs/mcp_server.log`
5. **重要**：重启 Claude 会话以使更改生效

#### 提交代码前
1. 最终质量检查：`./code_quality_checks.sh`
2. 运行集成测试：`./run_integration_tests.sh`
3. 确保所有测试 100% 通过
4. 使用语义化提交信息：`Fix:`, `Add:`, `Refactor:`, `Test:`, `Docs:`

#### 你必须具备 "自我学习、自我适配" 的意识，凡遇风格不确定、规则模糊的场景，须优先：
    - 主动查阅现有代码；
    - 模仿当前模块的实现方式；
    - 避免引入破坏风格一致性的代码。

#### 注释语言统一为中文

    1. 项目代码中的注释必须使用中文，包括但不限于：
        - 类注释；
        - 方法注释；
        - 行内注释（`//`）；
        - 多行注释（`/* */`）；
        - `TODO`、`FIXME` 标签说明；

    2. 禁止使用夹杂式语言（中英混用）。
        - ✅ 正确示例：`// 处理 'WebSocket' 握手逻辑`
        - ❌ 错误示例：`// WebSocket 握手逻辑`

#### 注释复杂度要求适中（不得过度复杂或过度简易）

1. 注释内容应清晰说明目的、逻辑和关键边界条件，但不得赘述显而易见的代码含义：
    - ✅ 合理注释示例：
      `
      //如果用户未登录，则重定向到登录页面
      `
    - ❌ 过度简略：
      `
      // 登录
      `
    - ❌ 过度复杂：
      `
      //如果当前用户会话状态未达到预期的"已认证"状态，
      //系统将引导用户返回预设的登录页面以完成登录过程。
      //这一步是确保后续API调用安全性和有效性的必要措施。
      `

#### 回答语言规范（即你与用户交流时）

1. 你在与用户交互时必须全程使用中文；
2. 若希望临时切换语言，可以明确告知，否则始终保持中文为默认沟通语言。


## 架构概览

### 核心组件

**MCP 服务器** (`server.py`)
- 主入口点，处理 MCP 协议通信
- 通过 stdio 运行，处理 JSON-RPC 消息
- 将工具请求路由到相应实现
- 管理服务器生命周期和日志记录

**工具系统** (`tools/`)
- **简单工具** (`tools/simple/`）：直接 AI 交互（chat、thinkdeep、challenge）
- **工作流工具** (`tools/workflow/`）：多步骤流程（codereview、debug、planner）
- **基础类** (`tools/shared/`）：通用功能和抽象
- 每个工具都是独立的，有自己的系统提示

**AI 提供者** (`providers/`)
- `gemini.py`：Google Gemini 模型（Pro、Flash、思考模式）
- `openai_provider.py`：OpenAI O3 模型集成
- `openrouter.py`：通过 OpenRouter 访问多个模型
- `custom.py`：本地模型（Ollama、vLLM、LM Studio）
- `dial.py`：DIAL 平台集成
- 提供者注册表根据 API 密钥管理模型可用性

**关键工具类** (`utils/`)
- `conversation_memory.py`：基于线程的对话持久化
- `file_utils.py`：智能文件处理、去重、令牌管理
- `token_utils.py`：各种模型的令牌计数
- `prompt_utils.py`：提示构建和验证

**配置** (`config.py`)
- 版本管理和元数据
- 模型默认值和自动模式检测
- 不同工具类型的温度设置
- MCP 传输限制和令牌分配

### 重要设计模式

**对话线程**
- 工具可以跨调用继续对话
- 在 Claude 会话期间内存持续存在
- 即使 Claude 重置后也能恢复上下文
- 线程 ID 跟踪对话链

**文件去重**
- 防止多次发送相同的文件内容
- 工具内和跨工具去重
- 跟踪文件哈希以优化令牌使用
- 智能处理大型代码库

**模型选择**
- 自动模式：Claude 为每个任务选择最佳模型
- 手动覆盖：用户可以指定模型
- 基于 API 密钥可用性的提供者路由
- 缺少提供者时的回退处理

**工作流强制执行**
- 带有强制暂停的多步骤流程
- 分析前的系统化调查
- 置信度跟踪（探索 → 确定）
- 基于置信度级别的专家咨询

## 测试策略

### 单元测试 (`tests/`)
- 模拟外部 API 调用
- 独立测试各个组件
- 运行：`python -m pytest tests/ -v -m "not integration"`
- 覆盖目标：关键路径的高覆盖率

### 集成测试
- 使用真实 API 提供者测试
- 可以使用本地模型（Ollama）进行免费测试
- 运行：`python -m pytest tests/ -v -m "integration"`
- 本地模型需要 CUSTOM_API_URL

### 模拟器测试 (`simulator_tests/`)
- MCP 服务器功能的端到端测试
- 模拟真实的 Claude CLI 交互
- 测试对话流程和工具协调
- 快速模式涵盖基本功能

### 测试组织
- 每个工具都有对应的测试文件
- 测试遵循命名约定：`test_<component>.py`
- `conftest.py` 中的固定装置用于通用设置
- `tests/data/` 中的模拟响应保证一致性

## 代码标准

### Python 风格
- **格式化**：Black，120 字符行长度
- **代码检查**：Ruff，全面的规则
- **导入**：isort，Black 配置文件
- **类型提示**：在有助于清晰度的地方使用

### 文档
- 所有公共函数/类的文档字符串
- 关注"为什么"而不仅仅是"什么"
- 为复杂函数包含使用示例
- 行为改变时更新

### 错误处理
- 特定的异常类型优于通用类型
- 带有上下文的有用错误消息
- 适当记录错误（debug/info/warning/error）
- 在可能的情况下优雅降级

### 日志记录
- 服务器日志：`logs/mcp_server.log`（20MB 轮换）
- 活动日志：`logs/mcp_activity.log`（仅工具调用）
- 使用适当的日志级别
- 在日志消息中包含上下文

## 常见开发任务

### 添加新工具
1. 在适当的目录中创建工具类（`simple/` 或 `workflow/`）
2. 继承自 `BaseTool` 或 `BaseWorkflowTool`
3. 实现必需的方法：`get_name()`、`get_description()`、`run()`
4. 在 `systemprompts/<toolname>.md` 中创建系统提示
5. 在 `server.py` 工具注册表中注册
6. 在 `tests/test_<toolname>.py` 中添加测试
7. 更新文档

### 添加新提供者
1. 在 `providers/` 中创建提供者类
2. 继承自 `BaseModelProvider`
3. 实现：`is_available()`、`chat()`、`get_model_info()`
4. 使用功能定义 `SUPPORTED_MODELS`
5. 在提供者注册表中注册
6. 为提供者功能添加测试
7. 更新配置文档

### 调试技巧
- 启用 DEBUG 日志：`LOG_LEVEL=DEBUG`
- 跟踪工具执行的活动日志：`tail -f logs/mcp_activity.log`
- 在模拟器测试中使用详细模式：`--verbose`
- 检查提供者可用性：使用 `listmodels` 工具
- 验证提示不超过 MCP 限制

### 性能考虑
- 文件去重减少令牌使用
- 对话内存支持上下文重用
- 模型选择影响成本和速度
- 令牌限制因模型而异（查看提供者规格）
- 根据任务复杂度使用适当的思考模式

## 安全性和最佳实践

### API 密钥管理
- 永远不要提交 API 密钥
- 使用 `.env` 文件（已忽略）
- 启动时验证密钥
- 支持多个提供者以提高灵活性

### 输入验证
- 清理文件路径
- 验证提示大小
- 检查模型可用性
- 优雅地处理缺失的参数

### 速率限制
- 遵守提供者速率限制
- 实施指数退避
- 清楚地记录速率限制错误
- 考虑超时设置

## 故障排除

### 常见问题

**服务器无法启动**
- 检查 Python 版本（3.9+）
- 验证虚拟环境已激活
- 确保至少配置了一个 API 密钥
- 查看日志中的具体错误

**测试失败**
- 首先运行代码质量检查
- 检查 API 密钥配置
- 验证模拟数据是最新的
- 使用单独的测试模式进行调试

**工具不工作**
- 检查系统提示是否存在
- 验证服务器中的工具注册
- 查看执行错误的日志
- 首先使用简单输入测试

**模型不可用**
- 验证提供者的 API 密钥
- 检查提供者的 SUPPORTED_MODELS 中的模型名称
- 使用 `listmodels` 查看可用模型
- 查看日志中特定于提供者的错误

### 获取帮助
- 查看现有测试以获取使用示例
- 查看工具实现以了解模式
- 使用详细日志进行调试
- 提交包含详细重现步骤的问题

## 最后说明

- 这是一个模型上下文协议（MCP）服务器
- 设计用于 Claude Code 和 Gemini CLI
- 专注于 AI 模型编排和协作
- 跨工具调用维护对话上下文
- 优先考虑开发者体验和代码质量

## 记忆系统配置

### Token 限制
- **记忆回忆限制**: 20000 tokens（可通过 `MEMORY_TOKEN_LIMIT` 环境变量调整）
- **回忆顺序**: 类型 → 索引 → 指定文件
- **质量过滤**: 自动过滤低质量记忆（默认阈值 0.3）

### 使用记忆系统
```bash
# 使用记忆回忆工具
recall --query="bug fix" --tags="login,auth" --specified_files="auth.py,user.py"

# 查看记忆统计（包含 token 使用情况）
recall --show_stats=true
```

记住：在任何代码更改后，重启您的 Claude 会话以使更改生效！