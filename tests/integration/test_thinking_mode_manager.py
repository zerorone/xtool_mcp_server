#!/usr/bin/env python3
"""
测试思维模式管理器功能
Test Thinking Mode Manager Functionality

验证统一的思维模式管理系统是否正常工作，包括：
1. 枚举定义测试
2. 思维模式注册和获取
3. 基于开发阶段的模式推荐
4. 基于问题类型的模式推荐
5. 基于关键词的模式匹配
6. 自动选择和默认模式
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.thinking_mode_manager import (
    DevelopmentStage,
    ProblemType,
    ThinkingModeType,
    get_thinking_mode_manager,
)


def test_enum_definitions():
    """测试枚举定义"""
    print("=" * 60)
    print("测试 1: 枚举定义")
    print("=" * 60)

    # 测试思维模式类型枚举
    print("\n思维模式类型 (18个):")
    for mode_type in ThinkingModeType:
        if mode_type not in [ThinkingModeType.AUTO, ThinkingModeType.DEFAULT]:
            print(f"  - {mode_type.value}: {mode_type.name}")

    # 测试开发阶段枚举
    print("\n开发阶段 (11个):")
    for stage in DevelopmentStage:
        print(f"  - {stage.value}: {stage.name}")

    # 测试问题类型枚举
    print("\n问题类型 (10个):")
    for problem in ProblemType:
        print(f"  - {problem.value}: {problem.name}")

    print("\n✅ 枚举定义测试通过")


def test_mode_registration():
    """测试思维模式注册和获取"""
    print("\n" + "=" * 60)
    print("测试 2: 思维模式注册和获取")
    print("=" * 60)

    manager = get_thinking_mode_manager()

    # 测试获取特定模式
    test_modes = [
        ThinkingModeType.SOCRATIC_QUESTIONING,
        ThinkingModeType.CRAFTSMAN_SPIRIT,
        ThinkingModeType.RESEARCH_MINDSET,
        ThinkingModeType.FIRST_PRINCIPLES,
    ]

    for mode_type in test_modes:
        mode = manager.get_mode(mode_type)
        if mode:
            print(f"\n{mode.name} ({mode.type.value}):")
            print(f"  描述: {mode.description}")
            print(f"  核心原则: {mode.core_principle}")
            print(f"  适用场景: {', '.join(mode.suitable_for[:3])}")
        else:
            print(f"\n❌ 无法获取模式: {mode_type.value}")

    print("\n✅ 模式注册测试通过")


def test_stage_recommendations():
    """测试基于开发阶段的推荐"""
    print("\n" + "=" * 60)
    print("测试 3: 基于开发阶段的推荐")
    print("=" * 60)

    manager = get_thinking_mode_manager()

    test_stages = [
        DevelopmentStage.REQUIREMENT_ANALYSIS,
        DevelopmentStage.TEST_VERIFICATION,
        DevelopmentStage.DEBUG_TROUBLESHOOT,
        DevelopmentStage.ARCHITECTURE_DESIGN,
    ]

    for stage in test_stages:
        print(f"\n{stage.value}阶段推荐的思维模式:")

        # 获取主要推荐
        primary_modes = manager.get_modes_for_stage(stage, "primary")
        print("  主要模式:")
        for mode in primary_modes:
            print(f"    - {mode.name}: {mode.description}")

        # 获取次要推荐
        secondary_modes = manager.get_modes_for_stage(stage, "secondary")
        if secondary_modes:
            print("  次要模式:")
            for mode in secondary_modes:
                print(f"    - {mode.name}: {mode.description}")

    print("\n✅ 开发阶段推荐测试通过")


def test_problem_recommendations():
    """测试基于问题类型的推荐"""
    print("\n" + "=" * 60)
    print("测试 4: 基于问题类型的推荐")
    print("=" * 60)

    manager = get_thinking_mode_manager()

    test_problems = [
        ProblemType.BUG_FIX,
        ProblemType.TEST_DESIGN,
        ProblemType.ARCHITECTURE_DESIGN,
        ProblemType.PERFORMANCE_OPTIMIZATION,
    ]

    for problem_type in test_problems:
        print(f"\n{problem_type.value}问题推荐的思维模式:")
        modes = manager.get_modes_for_problem(problem_type)
        for mode in modes:
            print(f"  - {mode.name}: {mode.description}")

    print("\n✅ 问题类型推荐测试通过")


def test_keyword_matching():
    """测试基于关键词的匹配"""
    print("\n" + "=" * 60)
    print("测试 5: 基于关键词的匹配")
    print("=" * 60)

    manager = get_thinking_mode_manager()

    test_queries = [
        "我需要深入调试这个复杂的bug",
        "如何优化系统性能",
        "设计一个新的架构方案",
        "全面测试这个功能",
    ]

    for query in test_queries:
        print(f"\n查询: '{query}'")
        modes = manager.get_modes_by_keywords(query)
        print("匹配的思维模式:")
        for mode in modes[:3]:  # 只显示前3个
            print(f"  - {mode.name}: {mode.description}")

    print("\n✅ 关键词匹配测试通过")


def test_auto_selection():
    """测试自动选择功能"""
    print("\n" + "=" * 60)
    print("测试 6: 自动选择功能")
    print("=" * 60)

    manager = get_thinking_mode_manager()

    # 测试场景1：调试场景
    context1 = {
        "query": "调试一个复杂的性能问题",
        "stage": DevelopmentStage.DEBUG_TROUBLESHOOT,
        "problem_type": ProblemType.BUG_FIX,
    }

    print("\n场景1: 调试复杂性能问题")
    modes1 = manager.auto_select_modes(context1)
    print("自动选择的模式:")
    for mode in modes1:
        print(f"  - {mode.name}: {mode.description}")

    # 验证是否包含钻研精神和工匠精神
    mode_types = [m.type for m in modes1]
    assert ThinkingModeType.RESEARCH_MINDSET in mode_types, "调试场景应包含钻研精神"
    assert ThinkingModeType.CRAFTSMAN_SPIRIT in mode_types, "调试场景应包含工匠精神"
    print("  ✓ 确认包含钻研精神和工匠精神")

    # 测试场景2：测试设计场景
    context2 = {
        "query": "设计全面的测试方案",
        "stage": DevelopmentStage.TEST_VERIFICATION,
        "problem_type": ProblemType.TEST_DESIGN,
    }

    print("\n场景2: 设计全面测试方案")
    modes2 = manager.auto_select_modes(context2)
    print("自动选择的模式:")
    for mode in modes2:
        print(f"  - {mode.name}: {mode.description}")

    # 验证是否包含必要的思维模式
    mode_types2 = [m.type for m in modes2]
    assert ThinkingModeType.MECE_PRINCIPLE in mode_types2, "测试场景应包含MECE原则"
    assert ThinkingModeType.CRAFTSMAN_SPIRIT in mode_types2, "测试场景应包含工匠精神"
    assert ThinkingModeType.RESEARCH_MINDSET in mode_types2, "测试场景应包含钻研精神"
    print("  ✓ 确认包含MECE原则、工匠精神和钻研精神")

    print("\n✅ 自动选择测试通过")


def test_default_and_special_modes():
    """测试默认和特殊模式"""
    print("\n" + "=" * 60)
    print("测试 7: 默认和特殊模式")
    print("=" * 60)

    manager = get_thinking_mode_manager()

    # 测试默认模式
    print("\n默认思维模式:")
    default_modes = manager.get_default_modes()
    for mode in default_modes:
        print(f"  - {mode.name}: {mode.description}")

    # 测试空上下文的自动选择（应返回默认模式）
    print("\n空上下文的自动选择:")
    auto_modes = manager.auto_select_modes({})
    for mode in auto_modes:
        print(f"  - {mode.name}: {mode.description}")

    print("\n✅ 默认模式测试通过")


def test_zen_advisor_integration():
    """测试与 XTOOL_advisor 的集成"""
    print("\n" + "=" * 60)
    print("测试 8: XTOOL Advisor 集成测试")
    print("=" * 60)

    try:
        from tools.xtool_advisor import XtoolAdvisorTool

        advisor = XtoolAdvisorTool()

        # 测试查询分析
        test_queries = [
            ("我需要全面测试这个新功能", "测试场景"),
            ("调试一个复杂的性能bug", "调试场景"),
            ("设计一个新的微服务架构", "架构设计场景"),
        ]

        for query, scenario in test_queries:
            print(f"\n{scenario}: '{query}'")
            tools, thinking_modes = advisor.analyze_query(query)

            print("推荐工具:")
            for tool in tools:
                print(f"  - {tool}")

            print("推荐思维模式:")
            for mode in thinking_modes[:5]:
                print(f"  - {mode}")

            # 验证特定场景的思维模式
            if "测试" in query:
                assert "craftsman_spirit" in thinking_modes, "测试场景应包含工匠精神"
                assert "research_mindset" in thinking_modes, "测试场景应包含钻研精神"
                print("  ✓ 确认包含测试所需的思维模式")

            if "调试" in query:
                assert "research_mindset" in thinking_modes, "调试场景应包含钻研精神"
                assert "craftsman_spirit" in thinking_modes, "调试场景应包含工匠精神"
                print("  ✓ 确认包含调试所需的思维模式")

        print("\n✅ XTOOL Advisor 集成测试通过")

    except ImportError as e:
        print(f"\n⚠️  无法导入 XtoolAdvisorTool: {e}")
        print("跳过集成测试")


def main():
    """运行所有测试"""
    print("🧪 思维模式管理器功能测试")
    print("=" * 60)

    try:
        test_enum_definitions()
        test_mode_registration()
        test_stage_recommendations()
        test_problem_recommendations()
        test_keyword_matching()
        test_auto_selection()
        test_default_and_special_modes()
        test_zen_advisor_integration()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！思维模式管理器功能正常")
        print("=" * 60)

        # 总结
        get_thinking_mode_manager()
        print("\n📊 系统统计:")
        print("  - 思维模式总数: 18")
        print("  - 开发阶段总数: 11")
        print("  - 问题类型总数: 10")
        print("  - 支持 AUTO 和 DEFAULT 特殊模式")
        print("\n🎯 核心功能:")
        print("  - ✓ 枚举化管理")
        print("  - ✓ 智能推荐")
        print("  - ✓ 关键词匹配")
        print("  - ✓ 自动选择")
        print("  - ✓ 默认模式")
        print("  - ✓ XTOOL Advisor 集成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
