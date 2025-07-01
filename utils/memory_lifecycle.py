"""
记忆生命周期管理模块

实现高级的记忆衰减、质量评分和生命周期管理功能：
- 多维度质量评分算法
- 智能衰减策略
- 记忆价值评估
- 自动归档和清理
- 记忆重要性动态调整
"""

import logging
import math
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from .intelligent_memory_retrieval import (
    MEMORY_DECAY_DAYS,
    MEMORY_QUALITY_THRESHOLD,
    calculate_memory_quality,
    get_memory_index,
    save_memory_index,
)
from .conversation_memory import _load_memory_layer, _save_memory_layer

logger = logging.getLogger(__name__)

# 高级配置
MEMORY_IMPORTANCE_BOOST = {
    "high": 2.0,      # 高重要性记忆衰减速度减半
    "medium": 1.0,    # 正常衰减
    "low": 0.5        # 低重要性记忆衰减速度加倍
}

MEMORY_TYPE_WEIGHTS = {
    "bug": 1.2,          # Bug 相关记忆权重更高
    "security": 1.5,     # 安全相关记忆最重要
    "architecture": 1.3, # 架构决策重要
    "feature": 1.0,      # 功能特性正常权重
    "todo": 0.8,         # TODO 权重较低
    "note": 0.7,         # 普通笔记权重最低
    "general": 0.9       # 一般记忆
}

# 衰减曲线类型
class DecayCurve:
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    STEP = "step"


