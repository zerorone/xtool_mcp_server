# Zen MCP Server 项目架构文档

## 项目概述

Zen MCP Server 是一个基于模型上下文协议（MCP）的 AI 协作服务器，它允许 Claude 和其他 AI 模型进行智能协作，提供代码分析、审查、调试等专业开发工具。

## 目录结构

```
xtool_mcp_server/
│
├── 🚀 核心文件
│   ├── server.py                    # MCP服务器主入口
│   ├── config.py                    # 全局配置中心
│   └── requirements.txt             # Python依赖管理
│
├── 🛠️ 工具系统 (tools/)
│   ├── shared/                      # 共享基础类
│   ├── simple/                      # 简单交互工具
│   └── workflow/                    # 多步骤工作流工具
│
├── 🤖 AI提供者 (providers/)
│   ├── gemini.py                    # Google Gemini集成
│   ├── openai_provider.py           # OpenAI O3集成
│   └── custom.py                    # 本地模型支持
│
├── 💬 系统提示 (systemprompts/)
│   └── *.md                         # 各工具的AI指令模板
│
├── 🔧 实用工具 (utils/)
│   ├── conversation_memory.py       # 对话上下文管理
│   ├── file_utils.py               # 智能文件处理
│   └── token_utils.py              # 令牌计算优化
│
├── 🧪 测试套件
│   ├── tests/                      # 单元测试
│   └── simulator_tests/            # 端到端集成测试
│
├── 📝 脚本和配置
│   ├── run-server.sh               # 一键启动脚本
│   ├── code_quality_checks.sh      # 代码质量检查
│   └── communication_simulator_test.py # 模拟测试框架
│
└── 📚 文档和日志
    ├── docs/                       # 详细文档
    ├── logs/                       # 运行日志
    └── CLAUDE.md                   # Claude开发指南
```

## 核心组件详解

### 1. 服务器核心 (server.py)

**职责**：
- 实现 MCP 协议规范
- 处理 JSON-RPC 消息通信
- 管理工具注册和发现
- 路由请求到相应工具

**关键功能**：
```python
# 工具注册表
tool_registry = {
    "chat": ChatTool(),
    "debug": DebugIssueTool(),
    "codereview": CodeReviewTool(),
    # ... 更多工具
}

# MCP 服务器初始化
server = Server("xtool_mcp_server")
```

### 2. 配置管理 (config.py)

**配置项**：
- `__version__`: 服务器版本
- `DEFAULT_MODEL`: 默认AI模型（支持"auto"模式）
- `TEMPERATURE_*`: 不同场景的温度设置
- `MCP_PROMPT_SIZE_LIMIT`: MCP传输限制

**智能配置**：
```python
# 自动模式检测
IS_AUTO_MODE = DEFAULT_MODEL.lower() == "auto"

# 动态计算MCP限制
MCP_PROMPT_SIZE_LIMIT = _calculate_mcp_prompt_limit()
```

### 3. 工具系统架构

#### 基础类层次

```
BaseTool (abstract)
├── 简单工具
│   ├── ChatTool         # 通用对话
│   ├── ThinkDeepTool    # 深度思考
│   └── ChallengeTool    # 批判性思考
│
└── BaseWorkflowTool (abstract)
    ├── CodeReviewTool   # 代码审查流程
    ├── DebugIssueTool   # 调试工作流
    └── PlannerTool      # 项目规划流程
```

#### 工具特性

**简单工具** (`tools/simple/`)：
- 单次AI交互
- 直接返回结果
- 适用于问答、讨论场景

**工作流工具** (`tools/workflow/`)：
- 多步骤执行流程
- 强制暂停和检查点
- 置信度追踪系统
- 条件性专家咨询

### 4. AI提供者系统

#### 提供者架构

```python
class BaseModelProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """检查提供者是否可用"""
    
    @abstractmethod
    async def chat(self, messages, **kwargs):
        """执行对话"""
    
    @abstractmethod
    def get_model_info(self, model_name):
        """获取模型信息"""
```

#### 支持的提供者

| 提供者 | 文件 | 特性 | 模型 |
|--------|------|------|------|
| Google Gemini | `gemini.py` | 思考模式、大上下文 | Pro, Flash |
| OpenAI | `openai_provider.py` | 强推理能力 | O3 |
| OpenRouter | `openrouter.py` | 多模型网关 | 100+模型 |
| Custom | `custom.py` | 本地模型 | Ollama, vLLM |
| DIAL | `dial.py` | 企业级API | 多提供者 |

### 5. 对话管理系统

#### 对话内存 (`utils/conversation_memory.py`)

**功能**：
- 线程级对话持久化
- 跨工具上下文共享
- 智能内存管理
- 上下文恢复机制

**实现**：
```python
class ConversationMemory:
    def save_conversation(self, thread_id, messages):
        """保存对话历史"""
    
    def get_conversation(self, thread_id):
        """获取对话历史"""
    
    def create_continuation_thread(self, parent_id):
        """创建继续对话线程"""
```

### 6. 文件处理系统

#### 智能文件管理 (`utils/file_utils.py`)

**特性**：
- 自动目录展开
- 文件内容去重
- 令牌限制管理
- 智能文件选择

**去重机制**：
```python
# 工具内去重
tool_file_hashes = {}

# 跨工具去重
global_file_cache = {}
```

