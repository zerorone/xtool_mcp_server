"""
AnalyzeWorkflow tool - Step-by-step code analysis with systematic investigation

This tool provides a structured workflow for comprehensive code and file analysis.
It guides the CLI agent through systematic investigation steps with forced pauses between each step
to ensure thorough code examination, pattern identification, and architectural assessment before proceeding.
The tool supports complex analysis scenarios including architectural review, performance analysis,
security assessment, and maintainability evaluation.

Key features:
- Step-by-step analysis workflow with progress tracking
- Context-aware file embedding (references during investigation, full content for analysis)
- Automatic pattern and insight tracking with categorization
- Expert analysis integration with external models
- Support for focused analysis (architecture, performance, security, quality)
- Confidence-based workflow optimization
"""

import logging
from typing import TYPE_CHECKING, Any, Literal, Optional

from pydantic import Field, model_validator

if TYPE_CHECKING:
    from tools.models import ToolModelCategory

from config import TEMPERATURE_ANALYTICAL
from systemprompts import ANALYZE_PROMPT
from tools.shared.base_models import WorkflowRequest

from .shared.progress_formatter_mixin import ProgressFormatterMixin
from .workflow.base import WorkflowTool

logger = logging.getLogger(__name__)

# Tool-specific field descriptions for analyze workflow
ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS = {
    "step": (
        "What to analyze or look for in this step. In step 1, describe what you want to analyze and begin forming "
        "an analytical approach after thinking carefully about what needs to be examined. Consider code quality, "
        "performance implications, architectural patterns, and design decisions. Map out the codebase structure, "
        "understand the business logic, and identify areas requiring deeper analysis. In later steps, continue "
        "exploring with precision and adapt your understanding as you uncover more insights."
    ),
    "step_number": (
        "The index of the current step in the analysis sequence, beginning at 1. Each step should build upon or "
        "revise the previous one."
    ),
    "total_steps": (
        "Your current estimate for how many steps will be needed to complete the analysis. "
        "Adjust as new findings emerge."
    ),
    "next_step_required": (
        "Set to true if you plan to continue the investigation with another step. False means you believe the "
        "analysis is complete and ready for expert validation."
    ),
    "findings": (
        "Summarize everything discovered in this step about the code being analyzed. Include analysis of architectural "
        "patterns, design decisions, tech stack assessment, scalability characteristics, performance implications, "
        "maintainability factors, security posture, and strategic improvement opportunities. Be specific and avoid "
        "vague language—document what you now know about the codebase and how it affects your assessment. "
        "IMPORTANT: Document both strengths (good patterns, solid architecture, well-designed components) and "
        "concerns (tech debt, scalability risks, overengineering, unnecessary complexity). In later steps, confirm "
        "or update past findings with additional evidence."
    ),
    "files_checked": (
        "List all files (as absolute paths, do not clip or shrink file names) examined during the analysis "
        "investigation so far. Include even files ruled out or found to be unrelated, as this tracks your "
        "exploration path."
    ),
    "relevant_files": (
        "Subset of files_checked (as full absolute paths) that contain code directly relevant to the analysis or "
        "contain significant patterns, architectural decisions, or examples worth highlighting. Only list those that are "
        "directly tied to important findings, architectural insights, performance characteristics, or strategic "
        "improvement opportunities. This could include core implementation files, configuration files, or files "
        "demonstrating key patterns."
    ),
    "relevant_context": (
        "List methods, functions, classes, or modules that are central to the analysis findings, in the format "
        "'ClassName.methodName', 'functionName', or 'module.ClassName'. Prioritize those that demonstrate important "
        "patterns, represent key architectural decisions, show performance characteristics, or highlight strategic "
        "improvement opportunities."
    ),
    "backtrack_from_step": (
        "If an earlier finding or assessment needs to be revised or discarded, specify the step number from which to "
        "start over. Use this to acknowledge investigative dead ends and correct the course."
    ),
    "images": (
        "Optional list of absolute paths to architecture diagrams, design documents, or visual references "
        "that help with analysis context. Only include if they materially assist understanding or assessment."
    ),
    "confidence": (
        "Your confidence level in the current analysis findings: exploring (early investigation), "
        "low (some insights but more needed), medium (solid understanding), high (comprehensive insights), "
        "very_high (very comprehensive insights), almost_certain (nearly complete analysis), "
        "certain (100% confidence - complete analysis ready for expert validation)"
    ),
    "analysis_type": "Type of analysis to perform (architecture, performance, security, quality, general)",
    "output_format": "How to format the output (summary, detailed, actionable)",
}


