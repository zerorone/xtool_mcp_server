# Gemini CLI Setup

> **Note**: While xtool MCP Server connects successfully to Gemini CLI, tool invocation is not working
> correctly yet. We'll update this guide once the integration is fully functional.

This guide explains how to configure xtool MCP Server to work with [Gemini CLI](https://github.com/google-gemini/gemini-cli).

## Prerequisites

- xtool MCP Server installed and configured
- Gemini CLI installed
- At least one API key configured in your `.env` file

## Configuration

1. Edit `~/.gemini/settings.json` and add:

```json
{
  "mcpServers": {
    "zen": {
      "command": "/path/to/xtool_mcp_server/xtool_mcp_server"
    }
  }
}
```

2. Replace `/path/to/xtool_mcp_server` with your actual Zen installation path.

3. If the `xtool_mcp_server` wrapper script doesn't exist, create it:

```bash
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec xtool_venv/bin/python server.py "$@"
```

Then make it executable: `chmod +x xtool_mcp_server`

4. Restart Gemini CLI.

All 15 Xtool tools are now available in your Gemini CLI session.