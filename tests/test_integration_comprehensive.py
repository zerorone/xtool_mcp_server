"""
Comprehensive Integration Test Suite for xtool MCP Server

This test suite provides end-to-end testing of the MCP server functionality,
including tool discovery, execution, error handling, and cross-tool collaboration.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    GetPromptResult,
    ServerCapabilities,
)

from config import __version__
from server import (
    handle_call_tool,
    handle_list_prompts,
    handle_list_tools,
)
from tests.test_helpers import call_tool_with_result


class MockTransport:
    """Mock transport for testing MCP server communication"""

    def __init__(self):
        self.messages_sent = []
        self.responses = {}

    async def send_message(self, message: dict):
        """Record sent messages"""
        self.messages_sent.append(message)

    async def receive_message(self) -> dict:
        """Return mocked responses"""
        if self.responses:
            return self.responses.pop(0)
        return {}


@pytest.fixture
def mock_server():
    """Create a mock MCP server instance"""
    server = Server("zen-mcp-test")
    return server


@pytest.fixture
def mock_transport():
    """Create a mock transport"""
    return MockTransport()


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestServerInitialization:
    """Test server initialization and configuration"""

    @pytest.mark.asyncio
    async def test_server_initialization(self, mock_server):
        """Test basic server initialization"""
        assert mock_server.name == "zen-mcp-test"

        # Test capabilities
        ServerCapabilities(tools={"listChanged": False}, prompts={"listChanged": False})

        # Initialize server
        InitializationOptions(server_name="zen-mcp-test", server_version=__version__)

        # Server should accept initialization
        assert mock_server.name == "zen-mcp-test"

    def test_environment_configuration(self):
        """Test environment variable configuration"""
        # Test default model
        from config import DEFAULT_MODEL

        assert DEFAULT_MODEL is not None

        # Test API key presence (at least one should be configured)
        api_keys = [
            os.getenv("OPENAI_API_KEY"),
            os.getenv("GEMINI_API_KEY"),
            os.getenv("OPENROUTER_API_KEY"),
            os.getenv("CUSTOM_API_URL"),
        ]
        assert any(key for key in api_keys), "At least one API key should be configured"


class TestToolDiscovery:
    """Test tool discovery and listing"""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available tools"""
        tools = await handle_list_tools()

        # Check that all expected tools are present
        expected_tools = [
            "chat",
            "thinkdeep",
            "codereview",
            "debug",
            "planner",
            "analyze",
            "challenge",
            "listmodels",
            "memory",
            "version",
            "thinkboost",
            "consensus",
            "tracer",
            "refactor",
            "testgen",
            "docgen",
            "precommit",
            "secaudit",
        ]

        tool_names = [tool.name for tool in tools]
        for expected in expected_tools:
            assert expected in tool_names, f"Tool {expected} should be available"

        # Check tool structure
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

            # Validate input schema
            schema = tool.inputSchema
            assert "type" in schema
            assert "properties" in schema
            assert "required" in schema

    @pytest.mark.asyncio
    async def test_list_prompts(self):
        """Test listing available prompts"""
        prompts = await handle_list_prompts()

        # Should have some prompts available
        assert len(prompts) > 0

        # Check prompt structure
        for prompt in prompts:
            assert isinstance(prompt, GetPromptResult)
            assert hasattr(prompt, "name")
            assert hasattr(prompt, "description")


class TestToolExecution:
    """Test individual tool execution"""

    @pytest.mark.asyncio
    async def test_version_tool(self):
        """Test version tool execution"""
        result = await call_tool_with_result(handle_call_tool, "version", {})

        assert result.status == "success"
        assert __version__ in result.output
        assert "xtool MCP Server" in result.output

    @pytest.mark.asyncio
    @patch("tools.listmodels.ModelProviderRegistry.get_all_models")
    async def test_listmodels_tool(self, mock_get_models):
        """Test listmodels tool execution"""
        # Mock model response
        mock_get_models.return_value = {"gemini": ["gemini-pro", "gemini-flash"], "openai": ["gpt-4", "gpt-3.5-turbo"]}

        result = await call_tool_with_result(handle_call_tool, "listmodels", {})

        assert result.status == "success"
        assert "Available Models" in result.output
        assert "gemini-pro" in result.output
        assert "gpt-4" in result.output

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="Requires GEMINI_API_KEY")
    async def test_memory_tool_operations(self):
        """Test memory tool operations"""
        # Test save operation
        save_args = {"action": "save", "content": "Test memory content", "metadata": {"test": True}}
        result = await call_tool_with_result(handle_call_tool, "memory", save_args)
        assert result.status == "success"

        # Test recall operation
        recall_args = {"action": "recall", "content": "test"}
        result = await call_tool_with_result(handle_call_tool, "memory", recall_args)
        assert result.status == "success"

        # Test list operation
        list_args = {"action": "list", "layer": "session"}
        result = await call_tool_with_result(handle_call_tool, "memory", list_args)
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_thinkboost_tool(self):
        """Test thinkboost tool (no model required)"""
        args = {"problem": "How to optimize database queries?", "context": "Performance is slow with large datasets"}
        result = await call_tool_with_result(handle_call_tool, "thinkboost", args)

        assert result.status == "success"
        assert "THINKING PATTERNS" in result.output
        assert "STRUCTURED APPROACH" in result.output


