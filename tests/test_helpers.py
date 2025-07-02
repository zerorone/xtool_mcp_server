"""
Test helpers for xtool MCP Server tests

This module provides helper functions to handle the actual return format
from the MCP server tools.
"""

import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ToolResult:
    """Helper class to parse tool execution results"""

    status: str
    output: str
    model: Optional[str] = None
    usage: Optional[dict[str, Any]] = None

    @classmethod
    def from_mcp_response(cls, response: list[Any]) -> "ToolResult":
        """Convert MCP response format to ToolResult"""
        if not response or not isinstance(response, list):
            return cls(status="error", output="Invalid response format")

        # Extract text content from first item
        first_item = response[0]
        if hasattr(first_item, "text"):
            text_content = first_item.text
        elif hasattr(first_item, "content"):
            text_content = first_item.content
        else:
            text_content = str(first_item)

        # Try to parse as JSON ToolOutput
        try:
            data = json.loads(text_content)
            # Handle different output field names
            output_content = data.get("output") or data.get("content", "")
            return cls(
                status=data.get("status", "unknown"),
                output=output_content,
                model=data.get("model"),
                usage=data.get("usage"),
            )
        except (json.JSONDecodeError, AttributeError):
            # If not JSON, treat as plain text output
            return cls(status="success" if text_content else "error", output=text_content)


async def call_tool_with_result(handle_call_tool_func, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
    """
    Call a tool and return a normalized ToolResult object

    Args:
        handle_call_tool_func: The handle_call_tool function from server
        tool_name: Name of the tool to call
        arguments: Arguments for the tool

    Returns:
        ToolResult object with normalized response
    """
    response = await handle_call_tool_func(tool_name, arguments)
    return ToolResult.from_mcp_response(response)
