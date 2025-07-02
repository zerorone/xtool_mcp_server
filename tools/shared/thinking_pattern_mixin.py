"""
Thinking Pattern Mixin - Universal thinking pattern integration for all tools

This mixin provides thinking pattern capabilities to any tool, enabling:
- Automatic pattern selection based on tool type and context
- Default pattern combinations for each tool category
- Pattern effectiveness tracking and learning
- Cross-tool pattern sharing and insights
"""

import logging

# from abc import ABC  # 移除ABC导入，这是一个Mixin类
from typing import Any, Optional

from utils.conversation_memory import recall_memory, save_memory
from utils.thinking_patterns import ThinkingPattern, thinking_registry

logger = logging.getLogger(__name__)


class ThinkingPatternMixin:
    """
    Mixin class that adds thinking pattern capabilities to any tool.

    This mixin can be added to any tool to provide intelligent thinking pattern
    selection and application without modifying the tool's core functionality.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.applied_patterns: list[ThinkingPattern] = []
        self.pattern_insights: dict[str, Any] = {}
        self._pattern_performance: dict[str, float] = {}
        # Configuration for thinking pattern behavior
        self._thinking_mode = "enhance_only"  # Options: "enhance_only", "full_ai"

    def get_default_thinking_patterns(self) -> list[str]:
        """
        Get default thinking patterns for this tool type.
        Should be overridden by each tool to define its optimal patterns.
        """
        tool_name = self.get_name() if hasattr(self, "get_name") else self.__class__.__name__.lower()

        # Default pattern combinations for each tool type
        tool_patterns = {
            "planner": [
                "Systems Thinking",
                "Strategic Planning",
                "Decomposition Analysis",
                "Risk Assessment",
                "Sequential Logic",
            ],
            "debug": [
                "Root Cause Analysis",
                "Pattern Recognition",
                "Hypothesis Testing",
                "Systematic Investigation",
                "Critical Thinking",
            ],
            "codereview": [
                "Critical Thinking",
                "Pattern Recognition",
                "Best Practices Analysis",
                "Risk Assessment",
                "Quality Assurance",
            ],
            "thinkdeep": ["Deep Analysis", "Multi-Perspective", "Synthesis", "Meta-Cognitive", "Philosophical Inquiry"],
            "analyze": [
                "Systematic Investigation",
                "Pattern Recognition",
                "Data Analysis",
                "Correlation Analysis",
                "Evidence-Based Reasoning",
            ],
            "refactor": [
                "Architecture Analysis",
                "Pattern Recognition",
                "Design Principles",
                "Impact Assessment",
                "Quality Optimization",
            ],
        }

        return tool_patterns.get(tool_name, ["Critical Thinking", "Pattern Recognition"])

    def select_thinking_patterns(
        self, context: str, problem_type: Optional[str] = None, max_patterns: int = 3
    ) -> list[ThinkingPattern]:
        """
        Select appropriate thinking patterns based on context and tool type.

        Args:
            context: The problem context or user input
            problem_type: Optional specific problem type
            max_patterns: Maximum number of patterns to select

        Returns:
            List of selected thinking patterns
        """
        # Get default patterns for this tool
        default_pattern_names = self.get_default_thinking_patterns()

        # Load pattern performance data from memory
        self._load_pattern_performance()

        # Auto-select patterns using registry
        auto_patterns = thinking_registry.select_patterns(
            context=context, problem_type=problem_type, max_patterns=max_patterns
        )

        # Combine default patterns with auto-selected ones
        combined_patterns = []
        pattern_names_seen = set()

        # First, add default patterns (high priority)
        for pattern_name in default_pattern_names[:max_patterns]:
            pattern = thinking_registry.get_pattern(pattern_name)
            if pattern and pattern.name not in pattern_names_seen:
                combined_patterns.append(pattern)
                pattern_names_seen.add(pattern.name)

        # Fill remaining slots with auto-selected patterns
        for pattern in auto_patterns:
            if len(combined_patterns) >= max_patterns:
                break
            if pattern.name not in pattern_names_seen:
                combined_patterns.append(pattern)
                pattern_names_seen.add(pattern.name)

        # Apply performance-based ranking
        if self._pattern_performance:
            combined_patterns.sort(key=lambda p: self._pattern_performance.get(p.name, 0.5), reverse=True)

        self.applied_patterns = combined_patterns[:max_patterns]
        logger.info(
            f"Selected patterns for {self.get_name() if hasattr(self, 'get_name') else 'tool'}: "
            f"{[p.name for p in self.applied_patterns]}"
        )

        return self.applied_patterns

    def apply_thinking_patterns(self, base_prompt: str, context: str) -> str:
        """
        Apply selected thinking patterns to enhance the base prompt.

        Args:
            base_prompt: The tool's original system prompt
            context: Current problem context

        Returns:
            Enhanced prompt with thinking pattern integration
        """
        if not self.applied_patterns:
            return base_prompt

        # Build pattern-enhanced prompt
        pattern_instructions = []

        for i, pattern in enumerate(self.applied_patterns, 1):
            pattern_section = f"""
