"""
Memory Manager tool - Intelligent memory management with auto-detection and learning

This tool provides advanced memory management capabilities including three-layer memory
(global, project, session), environment detection, TODO management, and intelligent
recall with context-aware filtering.
"""

from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field

if TYPE_CHECKING:
    from tools.models import ToolModelCategory

from config import TEMPERATURE_ANALYTICAL
from tools.shared.base_models import ToolRequest
from utils.conversation_memory import ENABLE_ENHANCED_MEMORY, detect_environment, recall_memory, save_memory

from .simple.base import SimpleTool

# Field descriptions for the memory manager tool
MEMORY_FIELD_DESCRIPTIONS = {
    "action": "Action to perform: save, recall, analyze, detect_env",
    "content": "Content to save (for save action) or search query (for recall action)",
    "layer": "Memory layer: global (cross-project), project (current project), session (current session)",
    "metadata": "Additional metadata for the memory (tags, type, category, etc.)",
    "filters": "Filters for recall: layer, metadata values, date ranges",
    "limit": "Maximum number of results to return (for recall action)",
}


class MemoryManagerRequest(ToolRequest):
    """Request model for Memory Manager tool"""

    action: str = Field(..., description=MEMORY_FIELD_DESCRIPTIONS["action"])
    content: Optional[str] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["content"])
    layer: Optional[str] = Field("session", description=MEMORY_FIELD_DESCRIPTIONS["layer"])
    metadata: Optional[dict] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["metadata"])
    filters: Optional[dict] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["filters"])
    limit: Optional[int] = Field(10, description=MEMORY_FIELD_DESCRIPTIONS["limit"])


