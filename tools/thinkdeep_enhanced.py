"""
Enhanced ThinkDeep Tool - Integrated with 25 Thinking Patterns

This enhanced version of ThinkDeep automatically selects and applies the most
appropriate thinking patterns based on the problem context. It integrates with
the memory system to learn from past pattern usage and effectiveness.

Key Enhancements:
- Automatic thinking pattern selection
- Pattern effectiveness tracking
- Integration with memory system for learning
- Multi-pattern synthesis for complex problems
- Pattern usage analytics
"""

import json
import logging
from typing import Optional

from pydantic import Field

from utils.conversation_memory import recall_memory, save_memory
from utils.thinking_patterns import thinking_registry

from .thinkdeep import ThinkDeepTool, ThinkDeepWorkflowRequest

logger = logging.getLogger(__name__)


class EnhancedThinkDeepRequest(ThinkDeepWorkflowRequest):
    """Enhanced request model with pattern selection capabilities"""

    # Pattern selection fields
    selected_patterns: Optional[list[str]] = Field(
        default=None,
        description="Manually selected thinking patterns to apply. If not provided, patterns will be auto-selected.",
    )
    problem_type: Optional[str] = Field(
        default=None,
        description="Type of problem (e.g., debugging, architecture, optimization) for better pattern selection",
    )
    pattern_synthesis: Optional[bool] = Field(
        default=True, description="Whether to synthesize insights from multiple patterns"
    )


