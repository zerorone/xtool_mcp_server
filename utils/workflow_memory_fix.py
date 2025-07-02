"""
工作流内存管理修复模块

解决 P0 级别的内存和并发问题：
1. 限制工作流步骤数
2. 实现滑动窗口防止无限累积
3. 添加线程安全保护
4. 优化内存使用
"""

import logging
import threading
import time
from collections import deque
from typing import Any, Optional

logger = logging.getLogger(__name__)


# P0 修复配置
class WorkflowLimits:
    """工作流限制配置"""

    MAX_WORKFLOW_STEPS = 50  # 最大步骤数
    MAX_FINDINGS_SIZE = 50  # 最大发现数量
    MAX_FILE_REFERENCES = 500  # 最大文件引用数
    MAX_CONTENT_LENGTH = 100_000  # 最大内容长度（字符）
    MAX_MEMORY_MB = 500  # 最大内存使用（MB）
    CLEANUP_INTERVAL = 300  # 清理间隔（秒）


class ThreadSafeWorkflowState:
    """线程安全的工作流状态管理器"""

    def __init__(self):
        self._lock = threading.RLock()  # 可重入锁
        self._states = {}  # 存储所有工作流状态
        self._access_times = {}  # 记录访问时间，用于清理
        self._cleanup_task = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """启动后台清理任务"""

        def cleanup_worker():
            while True:
                try:
                    self._cleanup_old_states()
                    time.sleep(WorkflowLimits.CLEANUP_INTERVAL)
                except Exception as e:
                    logger.error(f"清理任务出错: {e}")

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def get_state(self, workflow_id: str) -> Optional[dict[str, Any]]:
        """线程安全地获取工作流状态"""
        with self._lock:
            self._access_times[workflow_id] = time.time()
            return self._states.get(workflow_id)

    def update_state(self, workflow_id: str, state: dict[str, Any]) -> bool:
        """线程安全地更新工作流状态"""
        with self._lock:
            try:
                # 检查状态大小
                if not self._check_state_limits(state):
                    logger.warning(f"工作流 {workflow_id} 状态超出限制")
                    return False

                self._states[workflow_id] = state.copy()
                self._access_times[workflow_id] = time.time()
                return True
            except Exception as e:
                logger.error(f"更新状态失败: {e}")
                return False

    def remove_state(self, workflow_id: str) -> bool:
        """线程安全地移除工作流状态"""
        with self._lock:
            if workflow_id in self._states:
                del self._states[workflow_id]
                self._access_times.pop(workflow_id, None)
                return True
            return False

    def _check_state_limits(self, state: dict[str, Any]) -> bool:
        """检查状态是否超出限制"""
        # 检查步骤数
        step_count = state.get("step_number", 0)
        if step_count > WorkflowLimits.MAX_WORKFLOW_STEPS:
            return False

        # 检查findings大小
        findings = state.get("findings", [])
        if isinstance(findings, list) and len(findings) > WorkflowLimits.MAX_FINDINGS_SIZE:
            return False

        # 检查文件引用数量
        files = state.get("files", [])
        if isinstance(files, list) and len(files) > WorkflowLimits.MAX_FILE_REFERENCES:
            return False

        return True

    def _cleanup_old_states(self):
        """清理旧的工作流状态"""
        current_time = time.time()
        cutoff_time = current_time - (24 * 3600)  # 24小时前

        with self._lock:
            to_remove = []
            for workflow_id, access_time in self._access_times.items():
                if access_time < cutoff_time:
                    to_remove.append(workflow_id)

            for workflow_id in to_remove:
                self.remove_state(workflow_id)
                logger.info(f"清理过期工作流状态: {workflow_id}")

    def get_stats(self) -> dict[str, Any]:
        """获取状态统计信息"""
        with self._lock:
            return {
                "total_workflows": len(self._states),
                "memory_usage_estimate": sum(len(str(state)) for state in self._states.values()),
                "oldest_access": min(self._access_times.values()) if self._access_times else None,
                "newest_access": max(self._access_times.values()) if self._access_times else None,
            }


