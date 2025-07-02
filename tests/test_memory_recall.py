"""
测试记忆回忆工具的 token 限制和结构化回忆顺序功能
"""

import unittest

import pytest

from tools.memory_recall import MemoryRecallTool
from utils.intelligent_memory_retrieval import (
    MEMORY_TOKEN_LIMIT,
    enhanced_save_memory,
    get_memory_stats_with_tokens,
    token_aware_memory_recall,
)


class TestMemoryRecall(unittest.TestCase):
    """测试记忆回忆功能"""

    def setUp(self):
        """设置测试环境"""
        self.tool = MemoryRecallTool()
        self.test_memories = []

        # 创建一些测试记忆
        self._create_test_memories()

    def _create_test_memories(self):
        """创建测试记忆数据"""
        test_data = [
            {
                "content": "修复了用户登录的 bug，问题出现在密码验证逻辑中",
                "tags": ["bug", "login", "password"],
                "mem_type": "bug",
                "importance": "high",
            },
            {
                "content": "实现了新的用户注册功能，包括邮箱验证和密码强度检查",
                "tags": ["feature", "registration", "email"],
                "mem_type": "feature",
                "importance": "medium",
            },
            {
                "content": "重构了数据库访问层，提高了查询性能",
                "tags": ["refactor", "database", "performance"],
                "mem_type": "refactor",
                "importance": "low",
            },
            {
                "content": "添加了对 API 接口的安全性测试",
                "tags": ["test", "security", "api"],
                "mem_type": "test",
                "importance": "high",
            },
            {
                "content": "更新了项目文档，增加了 API 使用说明",
                "tags": ["documentation", "api", "guide"],
                "mem_type": "documentation",
                "importance": "medium",
            },
        ]

        # 保存测试记忆
        for i, data in enumerate(test_data):
            key = enhanced_save_memory(
                content=data["content"],
                layer="project",
                tags=data["tags"],
                mem_type=data["mem_type"],
                importance=data["importance"],
                key=f"test_memory_{i}",
            )
            self.test_memories.append(key)

    def test_token_limit_functionality(self):
        """测试 token 限制功能"""
        # 测试小的 token 限制
        result = token_aware_memory_recall(
            token_limit=100,  # 很小的限制
            include_metadata=True,
        )

        self.assertIsInstance(result, dict)
        self.assertIn("total_tokens", result)
        self.assertIn("memories", result)
        self.assertIn("truncated", result)
        self.assertIn("recall_summary", result)

        # 应该被截断或接近限制
        self.assertTrue(result["total_tokens"] <= 100)

        # 测试正常的 token 限制
        result = token_aware_memory_recall(token_limit=MEMORY_TOKEN_LIMIT, include_metadata=True)

        self.assertLessEqual(result["total_tokens"], MEMORY_TOKEN_LIMIT)

    def test_structured_recall_order(self):
        """测试结构化回忆顺序：类型 → 索引 → 指定文件"""
        result = token_aware_memory_recall(
            query="bug", tags=["login", "api"], specified_files=["user.py", "auth.py"], include_metadata=True
        )

        summary = result["recall_summary"]

        # 检查回忆顺序结构
        self.assertIn("by_type", summary)
        self.assertIn("by_index", summary)
        self.assertIn("specified_files", summary)

        # 验证类型回忆
        type_summary = summary["by_type"]
        self.assertIn("count", type_summary)
        self.assertIn("tokens", type_summary)
        self.assertIn("types_found", type_summary)

        # 验证索引回忆
        index_summary = summary["by_index"]
        self.assertIn("count", index_summary)
        self.assertIn("tokens", index_summary)
        self.assertIn("index_categories", index_summary)

        # 验证指定文件回忆
        files_summary = summary["specified_files"]
        self.assertIn("count", files_summary)
        self.assertIn("tokens", files_summary)

    def test_memory_recall_tool_run(self):
        """测试记忆回忆工具的运行"""
        # 测试基本功能
        result = self.tool.run(query="bug", tags="login,password", mem_type="bug", show_stats=True)

        self.assertIsInstance(result, str)
        self.assertIn("记忆回忆报告", result)
        self.assertIn("Token 使用情况", result)
        self.assertIn("按类型回忆", result)
        self.assertIn("按索引回忆", result)

    def test_memory_recall_with_specified_files(self):
        """测试指定文件的回忆功能"""
        result = self.tool.run(query="feature", specified_files="user.py,api.py,auth.py", show_stats=False)

        self.assertIsInstance(result, str)
        self.assertIn("指定文件回忆", result)

    def test_memory_recall_with_time_range(self):
        """测试时间范围回忆"""
        result = self.tool.run(
            query="test",
            days_back=7,  # 最近7天
            min_quality=0.5,
            show_stats=True,
        )

        self.assertIsInstance(result, str)
        self.assertIn("记忆回忆报告", result)

    def test_get_memory_stats_with_tokens(self):
        """测试获取包含 token 统计的记忆状态"""
        stats = get_memory_stats_with_tokens()

        if stats.get("enabled"):
            self.assertIn("total_memories", stats)
            self.assertIn("token_limit", stats)
            self.assertIn("layers", stats)
            self.assertIn("types", stats)
            self.assertIn("total_tokens", stats)
            self.assertIn("token_utilization", stats)

            # 验证 token 限制
            self.assertEqual(stats["token_limit"], MEMORY_TOKEN_LIMIT)

            # 验证利用率计算
            if stats["total_tokens"] > 0:
                expected_utilization = stats["total_tokens"] / MEMORY_TOKEN_LIMIT
                self.assertEqual(stats["token_utilization"], expected_utilization)

    def test_recall_by_type_priority(self):
        """测试按类型回忆时的优先级"""
        result = token_aware_memory_recall(
            mem_type="bug",  # 指定高优先级类型
            include_metadata=True,
        )

        # 应该优先找到 bug 类型的记忆
        bug_memories = [m for m in result["memories"] if m.get("metadata", {}).get("type") == "bug"]

        self.assertGreater(len(bug_memories), 0)

    def test_token_estimation_accuracy(self):
        """测试 token 估算的准确性"""
        # 创建一个长文本记忆
        long_content = "这是一个很长的内容，" * 1000  # 约4000个字符

        key = enhanced_save_memory(
            content=long_content, layer="project", tags=["long", "content"], mem_type="test", key="test_long_memory"
        )

        result = token_aware_memory_recall(
            query="long",
            token_limit=500,  # 小限制
            include_metadata=True,
        )

        # 应该被截断
        self.assertTrue(result["truncated"] or result["total_tokens"] <= 500)

        # 清理测试记忆
        self.test_memories.append(key)

    def test_recall_order_efficiency(self):
        """测试回忆顺序的效率"""
        # 测试多步骤回忆的 token 分配
        result = token_aware_memory_recall(
            query="performance",
            tags=["database", "optimization"],
            specified_files=["db.py", "cache.py"],
            token_limit=1000,
            include_metadata=True,
        )

        summary = result["recall_summary"]

        # 检查每个阶段的 token 使用
        type_tokens = summary["by_type"]["tokens"]
        index_tokens = summary["by_index"]["tokens"]
        files_tokens = summary["specified_files"]["tokens"]

        total_calculated = type_tokens + index_tokens + files_tokens

        # 总计算应该与实际使用相匹配
        self.assertEqual(total_calculated, result["total_tokens"])

        # 不应该超过限制
        self.assertLessEqual(result["total_tokens"], 1000)

    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效参数
        result = self.tool.run(
            min_quality=1.5,  # 无效值
            token_limit=-100,  # 无效值
        )

        # 应该返回错误信息或空结果
        self.assertIsInstance(result, str)

    def tearDown(self):
        """清理测试环境"""
        # 注意：在实际测试中，可能需要清理创建的测试记忆
        # 这里暂时跳过，因为它们使用了测试前缀
        pass


