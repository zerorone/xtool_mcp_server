#!/usr/bin/env python3
"""
测试工具的思维模式是否正确传递给模型提供者
"""

import asyncio
import logging
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.analyze import AnalyzeTool
from tools.chat import ChatTool
from tools.debug import DebugTool
from tools.thinkdeep import ThinkdeepTool

# 设置日志级别为 DEBUG 以查看详细信息
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# 创建一个自定义的日志处理器来捕获 generate_content 调用
class GenerateContentLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.calls = []

    def emit(self, record):
        # 捕获包含 thinking_mode 的日志
        if "thinking_mode" in record.getMessage():
            self.calls.append(record.getMessage())


# 添加自定义处理器
content_logger = GenerateContentLogger()
logging.getLogger().addHandler(content_logger)


async def test_tool_thinking_mode(tool_class, tool_name, request_args):
    """测试单个工具的思维模式"""
    print(f"\n{'=' * 60}")
    print(f"测试工具: {tool_name}")
    print(f"{'=' * 60}")

    tool = tool_class()

    # 测试不同的思维模式
    thinking_modes = ["minimal", "low", "medium", "high", "max", None]

    for mode in thinking_modes:
        print(f"\n测试思维模式: {mode}")

        # 准备请求参数
        args = request_args.copy()
        if mode is not None:
            args["thinking_mode"] = mode

        # 设置模型（如果有配置的话）
        if os.getenv("GEMINI_API_KEY"):
            args["model"] = "gemini-2.5-flash"
        elif os.getenv("OPENAI_API_KEY"):
            args["model"] = "gpt-4o-mini"
        else:
            print("警告: 没有配置 API 密钥，使用默认模型")

        try:
            # 清空之前的日志
            content_logger.calls.clear()

            # 执行工具
            result = await tool.execute(args)

            # 检查是否传递了 thinking_mode
            thinking_mode_found = False
            for call in content_logger.calls:
                if "thinking_mode=" in call or "thinking_mode:" in call:
                    print(f"✓ 找到 thinking_mode 传递: {call}")
                    thinking_mode_found = True
                    break

            if not thinking_mode_found:
                # 检查日志中是否有相关信息
                print("✗ 未找到 thinking_mode 传递")
                print(f"  捕获的日志: {content_logger.calls[:3]}...")  # 只显示前3条

        except Exception as e:
            print(f"✗ 执行失败: {e}")


async def main():
    """主测试函数"""
    print("开始测试工具的思维模式传递...")

    # 测试不同的工具
    tools_to_test = [
        (ChatTool, "chat", {"prompt": "测试思维模式传递", "files": []}),
        (
            ThinkdeepTool,
            "thinkdeep",
            {
                "step": "测试思维模式传递",
                "step_number": 1,
                "total_steps": 1,
                "next_step_required": False,
                "findings": "测试",
                "confidence": "low",
            },
        ),
        (
            DebugTool,
            "debug",
            {
                "step": "测试思维模式传递",
                "step_number": 1,
                "total_steps": 1,
                "next_step_required": False,
                "findings": "测试",
                "confidence": "low",
            },
        ),
        (
            AnalyzeTool,
            "analyze",
            {
                "step": "测试思维模式传递",
                "step_number": 1,
                "total_steps": 1,
                "next_step_required": False,
                "findings": "测试",
                "confidence": "low",
            },
        ),
    ]

    for tool_class, tool_name, request_args in tools_to_test:
        await test_tool_thinking_mode(tool_class, tool_name, request_args)

    print("\n\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
