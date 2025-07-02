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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .conversation_memory import _load_memory_layer, _save_memory_layer
from .intelligent_memory_retrieval import (
    MEMORY_DECAY_DAYS,
    MEMORY_QUALITY_THRESHOLD,
    calculate_memory_quality,
    get_memory_index,
    save_memory_index,
)

logger = logging.getLogger(__name__)

# 高级配置
MEMORY_IMPORTANCE_BOOST = {
    "high": 2.0,  # 高重要性记忆衰减速度减半
    "medium": 1.0,  # 正常衰减
    "low": 0.5,  # 低重要性记忆衰减速度加倍
}

MEMORY_TYPE_WEIGHTS = {
    "bug": 1.2,  # Bug 相关记忆权重更高
    "security": 1.5,  # 安全相关记忆最重要
    "architecture": 1.3,  # 架构决策重要
    "feature": 1.0,  # 功能特性正常权重
    "todo": 0.8,  # TODO 权重较低
    "note": 0.7,  # 普通笔记权重最低
    "general": 0.9,  # 一般记忆
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
        weights = {"base": 0.3, "content": 0.2, "structure": 0.15, "relevance": 0.15, "usage": 0.15, "feedback": 0.05}

        total_score = (
            weights["base"] * base_quality
            + weights["content"] * content_score
            + weights["structure"] * structure_score
            + weights["relevance"] * relevance_score
            + weights["usage"] * usage_score
            + weights["feedback"] * feedback_score
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
            "should_delete": overall_value < MEMORY_QUALITY_THRESHOLD * 0.5,
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
        resurrection_history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "old_quality": current_quality,
                "new_quality": boosted_quality,
                "reason": "accessed",
            }
        )
        metadata["resurrection_history"] = resurrection_history[-5:]  # 只保留最近5次

        memory["metadata"] = metadata
        return memory

    def batch_evaluate_memories(self, layer: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量评估记忆

        返回分类后的记忆列表
        """
        results = {
            "active": [],  # 活跃记忆
            "archive": [],  # 待归档
            "delete": [],  # 待删除
            "valuable": [],  # 高价值记忆
        }

        layers = [layer] if layer else ["global", "project"]

        for current_layer in layers:
            layer_data = _load_memory_layer(current_layer)

            for key, memory in layer_data.items():
                value_assessment = self.evaluate_memory_value(memory)

                memory_info = {"key": key, "layer": current_layer, "memory": memory, "assessment": value_assessment}

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

        stats = {"deleted": 0, "archived": 0, "updated": 0}

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
        structure_indicators = ["\n-", "\n*", "\n1.", "```", "    ", "\t"]
        structure_score = sum(1 for ind in structure_indicators if ind in content) / len(structure_indicators)

        # 信息密度（唯一词汇比例）
        words = content.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
        else:
            unique_ratio = 0

        return length_score * 0.4 + structure_score * 0.3 + unique_ratio * 0.3

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

        return field_score * 0.6 + tag_score * 0.4

    def _evaluate_relevance(self, memory: Dict[str, Any]) -> float:
        """评估关联性"""
        metadata = memory.get("metadata", {})

        # 被引用次数
        ref_count = metadata.get("reference_count", 0)
        ref_score = min(1.0, ref_count / 10)

        # 关联记忆数量
        related_count = len(metadata.get("related_memories", []))
        related_score = min(1.0, related_count / 5)

        return ref_score * 0.7 + related_score * 0.3

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

        return usage_score * 0.6 + recency_score * 0.4

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
        "recommendations": [],
    }

    # 计算健康分数
    if total_memories > 0:
        active_ratio = len(evaluation["active"]) / total_memories
        valuable_ratio = len(evaluation["valuable"]) / total_memories
        delete_ratio = len(evaluation["delete"]) / total_memories

        health_score = active_ratio * 0.5 + valuable_ratio * 0.3 - delete_ratio * 0.2
        health_report["health_score"] = max(0.0, min(1.0, health_score))

    # 生成建议
    if health_report["memories_to_delete"] > total_memories * 0.3:
        health_report["recommendations"].append("建议执行记忆清理，删除低价值记忆")

    if health_report["memories_to_archive"] > total_memories * 0.2:
        health_report["recommendations"].append("建议归档部分老旧记忆")

    if health_report["valuable_memories"] < total_memories * 0.1:
        health_report["recommendations"].append("高价值记忆比例较低，建议提升记忆质量")

    return health_report


# 记忆导出和导入功能


def export_memories(
    layers: Optional[List[str]] = None,
    export_format: str = "json",
    include_metadata: bool = True,
    include_statistics: bool = True,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    导出记忆数据

    Args:
        layers: 要导出的记忆层列表 ["global", "project", "session"]，默认导出所有
        export_format: 导出格式 ("json", "csv", "yaml")
        include_metadata: 是否包含元数据
        include_statistics: 是否包含统计信息
        output_file: 输出文件路径，如果None则返回数据

    Returns:
        导出的记忆数据或导出统计信息
    """
    import json
    from pathlib import Path

    if layers is None:
        layers = ["global", "project", "session"]

    export_data = {
        "export_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "6.0.0",
            "format": export_format,
            "layers_exported": layers,
            "include_metadata": include_metadata,
        },
        "memories": {},
        "statistics": {} if include_statistics else None,
    }

    total_memories = 0

    # 导出每个记忆层
    for layer in layers:
        try:
            # 加载记忆层数据
            layer_data = _load_memory_layer(layer)

            if not include_metadata:
                # 移除元数据，只保留核心内容
                cleaned_data = []
                for memory in layer_data:
                    cleaned_memory = {
                        "id": memory.get("id"),
                        "content": memory.get("content"),
                        "timestamp": memory.get("timestamp"),
                        "layer": memory.get("layer"),
                    }
                    cleaned_data.append(cleaned_memory)
                export_data["memories"][layer] = cleaned_data
            else:
                export_data["memories"][layer] = layer_data

            total_memories += len(layer_data)

            if include_statistics:
                # 计算层统计信息
                layer_stats = {
                    "total_count": len(layer_data),
                    "memory_types": {},
                    "tag_distribution": {},
                    "quality_distribution": {"high": 0, "medium": 0, "low": 0},
                }

                for memory in layer_data:
                    metadata = memory.get("metadata", {})

                    # 类型统计
                    memory_type = metadata.get("type", "unknown")
                    layer_stats["memory_types"][memory_type] = layer_stats["memory_types"].get(memory_type, 0) + 1

                    # 标签统计
                    tags = metadata.get("tags", [])
                    for tag in tags:
                        layer_stats["tag_distribution"][tag] = layer_stats["tag_distribution"].get(tag, 0) + 1

                    # 质量统计
                    quality = calculate_memory_quality(memory)
                    if quality >= 0.7:
                        layer_stats["quality_distribution"]["high"] += 1
                    elif quality >= 0.4:
                        layer_stats["quality_distribution"]["medium"] += 1
                    else:
                        layer_stats["quality_distribution"]["low"] += 1

                export_data["statistics"][layer] = layer_stats

        except Exception as e:
            logger.error(f"导出记忆层 {layer} 时出错: {e}")
            export_data["memories"][layer] = []
            if include_statistics:
                export_data["statistics"][layer] = {"error": str(e)}

    # 添加全局统计
    if include_statistics:
        export_data["statistics"]["global_summary"] = {
            "total_memories_exported": total_memories,
            "layers_count": len(layers),
            "export_timestamp": export_data["export_metadata"]["timestamp"],
        }

    # 保存到文件
    if output_file:
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if export_format.lower() == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

            elif export_format.lower() == "yaml":
                try:
                    import yaml

                    with open(output_path, "w", encoding="utf-8") as f:
                        yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
                except ImportError:
                    logger.error("YAML 格式需要安装 PyYAML 库")
                    raise

            elif export_format.lower() == "csv":
                import csv

                # CSV 格式导出扁平化的记忆数据
                csv_path = output_path.with_suffix(".csv")
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)

                    # 写入表头
                    writer.writerow(["id", "layer", "content", "timestamp", "type", "tags", "quality"])

                    # 写入数据
                    for layer, memories in export_data["memories"].items():
                        for memory in memories:
                            metadata = memory.get("metadata", {})
                            tags = ",".join(metadata.get("tags", []))
                            quality = calculate_memory_quality(memory)

                            writer.writerow(
                                [
                                    memory.get("id", ""),
                                    layer,
                                    memory.get("content", "")[:500],  # 截断长内容
                                    memory.get("timestamp", ""),
                                    metadata.get("type", ""),
                                    tags,
                                    f"{quality:.2f}",
                                ]
                            )

            logger.info(f"记忆导出成功：{output_file}，共导出 {total_memories} 条记忆")
            return {
                "success": True,
                "output_file": str(output_path),
                "total_exported": total_memories,
                "layers": layers,
            }

        except Exception as e:
            logger.error(f"保存导出文件时出错: {e}")
            return {"success": False, "error": str(e), "data": export_data}

    return export_data


