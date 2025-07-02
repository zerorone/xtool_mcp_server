这是 Zen MCP Server 的**共享基础架构模块**，提供了工具系统的核心框架。让我详细解释这些关键组件：

## 🏗️ 基础架构概览

### 1. **base_models.py** - 数据模型定义
定义了所有工具使用的 Pydantic 模型：

#### 核心请求模型
- **ToolRequest** - 所有工具的基础请求模型
  ```python
  - model: 模型选择（支持 "auto" 模式）
  - temperature: 温度控制（0.0-1.0）
  - thinking_mode: 思考深度（minimal/low/medium/high/max）
  - use_websearch: 是否启用网络搜索
  - continuation_id: 多轮对话的线程ID
  - images: 图像支持
  ```

- **WorkflowRequest** - 工作流工具的扩展请求模型
  ```python
  - step/step_number/total_steps: 步骤控制
  - findings: 发现的内容
  - files_checked/relevant_files: 文件跟踪
  - confidence: 置信度级别
  - hypothesis: 当前假设
  ```

- **ConsolidatedFindings** - 跨步骤的发现汇总

### 2. **base_tool.py** - 核心工具基类

这是所有工具的抽象基类，提供了丰富的功能：

#### 🔑 关键功能

1. **对话感知的文件处理**
   - 双重优先级策略：最新文件优先 + 去重
   - 跨工具文件跟踪
   - Token 感知的文件嵌入
   - 无状态到有状态的桥接

2. **智能模型管理**
   ```python
   - 自动模式：根据任务类型选择最佳模型
   - 模型验证：确保请求的模型可用
   - 温度校正：自动调整到模型支持的范围
   - 类别优化：EXTENDED_REASONING/FAST_RESPONSE/BALANCED
   ```

3. **高级特性**
   - 图像验证（大小、数量限制）
   - 网络搜索集成
   - 多语言支持（LOCALE）
   - 大型提示处理（prompt.txt 机制）

#### 必须实现的抽象方法
```python
@abstractmethod
def get_name() -> str  # 工具唯一名称
def get_description() -> str  # 详细描述
def get_input_schema() -> dict  # JSON Schema
def get_system_prompt() -> str  # 系统提示词
def get_request_model()  # Pydantic 模型类
async def prepare_prompt(request) -> str  # 构建提示词
```

### 3. **schema_builders.py** - Schema 构建器

提供一致的 JSON Schema 生成：

```python
SchemaBuilder.build_schema(
    tool_specific_fields={...},  # 工具特定字段
    required_fields=[...],       # 必需字段列表
    model_field_schema={...},    # 模型字段架构
    auto_mode=True/False        # 是否自动模式
)
```

## 🎯 架构亮点

### 1. **Token 管理策略**
```python
# 智能 Token 分配
- 对话历史优先
- 新文件次之
- 剩余内容最后
- 优雅降级处理
```

### 2. **文件去重机制**
```python
# 避免重复嵌入
- 检查对话历史中的文件
- 过滤已嵌入的文件
- 保留文件引用的逻辑访问
```

### 3. **模型选择逻辑**
```python
# 自动模式下的智能选择
- 根据 ToolModelCategory 选择
- 考虑任务复杂度
- 提供降级选项
```

### 4. **错误处理**
- 温度验证和自动修正
- 图像限制检查
- MCP 令牌限制验证
- 优雅的降级策略

## 🔧 扩展性设计

1. **简单工具** - 继承 `BaseTool`，实现最小接口
2. **工作流工具** - 使用 `WorkflowRequest`，支持多步骤
3. **自定义行为** - 覆盖钩子方法来定制功能

这个基础架构为整个工具生态系统提供了：
- ✅ 统一的接口标准
- ✅ 强大的功能复用
- ✅ 灵活的扩展机制
- ✅ 完善的错误处理
- ✅ 智能的资源管理

通过这个精心设计的基础架构，开发新工具变得简单而强大！