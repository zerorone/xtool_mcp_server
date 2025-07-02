"""
增强版调试工具 - 集成智能思维模式

这是一个示例，展示如何将增强思维混合类集成到现有的调试工具中，
提供更智能的问题分析和根因定位能力。
"""

from typing import TYPE_CHECKING, Optional

from pydantic import Field

if TYPE_CHECKING:
    pass

import logging

from config_data.thinking_patterns_config import ToolThinkingMode
from tools.debug import DebugIssueTool, DebugWorkflowRequest
from tools.shared.deep_thinking_mixin import DeepThinkingMixin, ThinkingModeStrategy

logger = logging.getLogger(__name__)


class EnhancedDebugRequest(DebugWorkflowRequest):
    """增强的调试请求，包含思维模式配置"""

    # 思维模式相关字段
    enable_thinking_patterns: Optional[bool] = Field(default=True, description="是否启用思维模式增强")
    thinking_strategy: Optional[str] = Field(
        default="hybrid", description="思维模式选择策略：tool_default, context_based, ai_powered, historical, hybrid"
    )
    custom_patterns: Optional[list[str]] = Field(default=None, description="自定义思维模式列表（覆盖自动选择）")


class EnhancedDebugTool(DebugIssueTool, DeepThinkingMixin):
    """
    增强版调试工具，集成智能思维模式

    通过应用多种思维模式（如根因分析、系统思维、假设驱动等），
    提供更深入的问题分析和更准确的根因定位。
    """

    def __init__(self):
        super().__init__()
        # 设置工具的思维模式
        self.set_tool_thinking_mode(ToolThinkingMode.DEBUG)

    def get_workflow_request_model(self):
        """返回增强的请求模型"""
        return EnhancedDebugRequest

    def get_system_prompt(self) -> str:
        """获取增强的系统提示词"""
        base_prompt = super().get_system_prompt()

        # 添加思维模式感知
        enhancement = """

## 🧠 思维模式增强能力

你现在具备了多种专业的调试思维模式：
- **根因分析**: 深入挖掘问题的根本原因，而不是表面症状
- **系统思维**: 理解问题在整个系统中的位置和影响
- **假设驱动**: 形成可验证的假设并系统地测试
- **逆向思维**: 从错误结果反推可能的原因
- **批判性思维**: 质疑假设，验证证据

在调试过程中，灵活运用这些思维模式来：
1. 更准确地定位问题根源
2. 避免陷入调试死胡同
3. 发现隐藏的相关问题
4. 提出更有效的解决方案
"""

        return base_prompt + enhancement

    def prepare_step_data(self, request: EnhancedDebugRequest) -> dict:
        """准备步骤数据，包含思维模式应用"""
        step_data = super().prepare_step_data(request)

        # 如果启用思维模式
        if request.enable_thinking_patterns:
            # 应用思维模式增强
            self._apply_thinking_enhancement(request, step_data)

        return step_data

    def _apply_thinking_enhancement(self, request: EnhancedDebugRequest, step_data: dict) -> None:
        """应用思维模式增强"""
        # 确定选择策略
        strategy_map = {
            "tool_default": ThinkingModeStrategy.TOOL_DEFAULT,
            "context_based": ThinkingModeStrategy.CONTEXT_BASED,
            "ai_powered": ThinkingModeStrategy.AI_POWERED,
            "historical": ThinkingModeStrategy.HISTORICAL,
            "hybrid": ThinkingModeStrategy.HYBRID,
        }
        strategy = strategy_map.get(request.thinking_strategy, ThinkingModeStrategy.HYBRID)
        self.set_selection_strategy(strategy)

        # 构建上下文
        context = f"{request.step} {request.hypothesis or ''} {' '.join(request.files_checked)}"

        # 选择思维模式
        if request.custom_patterns:
            # 使用自定义模式
            from config.thinking_patterns_config import get_pattern_details

            patterns = []
            for pattern_name in request.custom_patterns:
                details = get_pattern_details(pattern_name)
                if details:
                    patterns.append(details)
            self._applied_patterns = patterns
        else:
            # 自动选择
            patterns = self.select_thinking_patterns(context=context, problem_type="debugging", max_patterns=3)

        # 记录选择的模式
        logger.info(f"Debug step {request.step_number} using thinking patterns: {[p['name'] for p in patterns]}")

    def customize_workflow_response(self, response_data: dict, request: EnhancedDebugRequest, **kwargs) -> dict:
        """自定义响应，添加思维模式信息"""
        response_data = super().customize_workflow_response(response_data, request, **kwargs)

        if request.enable_thinking_patterns and self._applied_patterns:
            # 添加思维模式信息
            response_data["thinking_patterns"] = {
                "applied": [p["name"] for p in self._applied_patterns],
                "strategy": request.thinking_strategy,
                "insights": self._pattern_insights,
            }

            # 如果是最后一步，生成思维模式报告
            if not request.next_step_required:
                response_data["thinking_report"] = self.get_pattern_performance_report()
                response_data["thinking_synthesis"] = self.synthesize_pattern_insights()

                # 保存效果数据
                self._save_thinking_effectiveness(request)

        return response_data

    def _save_thinking_effectiveness(self, request: EnhancedDebugRequest) -> None:
        """保存思维模式效果数据"""
        # 计算总体效果分数
        effectiveness_score = self._calculate_debug_effectiveness(request)

        # 为每个应用的模式保存效果
        for pattern in self._applied_patterns:
            insights = self._pattern_insights.get(pattern["name"], {})
            self.track_pattern_effectiveness(
                pattern_name=pattern["name"],
                effectiveness_score=effectiveness_score,
                insights=insights,
                context=f"Debug: {request.hypothesis}",
            )

    def _calculate_debug_effectiveness(self, request: EnhancedDebugRequest) -> float:
        """计算调试效果分数"""
        score = 0.0

        # 基于置信度（40%权重）
        confidence_map = {
            "certain": 1.0,
            "almost_certain": 0.9,
            "very_high": 0.8,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.3,
            "exploring": 0.1,
        }
        score += confidence_map.get(request.confidence, 0.5) * 0.4

        # 基于发现的问题数量（30%权重）
        issues_score = min(len(request.issues_found) / 3, 1.0)
        score += issues_score * 0.3

        # 基于步骤效率（20%权重）
        efficiency_score = max(0, 1 - (request.step_number - 1) / 10)
        score += efficiency_score * 0.2

        # 基于是否找到根因（10%权重）
        if not request.next_step_required and request.confidence in ["certain", "almost_certain"]:
            score += 0.1

        return min(score, 1.0)

    def get_step_guidance_message(self, request: EnhancedDebugRequest) -> str:
        """获取增强的步骤指导"""
        base_guidance = super().get_step_guidance_message(request)

        if request.enable_thinking_patterns and request.next_step_required:
            # 添加思维模式建议
            current_context = f"{request.hypothesis} {' '.join(request.findings[-100:])}"
            recommended_patterns = self.get_recommended_patterns_for_next_step(
                current_context=current_context, current_findings=request.findings
            )

            if recommended_patterns:
                pattern_guidance = f"\n\n💡 **建议的思维模式**：{', '.join(recommended_patterns[:3])}"
                base_guidance += pattern_guidance

        return base_guidance

    def prepare_expert_analysis_context(self, consolidated_findings) -> str:
        """准备专家分析上下文，包含思维模式信息"""
        context = super().prepare_expert_analysis_context(consolidated_findings)

        if self._applied_patterns:
            # 添加思维模式应用情况
            patterns_info = "\n\n### 应用的思维模式\n"
            for pattern in self._applied_patterns:
                patterns_info += f"- **{pattern['name']}**: {pattern['description']}\n"

            # 添加思维模式效果
            if self._pattern_effectiveness:
                patterns_info += "\n### 思维模式效果\n"
                for name, score in self._pattern_effectiveness.items():
                    patterns_info += f"- {name}: {score:.2f}\n"

            context += patterns_info

        return context

    def format_debug_progress_with_thinking(self, request: EnhancedDebugRequest) -> str:
        """格式化包含思维模式的调试进度"""
        # 使用父类的进度表格
        progress_table = self.format_progress_table(
            step_number=request.step_number,
            total_steps=request.total_steps,
            phase_name=self._get_debug_phase_name(request),
            next_step_required=request.next_step_required,
            findings_summary=request.findings,
            files_examined=len(request.files_checked),
            relevant_files=len(request.relevant_files),
            issues_found=self._count_issues_by_severity(request.issues_found),
        )

        # 添加思维模式进度
        if request.enable_thinking_patterns and self._applied_patterns:
            thinking_table = self.format_thinking_progress_table()
            progress_table += "\n" + thinking_table

        return progress_table

    def _get_debug_phase_name(self, request: EnhancedDebugRequest) -> str:
        """获取调试阶段名称"""
        phases = ["问题识别", "假设形成", "证据收集", "根因分析", "解决验证"]
        phase_index = min((request.step_number - 1) * len(phases) // request.total_steps, len(phases) - 1)
        return phases[phase_index]

    def _count_issues_by_severity(self, issues: list) -> dict:
        """统计问题严重程度"""
        severity_count = {}
        for issue in issues:
            severity = issue.get("severity", "unknown")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        return severity_count
