#!/usr/bin/env python3
"""
测试 zen_advisor 在生产环境中的实际使用
Test zen_advisor in production environment
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.zen_advisor import ZenAdvisorTool, ZenAdvisorRequest


def test_zen_advisor():
    """测试 zen_advisor 工具"""
    print("🧪 测试 Zen Advisor 生产环境功能")
    print("=" * 60)
    
    # 创建工具实例
    advisor = ZenAdvisorTool()
    
    # 测试场景
    test_cases = [
        {
            "name": "测试场景",
            "query": "我需要全面测试这个新功能，确保没有任何bug",
            "context": "这是一个关键的支付功能模块"
        },
        {
            "name": "调试场景",
            "query": "调试一个复杂的性能问题，系统响应很慢",
            "context": "用户反馈在高并发时系统卡顿"
        },
        {
            "name": "架构设计",
            "query": "设计一个新的微服务架构，需要考虑可扩展性",
            "context": "预计用户量会在未来一年增长10倍"
        },
        {
            "name": "代码审查",
            "query": "审查一个关键模块的代码质量",
            "context": "这个模块处理用户的敏感数据"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")
        print("-" * 60)
        print(f"查询: {test_case['query']}")
        print(f"上下文: {test_case['context']}")
        
        # 创建请求
        request = ZenAdvisorRequest(
            query=test_case['query'],
            context=test_case['context'],
            auto_proceed=False,  # 测试时不自动执行
            wait_time=0  # 不等待
        )
        
        # 分析查询
        tools, thinking_modes, needs_context7 = advisor.analyze_query(request.query, request.context)
        
        print(f"\n推荐工具 ({len(tools)}):")
        for i, tool in enumerate(tools, 1):
            tool_info = advisor.TOOL_PATTERNS.get(tool, {})
            print(f"  {i}. {tool}")
            print(f"     描述: {tool_info.get('description', 'N/A')}")
        
        # 显示 Context7 规范检测结果
        if needs_context7:
            print("\n🔧 Context7 规范：需要（检测到代码开发场景）")
        else:
            print("\n🔧 Context7 规范：不需要")
        
        print(f"\n推荐思维模式 ({len(thinking_modes)}):")
        
        # 检查是否有管理器
        if hasattr(advisor, 'MANAGER_AVAILABLE') and advisor.MANAGER_AVAILABLE:
            print("  ✓ 使用统一思维模式管理器")
            for i, mode in enumerate(thinking_modes[:5], 1):
                try:
                    mode_type = advisor.ThinkingModeType(mode)
                    mode_obj = advisor.thinking_manager.get_mode(mode_type)
                    if mode_obj:
                        print(f"  {i}. {mode_obj.name} ({mode})")
                        print(f"     描述: {mode_obj.description}")
                        print(f"     核心原则: {mode_obj.core_principle}")
                except:
                    print(f"  {i}. {mode}")
        else:
            print("  ⚠️  使用降级模式")
            for i, mode in enumerate(thinking_modes[:5], 1):
                if hasattr(advisor, 'EXTENDED_THINKING_MODES') and mode in advisor.EXTENDED_THINKING_MODES:
                    mode_info = advisor.EXTENDED_THINKING_MODES[mode]
                    print(f"  {i}. {mode_info['name']} ({mode})")
                    print(f"     描述: {mode_info['description']}")
                else:
                    print(f"  {i}. {mode}")
        
        # 验证特定场景的要求
        if "测试" in test_case['query']:
            assert "craftsman_spirit" in thinking_modes, "测试场景必须包含工匠精神"
            assert "research_mindset" in thinking_modes, "测试场景必须包含钻研精神"
            print("\n  ✅ 验证通过: 包含工匠精神和钻研精神")
        
        if "调试" in test_case['query']:
            assert "research_mindset" in thinking_modes, "调试场景必须包含钻研精神"
            assert "craftsman_spirit" in thinking_modes, "调试场景必须包含工匠精神"
            print("\n  ✅ 验证通过: 包含钻研精神和工匠精神")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！Zen Advisor 在生产环境中工作正常")
    
    # 显示统计信息
    if hasattr(advisor, 'MANAGER_AVAILABLE') and advisor.MANAGER_AVAILABLE:
        print("\n📊 思维模式管理器统计:")
        print(f"  - 管理器状态: 已加载")
        print(f"  - 支持的思维模式: 18种")
        print(f"  - 支持的开发阶段: 11个")
        print(f"  - 支持的问题类型: 10种")
        print(f"  - 特殊模式: AUTO, DEFAULT")
    else:
        print("\n📊 降级模式统计:")
        print(f"  - 管理器状态: 未加载（使用基础模式）")
        print(f"  - 可用思维模式: {len(advisor.EXTENDED_THINKING_MODES) if hasattr(advisor, 'EXTENDED_THINKING_MODES') else 0}种")


if __name__ == "__main__":
    test_zen_advisor()