class SlidingWindowBuffer:
    """滑动窗口缓冲器，防止无限累积"""

    def __init__(self, max_size: int = WorkflowLimits.MAX_FINDINGS_SIZE):
        self.max_size = max_size
        self._buffer = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def append(self, item: Any) -> None:
        """添加项目到缓冲器"""
        with self._lock:
            self._buffer.append(item)

    def extend(self, items: list[Any]) -> None:
        """批量添加项目"""
        with self._lock:
            self._buffer.extend(items)

    def get_all(self) -> list[Any]:
        """获取所有项目"""
        with self._lock:
            return list(self._buffer)

    def get_recent(self, count: int) -> list[Any]:
        """获取最近的项目"""
        with self._lock:
            if count >= len(self._buffer):
                return list(self._buffer)
            return list(self._buffer)[-count:]

    def clear(self) -> None:
        """清空缓冲器"""
        with self._lock:
            self._buffer.clear()

    def size(self) -> int:
        """获取当前大小"""
        return len(self._buffer)


class WorkflowResourceMonitor:
    """工作流资源监控器"""

    def __init__(self):
        self._memory_usage = {}
        self._lock = threading.Lock()

    def track_memory(self, workflow_id: str, size_bytes: int) -> None:
        """跟踪内存使用"""
        with self._lock:
            self._memory_usage[workflow_id] = size_bytes

    def check_memory_limit(self, workflow_id: str) -> bool:
        """检查内存限制"""
        with self._lock:
            usage_mb = self._memory_usage.get(workflow_id, 0) / (1024 * 1024)
            return usage_mb <= WorkflowLimits.MAX_MEMORY_MB

    def get_memory_stats(self) -> dict[str, Any]:
        """获取内存统计"""
        with self._lock:
            total_bytes = sum(self._memory_usage.values())
            return {
                "total_workflows": len(self._memory_usage),
                "total_memory_mb": total_bytes / (1024 * 1024),
                "average_memory_mb": (total_bytes / len(self._memory_usage)) / (1024 * 1024)
                if self._memory_usage
                else 0,
                "max_memory_mb": max(self._memory_usage.values()) / (1024 * 1024) if self._memory_usage else 0,
            }


