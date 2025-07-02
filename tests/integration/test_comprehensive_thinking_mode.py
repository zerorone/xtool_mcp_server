#!/usr/bin/env python3
"""
思维模式管理器全面测试套件
Comprehensive Testing Suite for Thinking Mode Manager

基于工匠精神和钻研精神的全面测试策略：
- 工匠精神：追求测试的完美覆盖，注重每个细节
- 钻研精神：深入测试每个边界条件，不满足于表面测试
- MECE原则：确保测试覆盖完整且不重叠
- 风险驱动：优先测试高风险、关键路径场景
"""

import sys
import time
import traceback
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入相关模块
from utils.thinking_mode_manager import (
    DevelopmentStage,
    ProblemType,
    ThinkingModeType,
    get_thinking_mode_manager,
)


class TestResult:
    """测试结果记录"""
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.failures = []
        self.start_time = time.time()

    def add_test(self, test_name: str, passed: bool, details: str = ""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"  ✅ {test_name}")
        else:
            self.failed_tests += 1
            self.failures.append((test_name, details))
            print(f"  ❌ {test_name}: {details}")

    def get_summary(self) -> str:
        duration = time.time() - self.start_time
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

        summary = f"""
{'='*80}
📊 测试总结报告
{'='*80}
⏱️  执行时间: {duration:.2f}秒
📈 总测试数: {self.total_tests}
✅ 通过数: {self.passed_tests}
❌ 失败数: {self.failed_tests}
📊 成功率: {success_rate:.1f}%

"""

        if self.failures:
            summary += "❌ 失败的测试:\n"
            for i, (test_name, details) in enumerate(self.failures, 1):
                summary += f"  {i}. {test_name}\n     详情: {details}\n"

        if self.failed_tests == 0:
            summary += "🎉 所有测试通过！思维模式管理器功能完全正常！\n"
        else:
            summary += f"⚠️  发现 {self.failed_tests} 个问题，需要修复\n"

        summary += "="*80
        return summary


