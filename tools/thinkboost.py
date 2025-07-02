"""
ThinkBoost Tool - Enhance Claude Code's thinking with specialized patterns

This tool provides Claude Code with enhanced prompts using specialized thinking patterns.
It operates as a pure MCP tool that returns structured guidance for Claude Code to follow.
"""

import logging
from typing import Any

from mcp.types import TextContent

from tools.models import ToolModelCategory, ToolOutput
from tools.shared.base_models import ToolRequest
from tools.shared.base_tool import BaseTool
from tools.shared.thinking_pattern_mixin import ThinkingPatternMixin

logger = logging.getLogger(__name__)


class ThinkBoostTool(BaseTool, ThinkingPatternMixin):
    """
    ThinkBoost - Enhance Claude Code's thinking with specialized patterns.

    This tool provides structured thinking guidance to Claude Code rather than
    performing AI analysis itself. It's designed for pure MCP interaction.
    """

    def __init__(self):
        super().__init__()
        # Always use enhance_only mode for Claude Code interaction
        self._thinking_mode = "enhance_only"
        # Initialize pattern tracking from mixin
        self.applied_patterns = []
        self.pattern_insights = {}
        self._pattern_performance = {}

    def get_name(self) -> str:
        return "thinkboost"

    def get_description(self) -> str:
        return (
            "THINKBOOST - Enhance Claude Code's thinking with specialized patterns. "
            "Provides structured thinking guidance and cognitive frameworks for deeper analysis. "
            "Returns enhanced prompts and thinking strategies directly to Claude Code. "
            "Supports debugging, planning, analysis, design, and problem-solving contexts."
        )

    def get_input_schema(self) -> dict[str, Any]:
        """Return input schema for ThinkBoost."""
        return {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The task or problem you want thinking enhancement for"},
                "context": {"type": "string", "description": "Additional context about the problem domain"},
                "focus_area": {
                    "type": "string",
                    "enum": ["debugging", "planning", "analysis", "design", "architecture", "optimization", "review"],
                    "description": "Primary focus area for pattern selection",
                },
                "patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: Specific thinking patterns to apply (if empty, auto-selected)",
                },
            },
            "required": ["task"],
        }

    def requires_model(self) -> bool:
        """ThinkBoost doesn't need AI models - it enhances Claude Code's thinking."""
        return False

    def get_model_category(self) -> ToolModelCategory:
        return ToolModelCategory.FAST_RESPONSE

    async def prepare_prompt(self, request: ToolRequest) -> str:
        """Not used - ThinkBoost provides direct guidance."""
        return ""

    def format_response(self, response: str, request: ToolRequest, model_info: dict = None) -> str:
        """Not used - ThinkBoost provides direct guidance."""
        return response

    def get_request_model(self):
        """Return the request model."""
        return ToolRequest

    def get_system_prompt(self) -> str:
        """Return system prompt - not used since we don't call AI models."""
        return "ThinkBoost provides thinking pattern enhancement directly to Claude Code."

    def get_default_thinking_patterns(self) -> list[str]:
        """Get default patterns for general thinking enhancement."""
        return [
            "Critical Thinking",
            "Systematic Investigation",
            "Pattern Recognition",
            "Root Cause Analysis",
            "Multi-Perspective",
        ]

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute ThinkBoost to provide thinking enhancement to Claude Code."""

        # Extract arguments
        task = arguments.get("task", "")
        context = arguments.get("context", "")
        focus_area = arguments.get("focus_area", "analysis")
        manual_patterns = arguments.get("patterns", [])

        # Combine task and context for pattern selection
        full_context = f"{task} {context}".strip()

        # Select thinking patterns
        if manual_patterns:
            # Use manually specified patterns
            from utils.thinking_patterns import thinking_registry

            selected_patterns = []
            for pattern_name in manual_patterns:
                # Convert to the internal format (lowercase with underscores)
                internal_name = pattern_name.lower().replace(" ", "_")
                pattern = thinking_registry.get_pattern(internal_name)
                if pattern:
                    selected_patterns.append(pattern)
                else:
                    # Try exact match as fallback
                    pattern = thinking_registry.get_pattern(pattern_name)
                    if pattern:
                        selected_patterns.append(pattern)
            self.applied_patterns = selected_patterns
        else:
            # Auto-select based on focus area and context
            self.select_thinking_patterns(full_context, focus_area, max_patterns=3)

        # Create enhanced thinking guidance for Claude Code
        guidance = self._create_thinking_guidance(task, context, focus_area)

        # Create tool output
        tool_output = ToolOutput(
            status="success",
            content=guidance,
            content_type="text",
            metadata={
                "tool_name": self.get_name(),
                "tool_type": "thinking_enhancement",
                "applied_patterns": [p.name for p in self.applied_patterns],
                "focus_area": focus_area,
                "pattern_count": len(self.applied_patterns),
            },
        )

        return [TextContent(type="text", text=tool_output.model_dump_json())]

    def _create_thinking_guidance(self, task: str, context: str, focus_area: str) -> str:
        """Create structured thinking guidance for Claude Code."""

        guidance_parts = []

        # Header
        guidance_parts.append("# 🧠 ThinkBoost Enhanced Analysis Framework")
        guidance_parts.append(f"**Task**: {task}")
        if context:
            guidance_parts.append(f"**Context**: {context}")
        guidance_parts.append(f"**Focus Area**: {focus_area}")
        guidance_parts.append("")

        # Applied thinking patterns
        if self.applied_patterns:
            guidance_parts.append("## 🎯 Applied Thinking Patterns")
            guidance_parts.append("")

            for i, pattern in enumerate(self.applied_patterns, 1):
                guidance_parts.append(f"### Pattern {i}: {pattern.name}")
                guidance_parts.append(f"**Category**: {pattern.category.value}")
                guidance_parts.append(f"**Description**: {pattern.description}")
                guidance_parts.append("")
                guidance_parts.append("**Apply this pattern by**:")
                guidance_parts.append(pattern.prompt_template)
                guidance_parts.append("")
                guidance_parts.append(f"**Key Strengths**: {', '.join(pattern.strengths)}")
                guidance_parts.append(f"**Best Used For**: {', '.join(pattern.use_cases)}")
                guidance_parts.append("")

        # Structured analysis framework
        guidance_parts.append("## 📋 Structured Analysis Framework")
        guidance_parts.append("")

        framework_steps = {
            "debugging": [
                "1. **Problem Definition**: Clearly state the issue and its symptoms",
                "2. **Information Gathering**: Collect relevant data, logs, and context",
                "3. **Hypothesis Formation**: Generate possible explanations based on patterns",
                "4. **Systematic Investigation**: Test hypotheses methodically",
                "5. **Root Cause Identification**: Trace back to fundamental causes",
                "6. **Solution Development**: Design and validate fixes",
            ],
            "planning": [
                "1. **Goal Clarification**: Define clear, measurable objectives",
                "2. **Scope Analysis**: Understand boundaries and constraints",
                "3. **Decomposition**: Break down into manageable components",
                "4. **Dependency Mapping**: Identify relationships and sequences",
                "5. **Risk Assessment**: Evaluate potential challenges and mitigation",
                "6. **Resource Planning**: Allocate time, people, and tools effectively",
            ],
            "analysis": [
                "1. **Context Understanding**: Grasp the full scope and background",
                "2. **Data Collection**: Gather all relevant information systematically",
                "3. **Pattern Recognition**: Identify trends, anomalies, and relationships",
                "4. **Critical Evaluation**: Question assumptions and validate findings",
                "5. **Synthesis**: Combine insights into coherent understanding",
                "6. **Recommendations**: Propose actionable next steps",
            ],
        }

        steps = framework_steps.get(focus_area, framework_steps["analysis"])
        for step in steps:
            guidance_parts.append(step)
        guidance_parts.append("")

        # Integration instructions
        guidance_parts.append("## 🔄 Pattern Integration Guidelines")
        guidance_parts.append("")
        guidance_parts.append(
            "**Sequential Application**: Apply each thinking pattern in order, building insights progressively"
        )
        guidance_parts.append("**Cross-Validation**: Use different patterns to verify and strengthen conclusions")
        guidance_parts.append("**Adaptive Focus**: Adjust pattern emphasis based on emerging insights")
        guidance_parts.append("**Synthesis**: Combine pattern outputs for comprehensive understanding")
        guidance_parts.append("")

        # Quality checklist
        guidance_parts.append("## ✅ Quality Validation Checklist")
        guidance_parts.append("")
        guidance_parts.append("- [ ] All thinking patterns have been systematically applied")
        guidance_parts.append("- [ ] Multiple perspectives have been considered")
        guidance_parts.append("- [ ] Assumptions have been explicitly identified and questioned")
        guidance_parts.append("- [ ] Evidence supports all major conclusions")
        guidance_parts.append("- [ ] Alternative explanations have been explored")
        guidance_parts.append("- [ ] Practical implications and next steps are clear")

        return "\n".join(guidance_parts)