def import_memories(
    import_file: str,
    target_layers: Optional[Dict[str, str]] = None,
    merge_strategy: str = "skip_duplicates",
    validate_data: bool = True,
) -> Dict[str, Any]:
    """
    导入记忆数据

    Args:
        import_file: 导入文件路径
        target_layers: 层映射 {"source_layer": "target_layer"}，默认保持原层
        merge_strategy: 合并策略 ("skip_duplicates", "overwrite", "append_suffix")
        validate_data: 是否验证数据完整性

    Returns:
        导入结果统计
    """
    import json
    from pathlib import Path

    try:
        import_path = Path(import_file)
        if not import_path.exists():
            return {"success": False, "error": f"导入文件不存在: {import_file}"}

        # 读取导入文件
        file_extension = import_path.suffix.lower()

        if file_extension == ".json":
            with open(import_path, encoding="utf-8") as f:
                import_data = json.load(f)

        elif file_extension in [".yml", ".yaml"]:
            try:
                import yaml

                with open(import_path, encoding="utf-8") as f:
                    import_data = yaml.safe_load(f)
            except ImportError:
                return {"success": False, "error": "YAML 格式需要安装 PyYAML 库"}

        else:
            return {"success": False, "error": f"不支持的文件格式: {file_extension}"}

        # 验证导入数据格式
        if validate_data:
            if not isinstance(import_data, dict) or "memories" not in import_data:
                return {"success": False, "error": "导入数据格式无效"}

        imported_count = 0
        skipped_count = 0
        error_count = 0
        import_stats = {}

        memories_data = import_data.get("memories", {})

        for source_layer, memories in memories_data.items():
            if not isinstance(memories, list):
                logger.warning(f"跳过无效的记忆层: {source_layer}")
                continue

            # 确定目标层
            target_layer = source_layer
            if target_layers and source_layer in target_layers:
                target_layer = target_layers[source_layer]

            # 加载现有记忆
            existing_memories = _load_memory_layer(target_layer)
            existing_ids = {memory.get("id") for memory in existing_memories if memory.get("id")}

            layer_imported = 0
            layer_skipped = 0
            layer_errors = 0

            for memory in memories:
                try:
                    memory_id = memory.get("id")

                    # 处理重复记忆
                    if memory_id in existing_ids:
                        if merge_strategy == "skip_duplicates":
                            layer_skipped += 1
                            continue
                        elif merge_strategy == "append_suffix":
                            # 添加后缀避免冲突
                            suffix = 1
                            new_id = f"{memory_id}_imported_{suffix}"
                            while new_id in existing_ids:
                                suffix += 1
                                new_id = f"{memory_id}_imported_{suffix}"
                            memory["id"] = new_id
                        # overwrite 策略：直接覆盖，不需要特殊处理

                    # 确保记忆有必要的字段
                    if not memory.get("timestamp"):
                        memory["timestamp"] = datetime.now(timezone.utc).isoformat()

                    if not memory.get("layer"):
                        memory["layer"] = target_layer

                    # 添加导入标记
                    if "metadata" not in memory:
                        memory["metadata"] = {}
                    memory["metadata"]["imported"] = True
                    memory["metadata"]["import_timestamp"] = datetime.now(timezone.utc).isoformat()
                    memory["metadata"]["import_source"] = str(import_path)

                    # 添加到现有记忆列表
                    existing_memories.append(memory)
                    layer_imported += 1

                except Exception as e:
                    logger.error(f"导入记忆时出错: {e}")
                    layer_errors += 1

            # 保存更新后的记忆层
            if layer_imported > 0:
                try:
                    _save_memory_layer(target_layer, existing_memories)
                    logger.info(f"成功导入 {layer_imported} 条记忆到层 {target_layer}")
                except Exception as e:
                    logger.error(f"保存记忆层 {target_layer} 时出错: {e}")
                    layer_errors += layer_imported
                    layer_imported = 0

            import_stats[target_layer] = {"imported": layer_imported, "skipped": layer_skipped, "errors": layer_errors}

            imported_count += layer_imported
            skipped_count += layer_skipped
            error_count += layer_errors

        # 更新记忆索引
        try:
            from .intelligent_memory_retrieval import rebuild_memory_index

            rebuild_memory_index()
        except Exception as e:
            logger.warning(f"重建记忆索引时出错: {e}")

        result = {
            "success": True,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "error_count": error_count,
            "layer_stats": import_stats,
            "merge_strategy": merge_strategy,
            "source_file": str(import_path),
        }

        logger.info(f"记忆导入完成：导入 {imported_count} 条，跳过 {skipped_count} 条，错误 {error_count} 条")
        return result

    except Exception as e:
        logger.error(f"导入记忆时出错: {e}")
        return {"success": False, "error": str(e), "imported_count": 0}


