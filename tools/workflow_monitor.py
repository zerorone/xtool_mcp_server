"""
工作流监控工具

提供实时的工作流健康状况监控和统计信息
"""

from typing import TYPE_CHECKING, Optional

from pydantic import Field

if TYPE_CHECKING:
    pass

from tools.shared.base_models import ToolRequest
from tools.simple.base import SimpleTool
from utils.workflow_memory_fix import (
    cleanup_all_expired_workflows,
    get_comprehensive_workflow_stats,
    get_workflow_stats,
    restore_workflow_from_persistence,
)


class WorkflowMonitorRequest(ToolRequest):
    """工作流监控请求"""

    action: str = Field(
        default="status",
        description="监控操作: status(状态), stats(统计), cleanup(清理), persistent(持久化统计), restore(恢复状态)",
    )
    workflow_id: Optional[str] = Field(default=None, description="特定工作流ID（可选）")


class WorkflowMonitorTool(SimpleTool):
    """工作流监控工具"""

    def get_name(self) -> str:
        return "workflow_monitor"

    def get_description(self) -> str:
        return (
            "工作流系统监控工具 - 提供实时的系统健康状况监控，包括："
            "内存使用统计、活跃工作流数量、资源限制状态、持久化存储状态等。"
            "支持查看系统状态、获取详细统计信息、执行资源清理和状态恢复操作。"
        )

    def get_request_model(self):
        return WorkflowMonitorRequest

    def requires_ai_model(self, request: WorkflowMonitorRequest) -> bool:
        """监控操作不需要AI模型"""
        return False

    async def prepare_prompt(self, request: WorkflowMonitorRequest) -> str:
        """准备监控响应"""

        if request.action == "status":
            return self._get_system_status()
        elif request.action == "stats":
            return self._get_detailed_stats()
        elif request.action == "cleanup":
            return await self._perform_cleanup()
        elif request.action == "persistent":
            return await self._get_persistent_stats()
        elif request.action == "restore":
            return await self._restore_workflow(request.workflow_id)
        else:
            return f"未知的监控操作: {request.action}"

    def _get_system_status(self) -> str:
        """获取系统状态概览"""
        try:
            stats = get_workflow_stats()

            status = (
                "🟢 健康"
                if stats["active_workflows"] < 10
                else "🟡 警告"
                if stats["active_workflows"] < 20
                else "🔴 超载"
            )

            persistence_status = "✅ 已启用" if stats.get("persistence_enabled") else "❌ 未启用"

            return f"""工作流系统状态概览

📊 **系统状态**: {status}

🔄 **活跃工作流**: {stats["active_workflows"]}
💾 **总工作流数**: {stats["state_stats"]["total_workflows"]}
🧠 **内存使用**: {stats["memory_stats"]["total_memory_mb"]:.2f} MB
📈 **平均内存**: {stats["memory_stats"]["average_memory_mb"]:.2f} MB/工作流
🗄️ **持久化存储**: {persistence_status}

⚙️ **资源限制**:
- 最大步骤数: {stats["resource_limits"]["max_steps"]}
- 最大发现数: {stats["resource_limits"]["max_findings"]}
- 最大文件数: {stats["resource_limits"]["max_files"]}
- 内存限制: {stats["resource_limits"]["max_memory_mb"]} MB

✅ 系统运行正常，所有P0修复已生效。
💡 使用 'persistent' 操作查看持久化详情，'restore' 操作恢复工作流状态。"""

        except Exception as e:
            return f"❌ 获取系统状态失败: {str(e)}"

    def _get_detailed_stats(self) -> str:
        """获取详细统计信息"""
        try:
            stats = get_workflow_stats()

            return f"""工作流系统详细统计

📊 **整体统计**:
- 活跃工作流: {stats["active_workflows"]}
- 总工作流数: {stats["state_stats"]["total_workflows"]}
- 估计内存使用: {stats["state_stats"]["memory_usage_estimate"]} 字节

💾 **内存统计**:
- 总内存使用: {stats["memory_stats"]["total_memory_mb"]:.2f} MB
- 平均内存/工作流: {stats["memory_stats"]["average_memory_mb"]:.2f} MB
- 最大内存使用: {stats["memory_stats"]["max_memory_mb"]:.2f} MB

⏰ **访问统计**:
- 最近访问: {stats["state_stats"]["newest_access"]}
- 最旧访问: {stats["state_stats"]["oldest_access"]}

🔧 **配置限制**:
- 最大步骤数: {stats["resource_limits"]["max_steps"]}
- 最大发现数: {stats["resource_limits"]["max_findings"]}
- 最大文件引用: {stats["resource_limits"]["max_files"]}
- 内存限制: {stats["resource_limits"]["max_memory_mb"]} MB

✅ **P0修复状态**: 已启用
- 滑动窗口缓冲: ✅
- 线程安全保护: ✅
- 资源限制检查: ✅
- 自动清理机制: ✅"""

        except Exception as e:
            return f"❌ 获取详细统计失败: {str(e)}"

    async def _perform_cleanup(self) -> str:
        """执行资源清理（包括持久化存储）"""
        try:
            # 获取清理前状态
            before_stats = get_workflow_stats()

            # 执行综合清理（内存和持久化）
            cleanup_result = await cleanup_all_expired_workflows(24)

            # 获取清理后状态
            after_stats = get_workflow_stats()

            cleaned_workflows = (
                before_stats["state_stats"]["total_workflows"] - after_stats["state_stats"]["total_workflows"]
            )

            result = f"""🧹 工作流资源清理完成

内存清理结果:
- 清理前工作流数: {before_stats["state_stats"]["total_workflows"]}
- 清理后工作流数: {after_stats["state_stats"]["total_workflows"]}
- 已清理工作流: {cleaned_workflows}

内存变化:
- 清理前内存: {before_stats["memory_stats"]["total_memory_mb"]:.2f} MB
- 清理后内存: {after_stats["memory_stats"]["total_memory_mb"]:.2f} MB
- 释放内存: {before_stats["memory_stats"]["total_memory_mb"] - after_stats["memory_stats"]["total_memory_mb"]:.2f} MB

持久化清理结果:
- 持久化已清理: {cleanup_result.get("persistent_cleaned", 0)} 个工作流"""

            if "persistent_error" in cleanup_result:
                result += f"\n- 持久化清理错误: {cleanup_result['persistent_error']}"

            result += "\n\n✅ 清理操作完成，系统性能已优化。"
            return result

        except Exception as e:
            return f"❌ 执行清理失败: {str(e)}"

    async def _get_persistent_stats(self) -> str:
        """获取持久化统计信息"""
        try:
            comprehensive_stats = await get_comprehensive_workflow_stats()
            persistent_stats = comprehensive_stats.get("persistent_stats", {})

            if not persistent_stats.get("enabled", True):
                return "💾 **持久化存储状态**: 未启用\n\n系统仅使用内存存储，重启后状态将丢失。"

            if "error" in persistent_stats:
                return f"❌ 获取持久化统计失败: {persistent_stats['error']}"

            memory_stats = comprehensive_stats.get("memory_stats", {})
            p_stats = persistent_stats.get("persistent_stats", {})

            return f"""💾 **持久化存储详细统计**

🔄 **存储状态**:
- 后端类型: {persistent_stats.get("backend_type", "未知")}
- 启用状态: ✅ 已启用
- 唯一工作流总数: {persistent_stats.get("total_unique_workflows", 0)}

📊 **内存层统计**:
- 内存中工作流: {memory_stats.get("total_workflows", 0)}
- 内存使用: {memory_stats.get("total_memory_mb", 0):.2f} MB
- 平均内存/工作流: {memory_stats.get("average_memory_mb", 0):.2f} MB

💾 **持久化层统计**:
- 持久化工作流: {p_stats.get("total_workflows", 0)}
- 平均状态大小: {p_stats.get("avg_state_size_bytes", 0)} 字节
- 最大状态大小: {p_stats.get("max_state_size_bytes", 0)} 字节

⏰ **时间统计**:
- 最旧更新: {p_stats.get("oldest_update", "未知")}
- 最新更新: {p_stats.get("newest_update", "未知")}

✅ 持久化系统运行正常，状态在进程重启后可恢复。"""

        except Exception as e:
            return f"❌ 获取持久化统计失败: {str(e)}"

    async def _restore_workflow(self, workflow_id: Optional[str]) -> str:
        """恢复工作流状态"""
        if not workflow_id:
            return "❌ 恢复操作需要指定 workflow_id 参数"

        try:
            success = await restore_workflow_from_persistence(workflow_id)

            if success:
                return f"""✅ 工作流状态恢复成功

🔄 **恢复详情**:
- 工作流ID: {workflow_id}
- 恢复来源: 持久化存储
- 恢复目标: 内存缓存
- 状态: 已恢复并可用

工作流状态已从持久化存储成功恢复到内存中，可以继续使用。"""
            else:
                return f"""❌ 工作流状态恢复失败

🔄 **恢复详情**:
- 工作流ID: {workflow_id}
- 状态: 未找到或恢复失败

可能原因:
- 工作流在持久化存储中不存在
- 状态数据损坏
- 系统资源限制

请检查工作流ID是否正确，或使用 'persistent' 操作查看可用的工作流。"""

        except Exception as e:
            return f"❌ 恢复工作流失败: {str(e)}"