class ConcurrentWorkflowManager:
    """并发工作流管理器（支持持久化）"""

    def __init__(self):
        self.state_manager = ThreadSafeWorkflowState()
        self.resource_monitor = WorkflowResourceMonitor()
        self._active_workflows = set()
        self._lock = threading.Lock()
        # 延迟初始化持久化管理器，避免循环导入
        self._persistent_manager = None

    def _get_persistent_manager(self):
        """延迟获取持久化管理器"""
        if self._persistent_manager is None:
            try:
                from utils.persistent_workflow_state import get_persistent_workflow_manager

                self._persistent_manager = get_persistent_workflow_manager()
                logger.info("持久化状态管理器已初始化")
            except Exception as e:
                logger.warning(f"持久化管理器初始化失败: {e}")
                self._persistent_manager = None
        return self._persistent_manager

    async def start_workflow(self, workflow_id: str, initial_state: dict[str, Any]) -> bool:
        """启动工作流"""
        with self._lock:
            if workflow_id in self._active_workflows:
                logger.warning(f"工作流 {workflow_id} 已经在运行")
                return False

            # 检查资源限制
            if not self._check_resource_limits(initial_state):
                logger.error(f"工作流 {workflow_id} 超出资源限制")
                return False

            self._active_workflows.add(workflow_id)

        # 更新内存状态
        memory_success = self.state_manager.update_state(workflow_id, initial_state)

        # 尝试持久化保存
        persistent_success = True
        persistent_manager = self._get_persistent_manager()
        if persistent_manager:
            try:
                persistent_success = await persistent_manager.save_state(workflow_id, initial_state)
            except Exception as e:
                logger.warning(f"持久化保存失败: {e}")
                persistent_success = False

        # 如果内存更新失败，清理活跃工作流列表
        if not memory_success:
            with self._lock:
                self._active_workflows.discard(workflow_id)

        # 只要内存或持久化有一个成功，就认为操作成功
        return memory_success or persistent_success

    async def update_workflow(self, workflow_id: str, state_update: dict[str, Any]) -> bool:
        """更新工作流"""
        # 先尝试从内存获取状态
        current_state = self.state_manager.get_state(workflow_id)

        # 如果内存中没有，尝试从持久化存储恢复
        if not current_state:
            persistent_manager = self._get_persistent_manager()
            if persistent_manager:
                try:
                    current_state = await persistent_manager.load_state(workflow_id)
                    if current_state:
                        # 恢复到内存中
                        self.state_manager.update_state(workflow_id, current_state)
                        logger.info(f"从持久化存储恢复工作流状态: {workflow_id}")
                except Exception as e:
                    logger.warning(f"从持久化存储恢复状态失败: {e}")

        if not current_state:
            logger.error(f"工作流 {workflow_id} 不存在于内存和持久化存储中")
            return False

        # 合并状态
        merged_state = {**current_state, **state_update}

        # 检查限制
        if not self._check_resource_limits(merged_state):
            logger.warning(f"工作流 {workflow_id} 状态更新超出限制")
            return False

        # 更新内存状态
        memory_success = self.state_manager.update_state(workflow_id, merged_state)

        # 尝试持久化保存
        persistent_success = True
        persistent_manager = self._get_persistent_manager()
        if persistent_manager:
            try:
                persistent_success = await persistent_manager.save_state(workflow_id, merged_state)
            except Exception as e:
                logger.warning(f"持久化更新失败: {e}")
                persistent_success = False

        return memory_success or persistent_success

    async def finish_workflow(self, workflow_id: str) -> bool:
        """完成工作流"""
        with self._lock:
            self._active_workflows.discard(workflow_id)

        # 获取最终状态并保存到持久化存储
        final_state = self.state_manager.get_state(workflow_id)
        if final_state:
            # 标记工作流为已完成
            final_state["status"] = "completed"
            final_state["completed_at"] = time.time()

            # 持久化最终状态
            persistent_manager = self._get_persistent_manager()
            if persistent_manager:
                try:
                    await persistent_manager.save_state(workflow_id, final_state)
                    logger.info(f"工作流最终状态已持久化: {workflow_id}")
                except Exception as e:
                    logger.warning(f"持久化最终状态失败: {e}")

        # 保留状态一段时间用于查询，由清理任务处理
        return True

    def _check_resource_limits(self, state: dict[str, Any]) -> bool:
        """检查资源限制"""
        # 检查步骤数
        step_number = state.get("step_number", 0)
        if step_number > WorkflowLimits.MAX_WORKFLOW_STEPS:
            return False

        # 检查内容长度
        content = str(state)
        if len(content) > WorkflowLimits.MAX_CONTENT_LENGTH:
            return False

        return True

    def get_active_workflows(self) -> list[str]:
        """获取活跃的工作流列表"""
        with self._lock:
            return list(self._active_workflows)

    def get_global_stats(self) -> dict[str, Any]:
        """获取全局统计信息"""
        with self._lock:
            stats = {
                "active_workflows": len(self._active_workflows),
                "state_stats": self.state_manager.get_stats(),
                "memory_stats": self.resource_monitor.get_memory_stats(),
                "resource_limits": {
                    "max_steps": WorkflowLimits.MAX_WORKFLOW_STEPS,
                    "max_findings": WorkflowLimits.MAX_FINDINGS_SIZE,
                    "max_files": WorkflowLimits.MAX_FILE_REFERENCES,
                    "max_memory_mb": WorkflowLimits.MAX_MEMORY_MB,
                },
                "persistence_enabled": self._persistent_manager is not None,
            }
        return stats

    async def get_comprehensive_stats(self) -> dict[str, Any]:
        """获取包含持久化信息的综合统计"""
        basic_stats = self.get_global_stats()

        # 尝试获取持久化统计
        persistent_manager = self._get_persistent_manager()
        if persistent_manager:
            try:
                persistent_stats = await persistent_manager.get_comprehensive_stats()
                basic_stats["persistent_stats"] = persistent_stats
            except Exception as e:
                logger.warning(f"获取持久化统计失败: {e}")
                basic_stats["persistent_stats"] = {"error": str(e)}
        else:
            basic_stats["persistent_stats"] = {"enabled": False}

        return basic_stats