class AnalyzeWorkflowRequest(WorkflowRequest):
    """Request model for analyze workflow investigation steps"""

    # Required fields for each investigation step
    step: str = Field(..., description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["step"])
    step_number: int = Field(..., description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["step_number"])
    total_steps: int = Field(..., description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["total_steps"])
    next_step_required: bool = Field(..., description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["next_step_required"])

    # Investigation tracking fields
    findings: str = Field(..., description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["findings"])
    files_checked: list[str] = Field(
        default_factory=list, description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["files_checked"]
    )
    relevant_files: list[str] = Field(
        default_factory=list, description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["relevant_files"]
    )
    relevant_context: list[str] = Field(
        default_factory=list, description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["relevant_context"]
    )

    # Issues found during analysis (structured with severity)
    issues_found: list[dict] = Field(
        default_factory=list,
        description="Issues or concerns identified during analysis, each with severity level (critical, high, medium, low)",
    )

    # Optional backtracking field
    backtrack_from_step: Optional[int] = Field(
        None, description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["backtrack_from_step"]
    )

    # Optional images for visual context
    images: Optional[list[str]] = Field(default=None, description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["images"])

    # Analyze-specific fields (only used in step 1 to initialize)
    # Note: Use relevant_files field instead of files for consistency across workflow tools
    analysis_type: Optional[Literal["architecture", "performance", "security", "quality", "general"]] = Field(
        "general", description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["analysis_type"]
    )
    output_format: Optional[Literal["summary", "detailed", "actionable"]] = Field(
        "detailed", description=ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["output_format"]
    )

    # Keep thinking_mode and use_websearch from original analyze tool
    # temperature is inherited from WorkflowRequest

    @model_validator(mode="after")
    def validate_step_one_requirements(self):
        """Ensure step 1 has required relevant_files."""
        if self.step_number == 1:
            if not self.relevant_files:
                raise ValueError("Step 1 requires 'relevant_files' field to specify files or directories to analyze")
        return self


