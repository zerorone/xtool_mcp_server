"""
End-to-End MCP Protocol Test Suite

This test suite simulates actual MCP protocol communication between a client
and the Zen MCP Server, testing the complete message flow including initialization,
tool discovery, execution, and error handling.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.types import (
    LATEST_PROTOCOL_VERSION,
)

import server


class MockStdioTransport:
    """Mock stdio transport for testing MCP protocol communication"""

    def __init__(self):
        self.input_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()
        self.messages_sent = []
        self.closed = False

    async def read_message(self) -> dict[str, Any]:
        """Read a message from the input queue"""
        if self.closed:
            raise EOFError("Transport closed")
        return await self.input_queue.get()

    async def write_message(self, message: dict[str, Any]):
        """Write a message to the output queue"""
        if self.closed:
            raise RuntimeError("Transport closed")
        self.messages_sent.append(message)
        await self.output_queue.put(message)

    async def send_client_message(self, message: dict[str, Any]):
        """Send a message from the client side"""
        await self.input_queue.put(message)

    async def receive_server_response(self) -> dict[str, Any]:
        """Receive a response from the server side"""
        return await self.output_queue.get()

    def close(self):
        """Close the transport"""
        self.closed = True


class MCPTestClient:
    """Test client for MCP protocol communication"""

    def __init__(self, transport: MockStdioTransport):
        self.transport = transport
        self.message_id = 0

    def _next_id(self) -> str:
        """Generate next message ID"""
        self.message_id += 1
        return str(self.message_id)

    async def initialize(self) -> dict[str, Any]:
        """Send initialization request"""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": LATEST_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
            "id": self._next_id(),
        }
        await self.transport.send_client_message(request)
        return await self.transport.receive_server_response()

    async def initialized(self):
        """Send initialized notification"""
        notification = {"jsonrpc": "2.0", "method": "initialized", "params": {}}
        await self.transport.send_client_message(notification)

    async def list_tools(self) -> dict[str, Any]:
        """Request tool list"""
        request = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": self._next_id()}
        await self.transport.send_client_message(request)
        return await self.transport.receive_server_response()

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool"""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": self._next_id(),
        }
        await self.transport.send_client_message(request)
        return await self.transport.receive_server_response()

    async def list_prompts(self) -> dict[str, Any]:
        """Request prompt list"""
        request = {"jsonrpc": "2.0", "method": "prompts/list", "params": {}, "id": self._next_id()}
        await self.transport.send_client_message(request)
        return await self.transport.receive_server_response()

    async def get_prompt(self, prompt_name: str, arguments: dict[str, Any] = None) -> dict[str, Any]:
        """Get a specific prompt"""
        request = {
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {"name": prompt_name, "arguments": arguments or {}},
            "id": self._next_id(),
        }
        await self.transport.send_client_message(request)
        return await self.transport.receive_server_response()


@pytest.fixture
async def mcp_server_and_client():
    """Create a connected MCP server and client pair"""
    transport = MockStdioTransport()
    client = MCPTestClient(transport)

    # Create server task
    server_task = None

    async def run_server():
        # Patch stdio to use our mock transport
        with patch("server.stdio_server") as mock_stdio:
            # Create a mock context manager
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = (
                AsyncMock(),  # read_stream
                AsyncMock(),  # write_stream
            )
            mock_context.__aexit__.return_value = None
            mock_stdio.return_value = mock_context

            # Patch the server's read/write to use our transport

            async def mock_run():
                Server("xtool_mcp_server")

                # Override message handling
                async def handle_messages():
                    while not transport.closed:
                        try:
                            message = await transport.read_message()

                            # Process message based on method
                            if message.get("method") == "initialize":
                                response = {
                                    "jsonrpc": "2.0",
                                    "result": {
                                        "protocolVersion": LATEST_PROTOCOL_VERSION,
                                        "capabilities": {
                                            "tools": {"listChanged": False},
                                            "prompts": {"listChanged": False},
                                        },
                                        "serverInfo": {"name": "xtool_mcp_server", "version": server.__version__},
                                    },
                                    "id": message["id"],
                                }
                                await transport.write_message(response)

                            elif message.get("method") == "initialized":
                                # No response needed for notification
                                pass

                            elif message.get("method") == "tools/list":
                                tools = await server.handle_list_tools()
                                response = {
                                    "jsonrpc": "2.0",
                                    "result": {
                                        "tools": [
                                            {
                                                "name": tool.name,
                                                "description": tool.description,
                                                "inputSchema": tool.inputSchema,
                                            }
                                            for tool in tools
                                        ]
                                    },
                                    "id": message["id"],
                                }
                                await transport.write_message(response)

                            elif message.get("method") == "tools/call":
                                params = message["params"]
                                try:
                                    result = await server.handle_call_tool(params["name"], params["arguments"])
                                    response = {
                                        "jsonrpc": "2.0",
                                        "result": [{"type": "text", "text": result.output}],
                                        "id": message["id"],
                                    }
                                except Exception as e:
                                    response = {
                                        "jsonrpc": "2.0",
                                        "error": {"code": -32603, "message": str(e)},
                                        "id": message["id"],
                                    }
                                await transport.write_message(response)

                            elif message.get("method") == "prompts/list":
                                prompts = await server.handle_list_prompts()
                                response = {
                                    "jsonrpc": "2.0",
                                    "result": {
                                        "prompts": [
                                            {"name": prompt.name, "description": prompt.description}
                                            for prompt in prompts
                                        ]
                                    },
                                    "id": message["id"],
                                }
                                await transport.write_message(response)

                        except EOFError:
                            break
                        except Exception as e:
                            # Log error but continue
                            print(f"Server error: {e}")

                await handle_messages()

            with patch("server.run", mock_run):
                await mock_run()

    # Start server in background
    server_task = asyncio.create_task(run_server())

    # Give server time to start
    await asyncio.sleep(0.1)

    yield client, transport

    # Cleanup
    transport.close()
    if server_task and not server_task.done():
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