# 全局实例
_workflow_manager = None
_manager_lock = threading.Lock()


def get_workflow_manager() -> ConcurrentWorkflowManager:
    """获取全局工作流管理器实例（单例模式）"""
    global _workflow_manager
    if _workflow_manager is None:
        with _manager_lock:
            if _workflow_manager is None:
                _workflow_manager = ConcurrentWorkflowManager()
    return _workflow_manager


# 便捷函数
async def safe_start_workflow(workflow_id: str, initial_state: dict[str, Any]) -> bool:
    """安全启动工作流"""
    manager = get_workflow_manager()
    return await manager.start_workflow(workflow_id, initial_state)


async def safe_update_workflow(workflow_id: str, state_update: dict[str, Any]) -> bool:
    """安全更新工作流"""
    manager = get_workflow_manager()
    return await manager.update_workflow(workflow_id, state_update)


async def safe_finish_workflow(workflow_id: str) -> bool:
    """安全完成工作流"""
    manager = get_workflow_manager()
    return await manager.finish_workflow(workflow_id)


def create_sliding_findings_buffer(max_size: int = None) -> SlidingWindowBuffer:
    """创建滑动发现缓冲器"""
    size = max_size or WorkflowLimits.MAX_FINDINGS_SIZE
    return SlidingWindowBuffer(size)


def get_workflow_stats() -> dict[str, Any]:
    """获取工作流统计信息"""
    manager = get_workflow_manager()
    return manager.get_global_stats()


async def get_comprehensive_workflow_stats() -> dict[str, Any]:
    """获取包含持久化信息的综合工作流统计"""
    manager = get_workflow_manager()
    return await manager.get_comprehensive_stats()


async def restore_workflow_from_persistence(workflow_id: str) -> bool:
    """从持久化存储恢复工作流状态到内存"""
    manager = get_workflow_manager()
    persistent_manager = manager._get_persistent_manager()

    if not persistent_manager:
        logger.warning("持久化管理器未初始化")
        return False

    try:
        state = await persistent_manager.load_state(workflow_id)
        if state:
            # 恢复到内存中
            success = manager.state_manager.update_state(workflow_id, state)
            if success:
                logger.info(f"工作流状态已从持久化存储恢复: {workflow_id}")
            return success
        else:
            logger.info(f"持久化存储中未找到工作流: {workflow_id}")
            return False
    except Exception as e:
        logger.error(f"从持久化存储恢复工作流失败 {workflow_id}: {e}")
        return False


async def cleanup_all_expired_workflows(expire_hours: int = 24) -> dict[str, Any]:
    """清理所有过期的工作流状态（内存和持久化）"""
    manager = get_workflow_manager()

    # 清理内存中的过期状态
    manager.state_manager._cleanup_old_states()

    # 清理持久化存储中的过期状态
    cleanup_result = {"memory_cleaned": True, "persistent_cleaned": 0}

    persistent_manager = manager._get_persistent_manager()
    if persistent_manager:
        try:
            persistent_result = await persistent_manager.cleanup_expired(expire_hours)
            cleanup_result.update(persistent_result)
        except Exception as e:
            logger.error(f"清理持久化存储失败: {e}")
            cleanup_result["persistent_error"] = str(e)

    return cleanup_result
