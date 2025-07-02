# 🔄 Migration Guide: v5.x to v6.0

This guide helps you migrate from xtool MCP Server v5.x to v6.0.

## Overview

Version 6.0 is a major release that includes significant enhancements while maintaining backward compatibility for most features. The primary changes involve new capabilities rather than breaking changes.

## What's New in v6.0

### 1. Enhanced Memory System
- **Three-layer architecture**: Global, Project, and Session memory
- **Auto-detection**: Automatically detects and remembers project context
- **Smart saving**: Intelligently chooses the appropriate memory layer

### 2. Thinking Patterns Integration
- **25 expert thinking modes**: Each tool now supports multiple thinking patterns
- **Auto-selection**: System can automatically choose appropriate patterns
- **Pattern learning**: Learns from user preferences over time

### 3. Comprehensive Testing
- **Full test suite**: Integration, E2E, performance, and collaboration tests
- **91.1% coverage**: Extensive test coverage for reliability
- **Test infrastructure**: Helpers and runners for easy testing

### 4. Enhanced Documentation
- **Multi-language support**: Chinese documentation added
- **Comprehensive guides**: User guide, API setup guide, migration guide
- **Better examples**: More practical examples and use cases

## Migration Steps

### Step 1: Update Your Installation

```bash
# Pull the latest changes
cd xtool_mcp_server
git pull origin main

# Re-run the setup script
./run-server.sh
```

### Step 2: Review Configuration Changes

#### New Environment Variables (Optional)
```env
# Enhanced Memory System
ENABLE_ENHANCED_MEMORY=true  # Default: true
MEMORY_STORAGE_PATH=.XTOOL_memory  # Default: .XTOOL_memory
AUTO_DETECT_ENV=true  # Default: true
AUTO_SAVE_MEMORY=true  # Default: true

# Memory Limits
MEMORY_GLOBAL_MAX_ITEMS=10000
MEMORY_PROJECT_MAX_ITEMS=5000
MEMORY_SESSION_MAX_ITEMS=1000

# Thinking Modes
ENABLE_THINKING_MODES=true  # Default: true
THINKING_AUTO_MODE=true  # Default: true
THINKING_MAX_MODES=5
THINKING_LEARN_PATTERNS=true  # Default: true
```

### Step 3: Update Your Workflows

#### Memory Tool Changes
The memory tool now uses `action` parameter instead of `operation`:

**Old way (v5.x):**
```
使用 memory 工具：
operation: save
content: 项目信息
```

**New way (v6.0):**
```
使用 memory 工具：
action: save
content: 项目信息
```

#### Thinking Modes
Tools now support thinking mode specification:

```
使用 thinkdeep 工具：
prompt: 分析这个架构
thinking_modes: systematic,critical,strategic
```

### Step 4: Leverage New Features

#### 1. Project Context Auto-Detection
When you start working on a project, Zen automatically detects:
- Git repository information
- Project structure
- Dependencies
- TODO files

#### 2. Smart Memory Layers
```
# Global memory - persists across all projects
使用 memory 工具：
保存到全局：我的常用代码模式是...

# Project memory - specific to current project
使用 memory 工具：
保存：这个项目使用 Django 框架

# Session memory - temporary for current session
使用 memory 工具：
临时保存：当前调试的变量值
```

#### 3. Enhanced Workflows
Workflows now track confidence levels:
- `exploring` - Initial investigation
- `low` - Some understanding
- `medium` - Good understanding
- `high` - Strong confidence
- `certain` - Complete confidence

### Step 5: Test Your Setup

Run the comprehensive test suite:
```bash
# Run all tests
./run_comprehensive_tests.py

# Run specific test categories
python -m pytest tests/test_integration_comprehensive.py -v
```

## Breaking Changes

### Minimal Breaking Changes
1. **Memory tool parameter**: `operation` → `action`
2. **Model category**: `ToolModelCategory.ANALYTICAL` → `ToolModelCategory.BALANCED`

### Deprecated Features
None - all v5.x features are maintained.

## Troubleshooting

### Common Issues

#### 1. Memory Tool Errors
**Error**: "Field 'action' required"
**Solution**: Update your memory tool calls to use `action` instead of `operation`

#### 2. Test Failures
**Error**: "AttributeError: 'list' object has no attribute 'status'"
**Solution**: Tests now use the test_helpers module for response normalization

#### 3. Missing Dependencies
**Error**: "ModuleNotFoundError: No module named 'pytest'"
**Solution**: Re-run `./run-server.sh` to install new dependencies

### Getting Help

1. **Check logs**:
   ```bash
   tail -f logs/mcp_server.log
   ```

2. **Run diagnostics**:
   ```
   使用 version 工具查看系统状态
   使用 listmodels 工具确认模型可用性
   ```

3. **Community support**:
   - [GitHub Issues](https://github.com/gptopencn/xtool_mcp_server/issues)
   - [Discussions](https://github.com/gptopencn/xtool_mcp_server/discussions)

## Best Practices for v6.0

### 1. Utilize Memory Layers
- Use global memory for personal preferences and patterns
- Use project memory for project-specific context
- Use session memory for temporary debugging data

### 2. Leverage Thinking Modes
- Let auto-mode select patterns for you
- Specify modes for specialized tasks
- Review pattern usage in memory analysis

### 3. Run Tests Regularly
- Use the test suite to validate your setup
- Create custom tests for your workflows
- Monitor performance with stress tests

### 4. Keep Documentation Handy
- Refer to USER_GUIDE.md for detailed usage
- Check API_KEY_SETUP.md for provider configuration
- Use README_CN.md if you prefer Chinese documentation

## Summary

Version 6.0 brings powerful enhancements while maintaining the simplicity and reliability you expect from xtool MCP Server. The migration is straightforward with minimal breaking changes, and the new features significantly enhance your AI-assisted development experience.

Welcome to xtool MCP Server v6.0! 🚀