@pytest.mark.integration
class TestMemoryRecallIntegration(unittest.TestCase):
    """集成测试"""

    def test_full_memory_lifecycle(self):
        """测试完整的记忆生命周期"""
        # 1. 保存记忆
        memory_key = enhanced_save_memory(
            content="这是一个集成测试记忆，用于测试完整的生命周期",
            layer="project",
            tags=["integration", "test", "lifecycle"],
            mem_type="test",
            importance="high",
        )

        # 2. 回忆记忆
        result = token_aware_memory_recall(query="integration", tags=["test"], include_metadata=True)

        # 3. 验证回忆结果
        found_memory = None
        for memory in result["memories"]:
            if memory["key"] == memory_key:
                found_memory = memory
                break

        self.assertIsNotNone(found_memory)
        self.assertIn("integration", str(found_memory["content"]))

    def test_memory_recall_tool_integration(self):
        """测试记忆回忆工具的集成"""
        tool = MemoryRecallTool()

        # 保存测试记忆
        enhanced_save_memory(
            content="集成测试：API 接口性能优化",
            layer="project",
            tags=["integration", "api", "performance"],
            mem_type="enhancement",
            importance="medium",
        )

        # 使用工具回忆
        result = tool.run(query="API 性能", tags="performance,api", mem_type="enhancement", show_stats=True)

        # 验证结果
        self.assertIn("记忆回忆报告", result)
        self.assertIn("API", result)
        self.assertIn("性能", result)


if __name__ == "__main__":
    unittest.main()