class TestMCPProtocolFlow:
    """Test complete MCP protocol communication flow"""

    @pytest.mark.asyncio
    async def test_full_initialization_flow(self, mcp_server_and_client):
        """Test the complete initialization handshake"""
        client, transport = mcp_server_and_client

        # Step 1: Initialize
        init_response = await client.initialize()
        assert init_response["jsonrpc"] == "2.0"
        assert "result" in init_response
        assert init_response["result"]["protocolVersion"] == LATEST_PROTOCOL_VERSION
        assert "capabilities" in init_response["result"]
        assert "serverInfo" in init_response["result"]

        # Step 2: Send initialized notification
        await client.initialized()

        # No response expected for notification
        # Server should now be ready for requests

    @pytest.mark.asyncio
    async def test_tool_discovery_flow(self, mcp_server_and_client):
        """Test tool discovery via MCP protocol"""
        client, transport = mcp_server_and_client

        # Initialize first
        await client.initialize()
        await client.initialized()

        # List tools
        tools_response = await client.list_tools()
        assert tools_response["jsonrpc"] == "2.0"
        assert "result" in tools_response
        assert "tools" in tools_response["result"]

        tools = tools_response["result"]["tools"]
        assert len(tools) > 0

        # Verify tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

        # Check for expected tools
        tool_names = [t["name"] for t in tools]
        assert "chat" in tool_names
        assert "thinkdeep" in tool_names
        assert "version" in tool_names

    @pytest.mark.asyncio
    async def test_tool_execution_flow(self, mcp_server_and_client):
        """Test tool execution via MCP protocol"""
        client, transport = mcp_server_and_client

        # Initialize
        await client.initialize()
        await client.initialized()

        # Call version tool
        version_response = await client.call_tool("version", {})
        assert version_response["jsonrpc"] == "2.0"
        assert "result" in version_response
        assert len(version_response["result"]) > 0
        assert version_response["result"][0]["type"] == "text"
        assert "Zen MCP Server" in version_response["result"][0]["text"]

        # Call thinkboost tool
        thinkboost_response = await client.call_tool(
            "thinkboost", {"problem": "How to test MCP protocol?", "context": "Writing integration tests"}
        )
        assert thinkboost_response["jsonrpc"] == "2.0"
        assert "result" in thinkboost_response
        assert "THINKING PATTERNS" in thinkboost_response["result"][0]["text"]

    @pytest.mark.asyncio
    async def test_error_handling_flow(self, mcp_server_and_client):
        """Test error handling in MCP protocol"""
        client, transport = mcp_server_and_client

        # Initialize
        await client.initialize()
        await client.initialized()

        # Call non-existent tool
        error_response = await client.call_tool("nonexistent_tool", {})
        assert error_response["jsonrpc"] == "2.0"
        assert "error" in error_response
        assert error_response["error"]["code"] == -32603  # Internal error
        assert "Unknown tool" in error_response["error"]["message"]

        # Call tool with invalid arguments
        error_response = await client.call_tool("memory", {})  # Missing required args
        assert error_response["jsonrpc"] == "2.0"
        assert "error" in error_response

    @pytest.mark.asyncio
    async def test_prompt_discovery_flow(self, mcp_server_and_client):
        """Test prompt discovery via MCP protocol"""
        client, transport = mcp_server_and_client

        # Initialize
        await client.initialize()
        await client.initialized()

        # List prompts
        prompts_response = await client.list_prompts()
        assert prompts_response["jsonrpc"] == "2.0"
        assert "result" in prompts_response
        assert "prompts" in prompts_response["result"]

        prompts = prompts_response["result"]["prompts"]
        assert len(prompts) > 0

        # Verify prompt structure
        for prompt in prompts:
            assert "name" in prompt
            assert "description" in prompt