### 7. 测试架构

#### 三层测试策略

1. **单元测试** (`tests/`)
   - 隔离组件测试
   - Mock外部依赖
   - 快速执行反馈

2. **集成测试**
   - 真实API调用
   - 端到端流程
   - 本地模型支持

3. **模拟器测试** (`simulator_tests/`)
   - 模拟Claude CLI交互
   - 完整工作流验证
   - 对话连续性测试

#### 测试工具

```bash
# 快速质量检查
./code_quality_checks.sh

# 核心功能测试（6个关键测试）
python communication_simulator_test.py --quick

# 完整测试套件
./run_integration_tests.sh --with-simulator
```

## 工作流程图

### 1. 请求处理流程

```mermaid
graph TD
    A[Claude CLI] -->|JSON-RPC| B[MCP Server]
    B --> C{工具路由}
    C -->|简单工具| D[直接执行]
    C -->|工作流工具| E[多步骤流程]
    E --> F[步骤1: 收集信息]
    F --> G[步骤2: 分析]
    G --> H[步骤3: 专家咨询]
    H --> I[返回结果]
    D --> I
    I -->|格式化响应| A
```

### 2. 对话继续流程

```mermaid
graph LR
    A[初始对话] --> B[保存到内存]
    B --> C[生成线程ID]
    C --> D[后续工具调用]
    D --> E[加载历史上下文]
    E --> F[继续对话]
    F --> G[更新内存]
```

## 开发指南

### 添加新工具

1. **创建工具类**
```python
# tools/simple/newtool.py
class NewTool(BaseTool):
    def get_name(self) -> str:
        return "newtool"
    
    def get_description(self) -> str:
        return "新工具的描述"
    
    async def run(self, request: ToolRequest) -> ToolOutput:
        # 实现工具逻辑
        pass
```

2. **创建系统提示**
```markdown
# systemprompts/newtool.md
你是一个专业的...
```

3. **注册工具**
```python
# server.py
from tools.simple.newtool import NewTool

tool_registry["newtool"] = NewTool()
```

4. **编写测试**
```python
# tests/test_newtool.py
def test_newtool_basic():
    # 测试基本功能
    pass
```

### 添加新提供者

1. **实现提供者类**
```python
# providers/newprovider.py
class NewProvider(BaseModelProvider):
    SUPPORTED_MODELS = {
        "model-name": {
            "description": "模型描述",
            "context_window": 100000,
        }
    }
    
    def is_available(self) -> bool:
        return bool(os.getenv("NEW_API_KEY"))
```

2. **注册到系统**
```python
# providers/__init__.py
ModelProviderRegistry.register("newprovider", NewProvider())
```

## 配置示例

### 环境变量 (.env)

```bash
# API密钥配置
GEMINI_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here

# 自定义配置
DEFAULT_MODEL=auto
LOG_LEVEL=INFO
LOCALE=zh-CN

# 本地模型
CUSTOM_API_URL=http://localhost:11434/v1
CUSTOM_MODEL_NAME=llama3.2
```

### 模型别名配置 (conf/custom_models.json)

```json
{
  "aliases": {
    "llama": "llama3.2",
    "fast": "gemini-2.5-flash",
    "smart": "o3"
  },
  "models": {
    "llama3.2": {
      "provider": "custom",
      "context_window": 8192
    }
  }
}
```

## 部署选项

### 1. 本地开发
```bash
./run-server.sh
```

### 2. Docker部署
```bash
docker-compose up -d
```

### 3. 通过uvx安装
```bash
uvx --from git+https://github.com/BeehiveInnovations/xtool_mcp_server.git xtool_mcp_server
```

## 性能优化

### 令牌使用优化
- 文件去重减少重复发送
- 智能截断超长内容
- 模型特定的令牌计算

### 响应时间优化
- 提供者并行初始化
- 懒加载系统提示
- 缓存常用配置

### 内存管理
- 对话历史限制
- 定期清理过期数据
- 流式响应处理

## 安全考虑

### API密钥保护
- 环境变量存储
- 不记录敏感信息
- 启动时验证

### 输入验证
- 路径清理
- 大小限制
- 类型检查

### 错误处理
- 优雅降级
- 详细日志
- 用户友好提示

## 监控和调试

### 日志系统
```bash
# 主日志
tail -f logs/mcp_server.log

# 活动追踪
tail -f logs/mcp_activity.log | grep TOOL_CALL
```

### 调试模式
```bash
LOG_LEVEL=DEBUG ./run-server.sh
```

### 性能分析
- 工具执行时间记录
- 令牌使用统计
- API调用追踪

## 最佳实践

1. **代码质量**
   - 提交前运行 `./code_quality_checks.sh`
   - 保持测试覆盖率
   - 遵循Python风格指南

2. **工具设计**
   - 单一职责原则
   - 清晰的系统提示
   - 合理的默认值

3. **错误处理**
   - 预期失败场景
   - 提供恢复建议
   - 记录调试信息

4. **文档维护**
   - 更新CLAUDE.md
   - 编写工具文档
   - 保持示例最新

## 未来路线图

- [ ] 支持更多AI提供者
- [ ] 增强的对话记忆系统
- [ ] 可视化调试界面
- [ ] 插件系统架构
- [ ] 性能基准测试套件

---

本文档持续更新，反映项目的最新架构和最佳实践。