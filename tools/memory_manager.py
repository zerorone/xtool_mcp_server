"""
Memory Manager tool - Intelligent memory management with auto-detection and learning

This tool provides advanced memory management capabilities including three-layer memory
(global, project, session), environment detection, TODO management, and intelligent
recall with context-aware filtering.
"""

import os
from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field

if TYPE_CHECKING:
    from tools.models import ToolModelCategory

from config import TEMPERATURE_ANALYTICAL
from tools.shared.base_models import ToolRequest
from utils.conversation_memory import ENABLE_ENHANCED_MEMORY, detect_environment
from utils.intelligent_memory_retrieval import (
    cleanup_old_memories,
    enhanced_save_memory,
    intelligent_recall_memory,
    rebuild_memory_index,
)

from .simple.base import SimpleTool

# Field descriptions for the memory manager tool
MEMORY_FIELD_DESCRIPTIONS = {
    "action": "Action to perform: save, recall, analyze, detect_env, rebuild_index, cleanup, export, import",
    "content": "Content to save (for save action) or search query (for recall action)",
    "layer": "Memory layer: global (cross-project), project (current project), session (current session)",
    "metadata": "Additional metadata for the memory (tags, type, category, etc.)",
    "filters": "Filters for recall: layer, metadata values, date ranges",
    "limit": "Maximum number of results to return (for recall action)",
    "tags": "List of tags for indexing and searching memories",
    "mem_type": "Type of memory (bug, feature, decision, architecture, etc.)",
    "importance": "Importance level (high, medium, low)",
    "time_range": "Time range for filtering (start_date, end_date in ISO format)",
    "min_quality": "Minimum quality score for recall (0.0 to 1.0)",
    "match_mode": "Tag matching mode: 'any' (at least one tag) or 'all' (all tags must match)",
    "export_format": "Export format: json, yaml, csv (for export action)",
    "output_file": "Output file path for export or input file path for import",
    "target_layers": "Layer mapping for import: {source_layer: target_layer}",
    "merge_strategy": "Import merge strategy: skip_duplicates, overwrite, append_suffix",
    "include_metadata": "Include metadata in export (boolean)",
    "include_statistics": "Include statistics in export (boolean)",
}


