"""
Document Chunker - 智能文档分片工具

实现文档的智能分片功能，当输出超过指定 token 限制时，
自动将文档分成多个部分，同时保持内容的完整性和可读性。

主要特性：
1. 智能断点检测 - 在段落、章节边界分割
2. 代码块保护 - 确保代码块不被中断
3. 列表完整性 - 保持列表项的完整
4. 标记添加 - 自动添加分片标记（Part X/Y）
5. Token 计算 - 准确计算每个分片的 token 数
"""

import logging
import re
from dataclasses import dataclass

from utils.token_utils import estimate_tokens

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """表示文档的一个分片"""

    content: str
    part_number: int
    total_parts: int
    token_count: int
    start_line: int
    end_line: int

    @property
    def header(self) -> str:
        """生成分片头部标记"""
        return f"\n{'=' * 60}\n📄 Document Part {self.part_number}/{self.total_parts}\n{'=' * 60}\n"

    @property
    def footer(self) -> str:
        """生成分片尾部标记"""
        if self.part_number < self.total_parts:
            return f"\n{'=' * 60}\n➡️ Continued in Part {self.part_number + 1}/{self.total_parts}\n{'=' * 60}\n"
        else:
            return f"\n{'=' * 60}\n✅ End of Document (Total {self.total_parts} parts)\n{'=' * 60}\n"

    def format(self) -> str:
        """格式化分片内容，包含头部和尾部标记"""
        return f"{self.header}{self.content}{self.footer}"


