"""
记忆存储接口实现

基于文件系统的高性能记忆存储接口，支持：
- 原子操作和事务安全
- 并发访问控制
- 数据压缩和优化
- 备份和恢复
- 索引缓存管理
"""

import gzip
import json
import logging
import shutil
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock, RLock
from typing import Any, Optional, Union
from uuid import uuid4

from .enhanced_memory import MemoryItem

logger = logging.getLogger(__name__)


class StorageException(Exception):
    """存储操作异常"""

    pass


class StorageInterface(ABC):
    """存储接口抽象基类"""

    @abstractmethod
    def save_item(self, item_id: str, data: dict[str, Any]) -> bool:
        """保存单个项目"""
        pass

    @abstractmethod
    def load_item(self, item_id: str) -> Optional[dict[str, Any]]:
        """加载单个项目"""
        pass

    @abstractmethod
    def delete_item(self, item_id: str) -> bool:
        """删除单个项目"""
        pass

    @abstractmethod
    def list_items(self) -> list[str]:
        """列出所有项目ID"""
        pass

    @abstractmethod
    def exists(self, item_id: str) -> bool:
        """检查项目是否存在"""
        pass

    @abstractmethod
    def get_storage_info(self) -> dict[str, Any]:
        """获取存储信息"""
        pass