class MemoryManagerRequest(ToolRequest):
    """Request model for Memory Manager tool"""

    action: str = Field(..., description=MEMORY_FIELD_DESCRIPTIONS["action"])
    content: Optional[str] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["content"])
    layer: Optional[str] = Field("session", description=MEMORY_FIELD_DESCRIPTIONS["layer"])
    metadata: Optional[dict] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["metadata"])
    filters: Optional[dict] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["filters"])
    limit: Optional[int] = Field(10, description=MEMORY_FIELD_DESCRIPTIONS["limit"])
    tags: Optional[list[str]] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["tags"])
    mem_type: Optional[str] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["mem_type"])
    importance: Optional[str] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["importance"])
    time_range: Optional[list[str]] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["time_range"])
    min_quality: Optional[float] = Field(0.3, description=MEMORY_FIELD_DESCRIPTIONS["min_quality"])
    match_mode: Optional[str] = Field("any", description=MEMORY_FIELD_DESCRIPTIONS["match_mode"])
    export_format: Optional[str] = Field("json", description=MEMORY_FIELD_DESCRIPTIONS["export_format"])
    output_file: Optional[str] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["output_file"])
    target_layers: Optional[dict] = Field(None, description=MEMORY_FIELD_DESCRIPTIONS["target_layers"])
    merge_strategy: Optional[str] = Field("skip_duplicates", description=MEMORY_FIELD_DESCRIPTIONS["merge_strategy"])
    include_metadata: Optional[bool] = Field(True, description=MEMORY_FIELD_DESCRIPTIONS["include_metadata"])
    include_statistics: Optional[bool] = Field(True, description=MEMORY_FIELD_DESCRIPTIONS["include_statistics"])


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

    def get_request_model_name(self, request) -> Optional[str]:
        """Override model selection to always use Gemini 2.5 Flash for memory operations"""
        # 强制记忆模块只使用 Gemini 2.5 Flash 模型
        return "gemini-2.5-flash"

    def requires_ai_model(self, request: MemoryManagerRequest) -> bool:
        """
        Determine if this memory operation requires an AI model.

        Save, detect_env, rebuild_index, and cleanup operations don't need AI model.
        Recall and analyze operations might benefit from AI assistance.
        """
        # Direct operations that don't need AI
        if request.action in ["save", "detect_env", "rebuild_index", "cleanup", "export", "import"]:
            return False

        # Recall and analyze might use AI for better results
        return True

    def get_description(self) -> str:
        return (
            "INTELLIGENT MEMORY MANAGEMENT - Advanced memory system with multi-dimensional "
            "indexing (tags, type, time, quality), three layers (global, project, session), "
            "automatic environment detection, and intelligent recall algorithms. "
            "Features: tag-based categorization, type filtering, time-range queries, "
            "quality scoring, relevance ranking, and automatic memory cleanup. "
            "Perfect for: maintaining context across sessions, tracking decisions, "
            "categorizing knowledge, building searchable knowledge bases, and intelligent retrieval."
        )

    def get_system_prompt(self) -> str:
        return """You are an intelligent memory management assistant with advanced multi-dimensional
indexing and retrieval capabilities for storing, organizing, and analyzing information.

Your enhanced memory system features:

**Three-Layer Architecture:**
1. **Global Memory**: Cross-project knowledge, best practices, patterns, and reusable solutions
2. **Project Memory**: Project-specific information, bugs, decisions, and configurations
3. **Session Memory**: Current session context, temporary notes, and active tasks

**Multi-Dimensional Indexing:**
- **Tags**: Categorize memories with descriptive tags for easy filtering
- **Types**: Classify memories (bug, feature, decision, architecture, etc.)
- **Time**: Temporal indexing with date range queries
- **Quality**: Automatic quality scoring based on age, access, and relevance
- **Layers**: Cross-layer search capability

**Intelligent Operations:**
- **SAVE**: Auto-tag content, determine appropriate layer, calculate quality score
- **RECALL**: Multi-criteria search with relevance ranking and quality filtering
- **ANALYZE**: Statistical insights, pattern detection, and memory optimization
- **DETECT_ENV**: Scan project environment and auto-save relevant context
- **REBUILD_INDEX**: Reconstruct search indexes for optimal performance
- **CLEANUP**: Remove old, low-quality memories to maintain efficiency

**Advanced Features:**
- Automatic content analysis and tagging
- Relevance scoring based on query match, tags, and recency
- Memory decay with quality thresholds
- Access tracking for popularity-based ranking
- Time-based filtering and historical queries

Always optimize for:
- Fast retrieval through intelligent indexing
- High relevance through multi-factor scoring
- Knowledge preservation with quality assessment
- Efficient storage through periodic cleanup"""

    def get_default_temperature(self) -> float:
        return TEMPERATURE_ANALYTICAL

    def get_model_category(self) -> "ToolModelCategory":
        """Memory management requires analytical precision"""
        from tools.models import ToolModelCategory

        return ToolModelCategory.BALANCED

    def get_request_model(self):
        """Return the MemoryManager-specific request model"""
        return MemoryManagerRequest

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        """Return tool-specific field definitions for memory manager"""
        return {
            "action": {
                "type": "string",
                "enum": ["save", "recall", "analyze", "detect_env", "rebuild_index", "cleanup"],
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
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": MEMORY_FIELD_DESCRIPTIONS["tags"],
            },
            "mem_type": {"type": "string", "description": MEMORY_FIELD_DESCRIPTIONS["mem_type"]},
            "importance": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": MEMORY_FIELD_DESCRIPTIONS["importance"],
            },
            "time_range": {
                "type": "array",
                "items": {"type": "string"},
                "description": MEMORY_FIELD_DESCRIPTIONS["time_range"],
            },
            "min_quality": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": 0.3,
                "description": MEMORY_FIELD_DESCRIPTIONS["min_quality"],
            },
            "match_mode": {
                "type": "string",
                "enum": ["any", "all"],
                "default": "any",
                "description": MEMORY_FIELD_DESCRIPTIONS["match_mode"],
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
                    "enum": ["save", "recall", "analyze", "detect_env", "rebuild_index", "cleanup", "export", "import"],
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
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": MEMORY_FIELD_DESCRIPTIONS["tags"],
                },
                "mem_type": {"type": "string", "description": MEMORY_FIELD_DESCRIPTIONS["mem_type"]},
                "importance": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": MEMORY_FIELD_DESCRIPTIONS["importance"],
                },
                "time_range": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 2,
                    "description": MEMORY_FIELD_DESCRIPTIONS["time_range"],
                },
                "min_quality": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3,
                    "description": MEMORY_FIELD_DESCRIPTIONS["min_quality"],
                },
                "match_mode": {
                    "type": "string",
                    "enum": ["any", "all"],
                    "default": "any",
                    "description": MEMORY_FIELD_DESCRIPTIONS["match_mode"],
                },
                "export_format": {
                    "type": "string",
                    "enum": ["json", "yaml", "csv"],
                    "default": "json",
                    "description": MEMORY_FIELD_DESCRIPTIONS["export_format"],
                },
                "output_file": {"type": "string", "description": MEMORY_FIELD_DESCRIPTIONS["output_file"]},
                "target_layers": {"type": "object", "description": MEMORY_FIELD_DESCRIPTIONS["target_layers"]},
                "merge_strategy": {
                    "type": "string",
                    "enum": ["skip_duplicates", "overwrite", "append_suffix"],
                    "default": "skip_duplicates",
                    "description": MEMORY_FIELD_DESCRIPTIONS["merge_strategy"],
                },
                "include_metadata": {
                    "type": "boolean",
                    "default": True,
                    "description": MEMORY_FIELD_DESCRIPTIONS["include_metadata"],
                },
                "include_statistics": {
                    "type": "boolean",
                    "default": True,
                    "description": MEMORY_FIELD_DESCRIPTIONS["include_statistics"],
                },
            },
        }

        # Add common fields from SimpleTool (model field)
        # Note: SimpleTool's get_input_schema already includes common fields

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
        elif action == "rebuild_index":
            return await self._prepare_rebuild_index_prompt(request)
        elif action == "cleanup":
            return await self._prepare_cleanup_prompt(request)
        elif action == "export":
            return await self._prepare_export_prompt(request)
        elif action == "import":
            return await self._prepare_import_prompt(request)
        else:
            return f"Unknown memory action: {action}. Please use one of: save, recall, analyze, detect_env, rebuild_index, cleanup, export, import"

    async def _prepare_save_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for save action"""
        if not request.content:
            return "Error: Content is required for save action. Please provide content to save."

        # Save the memory with enhanced indexing
        key = enhanced_save_memory(
            content=request.content,
            layer=request.layer or "session",
            metadata=request.metadata,
            tags=request.tags,
            mem_type=request.mem_type,
            importance=request.importance,
        )

        if key:
            # Get the actual file path where memory was saved
            from utils.conversation_memory import _get_memory_storage_path

            file_path = _get_memory_storage_path(request.layer)
            file_info = f"- File Path: {file_path}" if file_path else "- Storage: In-memory only (session layer)"

            # Build enhanced details
            enhanced_details = []
            if request.tags:
                enhanced_details.append(f"- Tags: {', '.join(request.tags)}")
            if request.mem_type:
                enhanced_details.append(f"- Type: {request.mem_type}")
            if request.importance:
                enhanced_details.append(f"- Importance: {request.importance}")

            enhanced_info = "\n".join(enhanced_details) if enhanced_details else ""

            return f"""Successfully saved memory to {request.layer} layer with intelligent indexing.

