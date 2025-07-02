"""
工作流状态持久化管理器

为工作流系统提供持久化存储功能，解决状态在进程重启后丢失的问题。
支持多种存储后端：SQLite、Redis、文件系统等。
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.workflow_memory_fix import ThreadSafeWorkflowState

logger = logging.getLogger(__name__)


class PersistentStateBackend(ABC):
    """持久化状态后端抽象基类"""

    @abstractmethod
    async def save_state(self, workflow_id: str, state: Dict[str, Any]) -> bool:
        """保存工作流状态"""
        pass

    @abstractmethod
    async def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """加载工作流状态"""
        pass

    @abstractmethod
    async def delete_state(self, workflow_id: str) -> bool:
        """删除工作流状态"""
        pass

    @abstractmethod
    async def list_workflows(self) -> List[str]:
        """列出所有工作流ID"""
        pass

    @abstractmethod
    async def cleanup_expired(self, expire_before: float) -> int:
        """清理过期状态，返回清理数量"""
        pass


class SQLiteStateBackend(PersistentStateBackend):
    """SQLite 持久化后端"""

    def __init__(self, db_path: str = ".zen_memory/workflow_states.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_states (
                    workflow_id TEXT PRIMARY KEY,
                    state_data TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    access_count INTEGER DEFAULT 0
                )
            """)

            # 创建索引以优化查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_updated_at 
                ON workflow_states(updated_at)
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        try:
            # 启用 WAL 模式以支持并发读写
            conn.execute("PRAGMA journal_mode=WAL")
            # 设置同步模式为 NORMAL 以平衡性能和安全性
            conn.execute("PRAGMA synchronous=NORMAL")
            yield conn
        finally:
            conn.close()

    async def save_state(self, workflow_id: str, state: Dict[str, Any]) -> bool:
        """保存工作流状态"""
        try:
            state_json = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
            current_time = time.time()

            with self._lock:
                with self._get_connection() as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO workflow_states 
                        (workflow_id, state_data, created_at, updated_at, access_count)
                        VALUES (?, ?, 
                               COALESCE((SELECT created_at FROM workflow_states WHERE workflow_id = ?), ?),
                               ?,
                               COALESCE((SELECT access_count FROM workflow_states WHERE workflow_id = ?), 0) + 1)
                    """,
                        (workflow_id, state_json, workflow_id, current_time, current_time, workflow_id),
                    )
                    conn.commit()

            logger.debug(f"已保存工作流状态: {workflow_id}")
            return True

        except Exception as e:
            logger.error(f"保存工作流状态失败 {workflow_id}: {e}")
            return False

    async def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """加载工作流状态"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        """
                        SELECT state_data FROM workflow_states 
                        WHERE workflow_id = ?
                    """,
                        (workflow_id,),
                    )
                    row = cursor.fetchone()

                    if row:
                        # 更新访问计数
                        conn.execute(
                            """
                            UPDATE workflow_states 
                            SET access_count = access_count + 1, updated_at = ?
                            WHERE workflow_id = ?
                        """,
                            (time.time(), workflow_id),
                        )
                        conn.commit()

                        state = json.loads(row[0])
                        logger.debug(f"已加载工作流状态: {workflow_id}")
                        return state

            return None

        except Exception as e:
            logger.error(f"加载工作流状态失败 {workflow_id}: {e}")
            return None

    async def delete_state(self, workflow_id: str) -> bool:
        """删除工作流状态"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        """
                        DELETE FROM workflow_states WHERE workflow_id = ?
                    """,
                        (workflow_id,),
                    )
                    conn.commit()

                    deleted = cursor.rowcount > 0
                    if deleted:
                        logger.debug(f"已删除工作流状态: {workflow_id}")
                    return deleted

        except Exception as e:
            logger.error(f"删除工作流状态失败 {workflow_id}: {e}")
            return False

    async def list_workflows(self) -> List[str]:
        """列出所有工作流ID"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT workflow_id FROM workflow_states 
                        ORDER BY updated_at DESC
                    """)
                    return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"列出工作流失败: {e}")
            return []

    async def cleanup_expired(self, expire_before: float) -> int:
        """清理过期状态"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        """
                        DELETE FROM workflow_states 
                        WHERE updated_at < ?
                    """,
                        (expire_before,),
                    )
                    conn.commit()

                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        logger.info(f"清理了 {deleted_count} 个过期工作流状态")
                    return deleted_count

        except Exception as e:
            logger.error(f"清理过期状态失败: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_workflows,
                            AVG(LENGTH(state_data)) as avg_state_size,
                            MAX(LENGTH(state_data)) as max_state_size,
                            MIN(updated_at) as oldest_update,
                            MAX(updated_at) as newest_update
                        FROM workflow_states
                    """)
                    row = cursor.fetchone()

                    if row:
                        return {
                            "total_workflows": row[0],
                            "avg_state_size_bytes": int(row[1] or 0),
                            "max_state_size_bytes": int(row[2] or 0),
                            "oldest_update": row[3],
                            "newest_update": row[4],
                        }

            return {}

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}