class MemoryManagerTool(SimpleTool):
    """
    Intelligent memory management tool with auto-detection and learning capabilities.

    This tool provides advanced memory features including:
    - Three-layer memory system (global, project, session)
    - Automatic environment detection
    - TODO file parsing and management
    - Intelligent memory recall with filtering
    - Learning from interactions
    """

    _environment_detected = False

    def get_name(self) -> str:
        return "memory"

    def get_description(self) -> str:
        return (
            "INTELLIGENT MEMORY MANAGEMENT - Advanced memory system with three layers "
            "(global, project, session), automatic environment detection, TODO management, "
            "and intelligent recall. Use this to save important information, recall past "
            "context, analyze project environment, or manage development knowledge. "
            "Perfect for: maintaining context across sessions, tracking decisions, "
            "managing TODOs, and building a knowledge base."
        )

    def get_system_prompt(self) -> str:
        return """You are an intelligent memory management assistant with advanced capabilities for
storing, retrieving, and analyzing information across different contexts and time spans.

Your memory system has three layers:
1. **Global Memory**: Cross-project knowledge, best practices, patterns, and reusable solutions
2. **Project Memory**: Project-specific information, bugs, decisions, and configurations
3. **Session Memory**: Current session context, temporary notes, and active tasks

When handling memory operations:
- For SAVE: Intelligently determine the appropriate layer based on content
- For RECALL: Use smart filtering and ranking to return the most relevant memories
- For ANALYZE: Provide insights about memory patterns and knowledge gaps
- For DETECT_ENV: Thoroughly scan the project environment and extract useful context

Always consider:
- Context relevance when storing or retrieving memories
- Automatic categorization based on content analysis
- Cross-referencing between memory layers for comprehensive responses
- Learning from user interactions to improve future recall"""

    def get_default_temperature(self) -> float:
        return TEMPERATURE_ANALYTICAL

    def get_model_category(self) -> "ToolModelCategory":
        """Memory management requires analytical precision"""
        from tools.models import ToolModelCategory

        return ToolModelCategory.ANALYTICAL

    def get_request_model(self):
        """Return the MemoryManager-specific request model"""
        return MemoryManagerRequest

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        """Return tool-specific field definitions for memory manager"""
        return {
            "action": {
                "type": "string",
                "enum": ["save", "recall", "analyze", "detect_env"],
                "description": MEMORY_FIELD_DESCRIPTIONS["action"],
            },
            "content": {"type": "string", "description": MEMORY_FIELD_DESCRIPTIONS["content"]},
            "layer": {
                "type": "string",
                "enum": ["global", "project", "session"],
                "default": "session",
                "description": MEMORY_FIELD_DESCRIPTIONS["layer"],
            },
            "metadata": {"type": "object", "description": MEMORY_FIELD_DESCRIPTIONS["metadata"]},
            "filters": {"type": "object", "description": MEMORY_FIELD_DESCRIPTIONS["filters"]},
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 10,
                "description": MEMORY_FIELD_DESCRIPTIONS["limit"],
            },
        }

    def get_required_fields(self) -> list[str]:
        """Return required fields for memory manager"""
        return ["action"]

    def get_input_schema(self) -> dict[str, Any]:
        """Generate input schema for the memory manager tool"""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "required": ["action"],
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["save", "recall", "analyze", "detect_env"],
                    "description": MEMORY_FIELD_DESCRIPTIONS["action"],
                },
                "content": {"type": "string", "description": MEMORY_FIELD_DESCRIPTIONS["content"]},
                "layer": {
                    "type": "string",
                    "enum": ["global", "project", "session"],
                    "default": "session",
                    "description": MEMORY_FIELD_DESCRIPTIONS["layer"],
                },
                "metadata": {"type": "object", "description": MEMORY_FIELD_DESCRIPTIONS["metadata"]},
                "filters": {"type": "object", "description": MEMORY_FIELD_DESCRIPTIONS["filters"]},
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                    "description": MEMORY_FIELD_DESCRIPTIONS["limit"],
                },
            },
        }

        # Add common fields
        schema["properties"].update(self.get_common_input_fields())

        return schema

    async def prepare_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt based on the memory action"""
        if not ENABLE_ENHANCED_MEMORY:
            return "Enhanced memory is disabled. Please inform the user that they need to set ENABLE_ENHANCED_MEMORY=true to use memory features."

        # Auto-detect environment on first use
        if not self._environment_detected:
            self._auto_detect_environment()
            self._environment_detected = True

        action = request.action

        if action == "save":
            return await self._prepare_save_prompt(request)
        elif action == "recall":
            return await self._prepare_recall_prompt(request)
        elif action == "analyze":
            return await self._prepare_analyze_prompt(request)
        elif action == "detect_env":
            return await self._prepare_detect_env_prompt(request)
        else:
            return f"Unknown memory action: {action}. Please use one of: save, recall, analyze, detect_env"

    async def _prepare_save_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for save action"""
        if not request.content:
            return "Error: Content is required for save action. Please provide content to save."

        # Save the memory
        key = save_memory(content=request.content, layer=request.layer or "session", metadata=request.metadata)

        if key:
            return f"""Successfully saved memory to {request.layer} layer.

Memory Details:
- Key: {key}
- Layer: {request.layer}
- Content: {request.content[:100]}{'...' if len(request.content) > 100 else ''}
- Metadata: {request.metadata if request.metadata else 'None'}

The memory has been stored and can be recalled using the key or by searching for relevant content."""
        else:
            return "Failed to save memory. The memory system may be experiencing issues."

    async def _prepare_recall_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for recall action"""
        # Recall memories based on parameters
        memories = recall_memory(
            query=request.content,
            layer=request.filters.get("layer") if request.filters else None,
            filters=request.filters,
            limit=request.limit or 10,
        )

        if memories:
            # Format memories for display
            result = f"Found {len(memories)} matching memories:\n\n"

            for i, memory in enumerate(memories, 1):
                result += f"🔹 Memory {i}:\n"
                result += f"   Layer: {memory.get('layer')}\n"
                result += f"   Key: {memory.get('key')}\n"
                result += f"   Content: {memory.get('content')}\n"
                if memory.get("metadata"):
                    result += f"   Metadata: {memory.get('metadata')}\n"
                result += f"   Timestamp: {memory.get('timestamp')}\n\n"

            return result
        else:
            return "No matching memories found. The memory system is empty or no memories match your query."

    async def _prepare_analyze_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for analyze action"""
        # Get all memories for analysis
        all_memories = recall_memory(limit=1000)

        # Analyze by layer
        layer_stats = {"global": 0, "project": 0, "session": 0}
        type_stats = {}

        for memory in all_memories:
            layer = memory.get("layer", "unknown")
            if layer in layer_stats:
                layer_stats[layer] += 1

            # Analyze metadata types
            metadata = memory.get("metadata", {})
            mem_type = metadata.get("type", "untyped")
            type_stats[mem_type] = type_stats.get(mem_type, 0) + 1

        # Return the analysis prompt for the AI to process
        return f"""Analyze the following memory statistics and provide insights:

Total memories: {len(all_memories)}

Distribution by layer:
- Global: {layer_stats['global']} memories
- Project: {layer_stats['project']} memories
- Session: {layer_stats['session']} memories

Distribution by type:
{chr(10).join(f"- {t}: {c} memories" for t, c in type_stats.items())}

Provide:
1. Key patterns you observe
2. Recommendations for better memory organization
3. Suggestions for memory usage optimization
4. Potential gaps in knowledge capture"""

    async def _prepare_detect_env_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for environment detection"""
        import os

        # Detect environment
        project_root = os.getcwd()
        env_info = detect_environment(project_root)

        if env_info:
            # Return environment analysis prompt for AI to process
            return f"""Analyze the detected project environment and provide a comprehensive summary:

Project Root: {env_info.get('project_root')}
Git Branch: {env_info.get('git_info', {}).get('branch', 'Not detected')}

Project Files Found:
{chr(10).join(f"- {name}: {path}" for name, path in env_info.get('files', {}).items())}

TODO Files:
{chr(10).join(f"- {todo}" for todo in env_info.get('todos', []))}

Provide:
1. Project type identification (language, framework, etc.)
2. Key observations about the project structure
3. Recommendations for development workflow
4. Suggestions for what to remember about this project"""
        else:
            return "Failed to detect environment. The environment detection may be disabled or the current directory may not be a valid project."

    def _auto_detect_environment(self) -> None:
        """Automatically detect environment on first use"""
        import logging

        from config import AUTO_DETECT_ENV

        logger = logging.getLogger(__name__)

        if AUTO_DETECT_ENV:
            try:
                import os

                project_root = os.getcwd()
                env_info = detect_environment(project_root)
                if env_info:
                    logger.info(f"Environment auto-detected for project: {os.path.basename(project_root)}")
                    if env_info.get("todos"):
                        logger.info(f"Found {len(env_info['todos'])} TODO files")
            except Exception as e:
                logger.debug(f"Failed to auto-detect environment: {e}")