Memory Details:
- Key: {key}
- Layer: {request.layer}
{file_info}
- Content: {request.content[:100]}{"..." if len(request.content) > 100 else ""}
- Metadata: {request.metadata if request.metadata else "None"}
{enhanced_info}

The memory has been indexed and can be recalled using:
- The key directly
- Tags for categorized search
- Type-based filtering
- Time range queries
- Quality-based retrieval"""
        else:
            return "Failed to save memory. The memory system may be experiencing issues."

    async def _prepare_recall_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for recall action"""
        # Parse time range if provided
        time_range = None
        if request.time_range and len(request.time_range) == 2:
            try:
                from datetime import datetime, timezone

                start_date = datetime.fromisoformat(request.time_range[0].replace("Z", "+00:00"))
                end_date = datetime.fromisoformat(request.time_range[1].replace("Z", "+00:00"))
                time_range = (start_date, end_date)
            except Exception:
                # 忽略时间解析错误，继续处理
                pass

        # 检查是否需要使用高级召回
        use_advanced = False
        if request.content:  # 有查询文本时使用高级召回
            use_advanced = True

        if use_advanced:
            # 使用高级召回算法
            from utils.memory_recall_algorithms import advanced_memory_recall

            # 构建上下文信息
            context = {}
            if request.layer:
                context["layer"] = request.layer
            if request.tags:
                context["tags"] = request.tags
            if request.mem_type:
                context["type"] = request.mem_type
            if request.importance:
                context["importance"] = request.importance
            if time_range:
                context["timestamp"] = datetime.now(timezone.utc).isoformat()

            memories = advanced_memory_recall(
                query=request.content,
                context=context if context else None,
                tags=request.tags,
                mem_type=request.mem_type,
                layer=request.layer,
                time_range=time_range,
                min_quality=request.min_quality or 0.3,
                limit=request.limit or 10,
            )
        else:
            # 使用基础召回
            memories = intelligent_recall_memory(
                query=request.content,
                tags=request.tags,
                mem_type=request.mem_type,
                layer=request.layer,
                time_range=time_range,
                min_quality=request.min_quality or 0.3,
                match_mode=request.match_mode or "any",
                limit=request.limit or 10,
                include_metadata=True,
            )

        if memories:
            # Format memories for display with enhanced information
            result = f"Found {len(memories)} matching memories (sorted by relevance):\n\n"

            for i, memory in enumerate(memories, 1):
                result += f"🔹 Memory {i}:\n"
                result += f"   Layer: {memory.get('layer')}\n"
                result += f"   Key: {memory.get('key')}\n"
                result += f"   Relevance: {memory.get('relevance_score', 0):.2f}\n"

                # 显示高级评分（如果有）
                advanced_scores = memory.get("advanced_scores")
                if advanced_scores:
                    result += "   高级评分:\n"
                    if advanced_scores.get("semantic", 0) > 0:
                        result += f"     - 语义匹配: {advanced_scores['semantic']:.2f}\n"
                    if advanced_scores.get("pattern", 0) > 0:
                        result += f"     - 思维模式: {advanced_scores['pattern']:.2f}\n"
                    if advanced_scores.get("context", 0) > 0:
                        result += f"     - 上下文相似: {advanced_scores['context']:.2f}\n"

                # Show content preview
                content = memory.get("content", "")
                if isinstance(content, str):
                    content_preview = content[:200] + "..." if len(content) > 200 else content
                else:
                    content_preview = str(content)[:200] + "..." if len(str(content)) > 200 else str(content)
                result += f"   Content: {content_preview}\n"

                # Show metadata with enhanced fields
                metadata = memory.get("metadata", {})
                if metadata:
                    if metadata.get("tags"):
                        result += f"   Tags: {', '.join(metadata['tags'])}\n"
                    if metadata.get("type"):
                        result += f"   Type: {metadata['type']}\n"
                    if metadata.get("importance"):
                        result += f"   Importance: {metadata['importance']}\n"
                    if metadata.get("quality_score"):
                        result += f"   Quality: {metadata['quality_score']:.2f}\n"
                    if metadata.get("access_count"):
                        result += f"   Access Count: {metadata['access_count']}\n"

                result += f"   Timestamp: {memory.get('timestamp')}\n\n"

            # Add search summary
            if request.tags:
                result += f"Search filters: tags={request.tags}, mode={request.match_mode}\n"
            if request.mem_type:
                result += f"Type filter: {request.mem_type}\n"
            if time_range:
                result += f"Time range: {request.time_range[0]} to {request.time_range[1]}\n"

            return result
        else:
            filters_desc = []
            if request.tags:
                filters_desc.append(f"tags: {request.tags}")
            if request.mem_type:
                filters_desc.append(f"type: {request.mem_type}")
            if request.layer:
                filters_desc.append(f"layer: {request.layer}")

            filter_info = f" with filters ({', '.join(filters_desc)})" if filters_desc else ""
            return (
                f"No matching memories found{filter_info}. Try adjusting your search criteria or use broader filters."
            )

    async def _prepare_analyze_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for analyze action"""
        # Get index statistics
        from utils.intelligent_memory_retrieval import get_memory_index

        index = get_memory_index()

        # Get all memories for detailed analysis
        all_memories = intelligent_recall_memory(limit=1000, min_quality=0.0)

        # Analyze by layer
        layer_stats = {"global": 0, "project": 0, "session": 0}
        type_stats = {}
        tag_freq = {}
        quality_distribution = {"high": 0, "medium": 0, "low": 0}

        total_access_count = 0
        memories_with_access = 0

        for memory in all_memories:
            layer = memory.get("layer", "unknown")
            if layer in layer_stats:
                layer_stats[layer] += 1

            # Analyze metadata
            metadata = memory.get("metadata", {})

            # Type analysis
            mem_type = metadata.get("type", "untyped")
            type_stats[mem_type] = type_stats.get(mem_type, 0) + 1

            # Tag frequency analysis
            tags = metadata.get("tags", [])
            for tag in tags:
                tag_freq[tag] = tag_freq.get(tag, 0) + 1

            # Quality distribution
            quality = metadata.get("quality_score", 0.5)
            if quality >= 0.7:
                quality_distribution["high"] += 1
            elif quality >= 0.4:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1

            # Access statistics
            access_count = metadata.get("access_count", 0)
            if access_count > 0:
                memories_with_access += 1
                total_access_count += access_count

        # Sort tags by frequency
        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Calculate averages
        avg_access = total_access_count / memories_with_access if memories_with_access > 0 else 0

        # Return the analysis prompt for the AI to process
        return f"""Analyze the following enhanced memory statistics and provide insights:

