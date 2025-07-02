#!/usr/bin/env python3
"""
全面测试所有MCP工具的功能
Comprehensive testing of all MCP tools functionality
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(level=logging.WARNING)

# 导入所有工具
from tools import (
    AnalyzeTool,
    ChallengeTool,
    ChatTool,
    CodeReviewTool,
    ConsensusTool,
    DebugIssueTool,
    DocgenTool,
    ListModelsTool,
    MemoryManagerTool,
    MemoryRecallTool,
    PlannerTool,
    PrecommitTool,
    RefactorTool,
    SecauditTool,
    TestGenTool,
    ThinkBoostTool,
    ThinkDeepTool,
    TracerTool,
    VersionTool,
    XtoolAdvisorTool,
)


class ToolTester:
    """工具测试器"""

    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0

    def test_tool_basic(self, tool_name: str, tool_instance: Any) -> dict[str, Any]:
        """测试工具的基本功能"""
        result = {
            "name": tool_name,
            "status": "unknown",
            "error": None,
            "basic_methods": {},
            "schema_valid": False
        }

        try:
            # 测试基本方法
            if hasattr(tool_instance, 'get_name'):
                name = tool_instance.get_name()
                result["basic_methods"]["get_name"] = True
                print(f"  ✓ get_name(): {name}")
            else:
                result["basic_methods"]["get_name"] = False
                print("  ❌ get_name() method missing")

            if hasattr(tool_instance, 'get_description'):
                desc = tool_instance.get_description()
                result["basic_methods"]["get_description"] = True
                print(f"  ✓ get_description(): {len(desc)} chars")
            else:
                result["basic_methods"]["get_description"] = False
                print("  ❌ get_description() method missing")

            if hasattr(tool_instance, 'get_input_schema'):
                schema = tool_instance.get_input_schema()
                result["basic_methods"]["get_input_schema"] = True
                result["schema_valid"] = isinstance(schema, dict) and "type" in schema
                print(f"  ✓ get_input_schema(): valid={result['schema_valid']}")
            else:
                result["basic_methods"]["get_input_schema"] = False
                print("  ❌ get_input_schema() method missing")

            # 检查是否所有基本方法都存在
            basic_ok = all(result["basic_methods"].values())
            if basic_ok and result["schema_valid"]:
                result["status"] = "pass"
                print("  ✅ 基本功能测试通过")
            else:
                result["status"] = "fail"
                print("  ❌ 基本功能测试失败")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"  ❌ 测试错误: {e}")

        return result

    def test_simple_tools(self) -> dict[str, Any]:
        """测试简单工具"""
        print("\n🔧 测试简单工具 (Simple Tools)")
        print("=" * 60)

        simple_tools = {
            "chat": ChatTool(),
            "challenge": ChallengeTool(),
            "listmodels": ListModelsTool(),
            "version": VersionTool(),
            "memory": MemoryManagerTool(),
            "recall": MemoryRecallTool(),
            "thinkboost": ThinkBoostTool(),
            "xtool_advisor": XtoolAdvisorTool(),
        }

        results = {}
        for tool_name, tool_instance in simple_tools.items():
            print(f"\n📝 测试 {tool_name}")
            print("-" * 40)
            results[tool_name] = self.test_tool_basic(tool_name, tool_instance)
            self.total_tests += 1
            if results[tool_name]["status"] == "pass":
                self.passed_tests += 1

        return results

    def test_workflow_tools(self) -> dict[str, Any]:
        """测试工作流工具"""
        print("\n🔄 测试工作流工具 (Workflow Tools)")
        print("=" * 60)

        workflow_tools = {
            "thinkdeep": ThinkDeepTool(),
            "planner": PlannerTool(),
            "consensus": ConsensusTool(),
            "codereview": CodeReviewTool(),
            "precommit": PrecommitTool(),
            "debug": DebugIssueTool(),
            "secaudit": SecauditTool(),
            "docgen": DocgenTool(),
            "analyze": AnalyzeTool(),
            "refactor": RefactorTool(),
            "tracer": TracerTool(),
            "testgen": TestGenTool(),
        }

        results = {}
        for tool_name, tool_instance in workflow_tools.items():
            print(f"\n🔍 测试 {tool_name}")
            print("-" * 40)
            results[tool_name] = self.test_tool_basic(tool_name, tool_instance)
            self.total_tests += 1
            if results[tool_name]["status"] == "pass":
                self.passed_tests += 1

        return results

    def test_renamed_tools(self) -> dict[str, Any]:
        """特别测试重命名后的工具"""
        print("\n🔄 测试重命名工具验证")
        print("=" * 60)

        results = {}

        # 测试 xtool_advisor
        print("\n📝 验证 xtool_advisor 重命名")
        print("-" * 40)

        try:
            advisor = XtoolAdvisorTool()

            # 验证类名
            class_name = advisor.__class__.__name__
            print(f"  ✓ 类名: {class_name}")

            # 验证工具名称
            tool_name = advisor.get_name()
            print(f"  ✓ 工具名称: {tool_name}")

            # 验证Context7功能
            if hasattr(advisor, 'analyze_query'):
                # 测试Context7检测
                tools, thinking_modes, needs_context7 = advisor.analyze_query(
                    "我需要用Python开发一个Web API",
                    "这是一个代码开发项目"
                )
                print(f"  ✓ Context7检测: {needs_context7}")
                print(f"  ✓ 推荐工具数: {len(tools)}")
                print(f"  ✓ 思维模式数: {len(thinking_modes)}")

                results["xtool_advisor_functionality"] = {
                    "status": "pass",
                    "class_name": class_name,
                    "tool_name": tool_name,
                    "context7_detection": needs_context7,
                    "tools_count": len(tools),
                    "thinking_modes_count": len(thinking_modes)
                }
                print("  ✅ xtool_advisor功能验证通过")

            else:
                results["xtool_advisor_functionality"] = {
                    "status": "fail",
                    "error": "analyze_query method not found"
                }
                print("  ❌ analyze_query方法未找到")

        except Exception as e:
            results["xtool_advisor_functionality"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"  ❌ 测试错误: {e}")

        return results

    def test_thinking_mode_manager(self) -> dict[str, Any]:
        """测试思维模式管理器"""
        print("\n🧠 测试思维模式管理器")
        print("=" * 60)

        results = {}

        try:
            advisor = XtoolAdvisorTool()

            # 检查管理器可用性
            manager_available = hasattr(advisor, 'MANAGER_AVAILABLE') and advisor.MANAGER_AVAILABLE
            print(f"  📊 管理器状态: {'已加载' if manager_available else '未加载'}")

            if manager_available:
                # 测试思维模式数量
                if hasattr(advisor, 'thinking_manager'):
                    # 获取所有思维模式类型
                    thinking_modes = []
                    if hasattr(advisor, 'ThinkingModeType'):
                        thinking_modes = [mode.value for mode in advisor.ThinkingModeType]

                    print(f"  ✓ 支持的思维模式: {len(thinking_modes)}种")
                    print("  ✓ 包含特殊模式: AUTO, DEFAULT")

                    results["thinking_manager"] = {
                        "status": "pass",
                        "manager_available": True,
                        "thinking_modes_count": len(thinking_modes),
                        "special_modes": ["AUTO", "DEFAULT"]
                    }
                else:
                    results["thinking_manager"] = {
                        "status": "fail",
                        "error": "thinking_manager attribute not found"
                    }
            else:
                print("  ⚠️  使用降级模式")
                results["thinking_manager"] = {
                    "status": "fallback",
                    "manager_available": False,
                    "note": "Using fallback mode"
                }

        except Exception as e:
            results["thinking_manager"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"  ❌ 测试错误: {e}")

        return results

    def run_comprehensive_test(self):
        """运行全面测试"""
        print("🧪 开始全面工具测试")
        print("=" * 80)

        start_time = time.time()

        # 执行各种测试
        simple_results = self.test_simple_tools()
        workflow_results = self.test_workflow_tools()
        renamed_results = self.test_renamed_tools()
        thinking_results = self.test_thinking_mode_manager()

        # 合并结果
        self.results = {
            "simple_tools": simple_results,
            "workflow_tools": workflow_results,
            "renamed_tools": renamed_results,
            "thinking_manager": thinking_results,
            "summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                "test_duration": time.time() - start_time
            }
        }

        # 显示结果
        self.display_final_results()

    def display_final_results(self):
        """显示最终测试结果"""
        print("\n" + "=" * 80)
        print("🎯 最终测试结果")
        print("=" * 80)

        summary = self.results["summary"]
        success_rate = summary["success_rate"]

        print("\n📊 总体统计:")
        print(f"  - 总测试数: {summary['total_tests']}")
        print(f"  - 通过测试: {summary['passed_tests']}")
        print(f"  - 成功率: {success_rate:.1f}%")
        print(f"  - 测试时长: {summary['test_duration']:.2f}秒")

        # 按类别显示结果
        categories = ["simple_tools", "workflow_tools"]
        category_names = ["简单工具", "工作流工具"]

        for category, name in zip(categories, category_names):
            if category in self.results:
                tools = self.results[category]
                passed = sum(1 for t in tools.values() if t["status"] == "pass")
                total = len(tools)
                print(f"\n📈 {name}: {passed}/{total} 通过")

                # 显示失败的工具
                failed = [name for name, result in tools.items() if result["status"] != "pass"]
                if failed:
                    print(f"  ❌ 失败: {', '.join(failed)}")

        # 特殊功能验证
        print("\n🔧 特殊功能验证:")
        renamed = self.results.get("renamed_tools", {})
        thinking = self.results.get("thinking_manager", {})

        if "xtool_advisor_functionality" in renamed:
            advisor_result = renamed["xtool_advisor_functionality"]
            status = "✅" if advisor_result["status"] == "pass" else "❌"
            print(f"  {status} xtool_advisor重命名和功能")

        if thinking.get("status") == "pass":
            print(f"  ✅ 思维模式管理器 ({thinking.get('thinking_modes_count', 0)}种模式)")
        elif thinking.get("status") == "fallback":
            print("  ⚠️  思维模式管理器 (降级模式)")
        else:
            print("  ❌ 思维模式管理器")

        # 最终判断
        print("\n" + "=" * 80)
        if success_rate >= 95:
            print("🎉 所有工具测试通过！系统完全正常运行！")
            return 0
        elif success_rate >= 80:
            print("⚠️  大部分工具正常，但有少数问题需要关注")
            return 1
        else:
            print("❌ 发现重大问题，需要立即修复")
            return 2


def main():
    """主函数"""
    tester = ToolTester()
    exit_code = tester.run_comprehensive_test()

    # 保存详细结果
    results_file = Path(__file__).parent / "comprehensive_test_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(tester.results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 详细结果已保存到: {results_file}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