class AnalyzeTool(WorkflowTool, ProgressFormatterMixin):
    """
    Analyze workflow tool for step-by-step code analysis and expert validation.

    This tool implements a structured analysis workflow that guides users through
    methodical investigation steps, ensuring thorough code examination, pattern identification,
    and architectural assessment before reaching conclusions. It supports complex analysis scenarios
    including architectural review, performance analysis, security assessment, and maintainability evaluation.
    """

    def __init__(self):
        super().__init__()
        self.initial_request = None
        self.analysis_config = {}

    def get_name(self) -> str:
        return "analyze"

    def get_description(self) -> str:
        return (
            "COMPREHENSIVE ANALYSIS WORKFLOW - Step-by-step code analysis with expert validation. "
            "This tool guides you through a systematic investigation process where you:\n\n"
            "1. Start with step 1: describe your analysis investigation plan\n"
            "2. STOP and investigate code structure, patterns, and architectural decisions\n"
            "3. Report findings in step 2 with concrete evidence from actual code analysis\n"
            "4. Continue investigating between each step\n"
            "5. Track findings, relevant files, and insights throughout\n"
            "6. Update assessments as understanding evolves\n"
            "7. Once investigation is complete, always receive expert validation\n\n"
            "IMPORTANT: This tool enforces investigation between steps:\n"
            "- After each call, you MUST investigate before calling again\n"
            "- Each step must include NEW evidence from code examination\n"
            "- No recursive calls without actual investigation work\n"
            "- The tool will specify which step number to use next\n"
            "- Follow the required_actions list for investigation guidance\n\n"
            "Perfect for: comprehensive code analysis, architectural assessment, performance evaluation, "
            "security analysis, maintainability review, pattern detection, strategic planning."
        )

    def get_system_prompt(self) -> str:
        return ANALYZE_PROMPT

    def get_default_temperature(self) -> float:
        return TEMPERATURE_ANALYTICAL

    def get_model_category(self) -> "ToolModelCategory":
        """Analyze workflow requires thorough analysis and reasoning"""
        from tools.models import ToolModelCategory

        return ToolModelCategory.EXTENDED_REASONING

    def get_workflow_request_model(self):
        """Return the analyze workflow-specific request model."""
        return AnalyzeWorkflowRequest

    def get_input_schema(self) -> dict[str, Any]:
        """Generate input schema using WorkflowSchemaBuilder with analyze-specific overrides."""
        from .workflow.schema_builders import WorkflowSchemaBuilder

        # Fields to exclude from analyze workflow (inherited from WorkflowRequest but not used)
        excluded_fields = {"hypothesis", "confidence"}

        # Analyze workflow-specific field overrides
        analyze_field_overrides = {
            "step": {
                "type": "string",
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["step"],
            },
            "step_number": {
                "type": "integer",
                "minimum": 1,
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["step_number"],
            },
            "total_steps": {
                "type": "integer",
                "minimum": 1,
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["total_steps"],
            },
            "next_step_required": {
                "type": "boolean",
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["next_step_required"],
            },
            "findings": {
                "type": "string",
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["findings"],
            },
            "files_checked": {
                "type": "array",
                "items": {"type": "string"},
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["files_checked"],
            },
            "relevant_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["relevant_files"],
            },
            "confidence": {
                "type": "string",
                "enum": ["exploring", "low", "medium", "high", "very_high", "almost_certain", "certain"],
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["confidence"],
            },
            "backtrack_from_step": {
                "type": "integer",
                "minimum": 1,
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["backtrack_from_step"],
            },
            "images": {
                "type": "array",
                "items": {"type": "string"},
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["images"],
            },
            "issues_found": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Issues or concerns identified during analysis, each with severity level (critical, high, medium, low)",
            },
            "analysis_type": {
                "type": "string",
                "enum": ["architecture", "performance", "security", "quality", "general"],
                "default": "general",
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["analysis_type"],
            },
            "output_format": {
                "type": "string",
                "enum": ["summary", "detailed", "actionable"],
                "default": "detailed",
                "description": ANALYZE_WORKFLOW_FIELD_DESCRIPTIONS["output_format"],
            },
        }

        # Use WorkflowSchemaBuilder with analyze-specific tool fields
        return WorkflowSchemaBuilder.build_schema(
            tool_specific_fields=analyze_field_overrides,
            model_field_schema=self.get_model_field_schema(),
            auto_mode=self.is_effective_auto_mode(),
            tool_name=self.get_name(),
            excluded_workflow_fields=list(excluded_fields),
        )

    def get_required_actions(self, step_number: int, confidence: str, findings: str, total_steps: int) -> list[str]:
        """Define required actions for each investigation phase."""
        if step_number == 1:
            # Initial analysis investigation tasks
            return [
                "Read and understand the code files specified for analysis",
                "Map the tech stack, frameworks, and overall architecture",
                "Identify the main components, modules, and their relationships",
                "Understand the business logic and intended functionality",
                "Examine architectural patterns and design decisions used",
                "Look for strengths, risks, and strategic improvement areas",
            ]
        elif step_number < total_steps:
            # Need deeper investigation
            return [
                "Examine specific architectural patterns and design decisions in detail",
                "Analyze scalability characteristics and performance implications",
                "Assess maintainability factors: module cohesion, coupling, tech debt",
                "Identify security posture and potential systemic vulnerabilities",
                "Look for overengineering, unnecessary complexity, or missing abstractions",
                "Evaluate how well the architecture serves business and scaling goals",
            ]
        else:
            # Close to completion - need final verification
            return [
                "Verify all significant architectural insights have been documented",
                "Confirm strategic improvement opportunities are comprehensively captured",
                "Ensure both strengths and risks are properly identified with evidence",
                "Validate that findings align with the analysis type and goals specified",
                "Check that recommendations are actionable and proportional to the codebase",
                "Confirm the analysis provides clear guidance for strategic decisions",
            ]

    def should_call_expert_analysis(self, consolidated_findings, request=None) -> bool:
        """
        Always call expert analysis for comprehensive validation.

        Analysis benefits from a second opinion to ensure completeness.
        """
        # Check if user explicitly requested to skip assistant model
        if request and not self.get_request_use_assistant_model(request):
            return False

        # For analysis, we always want expert validation if we have any meaningful data
        return len(consolidated_findings.relevant_files) > 0 or len(consolidated_findings.findings) >= 1

    def prepare_expert_analysis_context(self, consolidated_findings) -> str:
        """Prepare context for external model call for final analysis validation."""
        context_parts = [
            f"=== ANALYSIS REQUEST ===\\n{self.initial_request or 'Code analysis workflow initiated'}\\n=== END REQUEST ==="
        ]

        # Add investigation summary
        investigation_summary = self._build_analysis_summary(consolidated_findings)
        context_parts.append(
            f"\\n=== AGENT'S ANALYSIS INVESTIGATION ===\\n{investigation_summary}\\n=== END INVESTIGATION ==="
        )

        # Add analysis configuration context if available
        if self.analysis_config:
            config_text = "\\n".join(f"- {key}: {value}" for key, value in self.analysis_config.items() if value)
            context_parts.append(f"\\n=== ANALYSIS CONFIGURATION ===\\n{config_text}\\n=== END CONFIGURATION ===")

        # Add relevant code elements if available
        if consolidated_findings.relevant_context:
            methods_text = "\\n".join(f"- {method}" for method in consolidated_findings.relevant_context)
            context_parts.append(f"\\n=== RELEVANT CODE ELEMENTS ===\\n{methods_text}\\n=== END CODE ELEMENTS ===")

        # Add assessment evolution if available
        if consolidated_findings.hypotheses:
            assessments_text = "\\n".join(
                f"Step {h['step']}: {h['hypothesis']}" for h in consolidated_findings.hypotheses
            )
            context_parts.append(f"\\n=== ASSESSMENT EVOLUTION ===\\n{assessments_text}\\n=== END ASSESSMENTS ===")

        # Add images if available
        if consolidated_findings.images:
            images_text = "\\n".join(f"- {img}" for img in consolidated_findings.images)
            context_parts.append(
                f"\\n=== VISUAL ANALYSIS INFORMATION ===\\n{images_text}\\n=== END VISUAL INFORMATION ==="
            )

        return "\\n".join(context_parts)

    def _build_analysis_summary(self, consolidated_findings) -> str:
        """Prepare a comprehensive summary of the analysis investigation."""
        summary_parts = [
            "=== SYSTEMATIC ANALYSIS INVESTIGATION SUMMARY ===",
            f"Total steps: {len(consolidated_findings.findings)}",
            f"Files examined: {len(consolidated_findings.files_checked)}",
            f"Relevant files identified: {len(consolidated_findings.relevant_files)}",
            f"Code elements analyzed: {len(consolidated_findings.relevant_context)}",
            "",
            "=== INVESTIGATION PROGRESSION ===",
        ]

        for finding in consolidated_findings.findings:
            summary_parts.append(finding)

        return "\\n".join(summary_parts)

    def should_include_files_in_expert_prompt(self) -> bool:
        """Include files in expert analysis for comprehensive validation."""
        return True

    def should_embed_system_prompt(self) -> bool:
        """Embed system prompt in expert analysis for proper context."""
        return True

    def get_expert_thinking_mode(self) -> str:
        """Use high thinking mode for thorough analysis."""
        return "high"

    def get_expert_analysis_instruction(self) -> str:
        """Get specific instruction for analysis expert validation."""
        return (
            "Please provide comprehensive analysis validation based on the investigation findings. "
            "Focus on identifying any remaining architectural insights, validating the completeness of the analysis, "
            "and providing final strategic recommendations following the structured format specified in the system prompt."
        )

    # Hook method overrides for analyze-specific behavior

    def prepare_step_data(self, request) -> dict:
        """
        Map analyze-specific fields for internal processing.
        """
        step_data = {
            "step": request.step,
            "step_number": request.step_number,
            "findings": request.findings,
            "files_checked": request.files_checked,
            "relevant_files": request.relevant_files,
            "relevant_context": request.relevant_context,
            "issues_found": request.issues_found,  # Analyze workflow uses issues_found for structured problem tracking
            "confidence": "medium",  # Fixed value for workflow compatibility
            "hypothesis": request.findings,  # Map findings to hypothesis for compatibility
            "images": request.images or [],
        }
        return step_data

    def should_skip_expert_analysis(self, request, consolidated_findings) -> bool:
        """
        Analyze workflow always uses expert analysis for comprehensive validation.

        Analysis benefits from a second opinion to ensure completeness and catch
        any missed insights or alternative perspectives.
        """
        return False

    def store_initial_issue(self, step_description: str):
        """Store initial request for expert analysis."""
        self.initial_request = step_description

    # Override inheritance hooks for analyze-specific behavior

    def get_completion_status(self) -> str:
        """Analyze tools use analysis-specific status."""
        return "analysis_complete_ready_for_implementation"

    def get_completion_data_key(self) -> str:
        """Analyze uses 'complete_analysis' key."""
        return "complete_analysis"

    def get_final_analysis_from_request(self, request):
        """Analyze tools use 'findings' field."""
        return request.findings

    def get_confidence_level(self, request) -> str:
        """Analyze tools use fixed confidence for consistency."""
        return "medium"

    def get_completion_message(self) -> str:
        """Analyze-specific completion message."""
        return (
            "Analysis complete. You have identified all significant patterns, "
            "architectural insights, and strategic opportunities. MANDATORY: Present the user with the complete "
            "analysis results organized by strategic impact, and IMMEDIATELY proceed with implementing the "
            "highest priority recommendations or provide specific guidance for improvements. Focus on actionable "
            "strategic insights."
        )

    def get_skip_reason(self) -> str:
        """Analyze-specific skip reason."""
        return "Completed comprehensive analysis locally"

    def get_skip_expert_analysis_status(self) -> str:
        """Analyze-specific expert analysis skip status."""
        return "skipped_due_to_complete_analysis"

    def prepare_work_summary(self) -> str:
        """Analyze-specific work summary."""
        return self._build_analysis_summary(self.consolidated_findings)

    def get_completion_next_steps_message(self, expert_analysis_used: bool = False) -> str:
        """
        Analyze-specific completion message.
        """
        base_message = (
            "ANALYSIS IS COMPLETE. You MUST now summarize and present ALL analysis findings organized by "
            "strategic impact (Critical → High → Medium → Low), specific architectural insights with code references, "
            "and exact recommendations for improvement. Clearly prioritize the top 3 strategic opportunities that need "
            "immediate attention. Provide concrete, actionable guidance for each finding—make it easy for a developer "
            "to understand exactly what strategic improvements to implement and how to approach them."
        )

        # Add expert analysis guidance only when expert analysis was actually used
        if expert_analysis_used:
            expert_guidance = self.get_expert_analysis_guidance()
            if expert_guidance:
                return f"{base_message}\n\n{expert_guidance}"

        return base_message

    def get_expert_analysis_guidance(self) -> str:
        """
        Provide specific guidance for handling expert analysis in code analysis.
        """
        return (
            "IMPORTANT: Analysis from an assistant model has been provided above. You MUST thoughtfully evaluate and validate "
            "the expert insights rather than treating them as definitive conclusions. Cross-reference the expert "
            "analysis with your own systematic investigation, verify that architectural recommendations are "
            "appropriate for this codebase's scale and context, and ensure suggested improvements align with "
            "the project's goals and constraints. Present a comprehensive synthesis that combines your detailed "
            "analysis with validated expert perspectives, clearly distinguishing between patterns you've "
            "independently identified and additional strategic insights from expert validation."
        )

    def get_step_guidance_message(self, request) -> str:
        """
        Analyze-specific step guidance with detailed investigation instructions.
        """
        step_guidance = self.get_analyze_step_guidance(request.step_number, request)
        return step_guidance["next_steps"]

    def get_analyze_step_guidance(self, step_number: int, request) -> dict[str, Any]:
        """
        Provide step-specific guidance for analyze workflow.
        """
        # Generate the next steps instruction based on required actions
        required_actions = self.get_required_actions(step_number, "medium", request.findings, request.total_steps)

        if step_number == 1:
            next_steps = (
                f"MANDATORY: DO NOT call the {self.get_name()} tool again immediately. You MUST first examine "
                f"the code files thoroughly using appropriate tools. CRITICAL AWARENESS: You need to understand "
                f"the architectural patterns, assess scalability and performance characteristics, identify strategic "
                f"improvement areas, and look for systemic risks, overengineering, and missing abstractions. "
                f"Use file reading tools, code analysis, and systematic examination to gather comprehensive information. "
                f"Only call {self.get_name()} again AFTER completing your investigation. When you call "
                f"{self.get_name()} next time, use step_number: {step_number + 1} and report specific "
                f"files examined, architectural insights found, and strategic assessment discoveries."
            )
        elif step_number < request.total_steps:
            next_steps = (
                f"STOP! Do NOT call {self.get_name()} again yet. Based on your findings, you've identified areas that need "
                f"deeper analysis. MANDATORY ACTIONS before calling {self.get_name()} step {step_number + 1}:\\n"
                + "\\n".join(f"{i + 1}. {action}" for i, action in enumerate(required_actions))
                + f"\\n\\nOnly call {self.get_name()} again with step_number: {step_number + 1} AFTER "
                + "completing these analysis tasks."
            )
        else:
            next_steps = (
                f"WAIT! Your analysis needs final verification. DO NOT call {self.get_name()} immediately. REQUIRED ACTIONS:\\n"
                + "\\n".join(f"{i + 1}. {action}" for i, action in enumerate(required_actions))
                + f"\\n\\nREMEMBER: Ensure you have identified all significant architectural insights and strategic "
                f"opportunities across all areas. Document findings with specific file references and "
                f"code examples where applicable, then call {self.get_name()} with step_number: {step_number + 1}."
            )

        return {"next_steps": next_steps}

    def format_analysis_progress_table(self, request: AnalyzeWorkflowRequest) -> str:
        """
        Format analysis progress using the shared progress formatter.
        """
        # Get phase name
        phase_name = self._get_phase_name(request)

        # Count issues by severity
        issues_by_severity = {}
        if request.issues_found:
            for issue in request.issues_found:
                severity = issue.get("severity", "unknown")
                issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1

        # Additional stats specific to analysis
        additional_stats = {
            "analysis_type": request.analysis_type,
            "output_format": request.output_format,
            "code_elements_analyzed": len(request.relevant_context),
        }

        # Use the mixin's formatter
        return self.format_progress_table(
            step_number=request.step_number,
            total_steps=request.total_steps,
            phase_name=phase_name,
            next_step_required=request.next_step_required,
            findings_summary=request.findings,
            files_examined=len(request.files_checked),
            relevant_files=len(request.relevant_files),
            issues_found=issues_by_severity,
            additional_stats=additional_stats,
        )

    def _get_phase_name(self, request: AnalyzeWorkflowRequest) -> str:
        """Determine the current analysis phase name based on type and progress"""
        if request.analysis_type == "architecture":
            phases = ["架构扫描", "模式识别", "依赖分析", "架构评估", "报告生成"]
        elif request.analysis_type == "performance":
            phases = ["性能扫描", "瓶颈识别", "资源分析", "优化建议", "报告生成"]
        elif request.analysis_type == "security":
            phases = ["安全扫描", "漏洞检测", "风险评估", "修复建议", "报告生成"]
        elif request.analysis_type == "quality":
            phases = ["质量扫描", "代码异味", "复杂度分析", "改进建议", "报告生成"]
        else:
            phases = ["初始扫描", "深度分析", "模式识别", "综合评估", "报告生成"]

        # Map step number to phase
        phase_index = min((request.step_number - 1) * len(phases) // request.total_steps, len(phases) - 1)
        return phases[phase_index]

    def customize_workflow_response(self, response_data: dict, request) -> dict:
        """
        Customize response to match analyze workflow format.
        """
        # Store initial request on first step
        if request.step_number == 1:
            self.initial_request = request.step
            # Store analysis configuration for expert analysis
            if request.relevant_files:
                self.analysis_config = {
                    "relevant_files": request.relevant_files,
                    "analysis_type": request.analysis_type,
                    "output_format": request.output_format,
                }

        # Convert generic status names to analyze-specific ones
        tool_name = self.get_name()
        status_mapping = {
            f"{tool_name}_in_progress": "analysis_in_progress",
            f"pause_for_{tool_name}": "pause_for_analysis",
            f"{tool_name}_required": "analysis_required",
            f"{tool_name}_complete": "analysis_complete",
        }

        if response_data["status"] in status_mapping:
            response_data["status"] = status_mapping[response_data["status"]]

        # Rename status field to match analyze workflow
        if f"{tool_name}_status" in response_data:
            response_data["analysis_status"] = response_data.pop(f"{tool_name}_status")
            # Add analyze-specific status fields
            response_data["analysis_status"]["insights_by_severity"] = {}
            for insight in self.consolidated_findings.issues_found:
                severity = insight.get("severity", "unknown")
                if severity not in response_data["analysis_status"]["insights_by_severity"]:
                    response_data["analysis_status"]["insights_by_severity"][severity] = 0
                response_data["analysis_status"]["insights_by_severity"][severity] += 1
            response_data["analysis_status"]["analysis_confidence"] = self.get_request_confidence(request)

        # Map complete_analyze to complete_analysis
        if f"complete_{tool_name}" in response_data:
            response_data["complete_analysis"] = response_data.pop(f"complete_{tool_name}")

        # Map the completion flag to match analyze workflow
        if f"{tool_name}_complete" in response_data:
            response_data["analysis_complete"] = response_data.pop(f"{tool_name}_complete")

        # Add progress table to the response
        progress_table = self.format_analysis_progress_table(request)
        if "message" in response_data:
            # Prepend progress table to the message
            response_data["message"] = progress_table + "\n\n" + response_data["message"]
        else:
            response_data["progress_report"] = progress_table

        return response_data

    # Required abstract methods from BaseTool
    def get_request_model(self):
        """Return the analyze workflow-specific request model."""
        return AnalyzeWorkflowRequest

    async def prepare_prompt(self, request) -> str:
        """Not used - workflow tools use execute_workflow()."""
        return ""  # Workflow tools use execute_workflow() directly