**Overview:**
- Total memories: {len(all_memories)}
- Indexed entries: {len(index.memory_metadata)}
- Unique tags: {len(index.tag_index)}
- Memory types: {len(index.type_index)}

**Distribution by Layer:**
- Global: {layer_stats["global"]} memories ({layer_stats["global"] / max(len(all_memories), 1) * 100:.1f}%)
- Project: {layer_stats["project"]} memories ({layer_stats["project"] / max(len(all_memories), 1) * 100:.1f}%)
- Session: {layer_stats["session"]} memories ({layer_stats["session"] / max(len(all_memories), 1) * 100:.1f}%)

**Distribution by Type:**
{chr(10).join(f"- {t}: {c} memories" for t, c in sorted(type_stats.items(), key=lambda x: x[1], reverse=True))}

**Top 10 Tags:**
{chr(10).join(f"- {tag}: {count} occurrences" for tag, count in top_tags)}

**Quality Distribution:**
- High quality (≥0.7): {quality_distribution["high"]} memories ({quality_distribution["high"] / max(len(all_memories), 1) * 100:.1f}%)
- Medium quality (0.4-0.7): {quality_distribution["medium"]} memories ({quality_distribution["medium"] / max(len(all_memories), 1) * 100:.1f}%)
- Low quality (<0.4): {quality_distribution["low"]} memories ({quality_distribution["low"] / max(len(all_memories), 1) * 100:.1f}%)