class EnhancedThinkDeepTool(ThinkDeepTool):
    """
    Enhanced ThinkDeep with Integrated Thinking Patterns

    This tool extends the original ThinkDeep with intelligent pattern selection
    and application, creating a more powerful reasoning engine.
    """

    def __init__(self):
        super().__init__()
        self.applied_patterns = []
        self.pattern_insights = {}

    def get_workflow_request_model(self):
        """Return the enhanced request model"""
        return EnhancedThinkDeepRequest

    def select_thinking_patterns(self, request: EnhancedThinkDeepRequest) -> list:
        """
        Select appropriate thinking patterns based on context
        """
        if request.selected_patterns:
            # Use manually selected patterns
            patterns = []
            for pattern_name in request.selected_patterns:
                pattern = thinking_registry.get_pattern(pattern_name)
                if pattern:
                    patterns.append(pattern)
            return patterns

        # Auto-select patterns based on context
        context = f"{request.problem_context or ''} {request.step}"
        problem_type = request.problem_type or self._infer_problem_type(request)

        # Get recommended patterns
        patterns = thinking_registry.select_patterns(
            context=context, problem_type=problem_type, max_patterns=3 if request.pattern_synthesis else 1
        )

        # Learn from past pattern usage
        self._enhance_pattern_selection_with_memory(patterns, problem_type)

        return patterns

    def _infer_problem_type(self, request: EnhancedThinkDeepRequest) -> str:
        """
        Infer problem type from context and focus areas
        """
        context_lower = (request.problem_context or "").lower()
        focus_areas = request.focus_areas or []

        # Problem type detection logic
        if any(word in context_lower for word in ["bug", "error", "issue", "fix"]):
            return "debugging"
        elif any(word in context_lower for word in ["design", "architecture", "structure"]):
            return "architecture"
        elif any(word in context_lower for word in ["performance", "optimize", "speed"]):
            return "optimization"
        elif any(word in context_lower for word in ["review", "validate", "check"]):
            return "review"
        elif any(word in context_lower for word in ["plan", "strategy", "roadmap"]):
            return "planning"
        elif "security" in focus_areas:
            return "security"
        else:
            return "problem_solving"

    def _enhance_pattern_selection_with_memory(self, patterns: list, problem_type: str):
        """
        Enhance pattern selection using historical effectiveness data
        """
        # Recall past pattern usage for similar problems
        memories = recall_memory(
            query=f"thinking pattern {problem_type}", filters={"type": "pattern_effectiveness"}, limit=20
        )

        if memories:
            # Analyze historical effectiveness
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

            # Calculate average effectiveness
            avg_scores = {name: sum(scores) / len(scores) for name, scores in pattern_scores.items()}

            # Re-order patterns based on historical effectiveness
            patterns.sort(key=lambda p: avg_scores.get(p.name, 0.5), reverse=True)

    def apply_thinking_patterns(self, request: EnhancedThinkDeepRequest) -> str:
        """
        Apply selected thinking patterns to generate enhanced insights
        """
        patterns = self.select_thinking_patterns(request)
        self.applied_patterns = patterns

        if not patterns:
            return ""  # Fallback to standard thinkdeep

        # Apply each pattern
        pattern_prompts = []
        for pattern in patterns:
            prompt = f"\n=== Applying {pattern.name.upper()} Pattern ===\n"
            prompt += pattern.prompt_template
            prompt += f"\n\nFocus on: {', '.join(pattern.strengths)}"
            pattern_prompts.append(prompt)

            # Track pattern application
            self.pattern_insights[pattern.name] = {
                "category": pattern.category.value,
                "use_cases": pattern.use_cases,
                "applied_to": request.problem_context or "general analysis",
            }

        # Combine pattern prompts
        combined_prompt = "\n\n".join(pattern_prompts)

        if request.pattern_synthesis and len(patterns) > 1:
            combined_prompt += "\n\n=== PATTERN SYNTHESIS ===\n"
            combined_prompt += "Synthesize insights from all applied thinking patterns:\n"
            combined_prompt += "1. Identify common themes and reinforcing insights\n"
            combined_prompt += "2. Resolve any conflicting recommendations\n"
            combined_prompt += "3. Create unified approach combining strengths of each pattern\n"
            combined_prompt += "4. Highlight unique insights from each pattern"

        return combined_prompt

    def get_system_prompt(self) -> str:
        """Enhanced system prompt with pattern awareness"""
        base_prompt = super().get_system_prompt()

        enhancement = """

THINKING PATTERN INTEGRATION:
You have access to 25 expert thinking patterns that can enhance your analysis:
- Analytical: First Principles, Systems, Critical, Analytical, Computational, Vertical, Inductive, Deductive
- Creative: Creative, Design, Lateral, Reverse, Analogical
- Strategic: Strategic, Business, Product
- Practical: Engineering, Agile, Lean, Modular, Concrete, User
- Systems: Systems, Holistic, Data

When specific patterns are applied, follow their structured approaches while maintaining
your deep thinking workflow. Synthesize insights across patterns for comprehensive analysis.

Track which patterns prove most effective for different problem types to improve future selection."""

        return base_prompt + enhancement

    def customize_workflow_response(self, response_data: dict, request, **kwargs) -> dict:
        """Add pattern-specific information to response"""
        response_data = super().customize_workflow_response(response_data, request, **kwargs)

        # Add pattern information
        if self.applied_patterns:
            response_data["thinking_patterns"] = {
                "applied": [p.name for p in self.applied_patterns],
                "categories": list({p.category.value for p in self.applied_patterns}),
                "insights": self.pattern_insights,
            }

        # Save pattern effectiveness on completion
        if not request.next_step_required and self.applied_patterns:
            self._save_pattern_effectiveness(request)

        return response_data

    def _save_pattern_effectiveness(self, request: EnhancedThinkDeepRequest):
        """
        Save pattern effectiveness data for future learning
        """
        problem_type = request.problem_type or self._infer_problem_type(request)

        # Calculate effectiveness based on confidence and findings
        effectiveness = self._calculate_effectiveness(request)

        for pattern in self.applied_patterns:
            memory_content = {
                "pattern_name": pattern.name,
                "problem_type": problem_type,
                "context": request.problem_context,
                "confidence": request.confidence,
                "effectiveness": effectiveness,
                "issues_found": len(request.issues_found),
                "insights_generated": len(request.relevant_context),
            }

            save_memory(
                content=json.dumps(memory_content),
                layer="global",
                metadata={"type": "pattern_effectiveness", "pattern": pattern.name, "problem_type": problem_type},
            )

    def _calculate_effectiveness(self, request: EnhancedThinkDeepRequest) -> float:
        """
        Calculate pattern effectiveness score (0-1)
        """
        score = 0.0

        # Confidence contribution (40%)
        confidence_scores = {
            "certain": 1.0,
            "almost_certain": 0.9,
            "very_high": 0.8,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.3,
            "exploring": 0.1,
        }
        score += confidence_scores.get(request.confidence, 0.5) * 0.4

        # Insights contribution (30%)
        insights_score = min(len(request.relevant_context) / 10, 1.0)
        score += insights_score * 0.3

        # Issues found contribution (20%)
        issues_score = min(len(request.issues_found) / 5, 1.0)
        score += issues_score * 0.2

        # Completion contribution (10%)
        if not request.next_step_required:
            score += 0.1

        return min(score, 1.0)

    def customize_expert_analysis_prompt(self, base_prompt: str, request, file_content: str = "") -> str:
        """Enhanced expert analysis with pattern context"""
        enhanced_prompt = super().customize_expert_analysis_prompt(base_prompt, request, file_content)

        if self.applied_patterns:
            pattern_context = "\n\nAPPLIED THINKING PATTERNS:\n"
            for pattern in self.applied_patterns:
                pattern_context += f"- {pattern.name}: {pattern.description}\n"

            pattern_context += (
                "\nConsider how well these patterns were applied and suggest alternative patterns if appropriate."
            )

            enhanced_prompt = pattern_context + "\n" + enhanced_prompt

        return enhanced_prompt

    def prepare_expert_analysis_context(self, consolidated_findings) -> str:
        """Add pattern usage to expert analysis context"""
        context = super().prepare_expert_analysis_context(consolidated_findings)

        if self.applied_patterns:
            context += "\n\nTHINKING PATTERNS APPLIED:"
            for pattern in self.applied_patterns:
                context += f"\n- {pattern.name} ({pattern.category.value})"
                if pattern.name in self.pattern_insights:
                    insights = self.pattern_insights[pattern.name]
                    context += f" - Applied to: {insights.get('applied_to', 'unknown')}"

        return context

    def get_step_guidance_message(self, request) -> str:
        """Enhanced guidance with pattern suggestions"""
        base_guidance = super().get_step_guidance_message(request)

        if request.next_step_required and not self.applied_patterns:
            # Suggest patterns for next step
            patterns = self.select_thinking_patterns(request)
            if patterns:
                base_guidance += (
                    f"\n\nSuggested thinking patterns for next step: {', '.join(p.name for p in patterns[:2])}"
                )

        return base_guidance
