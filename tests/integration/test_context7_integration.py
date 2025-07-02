#!/usr/bin/env python3
"""
测试 Context7 规范集成功能
Test Context7 Standard Integration Feature

验证 XTOOL_advisor 是否正确检测代码开发场景并推荐 Context7 规范
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.xtool_advisor import XtoolAdvisorRequest, XtoolAdvisorTool


def test_context7_detection():
    """测试 Context7 规范检测功能"""
    print("🧪 测试 Context7 规范检测功能")
    print("=" * 60)

    # 创建工具实例
    advisor = XtoolAdvisorTool()

    # 测试场景：应该触发 Context7 的场景
    should_trigger_context7 = [
        {
            "name": "Python代码开发",
            "query": "我需要用Python开发一个Web API",
            "context": "使用FastAPI框架"
        },
        {
            "name": "JavaScript函数编写",
            "query": "写一个JavaScript函数来处理用户登录",
            "context": "前端项目需要"
        },
        {
            "name": "Java类实现",
            "query": "实现一个Java类来管理数据库连接",
            "context": "Spring Boot项目"
        },
        {
            "name": "代码重构",
            "query": "重构这段代码，提高性能",
            "context": "现有的算法效率较低"
        },
        {
            "name": "API接口设计",
            "query": "设计一个RESTful API接口",
            "context": "需要支持CRUD操作"
        },
        {
            "name": "算法实现",
            "query": "实现一个排序算法",
            "context": "需要处理大量数据"
        },
        {
            "name": "数据结构编程",
            "query": "用C++实现一个二叉树",
            "context": "数据结构课程作业"
        },
        {
            "name": "SQL脚本编写",
            "query": "写一个SQL脚本来优化数据库查询",
            "context": "查询性能较慢"
        }
    ]

    # 测试场景：不应该触发 Context7 的场景
    should_not_trigger_context7 = [
        {
            "name": "需求分析",
            "query": "分析用户需求和业务流程",
            "context": "项目启动阶段"
        },
        {
            "name": "系统架构讨论",
            "query": "讨论微服务架构的优缺点",
            "context": "技术选型阶段"
        },
        {
            "name": "测试策略",
            "query": "制定全面的测试策略",
            "context": "质量保证计划"
        },
        {
            "name": "项目管理",
            "query": "如何管理敏捷开发项目",
            "context": "团队协作"
        },
        {
            "name": "概念理解",
            "query": "什么是微服务架构",
            "context": "学习新概念"
        },
        {
            "name": "性能分析",
            "query": "分析系统性能瓶颈",
            "context": "性能监控"
        }
    ]

    print("\n🔧 测试应该触发 Context7 的场景：")
    print("-" * 60)

    trigger_passed = 0
    trigger_total = len(should_trigger_context7)

    for scenario in should_trigger_context7:
        tools, thinking_modes, needs_context7 = advisor.analyze_query(
            scenario["query"],
            scenario["context"]
        )

        result = "✅ PASS" if needs_context7 else "❌ FAIL"
        trigger_passed += 1 if needs_context7 else 0

        print(f"{result} {scenario['name']}")
        print(f"     查询: {scenario['query']}")
        print(f"     Context7: {'需要' if needs_context7 else '不需要'}")
        if not needs_context7:
            print("     ⚠️  预期应该触发 Context7 但未触发")
        print()

    print(f"触发检测通过率: {trigger_passed}/{trigger_total} ({trigger_passed/trigger_total*100:.1f}%)")

    print("\n🚫 测试不应该触发 Context7 的场景：")
    print("-" * 60)

    no_trigger_passed = 0
    no_trigger_total = len(should_not_trigger_context7)

    for scenario in should_not_trigger_context7:
        tools, thinking_modes, needs_context7 = advisor.analyze_query(
            scenario["query"],
            scenario["context"]
        )

        result = "✅ PASS" if not needs_context7 else "❌ FAIL"
        no_trigger_passed += 1 if not needs_context7 else 0

        print(f"{result} {scenario['name']}")
        print(f"     查询: {scenario['query']}")
        print(f"     Context7: {'需要' if needs_context7 else '不需要'}")
        if needs_context7:
            print("     ⚠️  预期不应该触发 Context7 但触发了")
        print()

    print(f"非触发检测通过率: {no_trigger_passed}/{no_trigger_total} ({no_trigger_passed/no_trigger_total*100:.1f}%)")

    # 总体评估
    total_passed = trigger_passed + no_trigger_passed
    total_tests = trigger_total + no_trigger_total
    overall_rate = total_passed / total_tests * 100

    print("\n" + "=" * 60)
    print("📊 Context7 检测功能评估结果")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"通过数: {total_passed}")
    print(f"成功率: {overall_rate:.1f}%")

    if overall_rate >= 90:
        print("🎉 Context7 检测功能表现优秀！")
    elif overall_rate >= 80:
        print("✅ Context7 检测功能表现良好")
    elif overall_rate >= 70:
        print("⚠️  Context7 检测功能需要改进")
    else:
        print("❌ Context7 检测功能需要重大改进")

    return overall_rate >= 80


def test_context7_integration_with_advisor():
    """测试 Context7 与 XTOOL_advisor 的完整集成"""
    print("\n🔗 测试 Context7 与 XTOOL_advisor 的完整集成")
    print("=" * 60)

    advisor = XtoolAdvisorTool()

    # 创建一个代码开发场景的请求
    request = XtoolAdvisorRequest(
        query="用Python编写一个机器学习数据预处理模块",
        context="需要处理CSV文件并进行特征工程",
        auto_proceed=False,
        wait_time=0
    )

    # 分析查询
    tools, thinking_modes, needs_context7 = advisor.analyze_query(
        request.query,
        request.context
    )

    print(f"查询: {request.query}")
    print(f"上下文: {request.context}")
    print(f"\n推荐工具: {', '.join(tools)}")
    print(f"推荐思维模式: {', '.join(thinking_modes[:3])}")
    print(f"Context7 规范: {'需要' if needs_context7 else '不需要'}")

    # 验证集成效果
    integration_tests = [
        ("检测到代码开发", needs_context7),
        ("有工具推荐", len(tools) > 0),
        ("有思维模式推荐", len(thinking_modes) > 0),
    ]

    print("\n集成测试结果:")
    all_passed = True
    for test_name, passed in integration_tests:
        result = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {result} {test_name}")
        all_passed = all_passed and passed

    if all_passed:
        print("\n🎉 Context7 与 XTOOL_advisor 集成成功！")
    else:
        print("\n❌ Context7 与 XTOOL_advisor 集成存在问题")

    return all_passed


def test_context7_specific_languages():
    """测试特定编程语言的 Context7 检测"""
    print("\n💻 测试特定编程语言的 Context7 检测")
    print("=" * 60)

    advisor = XtoolAdvisorTool()

    language_tests = [
        ("Python", "用Python开发一个Web应用"),
        ("Java", "Java Spring Boot项目开发"),
        ("JavaScript", "JavaScript前端组件开发"),
        ("TypeScript", "TypeScript类型定义编写"),
        ("C++", "C++算法优化实现"),
        ("Go", "Go语言微服务开发"),
        ("Rust", "Rust系统编程"),
        ("PHP", "PHP后端API开发"),
        ("Ruby", "Ruby on Rails应用"),
        ("Swift", "Swift iOS应用开发"),
        ("Kotlin", "Kotlin Android开发"),
        ("C#", "C# .NET应用开发"),
        ("SQL", "SQL数据库优化"),
        ("Shell", "Shell脚本自动化"),
        ("HTML/CSS", "HTML CSS前端页面")
    ]

    detected_count = 0
    total_count = len(language_tests)

    for language, query in language_tests:
        tools, thinking_modes, needs_context7 = advisor.analyze_query(query)

        result = "✅" if needs_context7 else "❌"
        detected_count += 1 if needs_context7 else 0

        print(f"{result} {language}: {'检测到' if needs_context7 else '未检测到'}")

    detection_rate = detected_count / total_count * 100
    print(f"\n语言检测率: {detected_count}/{total_count} ({detection_rate:.1f}%)")

    return detection_rate >= 90


def main():
    """主测试函数"""
    print("🧪 Context7 规范集成功能全面测试")
    print("=" * 80)

    # 执行所有测试
    test_results = []

    test_results.append(("Context7 检测功能", test_context7_detection()))
    test_results.append(("完整集成测试", test_context7_integration_with_advisor()))
    test_results.append(("编程语言检测", test_context7_specific_languages()))

    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 Context7 集成功能测试总结")
    print("=" * 80)

    passed_count = 0
    total_count = len(test_results)

    for test_name, passed in test_results:
        result = "✅ PASS" if passed else "❌ FAIL"
        print(f"{result} {test_name}")
        passed_count += 1 if passed else 0

    success_rate = passed_count / total_count * 100
    print(f"\n总体通过率: {passed_count}/{total_count} ({success_rate:.1f}%)")

    if success_rate == 100:
        print("🎉 所有测试通过！Context7 集成功能完全正常！")
    elif success_rate >= 80:
        print("✅ 大部分测试通过，Context7 集成功能基本正常")
    else:
        print("⚠️  Context7 集成功能需要改进")

    print("\n💡 使用提示：")
    print("当系统检测到代码开发场景时，会自动提示使用 'use context7'")
    print("这将帮助获取最新的编程语言文档和开发规范")

    return success_rate >= 80


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
