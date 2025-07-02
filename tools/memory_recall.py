"""
记忆回忆工具 - 支持 token 限制和结构化回忆顺序

该工具使用新的 token 限制功能和结构化回忆顺序：
1. 类型回忆 - 按重要性排序的记忆类型
2. 索引回忆 - 使用多维度索引检索
3. 指定文件回忆 - 查看特定文件相关记忆

总 token 限制：20000 tokens
"""

import logging
from typing import Any, Optional

from tools.simple.base import SimpleTool
from utils.intelligent_memory_retrieval import (
    MEMORY_TOKEN_LIMIT,
    RECALL_ORDER,
    get_memory_stats_with_tokens,
    token_aware_memory_recall,
)

logger = logging.getLogger(__name__)


class MemoryRecallTool(SimpleTool):
    """
    记忆回忆工具，支持 token 限制和结构化回忆顺序。
    """

    def get_name(self) -> str:
        return "memory_recall"

    def get_request_model_name(self, request) -> Optional[str]:
        """Override model selection to always use Gemini 2.5 Flash for memory operations"""
        # 强制记忆模块只使用 Gemini 2.5 Flash 模型
        return "gemini-2.5-flash"

    def get_description(self) -> str:
        return (
            "智能记忆回忆工具，支持 token 限制和结构化回忆顺序。"
            f"总 token 限制：{MEMORY_TOKEN_LIMIT}。"
            f"回忆顺序：{' → '.join(RECALL_ORDER)}。"
            "可指定查询、标签、类型、层级、时间范围和文件列表。"
        )

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        """返回工具特定的字段定义"""
        return {
            "query": {
                "type": "string",
                "description": "文本搜索查询（可选）",
            },
            "tags": {
                "type": "string",
                "description": "标签过滤，用逗号分隔（可选）",
            },
            "mem_type": {
                "type": "string",
                "description": "记忆类型过滤（可选）",
            },
            "layer": {
                "type": "string",
                "description": "特定层搜索：global、project、session（可选）",
                "enum": ["global", "project", "session"],
            },
            "days_back": {
                "type": "integer",
                "minimum": 1,
                "description": "回忆多少天前的记忆（可选）",
            },
            "min_quality": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "最小质量分数 0.0-1.0（可选）",
            },
            "match_mode": {
                "type": "string",
                "enum": ["any", "all"],
                "default": "any",
                "description": "标签匹配模式：any 或 all",
            },
            "token_limit": {
                "type": "integer",
                "minimum": 1000,
                "maximum": 50000,
                "description": f"自定义 token 限制（默认：{MEMORY_TOKEN_LIMIT}）",
            },
            "specified_files": {
                "type": "string",
                "description": "指定文件列表，用逗号分隔（可选）",
            },
            "show_stats": {
                "type": "boolean",
                "default": False,
                "description": "是否显示记忆系统统计信息",
            },
        }

    def get_system_prompt(self) -> str:
        """返回记忆回忆工具的系统提示"""
        return """你是一个智能记忆回忆助手，专门负责从多层次记忆系统中检索和组织信息。

你的记忆系统具有以下特点：

**Token限制系统：**
- 总token限制：20,000 tokens
- 智能内容摘要和优先级排序
- 确保最重要的记忆优先返回

**结构化回忆顺序：**
1. **类型回忆** - 按重要性排序的记忆类型
2. **索引回忆** - 使用多维度索引检索  
3. **指定文件回忆** - 查看特定文件相关记忆

**三层架构：**
- **Global Memory**: 跨项目知识、最佳实践、通用解决方案
- **Project Memory**: 项目特定信息、bug、决策、配置
- **Session Memory**: 当前会话上下文、临时笔记、活动任务

你的任务是根据用户的查询参数，智能地检索相关记忆，并以清晰、结构化的方式呈现结果。
重点关注相关性、时效性和信息质量，确保用户获得最有价值的记忆内容。"""

    async def prepare_prompt(self, request) -> str:
        """准备记忆回忆的提示"""
        try:
            # 提取参数
            query = getattr(request, "query", None)
            tags = getattr(request, "tags", None)
            mem_type = getattr(request, "mem_type", None)
            layer = getattr(request, "layer", None)
            days_back = getattr(request, "days_back", None)
            min_quality = getattr(request, "min_quality", None)
            match_mode = getattr(request, "match_mode", "any")
            token_limit = getattr(request, "token_limit", None) or MEMORY_TOKEN_LIMIT
            specified_files = getattr(request, "specified_files", None)
            show_stats = getattr(request, "show_stats", False)

            # 执行token感知的记忆回忆
            result = await token_aware_memory_recall(
                query=query,
                tags=tags,
                mem_type=mem_type,
                layer=layer,
                days_back=days_back,
                min_quality=min_quality,
                match_mode=match_mode,
                token_limit=token_limit,
                specified_files=specified_files,
                show_stats=show_stats,
            )

            return f"""基于以下参数执行记忆回忆：

**回忆参数：**
- 查询: {query or "无"}
- 标签: {tags or "无"}  
- 类型: {mem_type or "所有"}
- 层级: {layer or "所有"}
- 时间范围: {f"{days_back}天前" if days_back else "无限制"}
- 最小质量: {min_quality or "默认"}
- 匹配模式: {match_mode}
- Token限制: {token_limit:,}
- 指定文件: {specified_files or "无"}

**回忆结果：**
{result}

请分析这些记忆信息，提供清晰的总结和关键洞察。"""

        except Exception as e:
            logger.error(f"记忆回忆准备失败: {e}")
            return f"记忆回忆准备过程中出现错误: {str(e)}"

    def run(
        self,
        query: Optional[str] = None,
        tags: Optional[str] = None,
        mem_type: Optional[str] = None,
        layer: Optional[str] = None,
        days_back: Optional[int] = None,
        min_quality: Optional[float] = None,
        match_mode: str = "any",
        token_limit: Optional[int] = None,
        specified_files: Optional[str] = None,
        show_stats: bool = False,
    ) -> str:
        """
        执行记忆回忆，返回结构化的回忆结果。

        Args:
            query: 文本搜索查询
            tags: 标签过滤（逗号分隔）
            mem_type: 记忆类型过滤
            layer: 特定层搜索 ("global", "project", "session")
            days_back: 回忆多少天前的记忆
            min_quality: 最小质量分数 (0.0-1.0)
            match_mode: 标签匹配模式 ("any" 或 "all")
            token_limit: 自定义 token 限制
            specified_files: 指定文件列表（逗号分隔）
            show_stats: 是否显示记忆系统统计信息

        Returns:
            结构化的回忆结果
        """
        try:
            logger.info(f"开始记忆回忆 - query: {query}, type: {mem_type}, layer: {layer}")

            # 解析参数
            tag_list = [t.strip() for t in tags.split(",")] if tags else None
            file_list = [f.strip() for f in specified_files.split(",")] if specified_files else None

            # 时间范围
            time_range = None
            if days_back:
                from datetime import datetime, timedelta, timezone

                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=days_back)
                time_range = (start_date, end_date)

            # 执行 token-aware 记忆回忆
            result = token_aware_memory_recall(
                query=query,
                tags=tag_list,
                mem_type=mem_type,
                layer=layer,
                time_range=time_range,
                min_quality=min_quality,
                match_mode=match_mode,
                token_limit=token_limit or MEMORY_TOKEN_LIMIT,
                include_metadata=True,
                specified_files=file_list,
            )

            # 构建回忆报告
            report = self._build_recall_report(result, show_stats)

            logger.info(f"记忆回忆完成 - 找到 {len(result['memories'])} 条记忆，使用 {result['total_tokens']} tokens")

            return report

        except Exception as e:
            error_msg = f"记忆回忆过程中发生错误：{str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _build_recall_report(self, result: dict[str, Any], show_stats: bool) -> str:
        """构建记忆回忆报告。"""
        lines = []

        # 标题和概览
        lines.append("# 📚 记忆回忆报告")
        lines.append("")
        lines.append(f"**Token 使用情况**: {result['total_tokens']}/{MEMORY_TOKEN_LIMIT} tokens")
        lines.append(f"**总记忆条数**: {len(result['memories'])}")
        lines.append(f"**是否截断**: {'是' if result['truncated'] else '否'}")
        lines.append("")

        # 回忆顺序摘要
        summary = result["recall_summary"]
        lines.append("## 🔍 回忆顺序摘要")
        lines.append("")

        # 1. 按类型回忆
        type_summary = summary["by_type"]
        lines.append("### 1️⃣ 按类型回忆")
        lines.append(f"- 找到记忆: {type_summary['count']} 条")
        lines.append(f"- 使用 tokens: {type_summary['tokens']}")
        if type_summary["types_found"]:
            lines.append(f"- 发现类型: {', '.join(type_summary['types_found'])}")
        lines.append("")

        # 2. 按索引回忆
        index_summary = summary["by_index"]
        lines.append("### 2️⃣ 按索引回忆")
        lines.append(f"- 找到记忆: {index_summary['count']} 条")
        lines.append(f"- 使用 tokens: {index_summary['tokens']}")
        if index_summary.get("index_categories"):
            lines.append(f"- 索引分类: {', '.join(index_summary['index_categories'])}")
        lines.append("")

        # 3. 指定文件回忆
        files_summary = summary["specified_files"]
        lines.append("### 3️⃣ 指定文件回忆")
        lines.append(f"- 找到记忆: {files_summary['count']} 条")
        lines.append(f"- 使用 tokens: {files_summary['tokens']}")
        if files_summary.get("files_processed"):
            lines.append(f"- 处理文件: {len(files_summary['files_processed'])} 个")
            lines.append(f"- 找到文件: {len(files_summary.get('files_found', []))} 个")
        lines.append("")

        # 记忆内容
        if result["memories"]:
            lines.append("## 📖 记忆内容")
            lines.append("")

            for i, memory in enumerate(result["memories"], 1):
                lines.append(f"### 记忆 {i}")
                lines.append(f"**层级**: {memory['layer']}")
                lines.append(f"**时间**: {memory.get('timestamp', 'N/A')}")
                lines.append(f"**相关度**: {memory.get('relevance_score', 0.0):.2f}")

                metadata = memory.get("metadata", {})
                if metadata.get("type"):
                    lines.append(f"**类型**: {metadata['type']}")
                if metadata.get("tags"):
                    lines.append(f"**标签**: {', '.join(metadata['tags'])}")
                if metadata.get("quality_score"):
                    lines.append(f"**质量分数**: {metadata['quality_score']:.2f}")

                lines.append("")
                lines.append("**内容**:")
                lines.append("```")
                content = str(memory.get("content", ""))
                # 限制单个记忆内容长度
                if len(content) > 1000:
                    content = content[:1000] + "..."
                lines.append(content)
                lines.append("```")
                lines.append("")

        # 系统统计信息
        if show_stats:
            lines.append("## 📊 记忆系统统计")
            lines.append("")
            stats = get_memory_stats_with_tokens()
            if stats.get("enabled"):
                lines.append(f"- 总记忆数: {stats['total_memories']}")
                lines.append(f"- 总 tokens: {stats['total_tokens']}")
                lines.append(f"- Token 利用率: {stats['token_utilization']:.1%}")
                lines.append("")

                lines.append("**分层统计**:")
                for layer, info in stats["layers"].items():
                    lines.append(f"- {layer}: {info['count']} 条记忆, {info['tokens']} tokens")
                lines.append("")

                if stats["types"]:
                    lines.append("**类型统计**:")
                    for mem_type, count in sorted(stats["types"].items()):
                        lines.append(f"- {mem_type}: {count} 条")
            else:
                lines.append("记忆系统未启用")

        return "\n".join(lines)
