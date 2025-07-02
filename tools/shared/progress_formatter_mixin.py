"""
Progress Formatter Mixin - Shared progress table formatting for workflow tools

This mixin provides consistent progress table formatting capabilities for all workflow tools,
enabling them to display progress in a standardized table format with phase and total progress tracking.
"""

import logging

# from abc import ABC  # 移除ABC导入，这是一个Mixin类
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ProgressFormatterMixin:
    """
    Mixin class that adds progress table formatting capabilities to workflow tools.

    This mixin provides:
    - Markdown-formatted progress tables
    - Phase progress tracking
    - Total progress calculation
    - Time estimation
    - Issue/finding statistics
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_time = None
        self._phase_times = {}

    def format_progress_table(
        self,
        step_number: int,
        total_steps: int,
        phase_name: str,
        next_step_required: bool,
        findings_summary: str = "",
        files_examined: int = 0,
        relevant_files: int = 0,
        issues_found: Optional[dict[str, int]] = None,
        additional_stats: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Format workflow progress as a markdown table.

        Args:
            step_number: Current step number
            total_steps: Total number of steps
            phase_name: Name of the current phase
            next_step_required: Whether next step is needed
            findings_summary: Brief summary of findings
            files_examined: Number of files examined
            relevant_files: Number of relevant files found
            issues_found: Dictionary of issue counts by severity
            additional_stats: Additional statistics to display

        Returns:
            Markdown-formatted progress table
        """
        # Initialize start time if not set
        if self._start_time is None:
            self._start_time = datetime.now()

        # Calculate progress percentages
        phase_progress = (step_number / max(total_steps, 1)) * 100
        total_progress = phase_progress  # Can be weighted differently if needed

        # Estimate remaining time
        time_estimate = self._estimate_remaining_time(step_number, total_steps)

        # Determine phase status
        phase_status = "🔄 进行中" if next_step_required else "✅ 完成"

        # Build main progress table
        table = f"""
## 📊 工作流进度报告

| 工作阶段 | 状态 | 阶段进度 | 总进度 | 预计剩余时间 |
|---------|------|----------|--------|-------------|
| {phase_name} | {phase_status} | {phase_progress:.1f}% | {total_progress:.1f}% | {time_estimate} |
"""

        # Add detailed progress section
        table += f"""
### 📈 详细进度
- **当前步骤**: {step_number}/{total_steps}
- **下一步需要**: {"是" if next_step_required else "否"}
- **已用时间**: {self._format_elapsed_time()}
"""

        # Add file statistics if applicable
        if files_examined > 0 or relevant_files > 0:
            table += f"""
### 📁 文件统计
- **检查文件数**: {files_examined}
- **相关文件数**: {relevant_files}
- **相关性比例**: {(relevant_files / max(files_examined, 1) * 100):.1f}%
"""

        # Add issues/findings breakdown if provided
        if issues_found:
            table += self._format_issues_table(issues_found)

        # Add findings summary if provided
        if findings_summary:
            table += f"""
### 🔍 当前发现摘要
{findings_summary[:500]}{"..." if len(findings_summary) > 500 else ""}
"""

        # Add additional statistics if provided
        if additional_stats:
            table += self._format_additional_stats(additional_stats)

        return table

    def _estimate_remaining_time(self, current_step: int, total_steps: int) -> str:
        """Estimate remaining time based on current progress."""
        if current_step == 0:
            return "计算中..."

        elapsed_time = (datetime.now() - self._start_time).total_seconds()
        avg_time_per_step = elapsed_time / current_step
        remaining_steps = total_steps - current_step
        estimated_remaining = avg_time_per_step * remaining_steps

        if estimated_remaining < 60:
            return f"{int(estimated_remaining)}秒"
        elif estimated_remaining < 3600:
            return f"{int(estimated_remaining / 60)}分钟"
        else:
            return f"{estimated_remaining / 3600:.1f}小时"

    def _format_elapsed_time(self) -> str:
        """Format elapsed time since start."""
        if self._start_time is None:
            return "未知"

        elapsed = (datetime.now() - self._start_time).total_seconds()

        if elapsed < 60:
            return f"{int(elapsed)}秒"
        elif elapsed < 3600:
            return f"{int(elapsed / 60)}分钟{int(elapsed % 60)}秒"
        else:
            hours = int(elapsed / 3600)
            minutes = int((elapsed % 3600) / 60)
            return f"{hours}小时{minutes}分钟"

    def _format_issues_table(self, issues: dict[str, int]) -> str:
        """Format issues/findings as a table."""
        table = "\n### ⚠️ 问题/发现统计\n| 严重程度 | 数量 |\n|---------|------|\n"

        # Define severity order
        severity_order = ["critical", "high", "medium", "low", "info"]
        severity_emojis = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}

        total_issues = 0
        for severity in severity_order:
            if severity in issues and issues[severity] > 0:
                emoji = severity_emojis.get(severity, "")
                table += f"| {emoji} {severity.upper()} | {issues[severity]} |\n"
                total_issues += issues[severity]

        if total_issues > 0:
            table += f"| **总计** | **{total_issues}** |\n"

        return table

    def _format_additional_stats(self, stats: dict[str, Any]) -> str:
        """Format additional statistics as a section."""
        content = "\n### 📊 其他统计\n"

        for key, value in stats.items():
            # Convert key from snake_case to readable format
            readable_key = key.replace("_", " ").title()

            # Format value based on type
            if isinstance(value, (int, float)):
                if isinstance(value, float):
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
            elif isinstance(value, bool):
                formatted_value = "是" if value else "否"
            elif isinstance(value, list):
                formatted_value = f"{len(value)} 项"
            elif isinstance(value, dict):
                formatted_value = f"{len(value)} 项"
            else:
                formatted_value = str(value)

            content += f"- **{readable_key}**: {formatted_value}\n"

        return content

    def get_phase_name_for_tool(self, tool_type: str, step_number: int, total_steps: int) -> str:
        """
        Get phase name based on tool type and progress.

        This method should be overridden by specific tools to provide
        their own phase naming logic.

        Args:
            tool_type: Type of tool (debug, codereview, etc.)
            step_number: Current step number
            total_steps: Total number of steps

        Returns:
            Phase name string
        """
        # Default phase names for common tool types
        default_phases = {
            "debug": ["问题识别", "根因分析", "假设验证", "解决方案", "验证修复"],
            "codereview": ["代码扫描", "模式识别", "问题分析", "改进建议", "报告生成"],
            "refactor": ["代码分析", "重构识别", "影响评估", "重构执行", "验证测试"],
            "secaudit": ["安全扫描", "漏洞检测", "风险评估", "修复建议", "合规检查"],
            "precommit": ["变更扫描", "验证检查", "测试运行", "合规审查", "提交准备"],
            "testgen": ["代码分析", "测试设计", "边界识别", "测试生成", "覆盖验证"],
            "docgen": ["代码扫描", "文档分析", "内容生成", "格式优化", "完成验证"],
        }

        phases = default_phases.get(tool_type, ["初始化", "处理中", "深度分析", "综合评估", "完成"])

        # Map step number to phase
        phase_index = min((step_number - 1) * len(phases) // total_steps, len(phases) - 1)
        return phases[phase_index]

    def create_summary_progress_table(
        self, completed_phases: int, total_phases: int, phase_details: Optional[dict[str, dict[str, Any]]] = None
    ) -> str:
        """
        Create a summary progress table showing overall workflow progress.

        Args:
            completed_phases: Number of completed phases
            total_phases: Total number of phases
            phase_details: Optional details for each phase

        Returns:
            Markdown-formatted summary table
        """
        overall_progress = (completed_phases / max(total_phases, 1)) * 100

        table = f"""
## 📊 总体工作流进度

**完成进度**: {overall_progress:.0f}% ({completed_phases}/{total_phases} 阶段)

| 阶段 | 状态 | 完成度 | 耗时 |
|------|------|--------|------|
"""

        if phase_details:
            for phase_name, details in phase_details.items():
                status = details.get("status", "待处理")
                completion = details.get("completion", 0)
                duration = details.get("duration", "-")

                status_emoji = {"完成": "✅", "进行中": "🔄", "待处理": "⏳", "跳过": "⏭️", "失败": "❌"}.get(
                    status, "❓"
                )

                table += f"| {phase_name} | {status_emoji} {status} | {completion}% | {duration} |\n"

        return table

    def track_phase_time(self, phase_name: str, is_start: bool = True) -> None:
        """
        Track time for individual phases.

        Args:
            phase_name: Name of the phase
            is_start: True if starting phase, False if ending
        """
        if is_start:
            self._phase_times[phase_name] = {"start": datetime.now(), "end": None, "duration": None}
        else:
            if phase_name in self._phase_times:
                self._phase_times[phase_name]["end"] = datetime.now()
                duration = (
                    self._phase_times[phase_name]["end"] - self._phase_times[phase_name]["start"]
                ).total_seconds()
                self._phase_times[phase_name]["duration"] = duration

    def get_phase_statistics(self) -> dict[str, Any]:
        """Get statistics about phase execution times."""
        stats = {
            "total_phases": len(self._phase_times),
            "completed_phases": sum(1 for p in self._phase_times.values() if p.get("end")),
            "average_phase_time": 0,
            "longest_phase": None,
            "shortest_phase": None,
        }

        completed_durations = [
            (name, p["duration"]) for name, p in self._phase_times.items() if p.get("duration") is not None
        ]

        if completed_durations:
            durations_only = [d[1] for d in completed_durations]
            stats["average_phase_time"] = sum(durations_only) / len(durations_only)

            longest = max(completed_durations, key=lambda x: x[1])
            shortest = min(completed_durations, key=lambda x: x[1])

            stats["longest_phase"] = {"name": longest[0], "duration": longest[1]}
            stats["shortest_phase"] = {"name": shortest[0], "duration": shortest[1]}

        return stats