**Access Patterns:**
- Memories accessed at least once: {memories_with_access} ({memories_with_access / max(len(all_memories), 1) * 100:.1f}%)
- Average access count: {avg_access:.1f}
- Total accesses: {total_access_count}

Provide comprehensive insights on:
1. Memory usage patterns and trends
2. Tag effectiveness and categorization quality
3. Knowledge gaps and underutilized areas
4. Recommendations for improved organization
5. Optimization opportunities for retrieval
6. Quality improvement strategies
7. Suggestions for memory lifecycle management"""

    async def _prepare_detect_env_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for environment detection"""
        import os

        # Detect environment
        project_root = os.getcwd()
        env_info = detect_environment(project_root)

        if env_info:
            # Return environment analysis prompt for AI to process
            return f"""Analyze the detected project environment and provide a comprehensive summary:

Project Root: {env_info.get("project_root")}
Git Branch: {env_info.get("git_info", {}).get("branch", "Not detected")}

Project Files Found:
{chr(10).join(f"- {name}: {path}" for name, path in env_info.get("files", {}).items())}

TODO Files:
{chr(10).join(f"- {todo}" for todo in env_info.get("todos", []))}

Provide:
1. Project type identification (language, framework, etc.)
2. Key observations about the project structure
3. Recommendations for development workflow
4. Suggestions for what to remember about this project"""
        else:
            return "Failed to detect environment. The environment detection may be disabled or the current directory may not be a valid project."

    async def _prepare_rebuild_index_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for rebuild index action"""
        try:
            index = rebuild_memory_index()
            entry_count = len(index.memory_metadata)

            # Get statistics
            tag_count = len(index.tag_index)
            type_count = len(index.type_index)
            layer_stats = {layer: len(keys) for layer, keys in index.layer_index.items()}

            return f"""Memory index rebuilt successfully!

Index Statistics:
- Total entries: {entry_count}
- Unique tags: {tag_count}
- Memory types: {type_count}
- Layer distribution:
  - Global: {layer_stats.get("global", 0)} entries
  - Project: {layer_stats.get("project", 0)} entries
  - Session: {layer_stats.get("session", 0)} entries

The index has been optimized for fast multi-dimensional searches:
- Tag-based filtering
- Type categorization
- Time-based queries
- Quality scoring
- Cross-layer search