class FileSystemStateBackend(PersistentStateBackend):
    """文件系统持久化后端（备用方案）"""

    def __init__(self, storage_dir: str = ".zen_memory/workflow_states"):
        self.storage_path = Path(storage_dir)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _get_state_file(self, workflow_id: str) -> Path:
        """获取状态文件路径"""
        # 使用安全的文件名编码
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in workflow_id)
        return self.storage_path / f"{safe_id}.json"

    async def save_state(self, workflow_id: str, state: Dict[str, Any]) -> bool:
        """保存工作流状态到文件"""
        try:
            file_path = self._get_state_file(workflow_id)

            # 添加元数据
            state_with_meta = {
                "workflow_id": workflow_id,
                "state": state,
                "created_at": time.time(),
                "updated_at": time.time(),
            }

            # 如果文件已存在，保留创建时间
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        existing = json.load(f)
                        state_with_meta["created_at"] = existing.get("created_at", time.time())
                except:
                    pass  # 如果读取失败，使用新的创建时间

            with self._lock:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(state_with_meta, f, ensure_ascii=False, indent=2)

            logger.debug(f"已保存工作流状态到文件: {file_path}")
            return True

        except Exception as e:
            logger.error(f"保存工作流状态到文件失败 {workflow_id}: {e}")
            return False

    async def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """从文件加载工作流状态"""
        try:
            file_path = self._get_state_file(workflow_id)

            if not file_path.exists():
                return None

            with self._lock:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                    # 更新访问时间
                    data["updated_at"] = time.time()
                    with open(file_path, "w", encoding="utf-8") as f_write:
                        json.dump(data, f_write, ensure_ascii=False, indent=2)

                    logger.debug(f"已从文件加载工作流状态: {file_path}")
                    return data.get("state")

        except Exception as e:
            logger.error(f"从文件加载工作流状态失败 {workflow_id}: {e}")
            return None

    async def delete_state(self, workflow_id: str) -> bool:
        """删除工作流状态文件"""
        try:
            file_path = self._get_state_file(workflow_id)

            if file_path.exists():
                with self._lock:
                    file_path.unlink()
                logger.debug(f"已删除工作流状态文件: {file_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"删除工作流状态文件失败 {workflow_id}: {e}")
            return False

    async def list_workflows(self) -> List[str]:
        """列出所有工作流ID"""
        try:
            workflow_files = []

            with self._lock:
                for file_path in self.storage_path.glob("*.json"):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            data = json.load(f)
                            workflow_id = data.get("workflow_id")
                            if workflow_id:
                                workflow_files.append((workflow_id, data.get("updated_at", 0)))
                    except:
                        continue  # 跳过损坏的文件

            # 按更新时间排序
            workflow_files.sort(key=lambda x: x[1], reverse=True)
            return [wf[0] for wf in workflow_files]

        except Exception as e:
            logger.error(f"列出工作流文件失败: {e}")
            return []

    async def cleanup_expired(self, expire_before: float) -> int:
        """清理过期状态文件"""
        try:
            deleted_count = 0

            with self._lock:
                for file_path in self.storage_path.glob("*.json"):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            data = json.load(f)
                            updated_at = data.get("updated_at", 0)

                            if updated_at < expire_before:
                                file_path.unlink()
                                deleted_count += 1
                                logger.debug(f"清理过期状态文件: {file_path}")
                    except:
                        # 如果文件损坏，也删除它
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except:
                            pass

            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个过期工作流状态文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理过期状态文件失败: {e}")
            return 0


class PersistentWorkflowStateManager:
    """持久化工作流状态管理器"""

    def __init__(self, backend: Optional[PersistentStateBackend] = None):
        # 优先使用 SQLite，失败时回退到文件系统
        if backend is None:
            try:
                self.backend = SQLiteStateBackend()
                logger.info("使用 SQLite 作为持久化后端")
            except Exception as e:
                logger.warning(f"SQLite 后端初始化失败，回退到文件系统: {e}")
                self.backend = FileSystemStateBackend()
                logger.info("使用文件系统作为持久化后端")
        else:
            self.backend = backend

        # 内存缓存层（继承现有的线程安全机制）
        self.memory_cache = ThreadSafeWorkflowState()
        self._lock = threading.Lock()

        # 启动后台同步任务
        self._start_sync_task()

    def _start_sync_task(self):
        """启动后台同步任务"""

        async def sync_worker():
            while True:
                try:
                    await self._sync_to_persistent()
                    await asyncio.sleep(60)  # 每分钟同步一次
                except Exception as e:
                    logger.error(f"后台同步任务出错: {e}")
                    await asyncio.sleep(5)  # 出错时短暂等待

        def run_sync_worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(sync_worker())

        sync_thread = threading.Thread(target=run_sync_worker, daemon=True)
        sync_thread.start()
        logger.info("持久化同步任务已启动")

    async def _sync_to_persistent(self):
        """同步内存状态到持久化存储"""
        try:
            # 获取内存中的所有状态
            memory_stats = self.memory_cache.get_stats()
            if memory_stats["total_workflows"] == 0:
                return

            # 这里我们假设内存缓存中的状态都需要持久化
            # 在实际实现中，可以添加"脏标记"来优化
            with self._lock:
                for workflow_id in list(self.memory_cache._states.keys()):
                    state = self.memory_cache.get_state(workflow_id)
                    if state:
                        await self.backend.save_state(workflow_id, state)

        except Exception as e:
            logger.error(f"同步到持久化存储失败: {e}")

    async def save_state(self, workflow_id: str, state: Dict[str, Any]) -> bool:
        """保存工作流状态（双写：内存+持久化）"""
        try:
            # 先写内存（快速访问）
            memory_success = self.memory_cache.update_state(workflow_id, state)

            # 异步写持久化存储
            persistent_success = await self.backend.save_state(workflow_id, state)

            if not memory_success:
                logger.warning(f"内存状态更新失败: {workflow_id}")

            if not persistent_success:
                logger.warning(f"持久化状态保存失败: {workflow_id}")

            # 只要有一个成功就认为操作成功
            return memory_success or persistent_success

        except Exception as e:
            logger.error(f"保存工作流状态失败 {workflow_id}: {e}")
            return False

    async def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """加载工作流状态（优先内存，回退到持久化）"""
        try:
            # 先尝试从内存加载
            state = self.memory_cache.get_state(workflow_id)
            if state is not None:
                return state

            # 内存中没有，从持久化存储加载
            state = await self.backend.load_state(workflow_id)
            if state is not None:
                # 加载到内存缓存中
                self.memory_cache.update_state(workflow_id, state)
                logger.debug(f"从持久化存储恢复状态到内存: {workflow_id}")

            return state

        except Exception as e:
            logger.error(f"加载工作流状态失败 {workflow_id}: {e}")
            return None

    async def delete_state(self, workflow_id: str) -> bool:
        """删除工作流状态（双删：内存+持久化）"""
        try:
            memory_success = self.memory_cache.remove_state(workflow_id)
            persistent_success = await self.backend.delete_state(workflow_id)

            return memory_success or persistent_success

        except Exception as e:
            logger.error(f"删除工作流状态失败 {workflow_id}: {e}")
            return False

    async def list_workflows(self) -> List[str]:
        """列出所有工作流ID（合并内存和持久化）"""
        try:
            # 获取内存中的工作流
            memory_workflows = set(self.memory_cache._states.keys())

            # 获取持久化存储中的工作流
            persistent_workflows = set(await self.backend.list_workflows())

            # 合并并去重
            all_workflows = memory_workflows | persistent_workflows
            return list(all_workflows)

        except Exception as e:
            logger.error(f"列出工作流失败: {e}")
            return []

    async def cleanup_expired(self, expire_hours: int = 24) -> Dict[str, int]:
        """清理过期状态"""
        try:
            expire_before = time.time() - (expire_hours * 3600)

            # 清理内存中的过期状态
            self.memory_cache._cleanup_old_states()

            # 清理持久化存储中的过期状态
            persistent_deleted = await self.backend.cleanup_expired(expire_before)

            return {"persistent_deleted": persistent_deleted, "expire_before_timestamp": expire_before}

        except Exception as e:
            logger.error(f"清理过期状态失败: {e}")
            return {"persistent_deleted": 0, "expire_before_timestamp": 0}

    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合统计信息"""
        try:
            # 内存统计
            memory_stats = self.memory_cache.get_stats()

            # 持久化统计
            if hasattr(self.backend, "get_stats"):
                persistent_stats = await self.backend.get_stats()
            else:
                persistent_stats = {}

            return {
                "memory_stats": memory_stats,
                "persistent_stats": persistent_stats,
                "backend_type": type(self.backend).__name__,
                "total_unique_workflows": len(await self.list_workflows()),
            }

        except Exception as e:
            logger.error(f"获取综合统计失败: {e}")
            return {}


# 全局实例
_persistent_manager = None
_persistent_lock = threading.Lock()


def get_persistent_workflow_manager() -> PersistentWorkflowStateManager:
    """获取全局持久化工作流管理器实例（单例模式）"""
    global _persistent_manager
    if _persistent_manager is None:
        with _persistent_lock:
            if _persistent_manager is None:
                _persistent_manager = PersistentWorkflowStateManager()
    return _persistent_manager


# 便捷的异步接口
async def save_workflow_state(workflow_id: str, state: Dict[str, Any]) -> bool:
    """保存工作流状态到持久化存储"""
    manager = get_persistent_workflow_manager()
    return await manager.save_state(workflow_id, state)


async def load_workflow_state(workflow_id: str) -> Optional[Dict[str, Any]]:
    """从持久化存储加载工作流状态"""
    manager = get_persistent_workflow_manager()
    return await manager.load_state(workflow_id)


async def delete_workflow_state(workflow_id: str) -> bool:
    """从持久化存储删除工作流状态"""
    manager = get_persistent_workflow_manager()
    return await manager.delete_state(workflow_id)


async def list_persisted_workflows() -> List[str]:
    """列出所有持久化的工作流"""
    manager = get_persistent_workflow_manager()
    return await manager.list_workflows()


async def cleanup_expired_workflows(expire_hours: int = 24) -> Dict[str, int]:
    """清理过期的工作流状态"""
    manager = get_persistent_workflow_manager()
    return await manager.cleanup_expired(expire_hours)