## Thinking Pattern {i}: {pattern.name}

**Approach**: {pattern.description}

**Apply this pattern by**:
{pattern.prompt_template}

**Focus Areas**: {", ".join(pattern.strengths)}
"""
            pattern_instructions.append(pattern_section)

        enhanced_prompt = f"""{base_prompt}

# THINKING PATTERN INTEGRATION

You are now enhanced with {len(self.applied_patterns)} specialized thinking patterns optimized for this task type.
Apply these patterns to deepen your analysis and improve solution quality:

{"".join(pattern_instructions)}

## Integration Guidelines:
1. **Sequential Application**: Apply each pattern's approach in the order presented
2. **Synthesis**: Combine insights from all patterns for comprehensive analysis
3. **Validation**: Use patterns to cross-check and validate your reasoning
4. **Adaptation**: Adjust pattern application based on emerging insights

## Pattern Effectiveness Tracking:
Track how each pattern contributes to your analysis quality. Note which patterns:
- Reveal new insights or perspectives
- Help identify issues or opportunities
- Improve solution robustness
- Guide decision-making

Remember: These patterns enhance your natural capabilities - use them as cognitive tools to achieve deeper, more thorough analysis.
"""

        return enhanced_prompt

    def track_pattern_effectiveness(self, pattern_name: str, effectiveness: float, insights: dict[str, Any]) -> None:
        """
        Track the effectiveness of a thinking pattern for learning.

        Args:
            pattern_name: Name of the pattern
            effectiveness: Effectiveness score (0.0 to 1.0)
            insights: Dictionary of insights gained from this pattern
        """
        self.pattern_insights[pattern_name] = {
            "effectiveness": effectiveness,
            "insights": insights,
            "context": getattr(self, "_current_context", ""),
            "tool": self.get_name() if hasattr(self, "get_name") else self.__class__.__name__,
        }

        # Update performance tracking
        self._pattern_performance[pattern_name] = effectiveness

        # Save to memory for cross-session learning
        memory_entry = {
            "type": "pattern_effectiveness",
            "pattern_name": pattern_name,
            "effectiveness": effectiveness,
            "tool": self.get_name() if hasattr(self, "get_name") else self.__class__.__name__,
            "insights": insights,
        }

        try:
            save_memory(
                content=memory_entry,
                layer="project",
                metadata={"tags": ["thinking_patterns", "effectiveness", pattern_name.lower().replace(" ", "_")]},
            )
        except Exception as e:
            logger.warning(f"Failed to save pattern effectiveness to memory: {e}")

    def get_pattern_recommendations(self, context: str) -> dict[str, Any]:
        """
        Get recommendations for pattern usage based on historical effectiveness.

        Args:
            context: Current problem context

        Returns:
            Dictionary with pattern recommendations and insights
        """
        self._load_pattern_performance()

        # Get patterns for this tool type
        default_patterns = self.get_default_thinking_patterns()

        recommendations = {"recommended_patterns": [], "performance_data": self._pattern_performance, "insights": {}}

        # Score patterns based on performance and context match
        pattern_scores = {}
        for pattern_name in default_patterns:
            pattern = thinking_registry.get_pattern(pattern_name)
            if pattern:
                context_score = pattern.matches_context(context)
                performance_score = self._pattern_performance.get(pattern_name, 0.5)
                combined_score = (context_score * 0.6) + (performance_score * 0.4)
                pattern_scores[pattern_name] = combined_score

        # Sort by combined score
        sorted_patterns = sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True)
        recommendations["recommended_patterns"] = [p[0] for p in sorted_patterns[:5]]

        return recommendations

    def _load_pattern_performance(self) -> None:
        """Load pattern performance data from memory."""
        try:
            memories = recall_memory(query="pattern effectiveness", layer="project", limit=50)

            pattern_scores = {}
            pattern_counts = {}

            for memory in memories:
                content = memory.get("content", {})
                if isinstance(content, str):
                    try:
                        import json

                        content = json.loads(content)
                    except json.JSONDecodeError:
                        continue

                pattern_name = content.get("pattern_name")
                effectiveness = content.get("effectiveness", 0.5)

                if pattern_name:
                    if pattern_name not in pattern_scores:
                        pattern_scores[pattern_name] = 0
                        pattern_counts[pattern_name] = 0

                    pattern_scores[pattern_name] += effectiveness
                    pattern_counts[pattern_name] += 1

            # Calculate average effectiveness for each pattern
            for pattern_name in pattern_scores:
                if pattern_counts[pattern_name] > 0:
                    avg_effectiveness = pattern_scores[pattern_name] / pattern_counts[pattern_name]
                    self._pattern_performance[pattern_name] = avg_effectiveness

        except Exception as e:
            logger.warning(f"Failed to load pattern performance data: {e}")

    def synthesize_pattern_insights(self) -> dict[str, Any]:
        """
        Synthesize insights from all applied patterns.

        Returns:
            Dictionary containing synthesized insights and recommendations
        """
        if not self.pattern_insights:
            return {}

        synthesis = {
            "patterns_applied": [p.name for p in self.applied_patterns],
            "key_insights": [],
            "cross_pattern_connections": [],
            "recommendations": [],
            "effectiveness_summary": {},
        }

        # Extract key insights
        for pattern_name, data in self.pattern_insights.items():
            insights = data.get("insights", {})
            effectiveness = data.get("effectiveness", 0.5)

            synthesis["effectiveness_summary"][pattern_name] = effectiveness

            if isinstance(insights, dict):
                for key, value in insights.items():
                    synthesis["key_insights"].append({"pattern": pattern_name, "insight_type": key, "content": value})

        # Find cross-pattern connections
        pattern_categories = {}
        for pattern in self.applied_patterns:
            category = pattern.category.value
            if category not in pattern_categories:
                pattern_categories[category] = []
            pattern_categories[category].append(pattern.name)

        synthesis["cross_pattern_connections"] = pattern_categories

        return synthesis

    def set_thinking_mode(self, mode: str) -> None:
        """
        Set the thinking pattern behavior mode.

        Args:
            mode: Either "enhance_only" or "full_ai"
                - "enhance_only": Only enhance prompts, return to Claude Code
                - "full_ai": Use tool's own AI model for complete analysis
        """
        if mode not in ["enhance_only", "full_ai"]:
            raise ValueError(f"Invalid thinking mode: {mode}. Use 'enhance_only' or 'full_ai'")
        self._thinking_mode = mode

    def get_thinking_mode(self) -> str:
        """Get the current thinking pattern behavior mode."""
        return self._thinking_mode

    def should_use_internal_ai(self) -> bool:
        """
        Determine if the tool should use its internal AI model or return enhanced prompt.

        Returns:
            bool: True if tool should use internal AI, False if should return to Claude Code
        """
        return self._thinking_mode == "full_ai"

    def create_enhanced_prompt_response(self, base_content: str, context: str) -> dict[str, Any]:
        """
        Create a response with enhanced prompt for Claude Code to process.

        Args:
            base_content: The base tool content/instruction
            context: Current problem context

        Returns:
            Dictionary containing enhanced prompt and metadata for Claude Code
        """
        enhanced_prompt = self.apply_thinking_patterns(base_content, context)

        return {
            "type": "enhanced_prompt",
            "content": enhanced_prompt,
            "thinking_patterns": {
                "applied": [p.name for p in self.applied_patterns],
                "categories": list({p.category.value for p in self.applied_patterns}),
                "descriptions": {p.name: p.description for p in self.applied_patterns},
            },
            "original_content": base_content,
            "context": context,
            "instructions": {
                "for_claude_code": "This content has been enhanced with specialized thinking patterns. "
                "Apply these cognitive approaches to provide deeper, more thorough analysis.",
                "pattern_guidance": "Use the thinking patterns as cognitive tools to enhance your reasoning process.",
            },
        }
