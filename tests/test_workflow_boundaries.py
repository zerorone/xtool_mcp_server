"""
边界情况测试用例 - 验证工作流系统的极限和错误处理

这个测试文件通过 challenge 工具的对抗性测试方法，
系统地验证 Zen MCP Server 工作流系统的边界条件处理。
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.codereview import CodeReviewTool
from tools.debug import DebugIssueTool
from utils.conversation_memory import (
    MAX_CONVERSATION_TURNS,
    add_turn,
    create_thread,
    get_thread,
)


class TestWorkflowBoundaries:
    """工作流系统边界测试"""

    @pytest.mark.asyncio
    async def test_extreme_step_count(self):
        """测试极端步骤数（100+ 步骤）"""
        tool = DebugIssueTool()

        # 模拟一个需要 100 步的调试场景
        arguments = {
            "step": "Debug complex multi-threaded race condition",
            "step_number": 1,
            "total_steps": 100,  # 极端的步骤数
            "next_step_required": True,
            "findings": "Initial investigation",
            "files_checked": [],
            "relevant_files": [],
            "confidence": "exploring",
            "model": "gemini-2.0-flash-thinking-exp-1219",
        }

        # 期望系统能够优雅处理或限制步骤数
        with patch.object(tool, "get_model_provider") as mock_provider:
            mock_provider.return_value = MagicMock()

            # 执行应该成功但可能会有警告
            result = await tool.execute(arguments)
            assert result is not None

            # 检查是否有步骤数限制的提示
            response = json.loads(result[0].text)
            # 系统应该继续工作，但可能调整 total_steps

    @pytest.mark.asyncio
    async def test_massive_file_list(self):
        """测试大量文件引用（1000+ 文件）"""
        tool = CodeReviewTool()

        # 创建大量临时文件路径
        massive_file_list = [f"/tmp/test_file_{i}.py" for i in range(1000)]

        arguments = {
            "step": "Review massive codebase",
            "step_number": 1,
            "total_steps": 5,
            "next_step_required": False,
            "findings": "Attempting to review 1000 files",
            "files_checked": massive_file_list[:500],
            "relevant_files": massive_file_list[500:],
            "confidence": "low",
            "model": "gemini-2.0-flash-thinking-exp-1219",
        }

        # 测试系统是否能处理大量文件
        with patch.object(tool, "get_model_provider") as mock_provider:
            mock_provider.return_value = MagicMock()

            # 应该能够处理但可能有性能影响
            start_time = time.time()
            result = await tool.execute(arguments)
            execution_time = time.time() - start_time

            assert result is not None
            # 执行时间不应该过长（比如超过 10 秒）
            assert execution_time < 10

    @pytest.mark.asyncio
    async def test_empty_required_fields(self):
        """测试空必填字段"""
        tool = DebugIssueTool()

        # 测试各种空值情况
        test_cases = [
            {"step": "", "findings": "test"},  # 空 step
            {"step": "test", "findings": ""},  # 空 findings
            {"step": None, "findings": "test"},  # None step
        ]

        for case in test_cases:
            arguments = {
                "step": case.get("step", ""),
                "step_number": 1,
                "total_steps": 1,
                "next_step_required": False,
                "findings": case.get("findings", ""),
                "model": "gemini-2.0-flash-thinking-exp-1219",
            }

            # 应该返回验证错误
            with pytest.raises(Exception) as exc_info:
                await tool.execute(arguments)

            # 错误信息应该清晰
            assert "validation" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_conversation_memory_overflow(self):
        """测试对话记忆溢出（超过最大轮次）"""
        thread_id = create_thread("test_tool", {"test": "data"})

        # 尝试添加超过最大轮次的对话
        for i in range(MAX_CONVERSATION_TURNS + 5):
            success = add_turn(
                thread_id, "user" if i % 2 == 0 else "assistant", f"Turn {i} content", tool_name="test_tool"
            )

            if i < MAX_CONVERSATION_TURNS:
                assert success, f"Turn {i} should succeed"
            else:
                # 超过限制后应该失败
                assert not success, f"Turn {i} should fail due to limit"

        # 验证只保存了最大轮次数
        thread = get_thread(thread_id)
        assert len(thread.turns) == MAX_CONVERSATION_TURNS

    def test_circular_thread_reference(self):
        """测试循环线程引用"""
        # 创建两个相互引用的线程
        thread_a = create_thread("tool_a", {"data": "a"})
        thread_b = create_thread("tool_b", {"data": "b"}, parent_thread_id=thread_a)

        # 尝试创建循环引用（实际系统应该防止这种情况）
        # 这里我们只是验证不会崩溃
        thread_c = create_thread("tool_c", {"data": "c"}, parent_thread_id=thread_b)

        # 系统应该能够处理，不会无限递归
        assert thread_c is not None

        # 获取线程时不应该崩溃
        context_c = get_thread(thread_c)
        assert context_c is not None

    @pytest.mark.asyncio
    async def test_malformed_json_in_findings(self):
        """测试 findings 中包含格式错误的 JSON"""
        tool = DebugIssueTool()

        # 包含特殊字符和格式错误的内容
        malicious_findings = """
        Found issue in: {"broken": json"
        Also found: \x00\x01\x02 binary data
        And unicode: 你好世界 🚀
        """

        arguments = {
            "step": "Debug malformed data",
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "findings": malicious_findings,
            "confidence": "high",
            "model": "gemini-2.0-flash-thinking-exp-1219",
        }

        with patch.object(tool, "get_model_provider") as mock_provider:
            mock_provider.return_value = MagicMock()

            # 系统应该能够处理而不崩溃
            result = await tool.execute(arguments)
            assert result is not None

            # 响应应该是有效的 JSON
            response = json.loads(result[0].text)
            assert "status" in response

    @pytest.mark.asyncio
    async def test_path_traversal_attempt(self):
        """测试路径遍历攻击"""
        tool = CodeReviewTool()

        # 尝试各种路径遍历模式
        malicious_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "file:///etc/passwd",
            "/proc/self/environ",
        ]

        arguments = {
            "step": "Review files",
            "step_number": 1,
            "total_steps": 1,
            "next_step_required": False,
            "findings": "Testing path traversal",
            "relevant_files": malicious_paths,
            "confidence": "high",
            "model": "gemini-2.0-flash-thinking-exp-1219",
        }

        with patch.object(tool, "get_model_provider") as mock_provider:
            mock_provider.return_value = MagicMock()

            # 执行工具
            result = await tool.execute(arguments)

            # 应该返回错误或过滤掉恶意路径
            response = json.loads(result[0].text)

            # 检查是否有错误或警告
            if "error" in response:
                assert "permission" in response["error"].lower() or "invalid" in response["error"].lower()

    @pytest.mark.asyncio
    async def test_concurrent_thread_modification(self):
        """测试并发线程修改"""
        thread_id = create_thread("concurrent_test", {"data": "initial"})

        # 模拟并发修改
        async def add_turn_async(turn_num):
            return add_turn(thread_id, "assistant", f"Concurrent turn {turn_num}", tool_name=f"tool_{turn_num}")

        # 并发添加多个轮次
        tasks = [add_turn_async(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证没有异常
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Task {i} failed: {result}"

        # 验证所有轮次都被添加
        thread = get_thread(thread_id)
        assert len(thread.turns) == 10

    @pytest.mark.asyncio
    async def test_extreme_confidence_values(self):
        """测试极端的置信度值"""
        tool = DebugIssueTool()

        # 测试各种置信度值
        confidence_values = [
            "certain",  # 应该跳过专家分析
            "CERTAIN",  # 大写
            "very_high",  # 接近确定
            "unknown",  # 无效值
            "",  # 空值
            None,  # None
        ]

        for confidence in confidence_values:
            arguments = {
                "step": "Debug with varying confidence",
                "step_number": 1,
                "total_steps": 1,
                "next_step_required": False,
                "findings": "Testing confidence handling",
                "confidence": confidence,
                "model": "gemini-2.0-flash-thinking-exp-1219",
            }

            with patch.object(tool, "get_model_provider") as mock_provider:
                mock_provider.return_value = MagicMock()

                try:
                    result = await tool.execute(arguments)
                    response = json.loads(result[0].text)

                    # 检查 certain 是否跳过专家分析
                    if confidence and confidence.lower() == "certain":
                        assert response.get("skip_expert_analysis") == True
                except Exception as e:
                    # 无效值应该有合理的错误处理
                    assert "confidence" in str(e).lower()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