class DocumentChunker:
    """
    智能文档分片器

    将长文档智能分割成多个部分，保持内容完整性。
    """

    # 默认配置
    DEFAULT_MAX_TOKENS = 30000  # 默认最大 token 数
    MIN_CHUNK_TOKENS = 5000  # 最小分片 token 数
    HEADER_FOOTER_TOKENS = 100  # 预留给头部和尾部标记的 token 数

    # 代码块和特殊块的正则表达式
    CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```", re.MULTILINE)
    FENCED_BLOCK_PATTERN = re.compile(r"(^|\n)(```|~~~)[\s\S]*?\2", re.MULTILINE)
    TABLE_PATTERN = re.compile(r"^\|.*\|$", re.MULTILINE)

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        """
        初始化文档分片器

        Args:
            max_tokens: 每个分片的最大 token 数
        """
        self.max_tokens = max_tokens
        self.effective_max_tokens = max_tokens - self.HEADER_FOOTER_TOKENS

    def should_chunk(self, content: str) -> bool:
        """
        判断内容是否需要分片

        Args:
            content: 要检查的内容

        Returns:
            bool: True 如果需要分片，False 否则
        """
        token_count = estimate_tokens(content)
        return token_count > self.max_tokens

    def chunk_document(self, content: str) -> list[DocumentChunk]:
        """
        将文档分成多个智能分片

        Args:
            content: 要分片的文档内容

        Returns:
            List[DocumentChunk]: 文档分片列表
        """
        # 如果不需要分片，直接返回
        if not self.should_chunk(content):
            token_count = estimate_tokens(content)
            return [
                DocumentChunk(
                    content=content,
                    part_number=1,
                    total_parts=1,
                    token_count=token_count,
                    start_line=1,
                    end_line=len(content.splitlines()),
                )
            ]

        # 将内容按行分割
        lines = content.splitlines(keepends=True)

        # 识别特殊块（代码块、表格等）
        special_blocks = self._identify_special_blocks(lines)

        # 智能分片
        chunks = self._create_chunks(lines, special_blocks)

        # 设置总片数
        total_parts = len(chunks)
        for chunk in chunks:
            chunk.total_parts = total_parts

        logger.info(f"Document chunked into {total_parts} parts")
        return chunks

    def _identify_special_blocks(self, lines: list[str]) -> list[tuple[int, int, str]]:
        """
        识别文档中的特殊块（代码块、表格等）

        Args:
            lines: 文档行列表

        Returns:
            List[Tuple[int, int, str]]: (开始行, 结束行, 类型) 的列表
        """
        special_blocks = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 检查代码块
            if line.strip().startswith("```") or line.strip().startswith("~~~"):
                fence = line.strip()[:3]
                start = i
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(fence):
                    i += 1
                if i < len(lines):
                    special_blocks.append((start, i, "code"))

            # 检查表格
            elif "|" in line and i + 1 < len(lines) and re.match(r"^[\s\-\|]+$", lines[i + 1]):
                start = i
                i += 2  # 跳过表头和分隔符
                while i < len(lines) and "|" in lines[i]:
                    i += 1
                special_blocks.append((start, i - 1, "table"))
                continue

            i += 1

        return special_blocks

    def _create_chunks(self, lines: list[str], special_blocks: list[tuple[int, int, str]]) -> list[DocumentChunk]:
        """
        根据智能断点创建文档分片

        Args:
            lines: 文档行列表
            special_blocks: 特殊块列表

        Returns:
            List[DocumentChunk]: 分片列表
        """
        chunks = []
        current_chunk_lines = []
        current_tokens = 0
        chunk_start_line = 1
        part_number = 1

        for i, line in enumerate(lines):
            line_tokens = estimate_tokens(line)

            # 检查是否在特殊块内
            in_special_block = any(start <= i <= end for start, end, _ in special_blocks)

            # 如果添加这一行会超过限制
            if current_tokens + line_tokens > self.effective_max_tokens and current_chunk_lines:
                # 如果在特殊块内，需要包含整个块
                if in_special_block:
                    # 找到包含当前行的特殊块
                    for start, end, _block_type in special_blocks:
                        if start <= i <= end:
                            # 如果当前分片已经包含了块的开始，继续添加到块结束
                            if any(
                                start <= j < len(current_chunk_lines) + chunk_start_line - 1 for j in range(start, i)
                            ):
                                current_chunk_lines.append(line)
                                current_tokens += line_tokens
                                continue
                            else:
                                # 否则，在块之前断开
                                break

                # 查找最佳断点
                if not in_special_block:
                    best_break = self._find_best_break_point(current_chunk_lines)

                    # 创建分片
                    chunk_content = "".join(current_chunk_lines[:best_break])
                    chunk = DocumentChunk(
                        content=chunk_content.rstrip(),
                        part_number=part_number,
                        total_parts=0,  # 稍后设置
                        token_count=estimate_tokens(chunk_content),
                        start_line=chunk_start_line,
                        end_line=chunk_start_line + best_break - 1,
                    )
                    chunks.append(chunk)

                    # 准备下一个分片
                    part_number += 1
                    current_chunk_lines = current_chunk_lines[best_break:] + [line]
                    chunk_start_line = chunk_start_line + best_break
                    current_tokens = estimate_tokens("".join(current_chunk_lines))
                    continue

            # 添加当前行
            current_chunk_lines.append(line)
            current_tokens += line_tokens

        # 处理剩余的内容
        if current_chunk_lines:
            chunk_content = "".join(current_chunk_lines)
            chunk = DocumentChunk(
                content=chunk_content.rstrip(),
                part_number=part_number,
                total_parts=0,  # 稍后设置
                token_count=estimate_tokens(chunk_content),
                start_line=chunk_start_line,
                end_line=chunk_start_line + len(current_chunk_lines) - 1,
            )
            chunks.append(chunk)

        return chunks

    def _find_best_break_point(self, lines: list[str]) -> int:
        """
        在行列表中找到最佳断点

        优先级：
        1. 章节边界（# 标题）
        2. 空行
        3. 段落结束（句号、问号、感叹号）
        4. 列表项边界
        5. 任意行

        Args:
            lines: 要检查的行列表

        Returns:
            int: 最佳断点索引（在此之前断开）
        """
        # 从后向前查找，但不要太靠前（至少保留 20% 的内容）
        min_index = max(1, len(lines) // 5)

        # 优先级 1: 章节边界
        for i in range(len(lines) - 1, min_index - 1, -1):
            if lines[i].strip().startswith("#") and i > 0 and lines[i - 1].strip() == "":
                return i

        # 优先级 2: 空行
        for i in range(len(lines) - 1, min_index - 1, -1):
            if lines[i].strip() == "" and i < len(lines) - 1:
                return i + 1

        # 优先级 3: 段落结束
        for i in range(len(lines) - 1, min_index - 1, -1):
            line = lines[i].strip()
            if line and (
                line.endswith(".")
                or line.endswith("。")
                or line.endswith("?")
                or line.endswith("？")
                or line.endswith("!")
                or line.endswith("！")
            ):
                return i + 1

        # 优先级 4: 列表项边界
        for i in range(len(lines) - 1, min_index - 1, -1):
            if re.match(r"^[\s]*[-*+•]\s", lines[i]) or re.match(r"^[\s]*\d+\.\s", lines[i]):
                return i

        # 默认：在 80% 处断开
        return int(len(lines) * 0.8)

    def format_chunks(self, chunks: list[DocumentChunk]) -> list[str]:
        """
        格式化所有分片，添加标记

        Args:
            chunks: 分片列表

        Returns:
            List[str]: 格式化后的分片内容列表
        """
        return [chunk.format() for chunk in chunks]


# 便捷函数
def chunk_document(content: str, max_tokens: int = 30000) -> list[str]:
    """
    便捷函数：将文档分片并格式化

    Args:
        content: 要分片的文档内容
        max_tokens: 每个分片的最大 token 数

    Returns:
        List[str]: 格式化后的分片内容列表
    """
    chunker = DocumentChunker(max_tokens)
    chunks = chunker.chunk_document(content)
    return chunker.format_chunks(chunks)


def estimate_chunk_count(content: str, max_tokens: int = 30000) -> int:
    """
    估算文档需要分成多少片

    Args:
        content: 文档内容
        max_tokens: 每个分片的最大 token 数

    Returns:
        int: 估计的分片数
    """
    total_tokens = estimate_tokens(content)
    effective_max = max_tokens - DocumentChunker.HEADER_FOOTER_TOKENS
    return max(1, (total_tokens + effective_max - 1) // effective_max)
