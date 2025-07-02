"""
综合测试增强记忆系统的所有功能
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 启用增强记忆
os.environ["ENABLE_ENHANCED_MEMORY"] = "true"

from utils.intelligent_memory_retrieval import enhanced_save_memory, get_memory_index, intelligent_recall_memory
from utils.memory_lifecycle import evaluate_memory_health, get_lifecycle_manager
from utils.memory_recall_algorithms import advanced_memory_recall


def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print("=" * 60)


def test_save_and_index():
    """测试保存和索引功能"""
    print_section("1. 测试保存和索引功能")

    # 保存不同类型的记忆
    memories = [
        {
            "content": "发现认证模块存在SQL注入漏洞，需要立即修复。使用参数化查询替代字符串拼接。",
            "tags": ["security", "sql-injection", "critical", "authentication"],
            "type": "security",
            "importance": "high",
            "layer": "project",
        },
        {
            "content": "实现了新的用户仪表板功能，包括数据可视化和实时更新。使用React和D3.js构建。",
            "tags": ["feature", "dashboard", "react", "visualization"],
            "type": "feature",
            "importance": "medium",
            "layer": "project",
        },
        {
            "content": "Python最佳实践：始终使用类型提示来提高代码可读性和可维护性。",
            "tags": ["python", "best-practice", "type-hints"],
            "type": "architecture",
            "importance": "medium",
            "layer": "global",
        },
        {
            "content": "TODO: 优化数据库查询性能，当前查询耗时超过5秒",
            "tags": ["todo", "performance", "database"],
            "type": "todo",
            "importance": "low",
            "layer": "session",
        },
    ]

    saved_keys = []
    for mem in memories:
        key = enhanced_save_memory(
            content=mem["content"],
            tags=mem["tags"],
            mem_type=mem["type"],
            importance=mem["importance"],
            layer=mem["layer"],
        )
        saved_keys.append(key)
        print(f"✓ 保存成功: {mem['type']} - {key[:30]}...")

    # 检查索引
    index = get_memory_index()
    print("\n索引统计:")
    print(f"- 总记忆数: {len(index.memory_metadata)}")
    print(f"- 标签数: {len(index.tag_index)}")
    print(f"- 类型数: {len(index.type_index)}")
    print(f"- 层级分布: {dict((k, len(v)) for k, v in index.layer_index.items())}")

    return saved_keys


def test_basic_recall():
    """测试基础召回功能"""
    print_section("2. 测试基础召回功能")

    # 按标签召回
    print("\n按标签召回 (tags=['security']):")
    results = intelligent_recall_memory(tags=["security"], limit=5)
    for i, mem in enumerate(results, 1):
        print(f"{i}. {mem['content'][:60]}...")
        print(f"   相关度: {mem.get('relevance_score', 0):.2f}")

    # 按类型召回
    print("\n按类型召回 (type='feature'):")
    results = intelligent_recall_memory(mem_type="feature", limit=5)
    for i, mem in enumerate(results, 1):
        print(f"{i}. {mem['content'][:60]}...")

    # 按层级召回
    print("\n按层级召回 (layer='global'):")
    results = intelligent_recall_memory(layer="global", limit=5)
    for i, mem in enumerate(results, 1):
        content = str(mem["content"])
        print(f"{i}. {content[:60]}...")


def test_advanced_recall():
    """测试高级召回功能"""
    print_section("3. 测试高级召回功能")

    # 语义搜索
    print("\n语义搜索 (query='authentication security'):")
    results = advanced_memory_recall(query="authentication security", limit=3)
    for i, mem in enumerate(results, 1):
        print(f"{i}. {mem['content'][:60]}...")
        scores = mem.get("advanced_scores", {})
        print(
            f"   语义匹配: {scores.get('semantic', 0):.2f}, "
            f"模式匹配: {scores.get('pattern', 0):.2f}, "
            f"最终得分: {scores.get('final', 0):.2f}"
        )

    # 带上下文的搜索
    print("\n上下文感知搜索 (查找相关的安全问题):")
    context = {"tags": ["security", "critical"], "type": "security", "importance": "high", "layer": "project"}
    results = advanced_memory_recall(query="vulnerability", context=context, context_weight=0.5, limit=3)
    for i, mem in enumerate(results, 1):
        print(f"{i}. {mem['content'][:60]}...")
        scores = mem.get("advanced_scores", {})
        print(f"   上下文相似度: {scores.get('context', 0):.2f}, 最终得分: {scores.get('final', 0):.2f}")

    # 思维模式匹配
    print("\n思维模式匹配 (查找包含批判性分析的记忆):")
    results = advanced_memory_recall(thinking_patterns=["critical_analysis", "systems_thinking"], limit=3)
    for i, mem in enumerate(results, 1):
        print(f"{i}. {mem['content'][:60]}...")


def test_lifecycle_management():
    """测试生命周期管理"""
    print_section("4. 测试生命周期管理")

    manager = get_lifecycle_manager()

    # 创建一个老旧的测试记忆
    old_memory_content = "这是一个60天前的旧记忆，应该会被标记为低质量"
    old_key = enhanced_save_memory(
        content=old_memory_content, tags=["old", "test"], mem_type="note", importance="low", layer="session"
    )

    # 手动修改时间戳来模拟老记忆
    from utils.conversation_memory import _load_memory_layer, _save_memory_layer

    layer_data = _load_memory_layer("session")
    if old_key in layer_data:
        layer_data[old_key]["timestamp"] = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        _save_memory_layer("session", layer_data)

    # 评估记忆健康
    health_report = evaluate_memory_health()
    print("\n记忆系统健康报告:")
    print(f"- 总记忆数: {health_report['total_memories']}")
    print(f"- 活跃记忆: {health_report['active_memories']}")
    print(f"- 高价值记忆: {health_report['valuable_memories']}")
    print(f"- 待归档: {health_report['memories_to_archive']}")
    print(f"- 待删除: {health_report['memories_to_delete']}")
    print(f"- 健康分数: {health_report['health_score']:.2f}/1.0")

    if health_report["recommendations"]:
        print("\n建议:")
        for rec in health_report["recommendations"]:
            print(f"  • {rec}")

    # 测试记忆复活
    print("\n\n测试记忆复活机制:")

    # 找一个老记忆
    old_memories = intelligent_recall_memory(tags=["old"], limit=1)
    if old_memories:
        old_mem = old_memories[0]
        content = str(old_mem["content"])
        print(f"找到老记忆: {content[:50]}...")

        # 获取当前质量分数
        metadata = old_mem.get("metadata", {})
        old_quality = metadata.get("quality_score", 0.5)
        print(f"当前质量分数: {old_quality:.2f}")

        # 模拟访问（复活）
        from utils.intelligent_memory_retrieval import update_memory_access

        update_memory_access(old_mem["key"], old_mem["layer"])

        # 重新获取查看质量是否提升
        refreshed_memories = intelligent_recall_memory(tags=["old"], limit=1)
        if refreshed_memories:
            new_quality = refreshed_memories[0].get("metadata", {}).get("quality_score", 0.5)
            print(f"复活后质量分数: {new_quality:.2f}")

    # 优化建议（模拟运行）
    print("\n\n存储优化分析（模拟）:")
    stats = manager.optimize_memory_storage(dry_run=True)
    print(f"- 可删除的低价值记忆: {stats['deleted']}")
    print(f"- 可归档的记忆: {stats['archived']}")


def test_auto_tagging():
    """测试自动标签功能"""
    print_section("5. 测试自动标签功能")

    # 不提供标签，让系统自动生成
    test_contents = [
        "Fixed critical bug in authentication module causing session timeout",
        "Implemented new feature for real-time data visualization",
        "Refactored database queries for better performance optimization",
        "Security vulnerability found in user input validation",
        "Added comprehensive unit tests for payment processing module",
    ]

    for content in test_contents:
        key = enhanced_save_memory(content=content, mem_type="general", layer="session")

        # 获取生成的标签
        memories = intelligent_recall_memory(limit=1)
        if memories:
            auto_tags = memories[0].get("metadata", {}).get("tags", [])
            print(f"\n内容: {content[:50]}...")
            print(f"自动标签: {', '.join(auto_tags)}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("增强记忆系统功能测试")
    print("=" * 60)

    # 运行测试
    saved_keys = test_save_and_index()
    test_basic_recall()
    test_advanced_recall()
    test_lifecycle_management()
    test_auto_tagging()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