class MemoryLifecycleManager:
    """
    高级记忆生命周期管理器
    
    提供：
    - 多种衰减曲线
    - 质量评分算法
    - 价值评估
    - 智能归档
    - 记忆复活机制
    """
    
    def __init__(self):
        self.decay_curve = os.getenv("MEMORY_DECAY_CURVE", DecayCurve.EXPONENTIAL)
        self.archive_threshold = float(os.getenv("MEMORY_ARCHIVE_THRESHOLD", "0.2"))
        self.resurrection_boost = float(os.getenv("MEMORY_RESURRECTION_BOOST", "0.3"))
        
    def calculate_advanced_quality(self, memory: Dict[str, Any]) -> float:
        """
        计算高级质量分数
        
        考虑因素：
        - 基础质量评分
        - 内容丰富度
        - 结构化程度
        - 关联性
        - 使用频率
        - 用户反馈
        """
        # 1. 基础质量分数
        base_quality = calculate_memory_quality(memory)
        
        # 2. 内容丰富度评分
        content_score = self._evaluate_content_richness(memory.get("content", ""))
        
        # 3. 结构化程度评分
        structure_score = self._evaluate_structure(memory)
        
        # 4. 关联性评分
        relevance_score = self._evaluate_relevance(memory)
        
        # 5. 使用频率评分
        usage_score = self._evaluate_usage(memory.get("metadata", {}))
        
        # 6. 用户反馈评分（如果有）
        feedback_score = self._evaluate_feedback(memory.get("metadata", {}))
        
        # 综合评分（加权平均）
        weights = {
            "base": 0.3,
            "content": 0.2,
            "structure": 0.15,
            "relevance": 0.15,
            "usage": 0.15,
            "feedback": 0.05
        }
        
        total_score = (
            weights["base"] * base_quality +
            weights["content"] * content_score +
            weights["structure"] * structure_score +
            weights["relevance"] * relevance_score +
            weights["usage"] * usage_score +
            weights["feedback"] * feedback_score
        )
        
        return min(1.0, max(0.0, total_score))
    
    def apply_decay(self, memory: Dict[str, Any], current_time: Optional[datetime] = None) -> float:
        """
        应用衰减算法
        
        支持多种衰减曲线：
        - 线性衰减
        - 指数衰减
        - 对数衰减
        - 阶梯衰减
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
            
        try:
            timestamp = memory.get("timestamp", "")
            created_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age_days = (current_time - created_time).days
        except Exception:
            # 无法解析时间，返回默认值
            return 0.5
        
        # 获取重要性系数
        metadata = memory.get("metadata", {})
        importance = metadata.get("importance", "medium")
        importance_factor = MEMORY_IMPORTANCE_BOOST.get(importance, 1.0)
        
        # 调整年龄（考虑重要性）
        adjusted_age = age_days / importance_factor
        
        # 应用不同的衰减曲线
        if self.decay_curve == DecayCurve.LINEAR:
            decay_value = self._linear_decay(adjusted_age)
        elif self.decay_curve == DecayCurve.EXPONENTIAL:
            decay_value = self._exponential_decay(adjusted_age)
        elif self.decay_curve == DecayCurve.LOGARITHMIC:
            decay_value = self._logarithmic_decay(adjusted_age)
        elif self.decay_curve == DecayCurve.STEP:
            decay_value = self._step_decay(adjusted_age)
        else:
            decay_value = 1.0
        
        # 应用类型权重
        mem_type = metadata.get("type", "general")
        type_weight = MEMORY_TYPE_WEIGHTS.get(mem_type, 1.0)
        
        return min(1.0, decay_value * type_weight)
    
    def evaluate_memory_value(self, memory: Dict[str, Any]) -> Dict[str, float]:
        """
        评估记忆的综合价值
        
        返回多维度的价值评分
        """
        quality = self.calculate_advanced_quality(memory)
        decay = self.apply_decay(memory)
        
        # 计算综合价值
        overall_value = quality * decay
        
        # 特殊价值指标
        metadata = memory.get("metadata", {})
        
        # 历史价值（老记忆可能有历史价值）
        historical_value = self._calculate_historical_value(memory)
        
        # 参考价值（被引用次数）
        reference_value = metadata.get("reference_count", 0) / 10.0
        reference_value = min(1.0, reference_value)
        
        # 独特性价值
        uniqueness_value = self._calculate_uniqueness(memory)
        
        return {
            "overall": overall_value,
            "quality": quality,
            "decay": decay,
            "historical": historical_value,
            "reference": reference_value,
            "uniqueness": uniqueness_value,
            "should_archive": overall_value < self.archive_threshold,
            "should_delete": overall_value < MEMORY_QUALITY_THRESHOLD * 0.5
        }
    
    def resurrect_memory(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """
        复活记忆机制
        
        当老记忆被重新访问时，提升其质量分数
        """
        metadata = memory.get("metadata", {})
        
        # 更新访问计数
        access_count = metadata.get("access_count", 0) + 1
        metadata["access_count"] = access_count
        metadata["last_accessed"] = datetime.now(timezone.utc).isoformat()
        
        # 应用复活提升
        current_quality = metadata.get("quality_score", 0.5)
        boosted_quality = min(1.0, current_quality + self.resurrection_boost)
        metadata["quality_score"] = boosted_quality
        
        # 记录复活历史
        resurrection_history = metadata.get("resurrection_history", [])
        resurrection_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_quality": current_quality,
            "new_quality": boosted_quality,
            "reason": "accessed"
        })
        metadata["resurrection_history"] = resurrection_history[-5:]  # 只保留最近5次
        
        memory["metadata"] = metadata
        return memory
    
    def batch_evaluate_memories(self, layer: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量评估记忆
        
        返回分类后的记忆列表
        """
        results = {
            "active": [],      # 活跃记忆
            "archive": [],     # 待归档
            "delete": [],      # 待删除
            "valuable": []     # 高价值记忆
        }
        
        layers = [layer] if layer else ["global", "project"]
        
        for current_layer in layers:
            layer_data = _load_memory_layer(current_layer)
            
            for key, memory in layer_data.items():
                value_assessment = self.evaluate_memory_value(memory)
                
                memory_info = {
                    "key": key,
                    "layer": current_layer,
                    "memory": memory,
                    "assessment": value_assessment
                }
                
                if value_assessment["should_delete"]:
                    results["delete"].append(memory_info)
                elif value_assessment["should_archive"]:
                    results["archive"].append(memory_info)
                elif value_assessment["overall"] > 0.8:
                    results["valuable"].append(memory_info)
                else:
                    results["active"].append(memory_info)
        
        return results
    
    def optimize_memory_storage(self, dry_run: bool = True) -> Dict[str, int]:
        """
        优化记忆存储
        
        执行：
        - 删除低价值记忆
        - 归档中等价值记忆
        - 更新索引
        """
        evaluation = self.batch_evaluate_memories()
        
        stats = {
            "deleted": 0,
            "archived": 0,
            "updated": 0
        }
        
        if not dry_run:
            index = get_memory_index()
            
            # 删除低价值记忆
            for item in evaluation["delete"]:
                layer_data = _load_memory_layer(item["layer"])
                if item["key"] in layer_data:
                    del layer_data[item["key"]]
                    index.remove_memory(item["key"])
                    stats["deleted"] += 1
                    _save_memory_layer(item["layer"], layer_data)
            
            # TODO: 实现归档功能
            # for item in evaluation["archive"]:
            #     # 移动到归档层
            #     stats["archived"] += 1
            
            # 保存更新后的索引
            save_memory_index(index)
            
            logger.info(f"Memory optimization completed: {stats}")
        else:
            # 模拟运行，只返回统计
            stats["deleted"] = len(evaluation["delete"])
            stats["archived"] = len(evaluation["archive"])
        
        return stats
    
    # 私有辅助方法
    
    def _evaluate_content_richness(self, content: Any) -> float:
        """评估内容丰富度"""
        if not isinstance(content, str):
            content = str(content)
        
        # 长度评分
        length_score = min(1.0, len(content) / 1000)  # 1000字符满分
        
        # 结构评分（包含列表、代码块等）
        structure_indicators = ['\n-', '\n*', '\n1.', '```', '    ', '\t']
        structure_score = sum(1 for ind in structure_indicators if ind in content) / len(structure_indicators)
        
        # 信息密度（唯一词汇比例）
        words = content.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
        else:
            unique_ratio = 0
        
        return (length_score * 0.4 + structure_score * 0.3 + unique_ratio * 0.3)
    
    def _evaluate_structure(self, memory: Dict[str, Any]) -> float:
        """评估结构化程度"""
        metadata = memory.get("metadata", {})
        
        # 检查必要字段
        required_fields = ["tags", "type", "importance"]
        present_fields = sum(1 for field in required_fields if field in metadata)
        field_score = present_fields / len(required_fields)
        
        # 标签质量
        tags = metadata.get("tags", [])
        tag_score = min(1.0, len(tags) / 5)  # 5个标签满分
        
        return (field_score * 0.6 + tag_score * 0.4)
    
    def _evaluate_relevance(self, memory: Dict[str, Any]) -> float:
        """评估关联性"""
        metadata = memory.get("metadata", {})
        
        # 被引用次数
        ref_count = metadata.get("reference_count", 0)
        ref_score = min(1.0, ref_count / 10)
        
        # 关联记忆数量
        related_count = len(metadata.get("related_memories", []))
        related_score = min(1.0, related_count / 5)
        
        return (ref_score * 0.7 + related_score * 0.3)
    
    def _evaluate_usage(self, metadata: Dict[str, Any]) -> float:
        """评估使用频率"""
        access_count = metadata.get("access_count", 0)
        
        # 使用对数函数平滑
        if access_count > 0:
            usage_score = min(1.0, math.log(access_count + 1) / math.log(50))
        else:
            usage_score = 0.0
        
        # 考虑最近访问时间
        last_accessed = metadata.get("last_accessed")
        if last_accessed:
            try:
                last_time = datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))
                days_since_access = (datetime.now(timezone.utc) - last_time).days
                recency_score = max(0.0, 1.0 - days_since_access / 30)  # 30天内线性衰减
            except Exception:
                recency_score = 0.0
        else:
            recency_score = 0.0
        
        return (usage_score * 0.6 + recency_score * 0.4)
    
    def _evaluate_feedback(self, metadata: Dict[str, Any]) -> float:
        """评估用户反馈"""
        # 用户评分（如果有）
        user_rating = metadata.get("user_rating", 0)
        if user_rating > 0:
            return user_rating / 5.0  # 假设5分制
        
        # 标记（有用/无用）
        if metadata.get("marked_useful"):
            return 1.0
        elif metadata.get("marked_useless"):
            return 0.0
        
        return 0.5  # 默认中性
    
    def _calculate_historical_value(self, memory: Dict[str, Any]) -> float:
        """计算历史价值"""
        try:
            timestamp = memory.get("timestamp", "")
            created_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created_time).days
            
            # 超过一定时间的记忆可能有历史价值
            if age_days > 365:  # 1年以上
                return min(1.0, (age_days - 365) / 365)  # 每额外一年增加价值
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def _calculate_uniqueness(self, memory: Dict[str, Any]) -> float:
        """计算独特性价值"""
        metadata = memory.get("metadata", {})
        
        # 基于标签的独特性（罕见标签价值更高）
        tags = metadata.get("tags", [])
        if not tags:
            return 0.5
        
        # TODO: 实现基于全局标签频率的独特性计算
        # 暂时使用标签数量作为简单指标
        return min(1.0, len(tags) / 10)
    
    # 衰减函数实现
    
    def _linear_decay(self, age_days: float) -> float:
        """线性衰减"""
        if age_days <= MEMORY_DECAY_DAYS:
            return 1.0
        else:
            return max(0.1, 1.0 - (age_days - MEMORY_DECAY_DAYS) / (MEMORY_DECAY_DAYS * 2))
    
    def _exponential_decay(self, age_days: float) -> float:
        """指数衰减"""
        if age_days <= MEMORY_DECAY_DAYS:
            return 1.0
        else:
            # e^(-λt) 其中 λ 控制衰减速度
            decay_rate = 0.05  # 衰减率
            return max(0.1, math.exp(-decay_rate * (age_days - MEMORY_DECAY_DAYS)))
    
    def _logarithmic_decay(self, age_days: float) -> float:
        """对数衰减（衰减速度逐渐减慢）"""
        if age_days <= MEMORY_DECAY_DAYS:
            return 1.0
        else:
            # 1 - log(1 + t) / log(1 + max_t)
            max_age = MEMORY_DECAY_DAYS * 10
            return max(0.1, 1.0 - math.log(1 + age_days - MEMORY_DECAY_DAYS) / math.log(1 + max_age))
    
    def _step_decay(self, age_days: float) -> float:
        """阶梯衰减"""
        if age_days <= MEMORY_DECAY_DAYS:
            return 1.0
        elif age_days <= MEMORY_DECAY_DAYS * 2:
            return 0.7
        elif age_days <= MEMORY_DECAY_DAYS * 4:
            return 0.5
        elif age_days <= MEMORY_DECAY_DAYS * 8:
            return 0.3
        else:
            return 0.1


