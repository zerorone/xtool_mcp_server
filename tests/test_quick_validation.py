"""
Quick validation test script for Zen MCP Server

This script runs basic tests that don't require API keys to validate
the core functionality is working.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from server import handle_call_tool, handle_list_tools
from tests.test_helpers import call_tool_with_result


async def test_version():
    """Test version tool"""
    print("\n✅ Testing version tool...")
    result = await call_tool_with_result(handle_call_tool, "version", {})
    print(f"Status: {result.status}")
    print(f"Output preview: {result.output[:200]}...")
    assert result.status == "success"
    assert "Zen MCP Server" in result.output
    print("Version tool test passed!")


async def test_thinkboost():
    """Test thinkboost tool"""
    print("\n✅ Testing thinkboost tool...")
    result = await call_tool_with_result(
        handle_call_tool,
        "thinkboost",
        {"problem": "How to optimize Python code?", "context": "Looking for performance improvements"},
    )
    print(f"Status: {result.status}")
    print(f"Output preview: {result.output[:200]}...")
    assert result.status == "success"
    assert "ThinkBoost" in result.output or "Thinking" in result.output
    print("Thinkboost tool test passed!")


async def test_listmodels():
    """Test listmodels tool"""
    print("\n✅ Testing listmodels tool...")
    result = await call_tool_with_result(handle_call_tool, "listmodels", {})
    print(f"Status: {result.status}")
    print(f"Output preview: {result.output[:200]}...")
    assert result.status == "success"
    assert "Available Models" in result.output
    print("Listmodels tool test passed!")


async def test_tool_discovery():
    """Test tool discovery"""
    print("\n✅ Testing tool discovery...")
    tools = await handle_list_tools()
    print(f"Found {len(tools)} tools")

    expected_tools = ["chat", "thinkdeep", "memory", "version", "thinkboost"]
    tool_names = [tool.name for tool in tools]

    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"

    print(f"All expected tools found: {', '.join(expected_tools)}")
    print("Tool discovery test passed!")


async def main():
    """Run all quick validation tests"""
    print("=" * 60)
    print("🚀 Zen MCP Server - Quick Validation Tests")
    print("=" * 60)

    try:
        await test_version()
        await test_thinkboost()
        await test_listmodels()
        await test_tool_discovery()

        print("\n" + "=" * 60)
        print("✅ All quick validation tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