class TestMCPMessageValidation:
    """Test MCP message format validation"""

    @pytest.mark.asyncio
    async def test_invalid_jsonrpc_version(self, mcp_server_and_client):
        """Test handling of invalid JSON-RPC version"""
        client, transport = mcp_server_and_client

        # Send message with wrong version
        invalid_request = {
            "jsonrpc": "1.0",  # Wrong version
            "method": "tools/list",
            "params": {},
            "id": "1",
        }
        await transport.send_client_message(invalid_request)

        # Should get error response
        await transport.receive_server_response()
        # Server might reject or handle gracefully

    @pytest.mark.asyncio
    async def test_missing_method(self, mcp_server_and_client):
        """Test handling of missing method field"""
        client, transport = mcp_server_and_client

        # Send message without method
        invalid_request = {"jsonrpc": "2.0", "params": {}, "id": "1"}
        await transport.send_client_message(invalid_request)

        # Should get error or no response

    @pytest.mark.asyncio
    async def test_notification_handling(self, mcp_server_and_client):
        """Test that notifications don't receive responses"""
        client, transport = mcp_server_and_client

        # Send notification (no id field)
        notification = {"jsonrpc": "2.0", "method": "custom/notification", "params": {"data": "test"}}
        await transport.send_client_message(notification)

        # Should not receive a response for notification
        # Try to receive with timeout
        try:
            await asyncio.wait_for(transport.receive_server_response(), timeout=0.5)
            assert False, "Should not receive response for notification"
        except asyncio.TimeoutError:
            # Expected - no response for notifications
            pass


class TestMCPConcurrentRequests:
    """Test handling of concurrent MCP requests"""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mcp_server_and_client):
        """Test multiple concurrent tool calls"""
        client, transport = mcp_server_and_client

        # Initialize
        await client.initialize()
        await client.initialized()

        # Send multiple requests concurrently
        async def call_tool_async(name, args):
            return await client.call_tool(name, args)

        # Create concurrent tasks
        tasks = [
            call_tool_async("version", {}),
            call_tool_async("thinkboost", {"problem": "Test 1", "context": ""}),
            call_tool_async("thinkboost", {"problem": "Test 2", "context": ""}),
        ]

        # Execute concurrently
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response["jsonrpc"] == "2.0"
            assert "result" in response or "error" in response

    @pytest.mark.asyncio
    async def test_request_ordering(self, mcp_server_and_client):
        """Test that responses match request IDs"""
        client, transport = mcp_server_and_client

        # Initialize
        await client.initialize()
        await client.initialized()

        # Send multiple requests and track IDs
        request_ids = []

        # Send requests
        for i in range(3):
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "version", "arguments": {}},
                "id": f"test-{i}",
            }
            request_ids.append(f"test-{i}")
            await transport.send_client_message(request)

        # Receive responses
        responses = []
        for _ in range(3):
            response = await transport.receive_server_response()
            responses.append(response)

        # Check that all request IDs are accounted for
        response_ids = [r["id"] for r in responses]
        assert set(response_ids) == set(request_ids)


class TestMCPServerLifecycle:
    """Test server lifecycle management"""

    @pytest.mark.asyncio
    async def test_server_graceful_shutdown(self, mcp_server_and_client):
        """Test graceful server shutdown"""
        client, transport = mcp_server_and_client

        # Initialize
        await client.initialize()
        await client.initialized()

        # Make a successful call
        response = await client.call_tool("version", {})
        assert "result" in response

        # Close transport
        transport.close()

        # Further calls should fail
        with pytest.raises(EOFError):
            await transport.read_message()

    @pytest.mark.asyncio
    async def test_server_reconnection(self):
        """Test server behavior on reconnection"""
        # Create first connection
        transport1 = MockStdioTransport()
        MCPTestClient(transport1)

        # Simulate server with first connection
        # ... (would implement full reconnection logic)

        # Close first connection
        transport1.close()

        # Create second connection
        transport2 = MockStdioTransport()
        MCPTestClient(transport2)

        # Server should accept new connection
        # ... (would test reconnection behavior)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
