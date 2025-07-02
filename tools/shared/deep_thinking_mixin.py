"""
深度思维模式混合类 - 为所有工具提供智能思维模式选择和应用

这个混合类提供了一个统一的接口，让所有工具都能够根据其类型和上下文
自动选择并应用最合适的思维模式组合。
"""

import json
import logging
from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from config_data.thinking_patterns_config import (
    THINKING_PATTERNS_TOOLBOX,
    ToolThinkingMode,
    get_pattern_details,
    get_thinking_patterns_for_mode,
    suggest_patterns_for_context,
)
from utils.conversation_memory import recall_memory, save_memory

logger = logging.getLogger(__name__)


class ThinkingModeStrategy(Enum):
    """思维模式选择策略"""

    TOOL_DEFAULT = "tool_default"  # 使用工具默认配置
    CONTEXT_BASED = "context_based"  # 基于上下文分析
    AI_POWERED = "ai_powered"  # 使用AI模型推荐
    HISTORICAL = "historical"  # 基于历史效果
    HYBRID = "hybrid"  # 混合策略


class DeepThinkingMixin(ABC):
    """
    深度思维模式混合类

    为任何工具提供智能思维模式选择、应用和学习能力。
    支持基于工具类型、上下文、历史数据和AI推荐的多种选择策略。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tool_thinking_mode = None
        self._applied_patterns = []
        self._pattern_insights = {}
        self._pattern_effectiveness = {}
        self._selection_strategy = ThinkingModeStrategy.HYBRID
        self._thinking_start_time = None
        self._pattern_application_times = {}

    def set_tool_thinking_mode(self, mode: ToolThinkingMode) -> None:
        """
        设置工具的思维模式

        Args:
            mode: 工具思维模式枚举值
        """
        self._tool_thinking_mode = mode
        logger.info(f"Tool thinking mode set to: {mode.value}")

    def get_tool_thinking_mode(self) -> ToolThinkingMode:
        """
        获取工具的思维模式，如果未设置则根据工具名称推断

        Returns:
            工具思维模式
        """
        if self._tool_thinking_mode:
            return self._tool_thinking_mode

        # 根据工具名称推断
        tool_name = self.get_name() if hasattr(self, "get_name") else ""
        mode_mapping = {
            "debug": ToolThinkingMode.DEBUG,
            "analyze": ToolThinkingMode.ANALYZE,
            "codereview": ToolThinkingMode.CODEREVIEW,
            "refactor": ToolThinkingMode.REFACTOR,
            "planner": ToolThinkingMode.PLANNER,
            "secaudit": ToolThinkingMode.SECAUDIT,
            "testgen": ToolThinkingMode.TESTGEN,
            "docgen": ToolThinkingMode.DOCGEN,
            "precommit": ToolThinkingMode.PRECOMMIT,
            "thinkdeep": ToolThinkingMode.THINKDEEP,
            "consensus": ToolThinkingMode.CONSENSUS,
            "tracer": ToolThinkingMode.TRACER,
            "chat": ToolThinkingMode.CHAT,
        }

        self._tool_thinking_mode = mode_mapping.get(tool_name, ToolThinkingMode.AUTO)
        return self._tool_thinking_mode

    def select_thinking_patterns(
        self,
        context: str,
        problem_type: Optional[str] = None,
        max_patterns: int = 5,
        strategy: Optional[ThinkingModeStrategy] = None,
    ) -> list[dict[str, Any]]:
        """
        选择适合的思维模式

        Args:
            context: 问题上下文
            problem_type: 问题类型（可选）
            max_patterns: 最大选择数量
            strategy: 选择策略（可选，默认使用混合策略）

        Returns:
            选中的思维模式详细信息列表
        """
        strategy = strategy or self._selection_strategy
        self._thinking_start_time = datetime.now()

        if strategy == ThinkingModeStrategy.TOOL_DEFAULT:
            patterns = self._select_by_tool_default(max_patterns)
        elif strategy == ThinkingModeStrategy.CONTEXT_BASED:
            patterns = self._select_by_context(context, problem_type, max_patterns)
        elif strategy == ThinkingModeStrategy.AI_POWERED:
            patterns = self._select_by_ai(context, problem_type, max_patterns)
        elif strategy == ThinkingModeStrategy.HISTORICAL:
            patterns = self._select_by_history(context, problem_type, max_patterns)
        else:  # HYBRID
            patterns = self._select_hybrid(context, problem_type, max_patterns)

        self._applied_patterns = patterns
        logger.info(f"Selected {len(patterns)} thinking patterns: {[p['name'] for p in patterns]}")

        return patterns

    def _select_by_tool_default(self, max_patterns: int) -> list[dict[str, Any]]:
        """基于工具默认配置选择思维模式"""
        mode = self.get_tool_thinking_mode()
        pattern_names = get_thinking_patterns_for_mode(mode, max_patterns)

        patterns = []
        for name in pattern_names:
            details = get_pattern_details(name)
            if details:
                patterns.append(details)

        return patterns

    def _select_by_context(self, context: str, problem_type: Optional[str], max_patterns: int) -> list[dict[str, Any]]:
        """基于上下文分析选择思维模式"""
        # 使用配置中的推荐函数
        pattern_names = suggest_patterns_for_context(context, problem_type)

        # 如果上下文推荐不足，补充工具默认模式
        if len(pattern_names) < max_patterns:
            default_patterns = self._select_by_tool_default(max_patterns - len(pattern_names))
            for p in default_patterns:
                if p["name"] not in pattern_names:
                    pattern_names.append(p["name"])

        patterns = []
        for name in pattern_names[:max_patterns]:
            details = get_pattern_details(name)
            if details:
                patterns.append(details)

        return patterns

    def _select_by_ai(self, context: str, problem_type: Optional[str], max_patterns: int) -> list[dict[str, Any]]:
        """使用AI模型推荐思维模式（需要实现）"""
        # TODO: 实现AI推荐逻辑
        # 暂时回退到混合策略
        logger.info("AI-powered selection not yet implemented, falling back to context-based")
        return self._select_by_context(context, problem_type, max_patterns)

    def _select_by_history(self, context: str, problem_type: Optional[str], max_patterns: int) -> list[dict[str, Any]]:
        """基于历史效果选择思维模式"""
        # 加载历史效果数据
        tool_name = self.get_name() if hasattr(self, "get_name") else "unknown"
        memories = recall_memory(
            query=f"thinking pattern effectiveness {tool_name}", filters={"type": "pattern_effectiveness"}, limit=50
        )

        # 分析历史效果
        pattern_scores = {}
        for memory in memories:
            content = memory.get("content", {})
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    continue

            pattern_name = content.get("pattern_name")
            effectiveness = content.get("effectiveness", 0.5)

            if pattern_name:
                if pattern_name not in pattern_scores:
                    pattern_scores[pattern_name] = []
                pattern_scores[pattern_name].append(effectiveness)

        # 计算平均效果
        avg_scores = {}
        for name, scores in pattern_scores.items():
            avg_scores[name] = sum(scores) / len(scores)

        # 选择效果最好的模式
        sorted_patterns = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)

        patterns = []
        for name, _ in sorted_patterns[:max_patterns]:
            details = get_pattern_details(name)
            if details:
                patterns.append(details)

        # 如果历史数据不足，补充默认模式
        if len(patterns) < max_patterns:
            default_patterns = self._select_by_tool_default(max_patterns - len(patterns))
            for p in default_patterns:
                if not any(ep["name"] == p["name"] for ep in patterns):
                    patterns.append(p)

        return patterns

    def _select_hybrid(self, context: str, problem_type: Optional[str], max_patterns: int) -> list[dict[str, Any]]:
        """混合策略选择思维模式"""
        all_patterns = {}
        weights = {}

        # 1. 工具默认模式（40%权重）
        default_patterns = self._select_by_tool_default(max_patterns * 2)
        for i, p in enumerate(default_patterns):
            all_patterns[p["name"]] = p
            weights[p["name"]] = weights.get(p["name"], 0) + 0.4 * (1 - i / len(default_patterns))

        # 2. 上下文推荐（30%权重）
        context_patterns = self._select_by_context(context, problem_type, max_patterns)
        for i, p in enumerate(context_patterns):
            all_patterns[p["name"]] = p
            weights[p["name"]] = weights.get(p["name"], 0) + 0.3 * (1 - i / len(context_patterns))

        # 3. 历史效果（30%权重）
        history_patterns = self._select_by_history(context, problem_type, max_patterns)
        for i, p in enumerate(history_patterns):
            all_patterns[p["name"]] = p
            weights[p["name"]] = weights.get(p["name"], 0) + 0.3 * (1 - i / len(history_patterns))

        # 按权重排序并选择
        sorted_patterns = sorted(weights.items(), key=lambda x: x[1], reverse=True)

        patterns = []
        for name, _ in sorted_patterns[:max_patterns]:
            if name in all_patterns:
                patterns.append(all_patterns[name])

        return patterns

    def apply_thinking_patterns(self, base_prompt: str, context: str = "") -> str:
        """
        应用选中的思维模式到提示词

        Args:
            base_prompt: 基础提示词
            context: 额外上下文（可选）

        Returns:
            增强后的提示词
        """
        if not self._applied_patterns:
            return base_prompt

        # 构建思维模式增强部分
        pattern_sections = []

        pattern_sections.append("# 🧠 思维模式增强")
        pattern_sections.append(f"\n您现在配备了 {len(self._applied_patterns)} 种专业思维模式来增强分析能力：\n")

        for i, pattern in enumerate(self._applied_patterns, 1):
            self._pattern_application_times[pattern["name"]] = datetime.now()

            section = f"""