class FileSystemStorage(StorageInterface):
    """
    文件系统存储实现

    特性：
    - 原子写入操作
    - 文件锁机制
    - 压缩存储（可选）
    - 自动备份
    """

    def __init__(
        self,
        storage_path: Union[str, Path],
        enable_compression: bool = False,
        enable_backup: bool = True,
        max_backup_files: int = 5,
        file_extension: str = ".json",
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.enable_compression = enable_compression
        self.enable_backup = enable_backup
        self.max_backup_files = max_backup_files
        self.file_extension = file_extension if not enable_compression else f"{file_extension}.gz"

        # 并发控制
        self._locks: dict[str, Lock] = {}
        self._locks_lock = RLock()

        # 缓存
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_lock = RLock()
        self._cache_enabled = True
        self._cache_ttl = 300  # 5分钟缓存
        self._cache_timestamps: dict[str, float] = {}

        logger.debug(f"文件系统存储初始化: {self.storage_path}")

    def _get_item_lock(self, item_id: str) -> Lock:
        """获取项目特定的锁"""
        with self._locks_lock:
            if item_id not in self._locks:
                self._locks[item_id] = Lock()
            return self._locks[item_id]

    def _get_file_path(self, item_id: str) -> Path:
        """获取项目文件路径"""
        return self.storage_path / f"{item_id}{self.file_extension}"

    def _get_backup_path(self, item_id: str, backup_num: int = 1) -> Path:
        """获取备份文件路径"""
        backup_dir = self.storage_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        return backup_dir / f"{item_id}.backup.{backup_num}{self.file_extension}"

    def _write_file(self, file_path: Path, data: dict[str, Any]) -> bool:
        """原子写入文件"""
        # 创建临时文件
        temp_file = file_path.with_suffix(f".tmp.{uuid4().hex[:8]}")

        try:
            if self.enable_compression:
                with gzip.open(temp_file, "wt", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            # 原子移动
            temp_file.replace(file_path)
            return True

        except Exception as e:
            logger.error(f"写入文件 {file_path} 失败: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return False

    def _read_file(self, file_path: Path) -> Optional[dict[str, Any]]:
        """读取文件"""
        if not file_path.exists():
            return None

        try:
            if self.enable_compression:
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    return json.load(f)
            else:
                with open(file_path, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {e}")
            return None

    def _create_backup(self, item_id: str) -> bool:
        """创建备份"""
        if not self.enable_backup:
            return True

        source_file = self._get_file_path(item_id)
        if not source_file.exists():
            return True

        try:
            # 轮转备份文件
            for i in range(self.max_backup_files - 1, 0, -1):
                old_backup = self._get_backup_path(item_id, i)
                new_backup = self._get_backup_path(item_id, i + 1)

                if old_backup.exists():
                    if new_backup.exists():
                        new_backup.unlink()
                    old_backup.rename(new_backup)

            # 创建新备份
            current_backup = self._get_backup_path(item_id, 1)
            shutil.copy2(source_file, current_backup)
            return True

        except Exception as e:
            logger.warning(f"创建备份失败 {item_id}: {e}")
            return False

    def _update_cache(self, item_id: str, data: dict[str, Any]):
        """更新缓存"""
        if not self._cache_enabled:
            return

        with self._cache_lock:
            self._cache[item_id] = data.copy()
            self._cache_timestamps[item_id] = time.time()

    def _get_from_cache(self, item_id: str) -> Optional[dict[str, Any]]:
        """从缓存获取"""
        if not self._cache_enabled:
            return None

        with self._cache_lock:
            if item_id not in self._cache:
                return None

            # 检查TTL
            cache_time = self._cache_timestamps.get(item_id, 0)
            if time.time() - cache_time > self._cache_ttl:
                del self._cache[item_id]
                del self._cache_timestamps[item_id]
                return None

            return self._cache[item_id].copy()

    def _invalidate_cache(self, item_id: str):
        """使缓存失效"""
        with self._cache_lock:
            self._cache.pop(item_id, None)
            self._cache_timestamps.pop(item_id, None)

    def save_item(self, item_id: str, data: dict[str, Any]) -> bool:
        """保存单个项目"""
        lock = self._get_item_lock(item_id)

        with lock:
            try:
                # 创建备份
                self._create_backup(item_id)

                # 保存文件
                file_path = self._get_file_path(item_id)
                success = self._write_file(file_path, data)

                if success:
                    # 更新缓存
                    self._update_cache(item_id, data)
                    logger.debug(f"保存项目 {item_id} 成功")
                else:
                    logger.error(f"保存项目 {item_id} 失败")

                return success

            except Exception as e:
                logger.error(f"保存项目 {item_id} 异常: {e}")
                return False

    def load_item(self, item_id: str) -> Optional[dict[str, Any]]:
        """加载单个项目"""
        # 先尝试缓存
        cached_data = self._get_from_cache(item_id)
        if cached_data is not None:
            return cached_data

        lock = self._get_item_lock(item_id)

        with lock:
            try:
                file_path = self._get_file_path(item_id)
                data = self._read_file(file_path)

                if data is not None:
                    # 更新缓存
                    self._update_cache(item_id, data)
                    logger.debug(f"加载项目 {item_id} 成功")
                else:
                    logger.debug(f"项目 {item_id} 不存在")

                return data

            except Exception as e:
                logger.error(f"加载项目 {item_id} 异常: {e}")
                return None

    def delete_item(self, item_id: str) -> bool:
        """删除单个项目"""
        lock = self._get_item_lock(item_id)

        with lock:
            try:
                file_path = self._get_file_path(item_id)

                if file_path.exists():
                    # 创建最后备份
                    self._create_backup(item_id)

                    # 删除文件
                    file_path.unlink()

                    # 清除缓存
                    self._invalidate_cache(item_id)

                    logger.debug(f"删除项目 {item_id} 成功")
                    return True
                else:
                    logger.debug(f"项目 {item_id} 不存在，无需删除")
                    return True

            except Exception as e:
                logger.error(f"删除项目 {item_id} 异常: {e}")
                return False

    def exists(self, item_id: str) -> bool:
        """检查项目是否存在"""
        # 先检查缓存
        if self._get_from_cache(item_id) is not None:
            return True

        file_path = self._get_file_path(item_id)
        return file_path.exists()

    def list_items(self) -> list[str]:
        """列出所有项目ID"""
        try:
            items = []
            pattern = f"*{self.file_extension}"

            for file_path in self.storage_path.glob(pattern):
                if file_path.is_file():
                    # 移除扩展名获取ID
                    item_id = file_path.name
                    if self.enable_compression:
                        item_id = item_id.replace(".json.gz", "")
                    else:
                        item_id = item_id.replace(".json", "")
                    items.append(item_id)

            return sorted(items)

        except Exception as e:
            logger.error(f"列出项目失败: {e}")
            return []

    def get_storage_info(self) -> dict[str, Any]:
        """获取存储信息"""
        try:
            total_size = 0
            file_count = 0

            for file_path in self.storage_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1

            return {
                "storage_path": str(self.storage_path),
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "compression_enabled": self.enable_compression,
                "backup_enabled": self.enable_backup,
                "cache_items": len(self._cache),
                "file_extension": self.file_extension,
            }

        except Exception as e:
            logger.error(f"获取存储信息失败: {e}")
            return {"storage_path": str(self.storage_path), "error": str(e)}

    @contextmanager
    def batch_operations(self) -> Iterator[None]:
        """批量操作上下文管理器"""
        old_cache_enabled = self._cache_enabled
        self._cache_enabled = False  # 批量操作时禁用缓存

        try:
            yield
        finally:
            self._cache_enabled = old_cache_enabled
            # 清除缓存强制重新加载
            with self._cache_lock:
                self._cache.clear()
                self._cache_timestamps.clear()

    def cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_items = []

        with self._cache_lock:
            for item_id, cache_time in self._cache_timestamps.items():
                if current_time - cache_time > self._cache_ttl:
                    expired_items.append(item_id)

            for item_id in expired_items:
                del self._cache[item_id]
                del self._cache_timestamps[item_id]

        if expired_items:
            logger.debug(f"清理了 {len(expired_items)} 个过期缓存项")

    def restore_from_backup(self, item_id: str, backup_num: int = 1) -> bool:
        """从备份恢复"""
        if not self.enable_backup:
            logger.warning("备份功能未启用")
            return False

        backup_path = self._get_backup_path(item_id, backup_num)
        if not backup_path.exists():
            logger.error(f"备份文件不存在: {backup_path}")
            return False

        target_path = self._get_file_path(item_id)
        lock = self._get_item_lock(item_id)

        with lock:
            try:
                shutil.copy2(backup_path, target_path)
                self._invalidate_cache(item_id)
                logger.info(f"从备份 {backup_num} 恢复项目 {item_id}")
                return True
            except Exception as e:
                logger.error(f"恢复备份失败: {e}")
                return False


class MemoryStorageManager:
    """
    记忆存储管理器

    统一管理三层记忆的存储接口，提供：
    - 分层存储管理
    - 批量操作支持
    - 存储优化
    - 统计和监控
    """

    def __init__(self, base_storage_path: Union[str, Path]):
        self.base_path = Path(base_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 为每层创建存储接口
        self.storages = {
            "global": FileSystemStorage(
                self.base_path / "global",
                enable_compression=True,  # 全局层启用压缩
                enable_backup=True,
                max_backup_files=10,
            ),
            "project": FileSystemStorage(
                self.base_path / "project",
                enable_compression=False,  # 项目层不压缩以提高性能
                enable_backup=True,
                max_backup_files=5,
            ),
            "session": FileSystemStorage(
                self.base_path / "session",
                enable_compression=False,  # 会话层不压缩和备份
                enable_backup=False,
                max_backup_files=0,
            ),
        }

        logger.info(f"记忆存储管理器初始化: {self.base_path}")

    def get_storage(self, layer: str) -> Optional[StorageInterface]:
        """获取指定层的存储接口"""
        return self.storages.get(layer)

    def save_memory_item(self, layer: str, item: MemoryItem) -> bool:
        """保存记忆项"""
        storage = self.get_storage(layer)
        if storage is None:
            logger.error(f"无效的存储层: {layer}")
            return False

        try:
            data = item.to_dict()
            return storage.save_item(item.id, data)
        except Exception as e:
            logger.error(f"保存记忆项失败: {e}")
            return False

    def load_memory_item(self, layer: str, item_id: str) -> Optional[MemoryItem]:
        """加载记忆项"""
        storage = self.get_storage(layer)
        if storage is None:
            logger.error(f"无效的存储层: {layer}")
            return None

        try:
            data = storage.load_item(item_id)
            if data is None:
                return None

            return MemoryItem.from_dict(data)
        except Exception as e:
            logger.error(f"加载记忆项失败: {e}")
            return None

    def delete_memory_item(self, layer: str, item_id: str) -> bool:
        """删除记忆项"""
        storage = self.get_storage(layer)
        if storage is None:
            logger.error(f"无效的存储层: {layer}")
            return False

        return storage.delete_item(item_id)

    def list_memory_items(self, layer: str) -> list[str]:
        """列出记忆项ID"""
        storage = self.get_storage(layer)
        if storage is None:
            logger.error(f"无效的存储层: {layer}")
            return []

        return storage.list_items()

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """获取综合统计信息"""
        stats = {"layers": {}, "total_storage": {"files": 0, "size_bytes": 0, "size_mb": 0.0}}

        for layer_name, storage in self.storages.items():
            layer_info = storage.get_storage_info()
            stats["layers"][layer_name] = layer_info

            # 累加总计
            stats["total_storage"]["files"] += layer_info.get("total_files", 0)
            stats["total_storage"]["size_bytes"] += layer_info.get("total_size_bytes", 0)

        stats["total_storage"]["size_mb"] = round(stats["total_storage"]["size_bytes"] / (1024 * 1024), 2)

        return stats

    def cleanup_all_caches(self):
        """清理所有层的缓存"""
        for storage in self.storages.values():
            if hasattr(storage, "cleanup_cache"):
                storage.cleanup_cache()
        logger.debug("清理了所有层的缓存")

    @contextmanager
    def batch_operations(self, layers: Optional[list[str]] = None) -> Iterator[None]:
        """批量操作上下文管理器"""
        if layers is None:
            layers = list(self.storages.keys())

        # 获取批量操作上下文
        contexts = []
        for layer in layers:
            storage = self.storages.get(layer)
            if storage and hasattr(storage, "batch_operations"):
                contexts.append(storage.batch_operations())

        # 进入所有上下文
        for ctx in contexts:
            ctx.__enter__()

        try:
            yield
        finally:
            # 退出所有上下文
            for ctx in reversed(contexts):
                ctx.__exit__(None, None, None)
