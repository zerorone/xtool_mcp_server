"""
记忆保存混入类 - 为工具提供自动保存记忆功能

这个混入类让工具能够在执行完成后自动保存重要的交互记忆。
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MemorySaveMixin:
    """
    为工具提供自动保存记忆的功能。

    使用方法:
    1. 工具类继承这个混入类
    2. 在工具执行完成后调用 save_interaction_memory
    3. 可以重写 should_save_memory 来控制何时保存记忆
    """

    def should_save_memory(self, request: Any, response: str) -> bool:
        """
        决定是否应该保存这次交互的记忆。

        默认行为:
        - 响应长度超过 500 字符
        - 或包含重要关键词

        子类可以重写这个方法来实现自定义逻辑。
        """
        # 检查响应长度
        if len(response) > 500:
            return True

        # 检查重要关键词
        important_keywords = [
            "解决方案",
            "solution",
            "建议",
            "recommendation",
            "bug",
            "错误",
            "error",
            "问题",
            "issue",
            "架构",
            "architecture",
            "设计",
            "design",
            "优化",
            "optimization",
            "性能",
            "performance",
            "安全",
            "security",
            "漏洞",
            "vulnerability",
        ]

        response_lower = response.lower()
        for keyword in important_keywords:
            if keyword in response_lower:
                return True

        return False

    def get_memory_metadata(self, request: Any, response: str) -> dict[str, Any]:
        """
        获取要保存的记忆元数据。

        子类可以重写这个方法来添加工具特定的元数据。
        """
        metadata = {
            "tool": getattr(self, "get_name", lambda: "unknown")(),
            "type": "tool_interaction",
            "importance": "medium",
        }

        # 根据内容自动添加标签
        tags = []

        # 检查工具类型
        tool_name = metadata["tool"]
        if "debug" in tool_name:
            tags.append("debugging")
            metadata["type"] = "debug_session"
        elif "analyze" in tool_name:
            tags.append("analysis")
            metadata["type"] = "analysis_result"
        elif "chat" in tool_name:
            tags.append("conversation")
            metadata["type"] = "chat_insight"
        elif "codereview" in tool_name:
            tags.append("code_review")
            metadata["type"] = "review_finding"
        elif "plan" in tool_name:
            tags.append("planning")
            metadata["type"] = "plan_output"

        # 根据内容添加标签
        response_lower = response.lower()
        if "bug" in response_lower or "error" in response_lower:
            tags.append("bug")
            metadata["importance"] = "high"
        if "security" in response_lower or "vulnerability" in response_lower:
            tags.append("security")
            metadata["importance"] = "high"
        if "performance" in response_lower or "optimization" in response_lower:
            tags.append("performance")
        if "architecture" in response_lower or "design" in response_lower:
            tags.append("architecture")

        metadata["tags"] = tags
        return metadata

    def save_interaction_memory(
        self, request: Any, response: str, layer: str = "session", force_save: bool = False
    ) -> Optional[str]:
        """
        保存工具交互的记忆。

        Args:
            request: 工具请求对象
            response: 工具响应内容
            layer: 记忆层级 (global, project, session)
            force_save: 是否强制保存（忽略 should_save_memory 检查）

        Returns:
            保存的记忆 key，如果未保存则返回 None
        """
        try:
            # 检查是否启用了增强记忆
            from utils.conversation_memory import ENABLE_ENHANCED_MEMORY

            if not ENABLE_ENHANCED_MEMORY:
                return None

            # 检查是否应该保存
            if not force_save and not self.should_save_memory(request, response):
                return None

            # 准备记忆内容
            prompt = getattr(request, "prompt", None) or getattr(request, "step", None) or str(request)

            memory_content = {
                "interaction": {
                    "tool": getattr(self, "get_name", lambda: "unknown")(),
                    "request": prompt,
                    "response": response[:2000] if len(response) > 2000 else response,  # 限制长度
                    "timestamp": self._get_timestamp(),
                }
            }

            # 获取元数据
            metadata = self.get_memory_metadata(request, response)

            # 保存记忆
            from utils.intelligent_memory_retrieval import enhanced_save_memory

            key = enhanced_save_memory(
                content=memory_content,
                layer=layer,
                metadata=metadata,
                tags=metadata.get("tags", []),
                mem_type=metadata.get("type", "tool_interaction"),
                importance=metadata.get("importance", "medium"),
            )

            if key:
                logger.info(f"自动保存了 {metadata['tool']} 工具的交互记忆到 {layer} 层: {key}")

            return key

        except Exception as e:
            logger.debug(f"保存交互记忆时出错: {e}")
            return None

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
