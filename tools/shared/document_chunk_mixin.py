"""
Document Chunk Mixin - 文档分片功能混入类

为工具提供文档分片功能，当输出超过指定 token 限制时，
自动将响应分成多个部分。

这个 mixin 可以被任何工具继承，提供：
1. 自动检测输出长度
2. 智能分片处理
3. 多部分响应返回
4. 用户交互提示
"""

import logging
from typing import Any, Optional, Union

from mcp.types import TextContent

from tools.models import ToolOutput
from utils.document_chunker import chunk_document
from utils.token_utils import estimate_tokens

logger = logging.getLogger(__name__)


class DocumentChunkMixin:
    """
    文档分片功能混入类

    为工具提供智能文档分片功能，处理超长输出。
    """

    # 默认分片阈值（可被工具覆盖）
    CHUNK_THRESHOLD_TOKENS = 30000

    def get_chunk_threshold(self) -> int:
        """
        获取分片阈值（token 数）

        工具可以覆盖此方法来自定义阈值。

        Returns:
            int: 触发分片的 token 数阈值
        """
        return self.CHUNK_THRESHOLD_TOKENS

    def should_chunk_response(self, content: str) -> bool:
        """
        判断响应是否需要分片

        Args:
            content: 响应内容

        Returns:
            bool: True 如果需要分片
        """
        if not content:
            return False

        token_count = estimate_tokens(content)
        threshold = self.get_chunk_threshold()

        if token_count > threshold:
            logger.info(
                f"{self.name} tool: Response has {token_count:,} tokens, "
                f"exceeding threshold of {threshold:,}. Will chunk."
            )
            return True
        return False

    def chunk_response(self, content: str) -> list[str]:
        """
        将响应内容分片

        Args:
            content: 要分片的内容

        Returns:
            List[str]: 分片后的内容列表
        """
        threshold = self.get_chunk_threshold()
        return chunk_document(content, max_tokens=threshold)

    def create_chunked_response(
        self, content: str, original_request: Any, model_info: Optional[dict] = None, chunk_index: int = 0
    ) -> Union[ToolOutput, list[TextContent]]:
        """
        创建分片响应

        当输出超过阈值时，返回第一片并提供继续选项。

        Args:
            content: 完整的响应内容
            original_request: 原始请求对象
            model_info: 模型信息
            chunk_index: 当前分片索引（0 表示第一片）

        Returns:
            ToolOutput 或 List[TextContent]: 包含分片内容和继续选项的响应
        """
        # 获取所有分片
        chunks = self.chunk_response(content)

        if chunk_index >= len(chunks):
            # 请求的分片索引超出范围
            return self._create_error_response(f"Invalid chunk index {chunk_index}. Document has {len(chunks)} parts.")

        # 获取当前分片
        current_chunk = chunks[chunk_index]

        # 如果这不是最后一片，创建继续选项
        if chunk_index < len(chunks) - 1:
            # 保存剩余内容的状态
            continuation_state = {
                "action": "continue_chunks",
                "chunks": chunks,
                "current_index": chunk_index,
                "original_request": original_request,
                "model_info": model_info,
            }

            # 创建继续提示
            continuation_prompt = (
                f"\n\n{'=' * 60}\n"
                f"📋 This is Part {chunk_index + 1} of {len(chunks)}. "
                f"The document continues in the next part.\n"
                f"{'=' * 60}\n\n"
                f"To view the next part, please use the continuation option."
            )

            # 添加继续提示到当前分片
            display_content = current_chunk + continuation_prompt

            # 创建带继续选项的输出
            # 注意：ContinuationOffer 需要 continuation_id, note, remaining_turns
            # 对于文档分片，我们使用特殊的 continuation_id
            return ToolOutput(
                content=display_content,
                content_type="text",
                status="continuation_available",
                metadata={
                    "chunk_info": {
                        "current_part": chunk_index + 1,
                        "total_parts": len(chunks),
                        "total_tokens": sum(estimate_tokens(c) for c in chunks),
                        "current_tokens": estimate_tokens(current_chunk),
                    },
                    "continuation_state": continuation_state,  # 存储在 metadata 中
                },
            )
        else:
            # 这是最后一片，不需要继续选项
            return ToolOutput(
                content=current_chunk,
                content_type="text",
                status="success",
                metadata={
                    "chunk_info": {
                        "current_part": chunk_index + 1,
                        "total_parts": len(chunks),
                        "total_tokens": sum(estimate_tokens(c) for c in chunks),
                        "current_tokens": estimate_tokens(current_chunk),
                    }
                },
            )

    def handle_chunk_continuation(self, state: dict[str, Any]) -> Union[ToolOutput, list[TextContent]]:
        """
        处理分片继续请求

        Args:
            state: 继续状态，包含分片信息

        Returns:
            下一个分片的响应
        """
        if state.get("action") != "continue_chunks":
            return self._create_error_response("Invalid continuation state")

        chunks = state.get("chunks", [])
        current_index = state.get("current_index", 0)
        next_index = current_index + 1

        if next_index >= len(chunks):
            return self._create_error_response(f"No more chunks available. Document has {len(chunks)} parts.")

        # 直接返回下一个分片
        current_chunk = chunks[next_index]

        # 如果还有更多分片，创建继续选项
        if next_index < len(chunks) - 1:
            continuation_state = {
                "action": "continue_chunks",
                "chunks": chunks,
                "current_index": next_index,
            }

            continuation_prompt = (
                f"\n\n{'=' * 60}\n"
                f"📋 This is Part {next_index + 1} of {len(chunks)}. "
                f"The document continues in the next part.\n"
                f"{'=' * 60}\n\n"
                f"To view the next part, please use the continuation option."
            )

            display_content = current_chunk + continuation_prompt

            return ToolOutput(
                content=display_content,
                content_type="text",
                status="continuation_available",
                metadata={
                    "chunk_info": {
                        "current_part": next_index + 1,
                        "total_parts": len(chunks),
                        "current_tokens": estimate_tokens(current_chunk),
                    },
                    "continuation_state": continuation_state,  # 存储在 metadata 中
                },
            )
        else:
            # 最后一片
            return ToolOutput(
                content=current_chunk,
                content_type="text",
                status="success",
                metadata={
                    "chunk_info": {
                        "current_part": next_index + 1,
                        "total_parts": len(chunks),
                        "current_tokens": estimate_tokens(current_chunk),
                    }
                },
            )

    def wrap_response_with_chunking(
        self, content: str, original_request: Any, model_info: Optional[dict] = None
    ) -> Union[str, ToolOutput]:
        """
        包装响应，如果需要则进行分片

        这是一个便捷方法，工具可以在 format_response 中调用。

        Args:
            content: 原始响应内容
            original_request: 原始请求
            model_info: 模型信息

        Returns:
            如果不需要分片返回原始内容字符串，
            如果需要分片返回 ToolOutput 对象
        """
        if self.should_chunk_response(content):
            logger.info(f"{self.name} tool: Chunking response due to size")
            return self.create_chunked_response(content, original_request, model_info)
        return content

    def _create_error_response(self, error_message: str) -> ToolOutput:
        """
        创建错误响应

        Args:
            error_message: 错误消息

        Returns:
            ToolOutput: 错误响应对象
        """
        return ToolOutput(
            content=f"Error: {error_message}", content_type="text", status="error", metadata={"error": error_message}
        )

    def estimate_response_chunks(self, content: str) -> int:
        """
        估算响应需要分成多少片

        Args:
            content: 响应内容

        Returns:
            int: 估计的分片数
        """
        from utils.document_chunker import estimate_chunk_count

        return estimate_chunk_count(content, self.get_chunk_threshold())
