"""
xtool MCP 服务器的配置和常量

本模块集中了 xtool MCP 服务器的所有配置设置。
它定义了模型配置、令牌限制、温度默认值以及应用程序中使用的其他常量。

配置值可以在适当的情况下通过环境变量覆盖。
"""

import os

# 版本和元数据
# 这些值用于服务器响应和跟踪发布版本
# 重要：这是版本和作者信息的唯一真实来源
# 语义版本控制：主版本号.次版本号.修订号
__version__ = "6.0.0"
# ISO 格式的最后更新日期
__updated__ = "2025-01-30"
# 主要维护者
__author__ = "Fahad Gilani"

# 模型配置
# DEFAULT_MODEL：所有 AI 操作使用的默认模型
# 这应该是一个稳定、高性能、适合代码分析的模型
# 可以通过设置 DEFAULT_MODEL 环境变量来覆盖
# 特殊值 "auto" 表示 Claude 应该为每个任务选择最佳模型
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "auto")

# 自动模式检测 - 当 DEFAULT_MODEL 为 "auto" 时，Claude 选择模型
IS_AUTO_MODE = DEFAULT_MODEL.lower() == "auto"

# 每个提供者（gemini.py、openai_provider.py、xai.py）定义自己的 SUPPORTED_MODELS
# 并附有详细描述。工具使用 ModelProviderRegistry.get_available_model_names()
# 仅从启用的提供者（拥有有效 API 密钥的提供者）获取模型。
#
# 这种架构确保：
# - 无命名空间冲突（模型仅在其提供者启用时出现）
# - 基于 API 密钥的过滤（防止向 Claude 显示错误的模型）
# - 正确的提供者路由（模型路由到正确的 API 端点）
# - 关注点的清晰分离（提供者拥有自己的模型定义）


# 不同工具类型的温度默认值
# 温度控制模型响应的随机性/创造性
# 较低的值（0.0-0.3）产生更确定、更专注的响应
# 较高的值（0.7-1.0）产生更有创意、更多样的响应

# TEMPERATURE_ANALYTICAL：用于需要精确性和一致性的任务
# 适用于代码审查、调试和错误分析等准确性至关重要的场景
TEMPERATURE_ANALYTICAL = 0.2  # 用于代码审查、调试

# TEMPERATURE_BALANCED：一般对话的中间值
# 在一致性和有用的多样性之间提供良好的平衡
TEMPERATURE_BALANCED = 0.5  # 用于一般聊天

# TEMPERATURE_CREATIVE：用于探索性任务的较高温度
# 用于头脑风暴、探索替代方案或架构讨论时
TEMPERATURE_CREATIVE = 0.7  # 用于架构、深度思考

# 思考模式默认值
# DEFAULT_THINKING_MODE_THINKDEEP：扩展推理工具的默认思考深度
# 更高的模式使用更多的计算预算但提供更深入的分析
DEFAULT_THINKING_MODE_THINKDEEP = os.getenv("DEFAULT_THINKING_MODE_THINKDEEP", "high")

# 共识工具默认值
# 共识超时和速率限制设置
DEFAULT_CONSENSUS_TIMEOUT = 120.0  # 每个模型 2 分钟
DEFAULT_CONSENSUS_MAX_INSTANCES_PER_COMBINATION = 2

# 注意：共识工具现在使用顺序处理以兼容 MCP
# 并发处理已被移除以避免异步模式违规

# MCP 协议传输限制
#
# 重要：此限制仅适用于 Claude CLI ↔ MCP 服务器传输边界。
# 它不限制 MCP 服务器内部操作，如系统提示、文件嵌入、
# 对话历史或发送到外部模型（Gemini/O3/OpenRouter）的内容。
#
# MCP 协议架构：
# Claude CLI ←→ MCP 服务器 ←→ 外部模型（Gemini/O3/等）
#     ↑                              ↑
#     │                              │
# MCP 传输                      内部处理
# （来自 MAX_MCP_OUTPUT_TOKENS 的令牌限制）    （无 MCP 限制 - 可以是 1M+ 令牌）
#
# MCP_PROMPT_SIZE_LIMIT：跨 MCP 传输的用户输入的最大字符大小
# MCP 协议有一个由 MAX_MCP_OUTPUT_TOKENS 控制的请求+响应组合限制。
# 为了确保 MCP 服务器 → Claude CLI 响应有足够的空间，我们将用户输入
# 限制在大约总令牌预算的 60% 转换为字符。较大的用户提示
# 必须作为 prompt.txt 文件发送以绕过 MCP 的传输约束。
#
# 令牌到字符转换比率：每个令牌约 4 个字符（代码/文本的平均值）
# 默认分配：60% 的令牌用于输入，40% 用于响应
#
# 受此常量限制的内容：
# - request.prompt 字段内容（来自 Claude CLI 的用户输入）
# - prompt.txt 文件内容（替代用户输入方法）
# - 任何其他直接用户输入字段
#
# 不受此常量限制的内容：
# - 工具内部添加的系统提示
# - 工具嵌入的文件内容
# - 从存储加载的对话历史
# - 网络搜索指令或其他内部添加
# - 发送到外部模型的完整提示（由模型特定的令牌限制管理）
#
# 这确保 MCP 传输保持在协议限制内，同时允许内部
# 处理使用完整的模型上下文窗口（200K-1M+ 令牌）。


