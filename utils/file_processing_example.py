"""
文件处理优化使用示例

演示如何在现有工具中集成增强的文件处理功能
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from utils.enhanced_file_processor import get_enhanced_file_processor
from utils.file_processing_integration import OptimizedFileHandler

logger = logging.getLogger(__name__)


class ExampleToolWithOptimizedFiles:
    """
    示例工具：展示如何集成优化的文件处理

    这个例子展示了现有工具如何无缝升级到使用优化的文件处理
    """

    def __init__(self, tool_name: str = "example_tool"):
        self.tool_name = tool_name

    async def process_files_traditionally(self, files: List[str], max_tokens: int = 50000) -> str:
        """传统的文件处理方式（用于对比）"""

        from utils.file_utils import read_files

        logger.info(f"[{self.tool_name}] 使用传统方法处理 {len(files)} 个文件")

        # 传统方法：同步读取，无缓存，无优化
        content = read_files(files, max_tokens=max_tokens, include_line_numbers=True)

        return content

    async def process_files_optimized(
        self, files: List[str], max_tokens: int = 50000, existing_files: Optional[Set[str]] = None
    ) -> tuple[str, Dict[str, Any]]:
        """优化的文件处理方式"""

        logger.info(f"[{self.tool_name}] 使用优化方法处理 {len(files)} 个文件")

        # 优化方法：异步读取，智能缓存，文件摘要
        content, processed_files, stats = await OptimizedFileHandler.prepare_file_content_optimized(
            request_files=files,
            max_tokens=max_tokens,
            existing_files=existing_files,
            tool_name=self.tool_name,
            include_line_numbers=True,
        )

        return content, stats

    async def demonstrate_optimization_benefits(self, test_files: List[str]):
        """演示优化效果"""

        print(f"\n🧪 {self.tool_name} 文件处理优化演示")
        print("=" * 60)

        # 测试传统方法
        print("\n📄 传统处理方法:")
        traditional_start = asyncio.get_event_loop().time()
        traditional_content = await self.process_files_traditionally(test_files)
        traditional_time = asyncio.get_event_loop().time() - traditional_start

        print(f"   - 处理时间: {traditional_time:.3f} 秒")
        print(f"   - 内容长度: {len(traditional_content):,} 字符")
        print(f"   - 文件数量: {len(test_files)}")

        # 测试优化方法（首次）
        print("\n🚀 优化处理方法（首次）:")
        optimized_start = asyncio.get_event_loop().time()
        optimized_content, stats = await self.process_files_optimized(test_files)
        optimized_time = asyncio.get_event_loop().time() - optimized_start

        print(f"   - 处理时间: {optimized_time:.3f} 秒")
        print(f"   - 内容长度: {len(optimized_content):,} 字符")
        print(f"   - 处理方法: {stats.get('method', 'unknown')}")
        print(f"   - 缓存命中: {stats.get('cache_hits', 0)}")
        print(f"   - 缓存未命中: {stats.get('cache_misses', 0)}")
        print(f"   - 摘要文件: {stats.get('files_summarized', 0)}")

        # 测试优化方法（第二次，展示缓存效果）
        print("\n⚡ 优化处理方法（第二次，缓存效果）:")
        cached_start = asyncio.get_event_loop().time()
        cached_content, cached_stats = await self.process_files_optimized(test_files)
        cached_time = asyncio.get_event_loop().time() - cached_start

        print(f"   - 处理时间: {cached_time:.3f} 秒")
        print(f"   - 内容长度: {len(cached_content):,} 字符")
        print(f"   - 处理方法: {cached_stats.get('method', 'unknown')}")
        print(f"   - 缓存命中: {cached_stats.get('cache_hits', 0)}")
        print(f"   - 缓存未命中: {cached_stats.get('cache_misses', 0)}")

        # 性能对比
        print("\n📊 性能对比:")
        speed_improvement = (traditional_time - cached_time) / traditional_time * 100
        print(f"   - 传统方法: {traditional_time:.3f} 秒")
        print(f"   - 优化方法（首次）: {optimized_time:.3f} 秒")
        print(f"   - 优化方法（缓存）: {cached_time:.3f} 秒")
        print(f"   - 性能提升: {speed_improvement:.1f}%")

        # 缓存统计
        processor = get_enhanced_file_processor()
        cache_stats = processor.get_cache_stats()

        print("\n💾 缓存状态:")
        memory_cache = cache_stats["cache_stats"]["memory_cache"]
        print(f"   - 内存缓存项: {memory_cache['items']}")
        print(f"   - 内存使用: {memory_cache['size_mb']:.2f} MB / {memory_cache['max_size_mb']} MB")

        disk_cache = cache_stats["cache_stats"]["disk_cache"]
        print(f"   - 磁盘缓存项: {disk_cache['items']}")
        print(f"   - 磁盘使用: {disk_cache['size_mb']:.2f} MB / {disk_cache['max_size_mb']} MB")


async def run_example():
    """运行文件处理优化示例"""

    # 创建示例工具
    example_tool = ExampleToolWithOptimizedFiles("file_optimization_demo")

    # 使用项目中的实际文件进行测试
    test_files = [
        "config.py",
        "server.py",
        "utils/file_utils.py",
        "utils/enhanced_file_processor.py",
        "tools/shared/base_tool.py",
    ]

    # 过滤存在的文件
    import os

    existing_files = [f for f in test_files if os.path.exists(f)]

    if existing_files:
        await example_tool.demonstrate_optimization_benefits(existing_files)
        print("\n🎉 文件处理优化演示完成！")
    else:
        print("❌ 未找到测试文件，请在项目根目录运行此示例")


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)

    # 运行示例
    asyncio.run(run_example())