## 思维模式 {i}: {pattern["name"]}

**方法描述**: {pattern["description"]}
**核心优势**: {", ".join(pattern["strengths"])}
**适用场景**: {", ".join(pattern["use_cases"])}

**应用指南**:
1. 运用{pattern["name"]}的核心方法分析问题
2. 关注其优势领域：{pattern["strengths"][0]}
3. 特别适合处理：{pattern["use_cases"][0]}
"""
            pattern_sections.append(section)

        # 添加综合应用指导
        pattern_sections.append("""
## 🔄 思维模式综合应用

1. **顺序应用**: 按照上述顺序依次应用每种思维模式
2. **交叉验证**: 使用不同模式验证和补充分析结果
3. **综合洞察**: 整合所有模式的发现，形成全面理解
4. **冲突解决**: 如果不同模式得出矛盾结论，深入分析原因
5. **效果追踪**: 记录哪些模式产生了关键洞察

## 💡 思维增强目标

- 提供更深入、更全面的分析
- 发现隐藏的模式和关系
- 产生创新的解决方案
- 避免认知偏见和盲点
- 提高决策质量
""")

        # 组合最终提示词
        enhanced_prompt = base_prompt + "\n\n" + "\n".join(pattern_sections)

        if context:
            enhanced_prompt += f"\n\n## 📋 具体上下文\n{context}"

        return enhanced_prompt

    def track_pattern_effectiveness(
        self, pattern_name: str, effectiveness_score: float, insights: dict[str, Any], context: Optional[str] = None
    ) -> None:
        """
        跟踪思维模式的效果

        Args:
            pattern_name: 模式名称
            effectiveness_score: 效果分数(0-1)
            insights: 产生的洞察
            context: 应用上下文
        """
        self._pattern_effectiveness[pattern_name] = effectiveness_score
        self._pattern_insights[pattern_name] = insights

        # 计算应用时长
        duration = None
        if pattern_name in self._pattern_application_times:
            duration = (datetime.now() - self._pattern_application_times[pattern_name]).total_seconds()

        # 保存到记忆系统
        tool_name = self.get_name() if hasattr(self, "get_name") else "unknown"
        memory_content = {
            "tool": tool_name,
            "pattern_name": pattern_name,
            "effectiveness": effectiveness_score,
            "insights": insights,
            "context": context or "",
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            save_memory(
                content=json.dumps(memory_content),
                layer="project",
                metadata={"type": "pattern_effectiveness", "tool": tool_name, "pattern": pattern_name},
            )
        except Exception as e:
            logger.warning(f"Failed to save pattern effectiveness: {e}")

    def get_pattern_performance_report(self) -> dict[str, Any]:
        """
        获取思维模式性能报告

        Returns:
            包含性能统计的字典
        """
        total_duration = (
            (datetime.now() - self._thinking_start_time).total_seconds() if self._thinking_start_time else 0
        )

        pattern_stats = []
        for pattern in self._applied_patterns:
            name = pattern["name"]
            stats = {
                "name": name,
                "category": pattern["category"],
                "effectiveness": self._pattern_effectiveness.get(name, 0),
                "insights_count": len(self._pattern_insights.get(name, {})),
                "duration": None,
            }

            if name in self._pattern_application_times:
                stats["duration"] = (datetime.now() - self._pattern_application_times[name]).total_seconds()

            pattern_stats.append(stats)

        return {
            "total_patterns": len(self._applied_patterns),
            "total_duration": total_duration,
            "average_effectiveness": sum(self._pattern_effectiveness.values()) / len(self._pattern_effectiveness)
            if self._pattern_effectiveness
            else 0,
            "pattern_stats": pattern_stats,
            "selection_strategy": self._selection_strategy.value,
            "tool_mode": self.get_tool_thinking_mode().value,
        }

    def synthesize_pattern_insights(self) -> dict[str, Any]:
        """
        综合所有思维模式的洞察

        Returns:
            综合洞察报告
        """
        synthesis = {
            "applied_patterns": [p["name"] for p in self._applied_patterns],
            "key_insights": [],
            "pattern_synergies": [],
            "contradictions": [],
            "recommendations": [],
        }

        # 收集所有洞察
        all_insights = []
        for pattern_name, insights in self._pattern_insights.items():
            if isinstance(insights, dict):
                for key, value in insights.items():
                    all_insights.append({"pattern": pattern_name, "type": key, "content": value})

        synthesis["key_insights"] = all_insights

        # 识别模式协同
        pattern_categories = {}
        for pattern in self._applied_patterns:
            category = pattern["category"]
            if category not in pattern_categories:
                pattern_categories[category] = []
            pattern_categories[category].append(pattern["name"])

        for category, patterns in pattern_categories.items():
            if len(patterns) > 1:
                synthesis["pattern_synergies"].append(
                    {"category": category, "patterns": patterns, "synergy_type": f"{category}类思维模式互补强化"}
                )

        # 生成建议
        if self._pattern_effectiveness:
            best_pattern = max(self._pattern_effectiveness.items(), key=lambda x: x[1])
            synthesis["recommendations"].append(f"建议优先使用{best_pattern[0]}（效果评分：{best_pattern[1]:.2f}）")

        return synthesis

    def format_thinking_progress_table(self) -> str:
        """
        格式化思维模式应用进度表

        Returns:
            Markdown格式的进度表
        """
        if not self._applied_patterns:
            return ""

        table = """
