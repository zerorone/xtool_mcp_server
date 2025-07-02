"""
Configuration package for Zen MCP Server
"""

# 从根级别配置模块导入所有配置常量
import sys
from pathlib import Path

# 将父目录添加到路径中以导入根级别的 config.py
config_root = Path(__file__).parent.parent
sys.path.insert(0, str(config_root))

try:
    # 从根级别的 config.py 导入所有配置
    from config import (
        AUTO_DETECT_ENV,
        AUTO_SAVE_MEMORY,
        DEFAULT_CONSENSUS_MAX_INSTANCES_PER_COMBINATION,
        DEFAULT_CONSENSUS_TIMEOUT,
        DEFAULT_MODEL,
        DEFAULT_THINKING_MODE_THINKDEEP,
        ENABLE_ENHANCED_MEMORY,
        ENABLE_THINKING_MODES,
        IS_AUTO_MODE,
        LOCALE,
        MCP_PROMPT_SIZE_LIMIT,
        MEMORY_GLOBAL_MAX_ITEMS,
        MEMORY_PROJECT_MAX_ITEMS,
        MEMORY_SESSION_MAX_ITEMS,
        MEMORY_STORAGE_PATH,
        TEMPERATURE_ANALYTICAL,
        TEMPERATURE_BALANCED,
        TEMPERATURE_CREATIVE,
        THINKING_AUTO_MODE,
        THINKING_LEARN_PATTERNS,
        THINKING_MAX_MODES,
        __author__,
        __updated__,
        __version__,
    )

    # 重新导出所有配置项
    __all__ = [
        "__version__",
        "__updated__",
        "__author__",
        "DEFAULT_MODEL",
        "IS_AUTO_MODE",
        "TEMPERATURE_ANALYTICAL",
        "TEMPERATURE_BALANCED",
        "TEMPERATURE_CREATIVE",
        "DEFAULT_THINKING_MODE_THINKDEEP",
        "DEFAULT_CONSENSUS_TIMEOUT",
        "DEFAULT_CONSENSUS_MAX_INSTANCES_PER_COMBINATION",
        "MCP_PROMPT_SIZE_LIMIT",
        "LOCALE",
        "ENABLE_ENHANCED_MEMORY",
        "MEMORY_STORAGE_PATH",
        "AUTO_DETECT_ENV",
        "AUTO_SAVE_MEMORY",
        "MEMORY_GLOBAL_MAX_ITEMS",
        "MEMORY_PROJECT_MAX_ITEMS",
        "MEMORY_SESSION_MAX_ITEMS",
        "ENABLE_THINKING_MODES",
        "THINKING_AUTO_MODE",
        "THINKING_MAX_MODES",
        "THINKING_LEARN_PATTERNS",
    ]

finally:
    # 清理路径
    if str(config_root) in sys.path:
        sys.path.remove(str(config_root))