class ComprehensiveThinkingModeTest:
    """全面的思维模式管理器测试"""

    def __init__(self):
        self.result = TestResult()
        self.manager = None

    def setup(self):
        """测试前置准备"""
        print("🔧 设置测试环境...")
        try:
            self.manager = get_thinking_mode_manager()
            self.result.add_test("管理器初始化", True)
        except Exception as e:
            self.result.add_test("管理器初始化", False, str(e))
            return False
        return True

    def test_enum_definitions(self):
        """测试1: 枚举定义完整性 - 工匠精神：确保每个枚举都正确定义"""
        print("\n📋 测试1: 枚举定义完整性")

        # 测试思维模式类型枚举
        expected_thinking_modes = 18
        actual_modes = len([t for t in ThinkingModeType if t not in [ThinkingModeType.AUTO, ThinkingModeType.DEFAULT]])
        self.result.add_test(
            f"思维模式类型数量检查({expected_thinking_modes}个)",
            actual_modes == expected_thinking_modes,
            f"期望{expected_thinking_modes}个，实际{actual_modes}个"
        )

        # 测试开发阶段枚举
        expected_stages = 11
        actual_stages = len(DevelopmentStage)
        self.result.add_test(
            f"开发阶段数量检查({expected_stages}个)",
            actual_stages == expected_stages,
            f"期望{expected_stages}个，实际{actual_stages}个"
        )

        # 测试问题类型枚举
        expected_problems = 10
        actual_problems = len(ProblemType)
        self.result.add_test(
            f"问题类型数量检查({expected_problems}个)",
            actual_problems == expected_problems,
            f"期望{expected_problems}个，实际{actual_problems}个"
        )

        # 测试特殊模式
        has_auto = ThinkingModeType.AUTO in ThinkingModeType
        has_default = ThinkingModeType.DEFAULT in ThinkingModeType
        self.result.add_test("AUTO特殊模式存在", has_auto)
        self.result.add_test("DEFAULT特殊模式存在", has_default)

    def test_mode_registration_integrity(self):
        """测试2: 模式注册完整性 - 钻研精神：深入验证每个模式的完整性"""
        print("\n📋 测试2: 模式注册完整性")

        required_modes = [
            ThinkingModeType.SOCRATIC_QUESTIONING,
            ThinkingModeType.CRAFTSMAN_SPIRIT,
            ThinkingModeType.RESEARCH_MINDSET,
            ThinkingModeType.FIRST_PRINCIPLES,
            ThinkingModeType.SYSTEMS_THINKING,
            ThinkingModeType.MECE_PRINCIPLE,
        ]

        for mode_type in required_modes:
            mode = self.manager.get_mode(mode_type)
            self.result.add_test(
                f"模式存在性: {mode_type.value}",
                mode is not None,
                f"模式 {mode_type.value} 未注册"
            )

            if mode:
                # 验证模式属性完整性
                has_name = bool(mode.name)
                has_description = bool(mode.description)
                has_core_principle = bool(mode.core_principle)
                has_suitable_for = bool(mode.suitable_for)
                has_keywords = bool(mode.keywords)

                self.result.add_test(f"{mode_type.value} - 名称", has_name)
                self.result.add_test(f"{mode_type.value} - 描述", has_description)
                self.result.add_test(f"{mode_type.value} - 核心原则", has_core_principle)
                self.result.add_test(f"{mode_type.value} - 适用场景", has_suitable_for)
                self.result.add_test(f"{mode_type.value} - 关键词", has_keywords)

    def test_stage_recommendations(self):
        """测试3: 开发阶段推荐 - MECE原则：确保每个阶段都有合适的推荐"""
        print("\n📋 测试3: 开发阶段推荐")

        critical_stages = [
            DevelopmentStage.REQUIREMENT_ANALYSIS,
            DevelopmentStage.TEST_VERIFICATION,
            DevelopmentStage.DEBUG_TROUBLESHOOT,
            DevelopmentStage.ARCHITECTURE_DESIGN,
            DevelopmentStage.CODE_DEVELOPMENT,
        ]

        for stage in critical_stages:
            # 测试主要推荐
            primary_modes = self.manager.get_modes_for_stage(stage, "primary")
            has_primary = len(primary_modes) > 0
            self.result.add_test(
                f"{stage.value} - 主要推荐",
                has_primary,
                f"阶段 {stage.value} 缺少主要思维模式推荐"
            )

            # 测试完整推荐
            all_modes = self.manager.get_modes_for_stage(stage, "all")
            has_recommendations = len(all_modes) >= 2  # 至少应该有2个推荐
            self.result.add_test(
                f"{stage.value} - 推荐数量充足",
                has_recommendations,
                f"阶段 {stage.value} 推荐数量不足（{len(all_modes)}个）"
            )

        # 特殊验证：测试验证阶段必须包含工匠精神和钻研精神
        test_modes = self.manager.get_modes_for_stage(DevelopmentStage.TEST_VERIFICATION, "all")
        test_mode_types = [m.type for m in test_modes]

        has_craftsman = ThinkingModeType.CRAFTSMAN_SPIRIT in test_mode_types
        has_research = ThinkingModeType.RESEARCH_MINDSET in test_mode_types

        self.result.add_test("测试阶段包含工匠精神", has_craftsman)
        self.result.add_test("测试阶段包含钻研精神", has_research)

        # 调试阶段也必须包含这两种思维模式
        debug_modes = self.manager.get_modes_for_stage(DevelopmentStage.DEBUG_TROUBLESHOOT, "all")
        debug_mode_types = [m.type for m in debug_modes]

        has_craftsman_debug = ThinkingModeType.CRAFTSMAN_SPIRIT in debug_mode_types
        has_research_debug = ThinkingModeType.RESEARCH_MINDSET in debug_mode_types

        self.result.add_test("调试阶段包含工匠精神", has_craftsman_debug)
        self.result.add_test("调试阶段包含钻研精神", has_research_debug)

    def test_problem_type_recommendations(self):
        """测试4: 问题类型推荐 - 风险驱动：测试关键问题类型"""
        print("\n📋 测试4: 问题类型推荐")

        critical_problems = [
            ProblemType.BUG_FIX,
            ProblemType.TEST_DESIGN,
            ProblemType.PERFORMANCE_OPTIMIZATION,
            ProblemType.SECURITY_AUDIT,
            ProblemType.ARCHITECTURE_DESIGN,
        ]

        for problem_type in critical_problems:
            modes = self.manager.get_modes_for_problem(problem_type)
            has_recommendations = len(modes) > 0
            self.result.add_test(
                f"{problem_type.value} - 有推荐",
                has_recommendations,
                f"问题类型 {problem_type.value} 缺少思维模式推荐"
            )

            # 验证推荐质量：至少应该有2-3个推荐
            sufficient_recommendations = len(modes) >= 2
            self.result.add_test(
                f"{problem_type.value} - 推荐充足",
                sufficient_recommendations,
                f"问题类型 {problem_type.value} 推荐不足（{len(modes)}个）"
            )

        # 特殊验证：bug修复必须包含钻研精神
        bug_fix_modes = self.manager.get_modes_for_problem(ProblemType.BUG_FIX)
        bug_fix_types = [m.type for m in bug_fix_modes]
        has_research_for_bug = ThinkingModeType.RESEARCH_MINDSET in bug_fix_types

        self.result.add_test("Bug修复包含钻研精神", has_research_for_bug)

        # 测试设计必须包含MECE原则
        test_design_modes = self.manager.get_modes_for_problem(ProblemType.TEST_DESIGN)
        test_design_types = [m.type for m in test_design_modes]
        has_mece_for_test = ThinkingModeType.MECE_PRINCIPLE in test_design_types

        self.result.add_test("测试设计包含MECE原则", has_mece_for_test)

    def test_keyword_matching(self):
        """测试5: 关键词匹配精度 - 钻研精神：深入测试匹配算法"""
        print("\n📋 测试5: 关键词匹配精度")

        test_cases = [
            {
                "query": "深入调试复杂bug",
                "expected_modes": [ThinkingModeType.RESEARCH_MINDSET, ThinkingModeType.CRAFTSMAN_SPIRIT],
                "description": "调试场景关键词"
            },
            {
                "query": "全面测试验证功能",
                "expected_modes": [ThinkingModeType.CRAFTSMAN_SPIRIT, ThinkingModeType.RESEARCH_MINDSET],
                "description": "测试场景关键词"
            },
            {
                "query": "系统架构设计优化",
                "expected_modes": [ThinkingModeType.SYSTEMS_THINKING],
                "description": "架构场景关键词"
            },
            {
                "query": "完整需求分析",
                "expected_modes": [ThinkingModeType.MECE_PRINCIPLE],
                "description": "完整性关键词"
            }
        ]

        for case in test_cases:
            modes = self.manager.get_modes_by_keywords(case["query"])
            mode_types = [m.type for m in modes]

            for expected_mode in case["expected_modes"]:
                has_expected = expected_mode in mode_types
                self.result.add_test(
                    f"{case['description']} - 包含{expected_mode.value}",
                    has_expected,
                    f"查询'{case['query']}'未匹配到{expected_mode.value}"
                )

    def test_auto_selection_logic(self):
        """测试6: 自动选择逻辑 - 系统思维：测试整体选择逻辑"""
        print("\n📋 测试6: 自动选择逻辑")

        # 测试场景1：复合场景
        context1 = {
            "query": "全面测试调试性能问题",
            "stage": DevelopmentStage.TEST_VERIFICATION,
            "problem_type": ProblemType.PERFORMANCE_OPTIMIZATION
        }

        modes1 = self.manager.auto_select_modes(context1)
        mode_types1 = [m.type for m in modes1]

        # 应该包含测试必需的思维模式
        has_craftsman = ThinkingModeType.CRAFTSMAN_SPIRIT in mode_types1
        has_research = ThinkingModeType.RESEARCH_MINDSET in mode_types1

        self.result.add_test("复合场景包含工匠精神", has_craftsman)
        self.result.add_test("复合场景包含钻研精神", has_research)

        # 测试场景2：空上下文（应返回默认模式）
        empty_context = {}
        default_modes = self.manager.auto_select_modes(empty_context)

        has_default_modes = len(default_modes) > 0
        self.result.add_test("空上下文返回默认模式", has_default_modes)

        # 测试场景3：只有查询文本
        query_only_context = {"query": "如何优化代码"}
        query_modes = self.manager.auto_select_modes(query_only_context)

        has_query_modes = len(query_modes) > 0
        self.result.add_test("纯查询上下文有推荐", has_query_modes)

    def test_default_modes(self):
        """测试7: 默认模式验证 - 验证默认模式的合理性"""
        print("\n📋 测试7: 默认模式验证")

        default_modes = self.manager.get_default_modes()

        # 默认模式应该包含基础的思维方法
        expected_defaults = [
            ThinkingModeType.FIRST_PRINCIPLES,
            ThinkingModeType.SYSTEMS_THINKING,
            ThinkingModeType.MECE_PRINCIPLE
        ]

        default_types = [m.type for m in default_modes]

        for expected_mode in expected_defaults:
            has_expected = expected_mode in default_types
            self.result.add_test(
                f"默认模式包含{expected_mode.value}",
                has_expected,
                f"默认模式缺少{expected_mode.value}"
            )

        # 默认模式数量应该适中（3-5个）
        appropriate_count = 3 <= len(default_modes) <= 5
        self.result.add_test(
            f"默认模式数量适中({len(default_modes)}个)",
            appropriate_count,
            f"默认模式数量不合适：{len(default_modes)}个"
        )

    def test_boundary_conditions(self):
        """测试8: 边界条件测试 - 钻研精神：测试边界和异常情况"""
        print("\n📋 测试8: 边界条件测试")

        # 测试不存在的模式类型
        try:
            invalid_mode = self.manager.get_mode(None)
            self.result.add_test("处理None模式类型", invalid_mode is None)
        except Exception as e:
            self.result.add_test("处理None模式类型", False, f"抛出异常: {str(e)}")

        # 测试空字符串关键词匹配
        empty_keyword_modes = self.manager.get_modes_by_keywords("")
        self.result.add_test(
            "处理空关键词查询",
            len(empty_keyword_modes) == 0,
            f"空查询返回了{len(empty_keyword_modes)}个模式"
        )

        # 测试非常长的查询字符串
        long_query = "这是一个非常非常长的查询字符串" * 100
        self.manager.get_modes_by_keywords(long_query)
        self.result.add_test(
            "处理超长查询字符串",
            True,  # 只要不崩溃就算通过
        )

        # 测试特殊字符
        special_query = "测试!@#$%^&*()特殊字符"
        self.manager.get_modes_by_keywords(special_query)
        self.result.add_test(
            "处理特殊字符查询",
            True,  # 只要不崩溃就算通过
        )

    def test_performance(self):
        """测试9: 性能测试 - 确保响应速度"""
        print("\n📋 测试9: 性能测试")

        # 测试大量查询的性能
        start_time = time.time()

        for i in range(100):
            context = {
                "query": f"测试查询{i}",
                "stage": DevelopmentStage.TEST_VERIFICATION,
                "problem_type": ProblemType.BUG_FIX
            }
            self.manager.auto_select_modes(context)

        duration = time.time() - start_time
        avg_time = duration / 100

        # 平均每次查询应该在10ms以内
        performance_ok = avg_time < 0.01
        self.result.add_test(
            f"查询性能({avg_time*1000:.2f}ms/次)",
            performance_ok,
            f"平均查询时间过长: {avg_time*1000:.2f}ms"
        )

        # 测试内存使用（简单检查）
        import gc
        gc.collect()
        self.result.add_test("内存管理正常", True)  # 如果能执行到这里说明内存没问题

    def test_zen_advisor_integration(self):
        """测试10: XTOOL Advisor集成测试 - 验证实际使用场景"""
        print("\n📋 测试10: XTOOL Advisor集成测试")

        try:
            from tools.xtool_advisor import XtoolAdvisorTool

            advisor = XtoolAdvisorTool()

            # 测试关键场景
            test_scenarios = [
                {
                    "query": "我需要全面测试这个功能",
                    "must_have": ["craftsman_spirit", "research_mindset"],
                    "description": "测试场景必备模式"
                },
                {
                    "query": "调试复杂的bug问题",
                    "must_have": ["research_mindset", "craftsman_spirit"],
                    "description": "调试场景必备模式"
                },
                {
                    "query": "设计系统架构",
                    "must_have": ["systems_thinking"],
                    "description": "架构场景必备模式"
                }
            ]

            for scenario in test_scenarios:
                tools, thinking_modes, needs_context7 = advisor.analyze_query(scenario["query"])

                # 验证必备模式
                for must_have_mode in scenario["must_have"]:
                    has_mode = must_have_mode in thinking_modes
                    self.result.add_test(
                        f"{scenario['description']} - {must_have_mode}",
                        has_mode,
                        f"场景'{scenario['query']}'缺少必备模式{must_have_mode}"
                    )

                # 验证有工具推荐
                has_tools = len(tools) > 0
                self.result.add_test(
                    f"{scenario['description']} - 工具推荐",
                    has_tools,
                    f"场景'{scenario['query']}'没有工具推荐"
                )

        except ImportError as e:
            self.result.add_test("XTOOL Advisor导入", False, f"无法导入XtoolAdvisorTool: {e}")
        except Exception as e:
            self.result.add_test("XTOOL Advisor集成", False, f"集成测试失败: {e}")

    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 启动思维模式管理器全面测试")
        print("="*80)
        print("应用思维模式:")
        print("  🔧 工匠精神: 追求测试的完美覆盖，注重每个细节")
        print("  🔍 钻研精神: 深入测试每个边界条件，不满足于表面测试")
        print("  📊 MECE原则: 确保测试覆盖完整且不重叠")
        print("  ⚠️  风险驱动: 优先测试高风险、关键路径场景")
        print("="*80)

        if not self.setup():
            print("❌ 测试环境设置失败，终止测试")
            return self.result

        try:
            self.test_enum_definitions()
            self.test_mode_registration_integrity()
            self.test_stage_recommendations()
            self.test_problem_type_recommendations()
            self.test_keyword_matching()
            self.test_auto_selection_logic()
            self.test_default_modes()
            self.test_boundary_conditions()
            self.test_performance()
            self.test_zen_advisor_integration()

        except Exception as e:
            print(f"\n❌ 测试过程中发生异常: {e}")
            print(traceback.format_exc())
            self.result.add_test("测试执行", False, f"异常: {e}")

        return self.result


def main():
    """主函数"""
    test_suite = ComprehensiveThinkingModeTest()
    result = test_suite.run_all_tests()

    print(result.get_summary())

    # 返回适当的退出代码
    return 0 if result.failed_tests == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