## 🧠 思维模式应用进度

| 思维模式 | 类别 | 应用状态 | 效果评分 | 洞察数量 |
|---------|------|---------|---------|---------|
"""

        for pattern in self._applied_patterns:
            name = pattern["name"]
            category = pattern["category"]
            status = "✅ 已应用" if name in self._pattern_effectiveness else "🔄 应用中"
            effectiveness = (
                f"{self._pattern_effectiveness.get(name, 0):.2f}" if name in self._pattern_effectiveness else "-"
            )
            insights_count = len(self._pattern_insights.get(name, {}))

            table += f"| {name} | {category} | {status} | {effectiveness} | {insights_count} |\n"

        # 添加汇总
        avg_effectiveness = (
            sum(self._pattern_effectiveness.values()) / len(self._pattern_effectiveness)
            if self._pattern_effectiveness
            else 0
        )
        total_insights = sum(len(insights) for insights in self._pattern_insights.values())

        table += f"\n**平均效果**: {avg_effectiveness:.2f} | **总洞察数**: {total_insights}\n"

        return table

    def set_selection_strategy(self, strategy: ThinkingModeStrategy) -> None:
        """设置思维模式选择策略"""
        self._selection_strategy = strategy
        logger.info(f"Thinking pattern selection strategy set to: {strategy.value}")

    def get_recommended_patterns_for_next_step(self, current_context: str, current_findings: str) -> list[str]:
        """
        为下一步推荐思维模式

        Args:
            current_context: 当前上下文
            current_findings: 当前发现

        Returns:
            推荐的思维模式名称列表
        """
        # 分析当前进展
        combined_context = f"{current_context} {current_findings}"

        # 基于当前进展推荐新模式
        new_patterns = suggest_patterns_for_context(combined_context)

        # 过滤已使用的模式
        used_patterns = [p["name"] for p in self._applied_patterns]
        recommended = [p for p in new_patterns if p not in used_patterns]

        # 如果推荐不足，基于效果推荐
        if len(recommended) < 3:
            # 推荐效果好的模式的相关模式
            if self._pattern_effectiveness:
                best_patterns = sorted(self._pattern_effectiveness.items(), key=lambda x: x[1], reverse=True)
                for pattern_name, _ in best_patterns[:2]:
                    pattern_info = get_pattern_details(pattern_name)
                    if pattern_info:
                        # 找相同类别的其他模式
                        category = pattern_info["category"]
                        for name, details in THINKING_PATTERNS_TOOLBOX.items():
                            if (
                                details["category"] == category
                                and name not in used_patterns
                                and name not in recommended
                            ):
                                recommended.append(name)
                                if len(recommended) >= 3:
                                    break

        return recommended[:5]