def migrate_memories(
    source_project: str, target_project: str, memory_types: Optional[List[str]] = None, preserve_timestamps: bool = True
) -> Dict[str, Any]:
    """
    跨项目记忆迁移

    Args:
        source_project: 源项目名称或路径
        target_project: 目标项目名称或路径
        memory_types: 要迁移的记忆类型列表，默认迁移所有
        preserve_timestamps: 是否保留原时间戳

    Returns:
        迁移结果
    """
    try:
        # 导出源项目记忆
        export_file = f"temp_export_{source_project}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_result = export_memories(layers=["project"], output_file=export_file, include_metadata=True)

        if not export_result.get("success", False):
            return {"success": False, "error": f"导出源项目记忆失败: {export_result.get('error', 'Unknown error')}"}

        # 过滤记忆类型
        if memory_types:
            # 重新读取导出文件并过滤
            with open(export_file, encoding="utf-8") as f:
                export_data = json.load(f)

            filtered_memories = []
            for memory in export_data.get("memories", {}).get("project", []):
                memory_type = memory.get("metadata", {}).get("type", "")
                if memory_type in memory_types:
                    filtered_memories.append(memory)

            export_data["memories"]["project"] = filtered_memories

            # 保存过滤后的数据
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        # 导入到目标项目
        import_result = import_memories(
            import_file=export_file, target_layers={"project": "project"}, merge_strategy="append_suffix"
        )

        # 清理临时文件
        try:
            os.remove(export_file)
        except Exception:
            pass

        if import_result.get("success", False):
            return {
                "success": True,
                "migrated_count": import_result.get("imported_count", 0),
                "source_project": source_project,
                "target_project": target_project,
                "memory_types": memory_types or "all",
            }
        else:
            return {"success": False, "error": f"导入目标项目失败: {import_result.get('error', 'Unknown error')}"}

    except Exception as e:
        logger.error(f"记忆迁移时出错: {e}")
        return {"success": False, "error": str(e)}
