"""
增强记忆系统核心类

基于深度架构分析的三层记忆系统实现：
1. 全局记忆层：跨项目通用知识和模式
2. 项目记忆层：特定项目的上下文和决策
3. 会话记忆层：临时对话状态和短期信息

设计原则：
- 分层存储：不同持久化策略
- 智能索引：语义+时间+质量多维度
- 自适应衰减：时间和使用频率双重因子
- 协调机制：层级间信息流转和冲突解决
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """
    标准记忆项数据模型

    根据架构分析设计的统一记忆数据结构，支持：
    - 多维度元数据标注
    - 质量评分和衰减计算
    - 语义向量存储（预留）
    - 层级间兼容性
    """

    # 核心标识
    id: str
    content: Union[str, Dict[str, Any]]
    layer: str  # "global", "project", "session"

    # 元数据
    type: str = "general"
    tags: List[str] = None
    category: str = "default"
    importance: str = "medium"  # "low", "medium", "high", "critical"

    # 时间信息
    created_at: str = None
    updated_at: str = None
    last_accessed: str = None

    # 质量和关联
    quality_score: float = 1.0
    access_count: int = 0
    relevance_score: float = 0.0
    related_items: List[str] = None

    # 语义向量（预留）
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None

    # 衰减控制
    decay_factor: float = 1.0
    min_retention_days: int = 7
    auto_cleanup: bool = True

    def __post_init__(self):
        """初始化后处理"""
        if self.tags is None:
            self.tags = []
        if self.related_items is None:
            self.related_items = []
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """从字典创建记忆项"""
        return cls(**data)

    def update_access(self):
        """更新访问信息"""
        self.last_accessed = datetime.now(timezone.utc).isoformat()
        self.access_count += 1
        self.updated_at = self.last_accessed

    def calculate_decay_score(self) -> float:
        """计算衰减分数"""
        try:
            now = datetime.now(timezone.utc)
            created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            last_access = datetime.fromisoformat(self.last_accessed.replace("Z", "+00:00"))

            # 时间衰减（指数衰减）
            age_days = (now - created).days
            time_decay = max(0.1, self.decay_factor ** (age_days / 30))

            # 访问频率加权
            access_boost = min(2.0, 1.0 + (self.access_count / 10))

            # 最近访问加权
            days_since_access = (now - last_access).days
            recency_factor = max(0.5, 1.0 - (days_since_access / 365))

            # 重要性加权
            importance_weights = {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0}
            importance_factor = importance_weights.get(self.importance, 1.0)

            # 综合分数
            final_score = time_decay * access_boost * recency_factor * importance_factor * self.quality_score

            return min(2.0, max(0.0, final_score))

        except Exception as e:
            logger.debug(f"计算衰减分数时出错: {e}")
            return self.quality_score


class MemoryLayer(ABC):
    """
    记忆层抽象基类

    定义三层记忆架构的通用接口：
    - 存储和检索操作
    - 索引管理
    - 衰减和清理
    """

    def __init__(self, layer_name: str, storage_path: Path):
        self.layer_name = layer_name
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._memory_items: Dict[str, MemoryItem] = {}
        self._indexes: Dict[str, Dict[str, Set[str]]] = {"type": {}, "tags": {}, "category": {}, "importance": {}}
        self.load_all()

    @abstractmethod
    def get_retention_policy(self) -> Dict[str, Any]:
        """获取层级特定的保留策略"""
        pass

    @abstractmethod
    def should_promote_to_higher_layer(self, item: MemoryItem) -> bool:
        """判断是否应该提升到更高层级"""
        pass

    def save_item(self, item: MemoryItem) -> str:
        """保存记忆项"""
        item.layer = self.layer_name
        item.updated_at = datetime.now(timezone.utc).isoformat()

        # 更新内存存储
        self._memory_items[item.id] = item

        # 更新索引
        self._update_indexes(item)

        # 持久化到文件
        self._persist_item(item)

        logger.debug(f"保存记忆项 {item.id} 到 {self.layer_name} 层")
        return item.id

    def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """获取记忆项"""
        item = self._memory_items.get(item_id)
        if item:
            item.update_access()
            self._persist_item(item)  # 更新访问信息
        return item

    def search_items(
        self,
        query: Optional[str] = None,
        type_filter: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        importance: Optional[str] = None,
        min_quality: float = 0.0,
        limit: int = 50,
    ) -> List[MemoryItem]:
        """搜索记忆项"""
        candidates = set(self._memory_items.keys())

        # 应用过滤器
        if type_filter:
            candidates &= self._indexes["type"].get(type_filter, set())

        if category:
            candidates &= self._indexes["category"].get(category, set())

        if importance:
            candidates &= self._indexes["importance"].get(importance, set())

        if tags:
            tag_matches = set()
            for tag in tags:
                tag_matches |= self._indexes["tags"].get(tag, set())
            candidates &= tag_matches

        # 获取候选项并过滤
        results = []
        for item_id in candidates:
            item = self._memory_items[item_id]

            # 质量过滤
            if item.calculate_decay_score() < min_quality:
                continue

            # 文本搜索
            if query:
                content_str = str(item.content).lower()
                if query.lower() not in content_str:
                    continue

            results.append(item)

        # 排序：相关度 > 质量 > 访问时间
        results.sort(key=lambda x: (x.relevance_score, x.calculate_decay_score(), x.last_accessed), reverse=True)

        return results[:limit]

    def remove_item(self, item_id: str) -> bool:
        """删除记忆项"""
        if item_id in self._memory_items:
            item = self._memory_items[item_id]
            self._remove_from_indexes(item)
            del self._memory_items[item_id]

            # 删除文件
            item_file = self.storage_path / f"{item_id}.json"
            if item_file.exists():
                item_file.unlink()

            logger.debug(f"删除记忆项 {item_id} 从 {self.layer_name} 层")
            return True
        return False

    def cleanup_expired_items(self) -> int:
        """清理过期记忆项"""
        policy = self.get_retention_policy()
        min_score = policy.get("min_decay_score", 0.1)
        max_age_days = policy.get("max_age_days", 365)

        now = datetime.now(timezone.utc)
        expired_items = []

        for item in self._memory_items.values():
            # 检查衰减分数
            if item.calculate_decay_score() < min_score and item.auto_cleanup:
                expired_items.append(item.id)
                continue

            # 检查最大年龄
            created = datetime.fromisoformat(item.created_at.replace("Z", "+00:00"))
            age_days = (now - created).days

            if age_days > max_age_days and item.auto_cleanup:
                # 检查最小保留期
                if age_days > item.min_retention_days:
                    expired_items.append(item.id)

        # 删除过期项
        removed_count = 0
        for item_id in expired_items:
            if self.remove_item(item_id):
                removed_count += 1

        if removed_count > 0:
            logger.info(f"{self.layer_name} 层清理了 {removed_count} 个过期记忆项")

        return removed_count

    def get_statistics(self) -> Dict[str, Any]:
        """获取层级统计信息"""
        total_items = len(self._memory_items)
        if total_items == 0:
            return {"total_items": 0, "avg_quality": 0.0, "types": {}, "categories": {}, "importance_levels": {}}

        # 计算统计
        total_quality = sum(item.calculate_decay_score() for item in self._memory_items.values())
        avg_quality = total_quality / total_items

        # 分类统计
        type_counts = {}
        category_counts = {}
        importance_counts = {}

        for item in self._memory_items.values():
            type_counts[item.type] = type_counts.get(item.type, 0) + 1
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
            importance_counts[item.importance] = importance_counts.get(item.importance, 0) + 1

        return {
            "total_items": total_items,
            "avg_quality": avg_quality,
            "types": type_counts,
            "categories": category_counts,
            "importance_levels": importance_counts,
            "storage_path": str(self.storage_path),
        }

    def load_all(self):
        """加载所有记忆项"""
        if not self.storage_path.exists():
            return

        for item_file in self.storage_path.glob("*.json"):
            try:
                with open(item_file, encoding="utf-8") as f:
                    data = json.load(f)
                    item = MemoryItem.from_dict(data)
                    self._memory_items[item.id] = item
                    self._update_indexes(item)
            except Exception as e:
                logger.warning(f"加载记忆项 {item_file} 时出错: {e}")

        logger.debug(f"从 {self.layer_name} 层加载了 {len(self._memory_items)} 个记忆项")

    def save_all(self):
        """保存所有记忆项"""
        for item in self._memory_items.values():
            self._persist_item(item)
        logger.debug(f"保存了 {self.layer_name} 层的所有记忆项")

    def _persist_item(self, item: MemoryItem):
        """持久化记忆项到文件"""
        item_file = self.storage_path / f"{item.id}.json"
        try:
            with open(item_file, "w", encoding="utf-8") as f:
                json.dump(item.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"持久化记忆项 {item.id} 时出错: {e}")

    def _update_indexes(self, item: MemoryItem):
        """更新索引"""
        # 类型索引
        if item.type not in self._indexes["type"]:
            self._indexes["type"][item.type] = set()
        self._indexes["type"][item.type].add(item.id)

        # 标签索引
        for tag in item.tags:
            if tag not in self._indexes["tags"]:
                self._indexes["tags"][tag] = set()
            self._indexes["tags"][tag].add(item.id)

        # 分类索引
        if item.category not in self._indexes["category"]:
            self._indexes["category"][item.category] = set()
        self._indexes["category"][item.category].add(item.id)

        # 重要性索引
        if item.importance not in self._indexes["importance"]:
            self._indexes["importance"][item.importance] = set()
        self._indexes["importance"][item.importance].add(item.id)

    def _remove_from_indexes(self, item: MemoryItem):
        """从索引中移除"""
        # 移除类型索引
        if item.type in self._indexes["type"]:
            self._indexes["type"][item.type].discard(item.id)

        # 移除标签索引
        for tag in item.tags:
            if tag in self._indexes["tags"]:
                self._indexes["tags"][tag].discard(item.id)

        # 移除分类索引
        if item.category in self._indexes["category"]:
            self._indexes["category"][item.category].discard(item.id)

        # 移除重要性索引
        if item.importance in self._indexes["importance"]:
            self._indexes["importance"][item.importance].discard(item.id)


class GlobalMemoryLayer(MemoryLayer):
    """
    全局记忆层

    跨项目通用知识和模式：
    - 长期持久化
    - 高质量要求
    - 通用模式和最佳实践
    """

    def __init__(self, storage_path: Path):
        super().__init__("global", storage_path)

    def get_retention_policy(self) -> Dict[str, Any]:
        """全局层保留策略：长期存储，高质量要求"""
        return {
            "min_decay_score": 0.3,
            "max_age_days": 730,  # 2年
            "auto_cleanup_enabled": True,
            "promotion_threshold": None,  # 最高层
        }

    def should_promote_to_higher_layer(self, item: MemoryItem) -> bool:
        """全局层是最高层，不需要提升"""
        return False


class ProjectMemoryLayer(MemoryLayer):
    """
    项目记忆层

    特定项目的上下文和决策：
    - 项目生命周期持久化
    - 中等质量要求
    - 项目特定信息
    """

    def __init__(self, storage_path: Path):
        super().__init__("project", storage_path)

    def get_retention_policy(self) -> Dict[str, Any]:
        """项目层保留策略：中期存储，中等质量要求"""
        return {
            "min_decay_score": 0.2,
            "max_age_days": 365,  # 1年
            "auto_cleanup_enabled": True,
            "promotion_threshold": 1.5,  # 高质量项目知识可提升到全局层
        }

    def should_promote_to_higher_layer(self, item: MemoryItem) -> bool:
        """判断是否应该提升到全局层"""
        decay_score = item.calculate_decay_score()
        policy = self.get_retention_policy()

        # 高质量、高访问频率、通用性强的记忆可以提升
        return (
            decay_score >= policy["promotion_threshold"]
            and item.access_count >= 10
            and item.importance in ["high", "critical"]
            and len(item.tags) >= 3
        )  # 标签多说明通用性强


class SessionMemoryLayer(MemoryLayer):
    """
    会话记忆层

    临时对话状态和短期信息：
    - 会话期间临时存储
    - 低质量要求
    - 对话上下文和临时状态
    """

    def __init__(self, storage_path: Path):
        super().__init__("session", storage_path)

    def get_retention_policy(self) -> Dict[str, Any]:
        """会话层保留策略：短期存储，低质量要求"""
        return {
            "min_decay_score": 0.1,
            "max_age_days": 7,  # 1周
            "auto_cleanup_enabled": True,
            "promotion_threshold": 1.0,  # 中等质量可提升到项目层
        }

    def should_promote_to_higher_layer(self, item: MemoryItem) -> bool:
        """判断是否应该提升到项目层"""
        decay_score = item.calculate_decay_score()
        policy = self.get_retention_policy()

        # 被频繁访问的会话信息可以提升到项目层
        return (
            decay_score >= policy["promotion_threshold"]
            and item.access_count >= 5
            and item.importance in ["medium", "high", "critical"]
        )


class EnhancedMemorySystem:
    """
    增强记忆系统主类

    协调三层记忆架构的核心系统：
    - 层级管理
    - 智能路由
    - 自动提升
    - 统一接口
    """

    def __init__(self, base_storage_path: Union[str, Path]):
        self.base_path = Path(base_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 初始化三层记忆
        self.global_layer = GlobalMemoryLayer(self.base_path / "global")
        self.project_layer = ProjectMemoryLayer(self.base_path / "project")
        self.session_layer = SessionMemoryLayer(self.base_path / "session")

        self.layers = {"global": self.global_layer, "project": self.project_layer, "session": self.session_layer}

        logger.info(f"增强记忆系统初始化完成，存储路径: {self.base_path}")

    def save_memory(
        self,
        content: Union[str, Dict[str, Any]],
        layer: str = "session",
        type_: str = "general",
        tags: Optional[List[str]] = None,
        category: str = "default",
        importance: str = "medium",
        **kwargs,
    ) -> str:
        """保存记忆到指定层级"""
        if layer not in self.layers:
            raise ValueError(f"无效的记忆层级: {layer}")

        # 创建记忆项
        item = MemoryItem(
            id=str(uuid4()),
            content=content,
            layer=layer,
            type=type_,
            tags=tags or [],
            category=category,
            importance=importance,
            **kwargs,
        )

        # 保存到指定层
        memory_layer = self.layers[layer]
        item_id = memory_layer.save_item(item)

        logger.debug(f"保存记忆 {item_id} 到 {layer} 层")
        return item_id

    def get_memory(self, item_id: str, layer: Optional[str] = None) -> Optional[MemoryItem]:
        """获取记忆项"""
        if layer:
            # 从指定层获取
            if layer in self.layers:
                return self.layers[layer].get_item(item_id)
            return None

        # 从所有层搜索
        for layer_name, memory_layer in self.layers.items():
            item = memory_layer.get_item(item_id)
            if item:
                return item

        return None

    def search_memories(
        self, query: Optional[str] = None, layers: Optional[List[str]] = None, **search_kwargs
    ) -> List[MemoryItem]:
        """跨层搜索记忆"""
        if layers is None:
            layers = ["global", "project", "session"]

        all_results = []
        for layer_name in layers:
            if layer_name in self.layers:
                layer_results = self.layers[layer_name].search_items(query=query, **search_kwargs)
                all_results.extend(layer_results)

        # 跨层排序
        all_results.sort(key=lambda x: (x.relevance_score, x.calculate_decay_score(), x.last_accessed), reverse=True)

        return all_results

    def promote_memories(self) -> Dict[str, int]:
        """自动提升记忆到更高层级"""
        promotion_counts = {"session_to_project": 0, "project_to_global": 0}

        # 会话层 -> 项目层
        for item in list(self.session_layer._memory_items.values()):
            if self.session_layer.should_promote_to_higher_layer(item):
                # 复制到项目层
                new_item = MemoryItem.from_dict(item.to_dict())
                new_item.id = str(uuid4())
                new_item.layer = "project"
                self.project_layer.save_item(new_item)

                # 从会话层删除
                self.session_layer.remove_item(item.id)
                promotion_counts["session_to_project"] += 1

        # 项目层 -> 全局层
        for item in list(self.project_layer._memory_items.values()):
            if self.project_layer.should_promote_to_higher_layer(item):
                # 复制到全局层
                new_item = MemoryItem.from_dict(item.to_dict())
                new_item.id = str(uuid4())
                new_item.layer = "global"
                self.global_layer.save_item(new_item)

                # 从项目层删除
                self.project_layer.remove_item(item.id)
                promotion_counts["project_to_global"] += 1

        total_promoted = sum(promotion_counts.values())
        if total_promoted > 0:
            logger.info(f"自动提升记忆: {promotion_counts}")

        return promotion_counts

    def cleanup_all_layers(self) -> Dict[str, int]:
        """清理所有层的过期记忆"""
        cleanup_counts = {}
        for layer_name, memory_layer in self.layers.items():
            cleanup_counts[layer_name] = memory_layer.cleanup_expired_items()

        total_cleaned = sum(cleanup_counts.values())
        if total_cleaned > 0:
            logger.info(f"清理记忆统计: {cleanup_counts}")

        return cleanup_counts

    def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {"layers": {}, "total_items": 0, "overall_quality": 0.0}

        total_quality = 0.0
        total_items = 0

        for layer_name, memory_layer in self.layers.items():
            layer_stats = memory_layer.get_statistics()
            stats["layers"][layer_name] = layer_stats

            total_items += layer_stats["total_items"]
            total_quality += layer_stats["avg_quality"] * layer_stats["total_items"]

        stats["total_items"] = total_items
        stats["overall_quality"] = total_quality / total_items if total_items > 0 else 0.0

        return stats

    def save_all(self):
        """保存所有层的记忆"""
        for memory_layer in self.layers.values():
            memory_layer.save_all()
        logger.info("保存了所有层的记忆")

    def shutdown(self):
        """系统关闭时的清理工作"""
        self.save_all()
        logger.info("增强记忆系统已关闭")


# 全局实例（可选，用于简化使用）
_global_memory_system: Optional[EnhancedMemorySystem] = None


def get_enhanced_memory_system(storage_path: Optional[str] = None) -> EnhancedMemorySystem:
    """获取全局记忆系统实例"""
    global _global_memory_system

    if _global_memory_system is None:
        if storage_path is None:
            storage_path = os.getenv("ENHANCED_MEMORY_PATH", ".zen_memory")
        _global_memory_system = EnhancedMemorySystem(storage_path)

    return _global_memory_system


def save_memory_item(content: Union[str, Dict[str, Any]], layer: str = "session", **kwargs) -> str:
    """便捷的记忆保存函数"""
    system = get_enhanced_memory_system()
    return system.save_memory(content, layer, **kwargs)


def search_memory_items(query: Optional[str] = None, **kwargs) -> List[MemoryItem]:
    """便捷的记忆搜索函数"""
    system = get_enhanced_memory_system()
    return system.search_memories(query, **kwargs)