def _calculate_mcp_prompt_limit() -> int:
    """
    根据 MAX_MCP_OUTPUT_TOKENS 环境变量计算 MCP 提示大小限制。

    返回：
        用户输入提示的最大字符数
    """
    # 检查 Claude 的 MAX_MCP_OUTPUT_TOKENS 环境变量
    max_tokens_str = os.getenv("MAX_MCP_OUTPUT_TOKENS")

    if max_tokens_str:
        try:
            max_tokens = int(max_tokens_str)
            # 为输入分配 60% 的令牌，转换为字符（每个令牌约 4 个字符）
            input_token_budget = int(max_tokens * 0.6)
            character_limit = input_token_budget * 4
            return character_limit
        except (ValueError, TypeError):
            # 如果 MAX_MCP_OUTPUT_TOKENS 不是有效整数，则回退到默认值
            pass

    # 默认回退值：60,000 个字符（相当于 25k 总量中的 ~15k 令牌输入）
    return 60_000


MCP_PROMPT_SIZE_LIMIT = _calculate_mcp_prompt_limit()

# 语言/地区配置
# LOCALE：AI 响应的语言/地区规范
# 设置后，所有 AI 工具将以指定语言响应，同时
# 保持其分析能力
# 示例："fr-FR"、"en-US"、"zh-CN"、"zh-TW"、"ja-JP"、"ko-KR"、"es-ES"、
# "de-DE"、"it-IT"、"pt-PT"
# 留空以使用默认语言（英语）
LOCALE = os.getenv("LOCALE", "")

# 线程配置
# 为无状态 MCP 环境提供简单的内存对话线程
# 对话仅在 Claude 会话期间持续

# 增强内存系统配置
# ENABLE_ENHANCED_MEMORY：增强内存功能的主开关
# 启用后，向对话系统添加三层内存（全局、项目、会话）
ENABLE_ENHANCED_MEMORY = os.getenv("ENABLE_ENHANCED_MEMORY", "true").lower() == "true"

# MEMORY_STORAGE_PATH：存储持久化内存文件的目录
# 默认值：当前工作目录中的 .XTOOL_memory
MEMORY_STORAGE_PATH = os.getenv("MEMORY_STORAGE_PATH", ".XTOOL_memory")

# AUTO_DETECT_ENV：自动检测并记住项目环境信息
# 启用后，检测 git 信息、项目文件、依赖项和 TODO 文件
AUTO_DETECT_ENV = os.getenv("MEMORY_AUTO_DETECT_ENV", "true").lower() == "true"

# AUTO_SAVE_MEMORY：自动将重要的对话轮次保存到内存层
# 使用智能启发式方法确定使用哪个层（全局/项目/会话）
AUTO_SAVE_MEMORY = os.getenv("MEMORY_AUTO_SAVE", "true").lower() == "true"

# 内存层限制
# 这些控制每个内存层中存储的最大项目数
MEMORY_GLOBAL_MAX_ITEMS = int(os.getenv("MEMORY_GLOBAL_MAX_ITEMS", "10000"))
MEMORY_PROJECT_MAX_ITEMS = int(os.getenv("MEMORY_PROJECT_MAX_ITEMS", "5000"))
MEMORY_SESSION_MAX_ITEMS = int(os.getenv("MEMORY_SESSION_MAX_ITEMS", "1000"))

# 思考模式配置
# ENABLE_THINKING_MODES：启用 25 种思考模式增强
ENABLE_THINKING_MODES = os.getenv("ENABLE_THINKING_MODES", "true").lower() == "true"

# THINKING_AUTO_MODE：根据上下文自动选择合适的思考模式
THINKING_AUTO_MODE = os.getenv("THINKING_AUTO_MODE", "true").lower() == "true"

# THINKING_MAX_MODES：同时使用的思考模式的最大数量
THINKING_MAX_MODES = int(os.getenv("THINKING_MAX_MODES", "5"))

# THINKING_LEARN_PATTERNS：从用户偏好中学习并调整模式选择
THINKING_LEARN_PATTERNS = os.getenv("THINKING_LEARN_PATTERNS", "true").lower() == "true"