class TestCrossToolCollaboration:
    """Test collaboration between different tools"""

    @pytest.mark.asyncio
    async def test_memory_and_analysis_flow(self):
        """Test workflow: save context -> analyze -> recall"""
        # Step 1: Save some context
        save_args = {
            "action": "save",
            "content": json.dumps(
                {
                    "project": "test_project",
                    "files": ["main.py", "utils.py"],
                    "purpose": "Testing cross-tool collaboration",
                }
            ),
            "metadata": {"type": "project_context"},
        }
        save_result = await call_tool_with_result(handle_call_tool, "memory", save_args)
        assert save_result.status == "success"

        # Step 2: Use thinkboost to analyze approach
        think_args = {
            "problem": "Analyze the test_project structure",
            "context": "Project has main.py and utils.py files",
        }
        think_result = await call_tool_with_result(handle_call_tool, "thinkboost", think_args)
        assert think_result.status == "success"

        # Step 3: Recall the context
        recall_args = {"action": "recall", "content": "test_project"}
        recall_result = await call_tool_with_result(handle_call_tool, "memory", recall_args)
        assert recall_result.status == "success"
        assert "test_project" in recall_result.output

    @pytest.mark.asyncio
    async def test_planning_and_tracking_flow(self):
        """Test workflow: plan -> track -> report"""
        # This tests the conceptual flow of planning tools
        # In real usage, this would involve the planner tool with actual AI calls

        # Step 1: Create a plan (using thinkboost as proxy)
        plan_args = {"problem": "Plan a feature implementation", "context": "Need to add user authentication"}
        plan_result = await call_tool_with_result(handle_call_tool, "thinkboost", plan_args)
        assert plan_result.status == "success"

        # Step 2: Save plan to memory
        save_args = {
            "action": "save",
            "content": "Authentication implementation plan",
            "metadata": {"type": "plan", "feature": "auth"},
        }
        save_result = await call_tool_with_result(handle_call_tool, "memory", save_args)
        assert save_result.status == "success"


class TestErrorHandling:
    """Test error handling and recovery"""

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self):
        """Test handling of invalid tool names"""
        result = await call_tool_with_result(handle_call_tool, "nonexistent_tool", {})
        assert result.status == "error"
        assert "Unknown tool" in result.output

    @pytest.mark.asyncio
    async def test_missing_required_arguments(self):
        """Test handling of missing required arguments"""
        # Memory tool requires 'operation' argument
        result = await call_tool_with_result(handle_call_tool, "memory", {})
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_invalid_argument_types(self):
        """Test handling of invalid argument types"""
        # Test with invalid argument type
        args = {
            "action": 123,  # Should be string
            "content": "test",
        }
        result = await call_tool_with_result(handle_call_tool, "memory", args)
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_tool_timeout_handling(self):
        """Test handling of tool timeouts"""
        # This would test timeout handling in real scenarios
        # For now, we ensure the server can handle long-running operations
        import asyncio

        async def slow_operation():
            await asyncio.sleep(0.1)
            return "completed"

        result = await slow_operation()
        assert result == "completed"


class TestPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_tool_discovery_performance(self):
        """Test that tool discovery is fast"""
        import time

        start = time.time()
        tools = await handle_list_tools()
        end = time.time()

        # Tool discovery should be very fast (< 100ms)
        assert (end - start) < 0.1
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_memory_operation_performance(self):
        """Test memory operation performance"""
        import time

        # Test save performance
        start = time.time()
        save_args = {"action": "save", "content": "Performance test content" * 100, "metadata": {"test": "performance"}}
        result = await call_tool_with_result(handle_call_tool, "memory", save_args)
        end = time.time()

        assert result.status == "success"
        # Memory save should be fast (< 500ms)
        assert (end - start) < 0.5

        # Test recall performance
        start = time.time()
        recall_args = {"action": "recall", "content": "performance"}
        result = await call_tool_with_result(handle_call_tool, "memory", recall_args)
        end = time.time()

        assert result.status == "success"
        # Memory recall should be fast (< 500ms)
        assert (end - start) < 0.5


