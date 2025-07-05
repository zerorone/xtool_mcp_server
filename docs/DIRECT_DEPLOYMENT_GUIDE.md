# 直接部署指南

本指南介绍如何像其他 MCP 服务器一样，直接部署和使用 xtool-mcp-server，无需 Docker。

## 🔒 核心特性：记忆隔离

**最重要的特性**：每个项目都有独立的 `.xtool_memory/` 目录，确保：
- ✅ 不同项目的记忆数据完全隔离
- ✅ 项目间不会相互干扰  
- ✅ 每个项目维护自己的上下文和历史
- ✅ 支持多个项目同时使用同一个XTool安装

## 部署方式对比

### 1. 直接运行（推荐）

类似于其他 MCP 服务器（如 @playwright/mcp），直接在宿主机运行：

**优点：**
- ⭐ **记忆隔离**：每个项目独立的 `.xtool_memory` 目录
- 无需 Docker，部署简单
- 与其他 MCP 服务器保持一致的使用体验
- 路径访问无障碍
- 多项目并行使用，互不干扰

**配置示例：**
```json
{
  "mcpServers": {
    "xtool-mcp": {
      "command": "python3",
      "args": [
        "/path/to/xtool-mcp-server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/xtool-mcp-server",
        "LOG_LEVEL": "INFO",
        "DEFAULT_MODEL": "google/gemini-2.5-flash",
        "MEMORY_TOOL_MODEL": "google/gemini-2.5-flash"
      }
    }
  }
}
```

### 2. 使用 uvx（即将支持）

发布到 PyPI 后，可以像其他 MCP 服务器一样使用 uvx：

```json
{
  "mcpServers": {
    "xtool-mcp": {
      "command": "uvx",
      "args": ["xtool-mcp-server"],
      "env": {
        "LOG_LEVEL": "INFO",
        "DEFAULT_MODEL": "google/gemini-2.5-flash"
      }
    }
  }
}
```

### 3. Docker 方式（复杂场景）

仅在需要隔离环境或分布式部署时使用 Docker。

## 快速开始

### 步骤 1：克隆仓库

```bash
git clone https://github.com/yourusername/xtool-mcp-server.git
cd xtool-mcp-server
```

### 步骤 2：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 3：在项目中配置

在你的项目根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "xtool-mcp": {
      "command": "python3",
      "args": [
        "/Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool-mcp-server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool-mcp-server",
        "LOG_LEVEL": "INFO",
        "DEFAULT_MODEL": "google/gemini-2.5-flash",
        "MEMORY_TOOL_MODEL": "google/gemini-2.5-flash"
      }
    }
  }
}
```

### 步骤 4：使用

启动 Claude Desktop，它会自动在你的项目目录运行 xtool-mcp-server，记忆文件会保存在：
- `{你的项目}/.xtool_memory/` - 项目级记忆
- `~/.xtool_global_memory/` - 全局记忆

## 记忆系统工作原理

直接运行时，xtool-mcp-server 会：

1. **自动检测运行环境**：
   - 如果在 Docker 中：使用 `/app/.xtool_memory`
   - 如果直接运行：使用当前工作目录的 `.xtool_memory`

2. **三层记忆结构**：
   - **全局记忆**：`~/.xtool_global_memory/global/`
   - **项目记忆**：`{项目目录}/.xtool_memory/project/`
   - **会话记忆**：`{项目目录}/.xtool_memory/session/`

3. **自动创建目录**：
   首次运行时会自动创建所需的记忆目录结构。

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DEFAULT_MODEL` | `auto` | 默认模型 |
| `MEMORY_TOOL_MODEL` | `google/gemini-2.5-flash` | 记忆工具使用的模型 |
| `OPENROUTER_API_KEY` | - | OpenRouter API 密钥 |
| `CLAUDE_API_KEY` | - | Claude API 密钥 |
| `OPENAI_API_KEY` | - | OpenAI API 密钥 |

## 迁移指南

### 从 Docker 迁移到直接运行

1. **更新 .mcp.json**：
   ```json
   // 旧配置（Docker）
   {
     "mcpServers": {
       "xtool-mcp": {
         "command": "./.xtool-mcp-wrapper.sh"
       }
     }
   }
   
   // 新配置（直接运行）
   {
     "mcpServers": {
       "xtool-mcp": {
         "command": "python3",
         "args": ["/path/to/xtool-mcp-server/server.py"],
         "env": {
           "PYTHONPATH": "/path/to/xtool-mcp-server"
         }
       }
     }
   }
   ```

2. **删除 wrapper 脚本**：
   ```bash
   rm .xtool-mcp-wrapper.sh
   ```

3. **记忆文件会自动保留**：
   记忆文件仍然保存在 `.xtool_memory` 目录，无需迁移。

## 故障排除

### 1. 记忆文件保存位置错误

确保：
- 使用直接运行方式而非 Docker
- Claude Desktop 在项目目录中启动 MCP 服务器
- 检查当前工作目录：在工具中使用 `pwd` 命令

### 2. Python 版本问题

需要 Python 3.10 或更高版本：
```bash
python3 --version
```

### 3. 依赖问题

重新安装依赖：
```bash
pip install -r requirements.txt --upgrade
```

## 最佳实践

1. **项目级配置**：每个项目都有自己的 `.mcp.json`
2. **记忆隔离**：每个项目的记忆保存在各自的 `.xtool_memory` 目录
3. **版本控制**：将 `.xtool_memory` 添加到 `.gitignore`
4. **环境变量**：敏感信息通过环境变量传递，不要硬编码

## 总结

直接部署方式让 xtool-mcp-server 的使用更加简单直观，与其他 MCP 服务器保持一致。记忆文件会正确保存在各个项目目录中，无需复杂的 Docker 卷映射。