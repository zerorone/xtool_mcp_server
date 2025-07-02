"""
增强的文件处理器

提供高性能的文件处理功能，包括：
1. 文件内容哈希缓存 - 避免重复读取
2. 异步并行文件读取 - 提升I/O性能
3. 智能文件摘要 - 处理大文件
4. 精确令牌估算 - 更好的资源管理
5. 分层缓存系统 - 内存+磁盘缓存
"""

import asyncio
import hashlib
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class FileContentHash:
    """文件内容哈希管理"""

    def __init__(self):
        self._hash_cache: Dict[str, Tuple[str, float, int]] = {}  # path -> (hash, mtime, size)
        self._lock = threading.Lock()

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """获取文件的SHA256哈希值，支持缓存"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            stat = path.stat()
            current_mtime = stat.st_mtime
            current_size = stat.st_size

            with self._lock:
                # 检查缓存
                if file_path in self._hash_cache:
                    cached_hash, cached_mtime, cached_size = self._hash_cache[file_path]
                    if cached_mtime == current_mtime and cached_size == current_size:
                        return cached_hash

            # 计算新哈希
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                # 分块读取，避免大文件内存问题
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)

            file_hash = hasher.hexdigest()

            with self._lock:
                # 更新缓存
                self._hash_cache[file_path] = (file_hash, current_mtime, current_size)

            return file_hash

        except Exception as e:
            logger.warning(f"计算文件哈希失败 {file_path}: {e}")
            return None

    def clear_cache(self):
        """清空哈希缓存"""
        with self._lock:
            self._hash_cache.clear()

    def cleanup_stale_entries(self):
        """清理过期的缓存条目"""
        with self._lock:
            to_remove = []
            for file_path in self._hash_cache:
                if not Path(file_path).exists():
                    to_remove.append(file_path)

            for file_path in to_remove:
                del self._hash_cache[file_path]

            logger.debug(f"清理了 {len(to_remove)} 个过期缓存项")


class ContentCache:
    """文件内容缓存系统"""

    def __init__(self, max_memory_mb: int = 50, max_disk_mb: int = 200):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_disk_bytes = max_disk_mb * 1024 * 1024

        # 内存缓存: hash -> (content, access_time, size)
        self._memory_cache: Dict[str, Tuple[str, float, int]] = {}
        self._memory_size = 0
        self._lock = threading.Lock()

        # 磁盘缓存目录
        self.cache_dir = Path(".zen_memory/file_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 缓存元数据
        self._disk_metadata_file = self.cache_dir / "metadata.json"
        self._disk_metadata = self._load_disk_metadata()

    def _load_disk_metadata(self) -> Dict[str, Dict[str, Any]]:
        """加载磁盘缓存元数据"""
        try:
            if self._disk_metadata_file.exists():
                with open(self._disk_metadata_file, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载磁盘缓存元数据失败: {e}")
        return {}

    def _save_disk_metadata(self):
        """保存磁盘缓存元数据"""
        try:
            with open(self._disk_metadata_file, "w", encoding="utf-8") as f:
                json.dump(self._disk_metadata, f, indent=2)
        except Exception as e:
            logger.warning(f"保存磁盘缓存元数据失败: {e}")

    def get_content(self, content_hash: str) -> Optional[str]:
        """获取缓存的内容"""
        # 先检查内存缓存
        with self._lock:
            if content_hash in self._memory_cache:
                content, _, size = self._memory_cache[content_hash]
                # 更新访问时间
                self._memory_cache[content_hash] = (content, time.time(), size)
                return content

        # 检查磁盘缓存
        return self._get_from_disk(content_hash)

    def store_content(self, content_hash: str, content: str) -> bool:
        """存储内容到缓存"""
        content_size = len(content.encode("utf-8"))
        current_time = time.time()

        # 优先存储到内存（如果空间足够）
        with self._lock:
            if self._memory_size + content_size <= self.max_memory_bytes:
                self._memory_cache[content_hash] = (content, current_time, content_size)
                self._memory_size += content_size
                return True
            else:
                # 内存不足，尝试清理
                self._cleanup_memory_cache()
                if self._memory_size + content_size <= self.max_memory_bytes:
                    self._memory_cache[content_hash] = (content, current_time, content_size)
                    self._memory_size += content_size
                    return True

        # 内存不足，存储到磁盘
        return self._store_to_disk(content_hash, content, content_size)

    def _cleanup_memory_cache(self):
        """清理内存缓存（LRU策略）"""
        if not self._memory_cache:
            return

        # 按访问时间排序，移除最久未访问的项目
        items = [(hash_key, access_time) for hash_key, (_, access_time, _) in self._memory_cache.items()]
        items.sort(key=lambda x: x[1])

        # 移除最旧的25%项目
        remove_count = max(1, len(items) // 4)
        for i in range(remove_count):
            hash_key = items[i][0]
            _, _, size = self._memory_cache[hash_key]
            del self._memory_cache[hash_key]
            self._memory_size -= size

        logger.debug(f"清理了 {remove_count} 个内存缓存项")

    def _get_from_disk(self, content_hash: str) -> Optional[str]:
        """从磁盘缓存获取内容"""
        try:
            cache_file = self.cache_dir / f"{content_hash[:2]}" / f"{content_hash}.txt"
            if not cache_file.exists():
                return None

            # 检查元数据
            if content_hash not in self._disk_metadata:
                return None

            metadata = self._disk_metadata[content_hash]

            # 更新访问时间
            metadata["access_time"] = time.time()
            self._save_disk_metadata()

            # 读取内容
            with open(cache_file, encoding="utf-8") as f:
                content = f.read()

            # 尝试提升到内存缓存
            self.store_content(content_hash, content)

            return content

        except Exception as e:
            logger.warning(f"从磁盘缓存读取失败 {content_hash}: {e}")
            return None

    def _store_to_disk(self, content_hash: str, content: str, content_size: int) -> bool:
        """存储内容到磁盘缓存"""
        try:
            # 检查磁盘空间
            current_disk_size = sum(metadata.get("size", 0) for metadata in self._disk_metadata.values())

            if current_disk_size + content_size > self.max_disk_bytes:
                self._cleanup_disk_cache()

            # 创建目录结构（使用哈希前缀分层）
            subdir = self.cache_dir / content_hash[:2]
            subdir.mkdir(exist_ok=True)

            cache_file = subdir / f"{content_hash}.txt"

            # 写入文件
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(content)

            # 更新元数据
            self._disk_metadata[content_hash] = {
                "size": content_size,
                "created_time": time.time(),
                "access_time": time.time(),
                "file_path": str(cache_file),
            }
            self._save_disk_metadata()

            return True

        except Exception as e:
            logger.warning(f"存储到磁盘缓存失败 {content_hash}: {e}")
            return False

    def _cleanup_disk_cache(self):
        """清理磁盘缓存（LRU策略）"""
        if not self._disk_metadata:
            return

        # 按访问时间排序
        items = [(hash_key, metadata["access_time"]) for hash_key, metadata in self._disk_metadata.items()]
        items.sort(key=lambda x: x[1])

        # 移除最旧的30%项目
        remove_count = max(1, len(items) // 3)
        for i in range(remove_count):
            hash_key = items[i][0]
            metadata = self._disk_metadata[hash_key]

            # 删除文件
            try:
                cache_file = Path(metadata["file_path"])
                if cache_file.exists():
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"删除缓存文件失败: {e}")

            # 删除元数据
            del self._disk_metadata[hash_key]

        self._save_disk_metadata()
        logger.debug(f"清理了 {remove_count} 个磁盘缓存项")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            memory_items = len(self._memory_cache)
            memory_size_mb = self._memory_size / (1024 * 1024)

        disk_items = len(self._disk_metadata)
        disk_size_mb = sum(metadata.get("size", 0) for metadata in self._disk_metadata.values()) / (1024 * 1024)

        return {
            "memory_cache": {
                "items": memory_items,
                "size_mb": round(memory_size_mb, 2),
                "max_size_mb": self.max_memory_bytes / (1024 * 1024),
            },
            "disk_cache": {
                "items": disk_items,
                "size_mb": round(disk_size_mb, 2),
                "max_size_mb": self.max_disk_bytes / (1024 * 1024),
            },
        }


class SmartFileSummarizer:
    """智能文件摘要生成器"""

    def __init__(self, max_summary_tokens: int = 2000):
        self.max_summary_tokens = max_summary_tokens

    def should_summarize(self, file_path: str, content: str, estimated_tokens: int) -> bool:
        """判断是否需要对文件进行摘要"""
        # 超过5000个令牌的文件需要摘要
        if estimated_tokens > 5000:
            return True

        # 特定类型的大文件需要摘要
        file_ext = Path(file_path).suffix.lower()
        if file_ext in [".log", ".txt", ".md"] and estimated_tokens > 3000:
            return True

        return False

    def generate_summary(self, file_path: str, content: str) -> str:
        """生成文件摘要"""
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext in [".py", ".js", ".ts", ".java", ".cpp", ".c"]:
                return self._summarize_code_file(content)
            elif file_ext in [".md", ".txt", ".rst"]:
                return self._summarize_text_file(content)
            elif file_ext in [".json", ".yaml", ".yml"]:
                return self._summarize_config_file(content)
            elif file_ext in [".log"]:
                return self._summarize_log_file(content)
            else:
                return self._summarize_generic_file(content)

        except Exception as e:
            logger.warning(f"生成文件摘要失败 {file_path}: {e}")
            return self._fallback_summary(content)

    def _summarize_code_file(self, content: str) -> str:
        """摘要代码文件"""
        lines = content.split("\n")

        # 提取重要元素
        imports = []
        classes = []
        functions = []
        constants = []

        for i, line in enumerate(lines[: min(200, len(lines))]):  # 只分析前200行
            stripped = line.strip()

            # 导入语句
            if (
                stripped.startswith("import ")
                or stripped.startswith("from ")
                or stripped.startswith("#include")
                or stripped.startswith("using")
            ):
                imports.append(stripped)

            # 类定义
            elif stripped.startswith("class ") or stripped.startswith("interface ") or stripped.startswith("struct "):
                classes.append(stripped)

            # 函数定义
            elif (
                stripped.startswith("def ")
                or stripped.startswith("function ")
                or "function" in stripped.lower()
                and "(" in stripped
            ):
                functions.append(stripped)

            # 常量（全大写变量）
            elif "=" in stripped and stripped.split("=")[0].strip().isupper():
                constants.append(stripped)

        # 构建摘要
        summary_parts = ["# 文件摘要\n"]

        if imports:
            summary_parts.append(f"## 导入 ({len(imports)}项):")
            summary_parts.extend(imports[:10])  # 最多显示10个导入
            if len(imports) > 10:
                summary_parts.append(f"... 还有 {len(imports) - 10} 个导入")
            summary_parts.append("")

        if classes:
            summary_parts.append(f"## 类定义 ({len(classes)}项):")
            summary_parts.extend(classes[:5])
            if len(classes) > 5:
                summary_parts.append(f"... 还有 {len(classes) - 5} 个类")
            summary_parts.append("")

        if functions:
            summary_parts.append(f"## 函数定义 ({len(functions)}项):")
            summary_parts.extend(functions[:10])
            if len(functions) > 10:
                summary_parts.append(f"... 还有 {len(functions) - 10} 个函数")
            summary_parts.append("")

        if constants:
            summary_parts.append(f"## 常量 ({len(constants)}项):")
            summary_parts.extend(constants[:5])
            if len(constants) > 5:
                summary_parts.append(f"... 还有 {len(constants) - 5} 个常量")

        # 添加文件统计
        summary_parts.append("\n## 文件统计:")
        summary_parts.append(f"- 总行数: {len(lines)}")
        summary_parts.append(f"- 非空行数: {len([l for l in lines if l.strip()])}")
        summary_parts.append(
            f"- 估计代码行数: {len([l for l in lines if l.strip() and not l.strip().startswith('#')])}"
        )

        return "\n".join(summary_parts)

    def _summarize_text_file(self, content: str) -> str:
        """摘要文本文件"""
        lines = content.split("\n")

        # 获取开头和结尾
        start_lines = lines[:20]
        end_lines = lines[-10:] if len(lines) > 30 else []

        # 查找标题（Markdown）
        headers = [line for line in lines if line.strip().startswith("#")]

        summary_parts = ["# 文件摘要\n"]

        if headers:
            summary_parts.append(f"## 标题结构 ({len(headers)}项):")
            summary_parts.extend(headers[:10])
            if len(headers) > 10:
                summary_parts.append(f"... 还有 {len(headers) - 10} 个标题")
            summary_parts.append("")

        summary_parts.append("## 文件开头:")
        summary_parts.extend(start_lines)

        if end_lines:
            summary_parts.append("\n## 文件结尾:")
            summary_parts.extend(end_lines)

        summary_parts.append("\n## 文件统计:")
        summary_parts.append(f"- 总行数: {len(lines)}")
        summary_parts.append(f"- 段落数: {len([l for l in lines if l.strip() == '']) + 1}")

        return "\n".join(summary_parts)

    def _summarize_config_file(self, content: str) -> str:
        """摘要配置文件"""
        lines = content.split("\n")

        # 查找主要配置项
        config_items = []
        for line in lines[:50]:  # 分析前50行
            stripped = line.strip()
            if ":" in stripped and not stripped.startswith("#"):
                config_items.append(stripped)

        summary_parts = ["# 配置文件摘要\n"]

        if config_items:
            summary_parts.append(f"## 主要配置项 ({len(config_items)}项):")
            summary_parts.extend(config_items[:15])
            if len(config_items) > 15:
                summary_parts.append(f"... 还有 {len(config_items) - 15} 个配置项")

        summary_parts.append("\n## 文件统计:")
        summary_parts.append(f"- 总行数: {len(lines)}")
        summary_parts.append(f"- 配置项: {len(config_items)}")

        return "\n".join(summary_parts)

    def _summarize_log_file(self, content: str) -> str:
        """摘要日志文件"""
        lines = content.split("\n")

        # 分析日志级别
        log_levels = {"ERROR": 0, "WARN": 0, "INFO": 0, "DEBUG": 0}
        for line in lines:
            for level in log_levels:
                if level in line.upper():
                    log_levels[level] += 1
                    break

        # 获取开头和结尾
        start_lines = lines[:10]
        end_lines = lines[-10:] if len(lines) > 20 else []

        summary_parts = ["# 日志文件摘要\n"]

        summary_parts.append("## 日志级别统计:")
        for level, count in log_levels.items():
            if count > 0:
                summary_parts.append(f"- {level}: {count}")

        summary_parts.append("\n## 日志开头:")
        summary_parts.extend(start_lines)

        if end_lines:
            summary_parts.append("\n## 日志结尾:")
            summary_parts.extend(end_lines)

        summary_parts.append("\n## 文件统计:")
        summary_parts.append(f"- 总行数: {len(lines)}")
        summary_parts.append(f"- 总日志条目: {sum(log_levels.values())}")

        return "\n".join(summary_parts)

    def _summarize_generic_file(self, content: str) -> str:
        """通用文件摘要"""
        lines = content.split("\n")

        # 获取开头和结尾
        start_lines = lines[:15]
        end_lines = lines[-10:] if len(lines) > 25 else []

        summary_parts = ["# 文件摘要\n"]

        summary_parts.append("## 文件开头:")
        summary_parts.extend(start_lines)

        if end_lines:
            summary_parts.append("\n## 文件结尾:")
            summary_parts.extend(end_lines)

        summary_parts.append("\n## 文件统计:")
        summary_parts.append(f"- 总行数: {len(lines)}")
        summary_parts.append(f"- 字符数: {len(content)}")

        return "\n".join(summary_parts)

    def _fallback_summary(self, content: str) -> str:
        """回退摘要（当其他方法失败时）"""
        lines = content.split("\n")
        start_lines = lines[:20]

        summary = ["# 文件摘要（简化版）\n"]
        summary.append("## 文件开头:")
        summary.extend(start_lines)
        summary.append(f"\n总行数: {len(lines)}")

        return "\n".join(summary)


class EnhancedFileProcessor:
    """增强的文件处理器"""

    def __init__(self):
        self.hash_manager = FileContentHash()
        self.content_cache = ContentCache()
        self.summarizer = SmartFileSummarizer()

        # 处理统计
        self.stats = {"cache_hits": 0, "cache_misses": 0, "files_summarized": 0, "parallel_reads": 0}
        self._stats_lock = threading.Lock()

    async def process_files_optimized(
        self, file_paths: List[str], token_budget: int, existing_files: Optional[Set[str]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """优化的文件处理流程"""

        if not file_paths:
            return "", {"processed_files": 0, "total_tokens": 0}

        # 过滤已存在的文件
        if existing_files:
            file_paths = [f for f in file_paths if f not in existing_files]

        # 并行读取文件信息
        file_info_list = await self._parallel_file_analysis(file_paths)

        # 根据令牌预算选择文件
        selected_files = self._select_files_by_budget(file_info_list, token_budget)

        # 并行读取和处理选定的文件
        processed_content = await self._parallel_file_processing(selected_files)

        # 构建最终内容
        final_content = self._build_final_content(processed_content)

        # 统计信息
        total_tokens = sum(info["estimated_tokens"] for info in selected_files)

        return final_content, {
            "processed_files": len(selected_files),
            "total_tokens": total_tokens,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "files_summarized": self.stats["files_summarized"],
        }

    async def _parallel_file_analysis(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """并行分析文件信息"""

        async def analyze_single_file(file_path: str) -> Optional[Dict[str, Any]]:
            """分析单个文件"""
            try:
                # 在线程池中运行，避免阻塞事件循环
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future = loop.run_in_executor(executor, self._analyze_file_sync, file_path)
                    return await future
            except Exception as e:
                logger.warning(f"分析文件失败 {file_path}: {e}")
                return None

        # 限制并发数，避免过多文件句柄
        semaphore = asyncio.Semaphore(10)

        async def bounded_analyze(file_path: str):
            async with semaphore:
                return await analyze_single_file(file_path)

        # 并行执行
        tasks = [bounded_analyze(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤有效结果
        file_info_list = []
        for result in results:
            if isinstance(result, dict) and result is not None:
                file_info_list.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"文件分析异常: {result}")

        with self._stats_lock:
            self.stats["parallel_reads"] += len(file_info_list)

        return file_info_list

    def _analyze_file_sync(self, file_path: str) -> Optional[Dict[str, Any]]:
        """同步分析文件（在线程池中运行）"""
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return None

            stat = path.stat()
            file_size = stat.st_size

            # 跳过过大的文件
            if file_size > 5 * 1024 * 1024:  # 5MB
                return None

            # 获取文件哈希
            content_hash = self.hash_manager.get_file_hash(file_path)
            if not content_hash:
                return None

            # 估算令牌数（基于文件大小和类型）
            estimated_tokens = self._estimate_tokens_from_file_info(file_path, file_size)

            return {
                "path": file_path,
                "size": file_size,
                "hash": content_hash,
                "estimated_tokens": estimated_tokens,
                "priority": self._calculate_file_priority(file_path),
            }

        except Exception as e:
            logger.warning(f"分析文件失败 {file_path}: {e}")
            return None

    def _estimate_tokens_from_file_info(self, file_path: str, file_size: int) -> int:
        """基于文件信息估算令牌数"""
        file_ext = Path(file_path).suffix.lower()

        # 基于文件类型的令牌率
        token_ratios = {
            ".py": 3.5,
            ".js": 3.2,
            ".ts": 3.2,
            ".jsx": 3.2,
            ".tsx": 3.2,
            ".java": 3.8,
            ".cpp": 3.6,
            ".c": 3.6,
            ".cs": 3.7,
            ".json": 2.5,
            ".yaml": 2.8,
            ".yml": 2.8,
            ".xml": 2.6,
            ".html": 2.4,
            ".css": 2.2,
            ".scss": 2.3,
            ".sass": 2.3,
            ".md": 3.0,
            ".txt": 4.0,
            ".rst": 3.2,
            ".sql": 3.5,
            ".sh": 3.8,
            ".ps1": 3.6,
            ".go": 3.4,
            ".rs": 3.3,
            ".php": 3.1,
            ".rb": 3.6,
        }

        ratio = token_ratios.get(file_ext, 3.0)  # 默认比率
        return int(file_size / ratio)

    def _calculate_file_priority(self, file_path: str) -> int:
        """计算文件优先级（用于排序）"""
        path = Path(file_path)

        # 基础优先级
        priority = 50

        # 根据文件类型调整优先级
        file_ext = path.suffix.lower()
        if file_ext in [".py", ".js", ".ts", ".java", ".cpp"]:
            priority += 20  # 代码文件优先级高
        elif file_ext in [".md", ".txt", ".rst"]:
            priority += 10  # 文档文件中等优先级
        elif file_ext in [".json", ".yaml", ".yml"]:
            priority += 15  # 配置文件较高优先级
        elif file_ext in [".log"]:
            priority -= 10  # 日志文件优先级低

        # 根据文件名调整优先级
        filename = path.name.lower()
        if any(keyword in filename for keyword in ["main", "index", "app", "core"]):
            priority += 15
        elif any(keyword in filename for keyword in ["test", "spec", "example"]):
            priority -= 5
        elif any(keyword in filename for keyword in ["config", "setting"]):
            priority += 10

        # 根据路径深度调整（越深优先级越低）
        depth = len(path.parts)
        priority -= depth * 2

        return priority

    def _select_files_by_budget(self, file_info_list: List[Dict[str, Any]], token_budget: int) -> List[Dict[str, Any]]:
        """根据令牌预算选择文件"""

        # 按优先级排序（高优先级在前）
        sorted_files = sorted(file_info_list, key=lambda x: x["priority"], reverse=True)

        selected_files = []
        total_tokens = 0

        for file_info in sorted_files:
            estimated_tokens = file_info["estimated_tokens"]

            # 为摘要预留空间
            if estimated_tokens > 3000:
                estimated_tokens = min(estimated_tokens // 3, 2000)  # 摘要大约是原文的1/3

            if total_tokens + estimated_tokens <= token_budget:
                selected_files.append(file_info)
                total_tokens += estimated_tokens
            else:
                # 检查是否可以通过摘要方式包含
                summary_tokens = min(estimated_tokens // 4, 1000)
                if total_tokens + summary_tokens <= token_budget:
                    file_info["force_summary"] = True
                    selected_files.append(file_info)
                    total_tokens += summary_tokens

        return selected_files

    async def _parallel_file_processing(self, selected_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """并行处理选定的文件"""

        async def process_single_file(file_info: Dict[str, Any]) -> Dict[str, Any]:
            """处理单个文件"""
            try:
                file_path = file_info["path"]
                content_hash = file_info["hash"]

                # 检查缓存
                cached_content = self.content_cache.get_content(content_hash)
                if cached_content:
                    with self._stats_lock:
                        self.stats["cache_hits"] += 1

                    file_info["content"] = cached_content
                    file_info["from_cache"] = True
                    return file_info

                # 缓存未命中，读取文件
                with self._stats_lock:
                    self.stats["cache_misses"] += 1

                # 在线程池中读取文件
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future = loop.run_in_executor(executor, self._read_and_process_file, file_info)
                    result = await future
                    return result

            except Exception as e:
                logger.warning(f"处理文件失败 {file_info['path']}: {e}")
                file_info["content"] = f"# 文件处理失败: {str(e)}"
                file_info["error"] = True
                return file_info

        # 限制并发数
        semaphore = asyncio.Semaphore(8)

        async def bounded_process(file_info: Dict[str, Any]):
            async with semaphore:
                return await process_single_file(file_info)

        # 并行执行
        tasks = [bounded_process(file_info) for file_info in selected_files]
        processed_files = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        valid_results = []
        for result in processed_files:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"文件处理异常: {result}")

        return valid_results

    def _read_and_process_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """读取和处理文件（在线程池中运行）"""
        try:
            file_path = file_info["path"]
            content_hash = file_info["hash"]

            # 读取文件内容
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()

            # 检查是否需要摘要
            force_summary = file_info.get("force_summary", False)
            estimated_tokens = file_info["estimated_tokens"]

            if force_summary or self.summarizer.should_summarize(file_path, content, estimated_tokens):
                content = self.summarizer.generate_summary(file_path, content)
                file_info["is_summary"] = True
                with self._stats_lock:
                    self.stats["files_summarized"] += 1

            # 缓存内容
            self.content_cache.store_content(content_hash, content)

            file_info["content"] = content
            file_info["from_cache"] = False

            return file_info

        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            file_info["content"] = f"# 文件读取失败: {str(e)}"
            file_info["error"] = True
            return file_info

    def _build_final_content(self, processed_files: List[Dict[str, Any]]) -> str:
        """构建最终的文件内容"""

        if not processed_files:
            return ""

        content_parts = []

        # 添加处理统计
        total_files = len(processed_files)
        cache_hits = sum(1 for f in processed_files if f.get("from_cache", False))
        summarized = sum(1 for f in processed_files if f.get("is_summary", False))

        content_parts.append("# 文件处理报告")
        content_parts.append(f"- 处理文件数: {total_files}")
        content_parts.append(f"- 缓存命中: {cache_hits}")
        content_parts.append(f"- 摘要文件: {summarized}")
        content_parts.append("")

        # 添加每个文件的内容
        for file_info in processed_files:
            file_path = file_info["path"]
            content = file_info["content"]

            # 文件头信息
            header_parts = [f"## 文件: {file_path}"]

            if file_info.get("is_summary"):
                header_parts.append("**(摘要版本)**")

            if file_info.get("from_cache"):
                header_parts.append("**(来自缓存)**")

            if file_info.get("error"):
                header_parts.append("**(处理出错)**")

            content_parts.append(" ".join(header_parts))
            content_parts.append("")
            content_parts.append(content)
            content_parts.append("")
            content_parts.append("---")
            content_parts.append("")

        return "\n".join(content_parts)

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        cache_stats = self.content_cache.get_stats()

        return {
            "processing_stats": self.stats.copy(),
            "cache_stats": cache_stats,
            "hash_cache_size": len(self.hash_manager._hash_cache),
        }

    def cleanup_caches(self):
        """清理缓存"""
        self.hash_manager.cleanup_stale_entries()
        # 内容缓存会自动清理，无需手动调用


# 全局实例
_enhanced_processor = None
_processor_lock = threading.Lock()


def get_enhanced_file_processor() -> EnhancedFileProcessor:
    """获取全局增强文件处理器实例（单例模式）"""
    global _enhanced_processor
    if _enhanced_processor is None:
        with _processor_lock:
            if _enhanced_processor is None:
                _enhanced_processor = EnhancedFileProcessor()
    return _enhanced_processor


# 便捷接口
async def process_files_with_optimization(
    file_paths: List[str], token_budget: int, existing_files: Optional[Set[str]] = None
) -> Tuple[str, Dict[str, Any]]:
    """使用优化后的文件处理器处理文件"""
    processor = get_enhanced_file_processor()
    return await processor.process_files_optimized(file_paths, token_budget, existing_files)


def get_file_processing_stats() -> Dict[str, Any]:
    """获取文件处理统计信息"""
    processor = get_enhanced_file_processor()
    return processor.get_cache_stats()


def cleanup_file_caches():
    """清理文件缓存"""
    processor = get_enhanced_file_processor()
    processor.cleanup_caches()