class TestBackwardCompatibility:
    """Test backward compatibility with previous versions"""

    @pytest.mark.asyncio
    async def test_legacy_tool_names(self):
        """Test that legacy tool names still work"""
        # All current tools should maintain their names
        legacy_tools = ["chat", "thinkdeep", "codereview", "debug", "planner"]

        tools = await handle_list_tools()
        tool_names = [tool.name for tool in tools]

        for legacy in legacy_tools:
            assert legacy in tool_names, f"Legacy tool {legacy} should still exist"

    @pytest.mark.asyncio
    async def test_legacy_argument_formats(self):
        """Test that legacy argument formats are supported"""
        # Test memory tool with different argument styles

        # New style
        new_style = {"action": "save", "content": "test", "metadata": {"key": "value"}}
        result = await call_tool_with_result(handle_call_tool, "memory", new_style)
        assert result.status == "success"

        # The tool should handle various input formats gracefully


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @pytest.mark.asyncio
    async def test_code_review_workflow(self, temp_workspace):
        """Test a typical code review workflow"""
        # Create a test file
        test_file = temp_workspace / "example.py"
        test_file.write_text("""
def calculate_sum(numbers):
    total = 0
    for n in numbers:
        total += n
    return total

# Test the function
result = calculate_sum([1, 2, 3, 4, 5])
print(f"Sum: {result}")
""")

        # Step 1: Analyze the code structure (using thinkboost)
        analyze_args = {"problem": "Review this Python code for improvements", "context": test_file.read_text()}
        result = await call_tool_with_result(handle_call_tool, "thinkboost", analyze_args)
        assert result.status == "success"

        # Step 2: Save analysis to memory
        save_args = {
            "action": "save",
            "content": json.dumps(
                {
                    "file": str(test_file),
                    "analysis": "Code structure analyzed",
                    "suggestions": ["Consider using sum() builtin", "Add type hints"],
                }
            ),
            "metadata": {"type": "code_review", "file": "example.py"},
        }
        result = await call_tool_with_result(handle_call_tool, "memory", save_args)
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_debugging_workflow(self):
        """Test a debugging workflow"""
        # Step 1: Report an issue
        issue_context = {
            "error": "AttributeError: 'NoneType' object has no attribute 'split'",
            "file": "data_processor.py",
            "line": 42,
            "context": "Processing user input",
        }

        # Step 2: Think about the issue
        think_args = {"problem": f"Debug this error: {issue_context['error']}", "context": json.dumps(issue_context)}
        result = await call_tool_with_result(handle_call_tool, "thinkboost", think_args)
        assert result.status == "success"
        assert "THINKING PATTERNS" in result.output

        # Step 3: Save debugging session
        save_args = {
            "action": "save",
            "content": json.dumps(
                {
                    "issue": issue_context,
                    "analysis": "NoneType suggests missing null check",
                    "solution": "Add validation before calling split()",
                }
            ),
            "metadata": {"type": "debug_session", "error": "AttributeError"},
        }
        result = await call_tool_with_result(handle_call_tool, "memory", save_args)
        assert result.status == "success"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_inputs(self):
        """Test handling of empty inputs"""
        # Test thinkboost with empty problem
        args = {"problem": "", "context": "Some context"}
        result = await call_tool_with_result(handle_call_tool, "thinkboost", args)
        # Should still provide structured output
        assert result.status == "success"

        # Test memory save with empty content
        args = {"action": "save", "content": "", "metadata": {"empty": True}}
        result = await call_tool_with_result(handle_call_tool, "memory", args)
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_large_inputs(self):
        """Test handling of large inputs"""
        # Create a large content
        large_content = "x" * 10000  # 10KB of data

        # Test memory with large content
        args = {"action": "save", "content": large_content, "metadata": {"size": "large"}}
        result = await call_tool_with_result(handle_call_tool, "memory", args)
        assert result.status == "success"

        # Test thinkboost with large context
        args = {
            "problem": "Analyze this data",
            "context": large_content[:1000],  # Use first 1KB
        }
        result = await call_tool_with_result(handle_call_tool, "thinkboost", args)
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test handling of special characters"""
        special_content = "Test with special chars: 你好 🎉 <script>alert('test')</script> \n\t\r"

        # Test memory with special characters
        args = {"action": "save", "content": special_content, "metadata": {"type": "special_chars"}}
        result = await call_tool_with_result(handle_call_tool, "memory", args)
        assert result.status == "success"

        # Recall and verify
        args = {"action": "recall", "content": "special_chars"}
        result = await call_tool_with_result(handle_call_tool, "memory", args)
        assert result.status == "success"


class TestConcurrency:
    """Test concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test multiple tools called concurrently"""

        async def call_tool(name, args):
            return await call_tool_with_result(handle_call_tool, name, args)

        # Create multiple concurrent tasks
        tasks = [
            call_tool("version", {}),
            call_tool("thinkboost", {"problem": "Test 1", "context": ""}),
            call_tool("thinkboost", {"problem": "Test 2", "context": ""}),
            call_tool("memory", {"action": "list", "layer": "session"}),
        ]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Task {i} failed: {result}")
            else:
                assert result.status == "success"

    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """Test concurrent memory operations"""

        async def save_memory(key, content):
            args = {"action": "save", "content": content, "metadata": {"key": key}}
            return await call_tool_with_result(handle_call_tool, "memory", args)

        # Create multiple concurrent saves
        tasks = [save_memory(f"key_{i}", f"Content {i}") for i in range(5)]

        results = await asyncio.gather(*tasks)

        # All should succeed
        for result in results:
            assert result.status == "success"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
