"""
文件处理集成层

将增强的文件处理器集成到现有的工具基础设施中，
提供向后兼容的接口，同时启用优化功能。
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.enhanced_file_processor import (
    cleanup_file_caches,
    get_file_processing_stats,
    process_files_with_optimization,
)
from utils.file_utils import expand_paths
from utils.file_utils import read_files as original_read_files
from utils.token_utils import estimate_tokens

logger = logging.getLogger(__name__)


class FileProcessingIntegration:
    """文件处理集成管理器"""

    def __init__(self):
        self.enabled = True
        self._fallback_to_original = False

        # 性能统计
        self.stats = {"optimized_calls": 0, "fallback_calls": 0, "total_time_saved": 0.0, "cache_hit_rate": 0.0}

    def should_use_optimized_processing(
        self, files: List[str], max_tokens: int, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """判断是否应该使用优化的文件处理"""

        # 如果禁用了优化功能
        if not self.enabled or self._fallback_to_original:
            return False

        # 少于3个文件时，原始处理更简单
        if len(files) < 3:
            return False

        # 大文件列表或高令牌预算时使用优化处理
        if len(files) >= 5 or max_tokens >= 10000:
            return True

        # 如果有大文件，使用优化处理（摘要功能）
        try:
            total_size = 0
            for file_path in files:
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    if total_size > 1024 * 1024:  # 1MB总大小
                        return True
        except:
            pass  # 文件访问错误时回退到原始处理

        return False

    async def process_files_enhanced(
        self,
        files: List[str],
        max_tokens: int = 50000,
        reserve_tokens: int = 1000,
        include_line_numbers: bool = True,
        existing_files: Optional[Set[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        增强的文件处理入口点

        Returns:
            tuple: (content, processed_files, stats)
        """

        if not files:
            return "", [], {"processed_files": 0, "optimized": False}

        # 判断是否使用优化处理
        use_optimized = self.should_use_optimized_processing(files, max_tokens, context)

        if use_optimized:
            return await self._process_with_optimization(files, max_tokens, reserve_tokens, existing_files, context)
        else:
            return await self._process_with_fallback(files, max_tokens, reserve_tokens, include_line_numbers, context)

    async def _process_with_optimization(
        self,
        files: List[str],
        max_tokens: int,
        reserve_tokens: int,
        existing_files: Optional[Set[str]],
        context: Optional[Dict[str, Any]],
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """使用优化的文件处理器"""

        try:
            # 扩展目录到文件列表
            expanded_files = expand_paths(files)

            # 调用优化处理器
            content, processing_stats = await process_files_with_optimization(
                expanded_files, max_tokens - reserve_tokens, existing_files
            )

            # 更新统计
            self.stats["optimized_calls"] += 1
            processing_stats["optimized"] = True
            processing_stats["method"] = "enhanced_processor"

            logger.info(
                f"优化文件处理完成: {processing_stats['processed_files']} 文件, "
                f"{processing_stats['total_tokens']} 令牌, "
                f"缓存命中: {processing_stats.get('cache_hits', 0)}"
            )

            return content, expanded_files[: processing_stats["processed_files"]], processing_stats

        except Exception as e:
            logger.warning(f"优化文件处理失败，回退到原始方法: {e}")
            self._fallback_to_original = True
            return await self._process_with_fallback(files, max_tokens, reserve_tokens, True, context)

    async def _process_with_fallback(
        self,
        files: List[str],
        max_tokens: int,
        reserve_tokens: int,
        include_line_numbers: bool,
        context: Optional[Dict[str, Any]],
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """使用原始文件处理器"""

        try:
            # 在线程池中运行原始的同步处理
            loop = asyncio.get_event_loop()

            def sync_process():
                content = original_read_files(
                    files,
                    max_tokens=max_tokens,
                    reserve_tokens=reserve_tokens,
                    include_line_numbers=include_line_numbers,
                )

                # 扩展文件列表获取实际处理的文件
                expanded_files = expand_paths(files)

                # 估算令牌数
                estimated_tokens = estimate_tokens(content)

                return (
                    content,
                    expanded_files,
                    {
                        "processed_files": len(expanded_files),
                        "total_tokens": estimated_tokens,
                        "optimized": False,
                        "method": "original_processor",
                    },
                )

            content, processed_files, stats = await loop.run_in_executor(None, sync_process)

            # 更新统计
            self.stats["fallback_calls"] += 1

            logger.debug(f"原始文件处理完成: {stats['processed_files']} 文件, {stats['total_tokens']} 令牌")

            return content, processed_files, stats

        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            return (
                f"# 文件处理错误\n\n{str(e)}",
                [],
                {"processed_files": 0, "total_tokens": 0, "optimized": False, "error": str(e)},
            )


# 全局集成实例
_integration_instance = None


def get_file_processing_integration() -> FileProcessingIntegration:
    """获取文件处理集成实例"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = FileProcessingIntegration()
    return _integration_instance


# 兼容性接口：增强现有的文件处理函数
async def read_files_enhanced(
    files: List[str],
    max_tokens: int = 50000,
    reserve_tokens: int = 1000,
    include_line_numbers: bool = True,
    existing_files: Optional[Set[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    增强版的 read_files 函数，自动选择最优处理方式

    兼容现有接口，同时提供优化功能
    """

    integration = get_file_processing_integration()
    content, _, _ = await integration.process_files_enhanced(
        files=files,
        max_tokens=max_tokens,
        reserve_tokens=reserve_tokens,
        include_line_numbers=include_line_numbers,
        existing_files=existing_files,
        context=context,
    )

    return content


async def read_files_with_stats(
    files: List[str],
    max_tokens: int = 50000,
    reserve_tokens: int = 1000,
    include_line_numbers: bool = True,
    existing_files: Optional[Set[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    读取文件并返回处理统计信息
    """

    integration = get_file_processing_integration()
    content, processed_files, stats = await integration.process_files_enhanced(
        files=files,
        max_tokens=max_tokens,
        reserve_tokens=reserve_tokens,
        include_line_numbers=include_line_numbers,
        existing_files=existing_files,
        context=context,
    )

    stats["processed_file_paths"] = processed_files
    return content, stats


def enable_optimized_file_processing(enabled: bool = True):
    """启用或禁用优化的文件处理"""
    integration = get_file_processing_integration()
    integration.enabled = enabled
    integration._fallback_to_original = not enabled

    if enabled:
        logger.info("已启用优化文件处理")
    else:
        logger.info("已禁用优化文件处理，将使用原始方法")


def get_comprehensive_file_stats() -> Dict[str, Any]:
    """获取综合的文件处理统计信息"""
    integration = get_file_processing_integration()

    # 获取增强处理器的统计
    enhanced_stats = get_file_processing_stats()

    # 组合统计信息
    return {
        "integration_stats": integration.stats,
        "enhanced_processor_stats": enhanced_stats,
        "optimization_enabled": integration.enabled,
        "fallback_mode": integration._fallback_to_original,
    }


def cleanup_all_file_caches():
    """清理所有文件缓存"""
    try:
        cleanup_file_caches()
        logger.info("文件缓存清理完成")
    except Exception as e:
        logger.warning(f"清理文件缓存失败: {e}")


# 向工具提供的便捷接口
class OptimizedFileHandler:
    """
    为工具提供的优化文件处理接口

    可以在现有工具中直接使用，无需修改大量代码
    """

    @staticmethod
    async def prepare_file_content_optimized(
        request_files: List[str],
        max_tokens: int,
        reserve_tokens: int = 1000,
        existing_files: Optional[Set[str]] = None,
        tool_name: str = "unknown",
        include_line_numbers: bool = True,
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        为工具优化的文件内容准备方法

        这个方法可以直接替换工具中的文件处理逻辑
        """

        if not request_files:
            return "", [], {"processed_files": 0}

        context = {"tool_name": tool_name, "include_line_numbers": include_line_numbers}

        content, processed_files, stats = await read_files_with_stats(
            files=request_files,
            max_tokens=max_tokens,
            reserve_tokens=reserve_tokens,
            include_line_numbers=include_line_numbers,
            existing_files=existing_files,
            context=context,
        )

        logger.info(
            f"[{tool_name}] 文件处理完成: {stats['processed_files']} 文件, "
            f"方法: {stats.get('method', 'unknown')}, "
            f"优化: {stats.get('optimized', False)}"
        )

        return content, processed_files, stats

    @staticmethod
    def should_optimize_for_tool(tool_name: str, file_count: int, total_tokens: int) -> bool:
        """
        为特定工具判断是否应该启用优化
        """

        # 某些工具特别适合优化处理
        optimization_friendly_tools = {"analyze", "codereview", "debug", "precommit", "secaudit", "testgen", "refactor"}

        if tool_name.lower() in optimization_friendly_tools:
            return file_count >= 2 or total_tokens >= 5000

        # 其他工具使用保守策略
        return file_count >= 5 or total_tokens >= 15000
