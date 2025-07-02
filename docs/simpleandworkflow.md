## 2. **Workflow 工具系统**

### **workflow/__init__.py**
```python
# 定义了 workflow 工具包的公开接口
# workflow 工具是多步骤工具，支持：
# - 强制暂停和继续
# - 系统化的调查分析
# - 与外部 AI 模型集成
```

### **workflow/base.py (WorkflowTool)**
这是所有 workflow 工具的基类，提供：

- **多步骤工作流编排**
- **自动 schema 生成**
- **专家分析集成**
- **进度跟踪**

```python
class WorkflowTool(BaseTool, BaseWorkflowMixin):
    # 继承自两个基类，获得：
    # - BaseTool: 基础工具功能
    # - BaseWorkflowMixin: 工作流功能
```

### **workflow/schema_builders.py**
为 workflow 工具生成 JSON Schema：

```python
# 定义了 workflow 特有的字段：
- step: 当前步骤描述
- step_number: 步骤编号
- findings: 发现的内容
- confidence: 置信度
- files_checked: 检查过的文件
```

### **workflow/workflow_mixin.py**
这是最复杂的文件，提供工作流的核心功能：

```python
class BaseWorkflowMixin(ABC):
    # 核心功能：
    # 1. 多步骤执行控制
    # 2. 上下文感知的文件处理
    # 3. 专家分析调用
    # 4. 对话记忆集成
```

**关键特性：**
- **智能文件嵌入**：中间步骤只引用文件名，最终步骤嵌入完整内容
- **工作历史跟踪**：保存每个步骤的发现和进展
- **回退支持**：可以回到之前的步骤
- **专家分析集成**：在工作完成后调用外部 AI 模型

## 3. **Simple 工具系统**

### **simple/__init__.py**
```python
# 定义了 simple 工具包的公开接口
# simple 工具是单步骤工具：
# - 请求 → AI 模型 → 响应
# - 不需要多步骤工作流
```

### **simple/base.py (SimpleTool)**
所有简单工具的基类：

```python
class SimpleTool(BaseTool):
    # 提供：
    # - 自动 schema 生成
    # - 标准化的执行流程
    # - 文件和图片处理
    # - 对话继续功能
```

**主要方法：**
- `execute()` - 标准执行流程
- `prepare_prompt()` - 准备提示词（子类实现）
- `format_response()` - 格式化响应（子类可覆盖）

## 工具系统的整体架构

```
BaseTool (基础工具类)
    ├── SimpleTool (简单工具)
    │   ├── ChatTool (聊天)
    │   ├── ConsensusTool (共识分析)
    │   └── ...
    │
    └── WorkflowTool (工作流工具)
        ├── DebugTool (调试)
        ├── CodeReviewTool (代码审查)
        └── ...
```

## 关键设计模式

### 1. **继承和混入模式**
```python
# WorkflowTool 使用多重继承
class WorkflowTool(BaseTool, BaseWorkflowMixin):
    # 获得两个基类的所有功能
```

### 2. **模板方法模式**
```python
# 基类定义流程，子类实现细节
@abstractmethod
def prepare_prompt(self, request):
    pass  # 子类必须实现
```

### 3. **钩子方法模式**
```python
# 提供可选的扩展点
def format_response(self, response, request):
    return response  # 子类可以覆盖
```

### 4. **上下文管理**
```python
# 智能管理文件内容和对话历史
if is_final_step:
    self._embed_workflow_files()  # 嵌入完整文件
else:
    self._reference_workflow_files()  # 只引用文件名
```

## 实际使用示例

### Simple 工具使用：
```python
# 用户调用 chat 工具
chat_tool = ChatTool()
response = await chat_tool.execute({
    "prompt": "解释一下这段代码",
    "files": ["/path/to/code.py"],
    "model": "claude-3.5-sonnet"
})
```

### Workflow 工具使用：
```python
# 用户调用 debug 工具（多步骤）
debug_tool = DebugTool()

# 第一步
response1 = await debug_tool.execute({
    "step": "找出登录功能的bug",
    "step_number": 1,
    "findings": "开始调查...",
    "next_step_required": True
})

# 第二步（基于第一步的发现）
response2 = await debug_tool.execute({
    "step": "找出登录功能的bug",
    "step_number": 2,
    "findings": "发现了认证逻辑问题...",
    "next_step_required": False,  # 最后一步
    "continuation_id": "xxx"  # 继续之前的对话
})
```

这个系统的巧妙之处在于：
- **模块化设计**：不同类型的工具有不同的基类
- **代码复用**：通过继承和混入最大化复用
- **灵活扩展**：新工具只需实现少量方法
- **智能优化**：自动处理文件、对话历史和 token 限制