# 全局实例
_lifecycle_manager: Optional[MemoryLifecycleManager] = None


def get_lifecycle_manager() -> MemoryLifecycleManager:
    """获取生命周期管理器实例"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = MemoryLifecycleManager()
    return _lifecycle_manager


def evaluate_memory_health() -> Dict[str, Any]:
    """
    评估整体记忆系统健康状况
    
    返回健康报告
    """
    manager = get_lifecycle_manager()
    evaluation = manager.batch_evaluate_memories()
    
    total_memories = sum(len(cat) for cat in evaluation.values())
    
    health_report = {
        "total_memories": total_memories,
        "active_memories": len(evaluation["active"]),
        "valuable_memories": len(evaluation["valuable"]),
        "memories_to_archive": len(evaluation["archive"]),
        "memories_to_delete": len(evaluation["delete"]),
        "health_score": 0.0,
        "recommendations": []
    }
    
    # 计算健康分数
    if total_memories > 0:
        active_ratio = len(evaluation["active"]) / total_memories
        valuable_ratio = len(evaluation["valuable"]) / total_memories
        delete_ratio = len(evaluation["delete"]) / total_memories
        
        health_score = (active_ratio * 0.5 + valuable_ratio * 0.3 - delete_ratio * 0.2)
        health_report["health_score"] = max(0.0, min(1.0, health_score))
    
    # 生成建议
    if health_report["memories_to_delete"] > total_memories * 0.3:
        health_report["recommendations"].append("建议执行记忆清理，删除低价值记忆")
    
    if health_report["memories_to_archive"] > total_memories * 0.2:
        health_report["recommendations"].append("建议归档部分老旧记忆")
    
    if health_report["valuable_memories"] < total_memories * 0.1:
        health_report["recommendations"].append("高价值记忆比例较低，建议提升记忆质量")
    
    return health_report