All memories are now properly indexed and searchable."""
        except Exception as e:
            return f"Failed to rebuild memory index: {str(e)}"

    async def _prepare_cleanup_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for cleanup action"""
        try:
            # Get initial count
            from utils.intelligent_memory_retrieval import get_memory_index

            index_before = get_memory_index()
            count_before = len(index_before.memory_metadata)

            # Perform cleanup
            cleanup_old_memories()

            # Get final count
            index_after = get_memory_index()
            count_after = len(index_after.memory_metadata)
            removed_count = count_before - count_after

            return f"""Memory cleanup completed!

Cleanup Results:
- Memories before cleanup: {count_before}
- Memories after cleanup: {count_after}
- Memories removed: {removed_count}

Cleanup criteria:
- Age threshold: Memories older than {os.getenv("MEMORY_DECAY_DAYS", "30")} days
- Quality threshold: Memories with quality score below {os.getenv("MEMORY_QUALITY_THRESHOLD", "0.3")}

The memory system has been optimized by removing old, low-quality entries while preserving important knowledge."""
        except Exception as e:
            return f"Failed to cleanup memories: {str(e)}"

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

    async def _prepare_export_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for export action"""
        from utils.memory_lifecycle import export_memories

        try:
            # 确定要导出的层
            layers = None
            if request.layer:
                layers = [request.layer]

            # 执行导出
            result = export_memories(
                layers=layers,
                export_format=request.export_format or "json",
                include_metadata=request.include_metadata if request.include_metadata is not None else True,
                include_statistics=request.include_statistics if request.include_statistics is not None else True,
                output_file=request.output_file,
            )

            if result.get("success", False):
                return f"""记忆导出成功！

导出详情:
- 输出文件: {result["output_file"]}
- 导出数量: {result["total_exported"]} 条记忆
- 导出层级: {", ".join(result["layers"])}
- 导出格式: {request.export_format or "json"}
- 包含元数据: {"是" if request.include_metadata else "否"}
- 包含统计: {"是" if request.include_statistics else "否"}

文件已保存到指定位置，可用于备份、迁移或数据分析。"""

            elif request.output_file is None:
                # 返回数据而非保存文件
                stats = result.get("statistics", {}).get("global_summary", {})
                return f"""记忆数据导出完成！

导出统计:
- 总计记忆数: {stats.get("total_memories_exported", 0)}
- 导出层数: {stats.get("layers_count", 0)}
- 导出时间: {stats.get("export_timestamp", "N/A")}

数据已准备完毕，请指定 output_file 参数以保存到文件。"""

            else:
                error_msg = result.get("error", "未知错误")
                return f"记忆导出失败: {error_msg}"

        except Exception as e:
            return f"记忆导出时发生错误: {str(e)}"

    async def _prepare_import_prompt(self, request: MemoryManagerRequest) -> str:
        """Prepare prompt for import action"""
        from utils.memory_lifecycle import import_memories

        if not request.output_file:
            return "错误: 导入操作需要指定 output_file 参数作为导入文件路径。"

        try:
            # 执行导入
            result = import_memories(
                import_file=request.output_file,
                target_layers=request.target_layers,
                merge_strategy=request.merge_strategy or "skip_duplicates",
                validate_data=True,
            )

            if result.get("success", False):
                return f"""记忆导入成功！

导入结果:
- 源文件: {result["source_file"]}
- 导入数量: {result["imported_count"]} 条记忆
- 跳过数量: {result["skipped_count"]} 条记忆 (重复)
- 错误数量: {result["error_count"]} 条记忆
- 合并策略: {result["merge_strategy"]}

各层级导入详情:
{self._format_layer_stats(result.get("layer_stats", {}))}

记忆索引已自动重建，所有导入的记忆现在可以正常搜索和召回。"""

            else:
                error_msg = result.get("error", "未知错误")
                return f"记忆导入失败: {error_msg}"

        except Exception as e:
            return f"记忆导入时发生错误: {str(e)}"

    def _format_layer_stats(self, layer_stats: dict) -> str:
        """格式化层级统计信息"""
        if not layer_stats:
            return "- 无层级统计信息"

        lines = []
        for layer, stats in layer_stats.items():
            lines.append(
                f"- {layer}: 导入 {stats.get('imported', 0)}, 跳过 {stats.get('skipped', 0)}, 错误 {stats.get('errors', 0)}"
            )

        return "\n".join(lines)
