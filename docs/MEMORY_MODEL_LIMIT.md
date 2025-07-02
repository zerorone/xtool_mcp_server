# 记忆工具模型限制配置

## 背景

记忆工具（Memory Tool）在使用过程中可能会频繁调用 AI 模型，特别是在分析和处理记忆内容时。某些高级模型（如 Claude Opus 4）的 API 调用成本较高，可能会快速消耗 API 额度。

## 更新：智能跳过 AI 调用

我们已经优化了记忆工具，使其在不需要 AI 的操作中自动跳过模型调用：

- **保存操作** (`save`): 直接保存，不调用 AI 模型
- **环境检测** (`detect_env`): 直接执行，不调用 AI 模型
- **召回操作** (`recall`): 仍可能使用 AI 增强结果
- **分析操作** (`analyze`): 仍需要 AI 进行智能分析

## 解决方案

我们在 `.env` 配置文件中添加了 `MEMORY_TOOL_MODEL` 配置项，允许用户指定记忆工具使用的特定模型，而不影响其他工具的模型选择。

## 配置方法

在 `.env` 文件中添加以下配置：

```bash
# 可选：记忆工具使用的模型限制
# 由于记忆工具会频繁调用，建议使用成本较低的模型
# 留空则使用默认模型选择机制
MEMORY_TOOL_MODEL=gemini-2.5-flash
```

### 推荐的模型选择

1. **Gemini 2.5 Flash** (`gemini-2.5-flash`)
   - 优点：速度快，成本低，上下文窗口大（1M）
   - 适用：大多数记忆管理场景

2. **OpenAI O3 Mini** (`o3-mini`)
   - 优点：平衡的性能和成本
   - 适用：需要更好推理能力的场景

3. **Claude 3.5 Haiku** (`claude-3.5-haiku`)
   - 优点：快速响应，成本较低
   - 适用：需要 Claude 系列模型特性的场景

4. **本地模型** (如果配置了 `CUSTOM_API_URL`)
   - 优点：无 API 成本
   - 适用：有本地部署能力的用户

## 实现细节

在 `tools/memory_manager.py` 中，我们覆盖了 `get_request_model_name` 方法：

```python
def get_request_model_name(self, request) -> Optional[str]:
    """Override model selection to use configured memory tool model"""
    # Check if there's a specific model configured for memory tool
    memory_model = os.getenv("MEMORY_TOOL_MODEL")
    if memory_model:
        return memory_model
    
    # Otherwise use the default behavior
    return super().get_request_model_name(request)
```

这确保了：
- 如果设置了 `MEMORY_TOOL_MODEL`，记忆工具将始终使用该模型
- 如果未设置，则使用默认的模型选择逻辑（包括 auto 模式）
- 其他工具不受此配置影响

## 技术实现

### 1. SimpleTool 基类增强

在 `tools/simple/base.py` 中添加了 `requires_ai_model` 方法：

```python
def requires_ai_model(self, request) -> bool:
    """
    Determine if this request requires an AI model.
    Override this method to return False for operations that don't need AI.
    """
    return True  # 默认需要 AI
```

execute 方法会检查这个标志，如果返回 False，则直接返回结果而不调用 AI 模型。

### 2. MemoryManagerTool 实现

在 `tools/memory_manager.py` 中覆盖了该方法：

```python
def requires_ai_model(self, request: MemoryManagerRequest) -> bool:
    # Save 和 detect_env 操作不需要 AI
    if request.action in ["save", "detect_env"]:
        return False
    # Recall 和 analyze 可能需要 AI 增强
    return True
```

## 性能优势

1. **节省成本**: 保存操作不再消耗 API 额度
2. **提升速度**: 直接操作比 AI 调用快得多
3. **更加可靠**: 减少了网络延迟和 API 错误的影响

## 注意事项

1. 确保指定的模型在你的 API 配置中可用
2. 选择的模型应该有足够的上下文窗口来处理记忆内容
3. 如果遇到模型不可用的错误，请检查相应提供者的 API 密钥配置
4. 保存操作现在会立即完成，不需要等待 AI 响应