# Zen MCP Server 使用指南

本文档详细说明了如何使用 Zen MCP Server 中的各种工具。

## 使用方式

### 1. 通过 Claude 或 Gemini CLI（推荐）

这是最常见和推荐的使用方式。Zen MCP Server 设计为 MCP（Model Context Protocol）服务器，与 Claude Code 或 Gemini CLI 配合使用。

#### 在 Claude 中使用

首先确保已经配置好 MCP 服务器（参见 README.md 中的快速启动部分），然后在 Claude 中使用自然语言调用工具：

```
# 通用聊天和协作思考
使用 zen 聊天功能讨论这个架构设计

# 深度思考
使用 zen 的 thinkdeep 和 gemini pro 深入分析这个算法的性能问题

# 代码审查
使用 zen 对这段代码进行安全性代码审查

# 调试
使用 zen 调试为什么这个测试失败了，bug 可能在 my_class.swift 中

# 分析文件
使用 zen 分析这些文件以理解数据流

# 规划项目
使用 zen 的 planner 将这个微服务迁移项目分解为可管理的步骤

# 获取共识
使用 zen 的 consensus，让 o3 支持而 flash 反对，评估是否应该将 API 迁移到 GraphQL
```

#### 使用结构化提示（Claude Code）

在 Claude Code 中，可以使用 `/zen:` 前缀的结构化提示：

```
/zen:chat 问 local-llama 2+2 等于多少

/zen:thinkdeep 使用 o3 告诉我为什么 sorting.swift 中的代码不工作

/zen:planner 将微服务迁移项目分解为可管理的步骤

/zen:consensus 使用 o3:for 和 flash:against 告诉我是否应该为项目添加功能 X

/zen:codereview 审查安全模块 ABC

/zen:debug 表格视图滚动不正常，很卡顿，我怀疑代码在 my_controller.m 中

/zen:analyze 检查这些文件，告诉我是否正确使用了 CoreAudio 框架

/zen:docgen 为 UserManager 类生成包含复杂度分析的综合文档
```

### 2. 直接运行测试脚本（用于开发和测试）

如果你想直接测试某个工具的功能，可以创建类似 `test_memory_tool.py` 的脚本：

```python
#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from providers.registry import ModelProviderRegistry
from tools.chat import ChatTool, ChatRequest
from server import configure_providers

async def test_chat_tool():
    # 初始化提供者
    configure_providers()
    
    # 创建工具实例
    tool = ChatTool()
    
    # 创建请求
    request = ChatRequest(
        prompt="请解释什么是依赖注入",
        model="gemini-2.5-flash"  # 或使用 "auto" 让系统自动选择
    )
    
    # 执行工具
    result = await tool.execute(request.model_dump())
    print(result)

if __name__ == "__main__":
    asyncio.run(test_chat_tool())
```

### 3. 通过 MCP 协议直接调用（高级用法）

Zen MCP Server 运行在 stdio 上，使用 JSON-RPC 协议。理论上可以直接发送 JSON-RPC 消息来调用工具，但这种方式较为复杂，不推荐。

## 可用工具列表

1. **chat** - 通用开发聊天和协作思考
2. **thinkdeep** - 扩展推理和问题解决
3. **challenge** - 批判性挑战提示，防止"你说得对"响应
4. **planner** - 复杂项目的交互式顺序规划
5. **consensus** - 多模型共识分析
6. **codereview** - 专业代码审查
7. **precommit** - 提交前验证
8. **debug** - 系统调查和调试
9. **analyze** - 通用文件和代码分析
10. **refactor** - 智能代码重构
11. **tracer** - 静态代码分析提示生成器
12. **testgen** - 综合测试生成
13. **secaudit** - 综合安全审计
14. **docgen** - 综合文档生成
15. **listmodels** - 显示所有可用的 AI 模型
16. **version** - 获取服务器版本和配置

## 模型选择

### 自动模式（推荐）

当 `DEFAULT_MODEL=auto` 时，Claude 会自动为每个任务选择最佳模型：

- 复杂架构审查 → Claude 选择 Gemini Pro
- 快速格式检查 → Claude 选择 Flash
- 逻辑调试 → Claude 选择 O3
- 一般解释 → Claude 选择 Flash 以获得速度
- 本地分析 → Claude 选择你的 Ollama 模型

### 手动指定模型

你可以在提示中明确指定模型：

```
使用 flash 进行快速分析
使用 o3 调试这个问题
使用 gemini pro 进行深入的架构审查
使用 local-llama 进行本地化和添加缺失的翻译
```

## 配置要求

使用前需要配置至少一个 API 密钥：

```bash
# 编辑 .env 文件
nano .env

# 添加至少一个 API 密钥：
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
OPENROUTER_API_KEY=your-openrouter-key
DIAL_API_KEY=your-dial-api-key

# 或配置本地模型：
CUSTOM_API_URL=http://localhost:11434/v1  # Ollama 示例
CUSTOM_MODEL_NAME=llama3.2
```

## 注意事项

1. **重启会话**：在修改代码或配置后，需要重启 Claude 会话以使更改生效。

2. **上下文续接**：Zen 的强大功能之一是跨工具和会话的对话续接。即使在 Claude 的上下文重置后，其他模型仍可以保持完整的历史记录。

3. **工作流工具**：某些工具（如 `codereview`、`debug`、`precommit`）是工作流工具，会引导 Claude 通过多个步骤进行系统化调查。

4. **置信度跟踪**：工作流工具会跟踪置信度级别（exploring → low → medium → high → certain），当置信度达到 100% 时可能会跳过外部模型咨询以节省成本。

## 更多信息

- 详细的工具文档请查看 `docs/tools/` 目录
- 高级用法请参见 `docs/advanced-usage.md`
- 配置选项请参见 `docs/configuration.md`
- 故障排除请参见 `docs/troubleshooting.md`