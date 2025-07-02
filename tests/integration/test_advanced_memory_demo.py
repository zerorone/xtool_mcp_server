"""
高级记忆系统功能演示
展示语义搜索、上下文相似度和生命周期管理
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 启用增强记忆
os.environ["ENABLE_ENHANCED_MEMORY"] = "true"

# 导入高级功能
from utils.intelligent_memory_retrieval import enhanced_save_memory
from utils.memory_lifecycle import evaluate_memory_health, get_lifecycle_manager
from utils.memory_recall_algorithms import advanced_memory_recall


def demo_semantic_search():
    """演示语义搜索功能"""
    print("\n" + "=" * 60)
    print("语义搜索演示")
    print("=" * 60)

    # 保存一些相关记忆
    memories = [
        {
            "content": "Authentication system uses JWT tokens with RS256 algorithm for enhanced security",
            "tags": ["auth", "jwt", "security"],
            "type": "security",
        },
        {
            "content": "Login flow: user submits credentials -> server validates -> JWT token generated",
            "tags": ["auth", "login", "flow"],
            "type": "architecture",
        },
        {
            "content": "Security best practice: always validate JWT tokens on server side",
            "tags": ["security", "jwt", "validation"],
            "type": "security",
        },
    ]

    for mem in memories:
        enhanced_save_memory(content=mem["content"], tags=mem["tags"], mem_type=mem["type"], layer="project")

    # 语义搜索 - 不是精确匹配
    print("\n搜索: 'token authentication' (非精确匹配)")
    results = advanced_memory_recall(query="token authentication", limit=5)

    for i, mem in enumerate(results, 1):
        content = str(mem["content"])
        scores = mem.get("advanced_scores", {})
        print(f"\n{i}. {content[:80]}...")
        print(f"   语义得分: {scores.get('semantic', 0):.2f}")
        print(f"   最终得分: {scores.get('final', 0):.2f}")


def demo_context_aware_search():
    """演示上下文感知搜索"""
    print("\n" + "=" * 60)
    print("上下文感知搜索演示")
    print("=" * 60)

    # 定义搜索上下文
    context = {"tags": ["security", "auth"], "type": "security", "importance": "high"}

    print("\n在安全相关上下文中搜索 'best practice'")
    results = advanced_memory_recall(
        query="best practice",
        context=context,
        context_weight=0.6,  # 上下文权重
        limit=5,
    )

    for i, mem in enumerate(results, 1):
        content = str(mem["content"])
        scores = mem.get("advanced_scores", {})
        print(f"\n{i}. {content[:80]}...")
        print(f"   上下文相似度: {scores.get('context', 0):.2f}")
        print(f"   最终得分: {scores.get('final', 0):.2f}")


def demo_memory_lifecycle():
    """演示记忆生命周期管理"""
    print("\n" + "=" * 60)
    print("记忆生命周期管理演示")
    print("=" * 60)

    manager = get_lifecycle_manager()

    # 创建不同质量的记忆
    test_memories = [
        {
            "content": """
            Comprehensive API Documentation

            ## Authentication
            Our API uses OAuth2 for authentication with the following endpoints:
            - POST /auth/login - User login
            - POST /auth/refresh - Refresh token
            - POST /auth/logout - User logout

            ## Error Handling
            All errors return standardized JSON responses:
            ```json
            {
                "error": "error_code",
                "message": "Human readable message",
                "details": {}
            }
            ```

            ## Rate Limiting
            - 100 requests per minute for authenticated users
            - 20 requests per minute for anonymous users
            """,
            "tags": ["api", "documentation", "authentication", "oauth2"],
            "type": "documentation",
            "importance": "high",
            "layer": "project",
        },
        {"content": "TODO: update docs", "tags": ["todo"], "type": "todo", "importance": "low", "layer": "session"},
    ]

    saved_keys = []
    for mem in test_memories:
        key = enhanced_save_memory(
            content=mem["content"],
            tags=mem["tags"],
            mem_type=mem["type"],
            importance=mem["importance"],
            layer=mem["layer"],
        )
        saved_keys.append(key)

    # 评估记忆价值
    print("\n记忆价值评估:")
    for i, key in enumerate(saved_keys):
        # 获取记忆
        from utils.conversation_memory import _load_memory_layer

        layer = test_memories[i]["layer"]
        layer_data = _load_memory_layer(layer)

        if key in layer_data:
            memory = layer_data[key]
            value_report = manager.evaluate_memory_value(memory)

            print(f"\n记忆 {i + 1}: {test_memories[i]['content'][:50]}...")
            print(f"  质量分数: {value_report['quality']:.2f}")
            print(f"  衰减值: {value_report['decay']:.2f}")
            print(f"  综合价值: {value_report['overall']:.2f}")
            print(f"  应该归档: {'是' if value_report['should_archive'] else '否'}")
            print(f"  应该删除: {'是' if value_report['should_delete'] else '否'}")


def demo_thinking_pattern_match():
    """演示思维模式匹配"""
    print("\n" + "=" * 60)
    print("思维模式匹配演示")
    print("=" * 60)

    # 保存包含不同思维模式的记忆
    pattern_memories = [
        {
            "content": """
            Critical analysis of the authentication system:
            - Current implementation uses basic auth which is insecure
            - Password storage uses MD5 which is cryptographically broken
            - No rate limiting exposes system to brute force attacks
            - Recommendation: migrate to OAuth2 with bcrypt hashing
            """,
            "tags": ["security", "analysis", "authentication"],
            "type": "security",
        },
        {
            "content": """
            Debugging session findings:
            - Traced the memory leak to unclosed database connections
            - Root cause: connection pool not properly configured
            - Impact: server crashes after ~1000 requests
            - Solution: implement proper connection lifecycle management
            """,
            "tags": ["debug", "memory-leak", "database"],
            "type": "bug",
        },
    ]

    for mem in pattern_memories:
        enhanced_save_memory(content=mem["content"], tags=mem["tags"], mem_type=mem["type"], layer="project")

    # 搜索包含批判性分析的记忆
    print("\n搜索包含'批判性分析'思维模式的记忆:")
    results = advanced_memory_recall(thinking_patterns=["critical_analysis"], limit=5)

    for i, mem in enumerate(results, 1):
        content = str(mem["content"])
        scores = mem.get("advanced_scores", {})
        print(f"\n{i}. {content[:100]}...")
        print(f"   模式匹配得分: {scores.get('pattern', 0):.2f}")


def main():
    """运行所有演示"""
    print("\n高级记忆系统功能演示")
    print("=" * 60)

    # 运行各个演示
    demo_semantic_search()
    demo_context_aware_search()
    demo_memory_lifecycle()
    demo_thinking_pattern_match()

    # 系统健康报告
    print("\n" + "=" * 60)
    print("系统健康报告")
    print("=" * 60)

    health = evaluate_memory_health()
    print("\n整体健康状况:")
    print(f"  总记忆数: {health['total_memories']}")
    print(f"  健康分数: {health['health_score']:.2f}/1.0")

    if health["recommendations"]:
        print("\n建议:")
        for rec in health["recommendations"]:
            print(f"  • {rec}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
