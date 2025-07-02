# XTool MCP Server 项目结构重组总结

## 项目概述
- **项目名称**: XTool MCP Server（原 zen-mcp-server）
- **项目类型**: AI Model Context Protocol 服务器
- **支持功能**: 22+ 种AI工具（分析、调试、重构、代码审查等）
- **支持模型**: Gemini、OpenAI、OpenRouter、XAI、自定义模型

## 重组目标
将原本扁平化的项目结构重新组织为分层明确、职责清晰的专业目录结构，提高项目的可维护性和易用性。

## 新目录结构

### 1. build/ - 构建相关文件
```
build/
├── docker/              # Docker构建文件
│   ├── Dockerfile       # 主Dockerfile
│   └── Dockerfile.lightweight  # 轻量级Dockerfile
└── scripts/             # 构建和部署脚本
    ├── run-server.sh    # 服务器启动脚本
    ├── code_quality_checks.sh  # 代码质量检查
    └── 其他构建脚本
```

### 2. deployment/ - 部署配置
```
deployment/
├── compose/             # Docker Compose文件
│   ├── docker-compose.dev.yml     # 开发环境
│   ├── docker-compose.prod.yml    # 生产环境
│   └── docker-compose.enhanced.yml # 增强环境
└── configs/             # 配置文件
    ├── .env.example     # 环境变量示例
    ├── pyproject.toml   # Python项目配置
    └── 其他配置文件
```

### 3. docs/ - 文档
```
docs/
├── deployment/          # 部署相关文档
│   ├── DOCKER_DEPLOYMENT_GUIDE.md
│   └── QUICK_START_DOCKER.md
├── development/         # 开发相关文档
│   ├── CLAUDE.md        # Claude Code指南
│   ├── CLAUDE_CODE_SETUP.md
│   └── PROJECT_STRUCTURE.md
└── tools/               # 工具说明文档
    ├── analyze.md
    ├── debug.md
    └── 其他工具文档
```

### 4. archives/ - 归档文件
```
archives/
├── backups/             # 备份文件
│   └── *.zen_backup     # 重命名过程中的备份
└── reports/             # 项目报告和变更日志
    ├── CHANGELOG.md
    ├── PROJECT_RENAME_FINAL_REPORT.md
    └── 其他报告文件
```

### 5. tests/ - 测试文件
```
tests/
├── integration/         # 集成测试
│   ├── test_all_tools_comprehensive.py
│   ├── test_memory_features.py
│   └── 其他集成测试
└── 其他单元测试文件
```

## 重要的便捷脚本

### 根目录便捷脚本
为了保持向后兼容性，在根目录保留了以下便捷脚本：

1. **quick-start.sh** - 快速启动脚本
   - 调用 `build/scripts/run-server.sh`
   - 提供最简单的启动方式

2. **build.sh** - Docker构建脚本
   - 简化Docker镜像构建过程

3. **healthcheck.py** - Docker健康检查脚本
   - 容器健康状态检查

## 路径更新对照表

| 原路径 | 新路径 |
|--------|--------|
| `./run-server.sh` | `build/scripts/run-server.sh` |
| `./docker-compose.dev.yml` | `deployment/compose/docker-compose.dev.yml` |
| `./Dockerfile.lightweight` | `build/docker/Dockerfile.lightweight` |
| `./code_quality_checks.sh` | `build/scripts/code_quality_checks.sh` |

## 向后兼容性措施

1. **保留便捷脚本**: 在根目录保留关键的启动和构建脚本
2. **更新文档引用**: 修改 README.md 和 CLAUDE.md 中所有路径引用
3. **更新构建配置**: 修改 .dockerignore 排除规则
4. **创建快速参考**: 新增 QUICK_REFERENCE.md 提供快速上手指南

## 重组带来的好处

### 1. 项目结构更加专业化
- 清晰的目录层次结构
- 职责分离明确
- 符合现代软件项目标准

### 2. 提高可维护性
- 相关文件集中管理
- 减少根目录文件混乱
- 便于后续扩展和维护

### 3. 提高易用性
- 保留便捷脚本确保易用性
- 清晰的文档结构便于查找
- 专业化部署配置管理

### 4. 改善开发体验
- 开发者能更快定位相关文件
- 新人上手更容易
- 项目结构一目了然

## 重要提醒

1. **启动方式**: 现在可以使用 `./quick-start.sh` 或 `build/scripts/run-server.sh` 启动服务器
2. **文档查找**: 所有文档现在按类型分类存放在 `docs/` 目录下
3. **部署配置**: Docker相关配置文件现在统一在 `deployment/` 目录
4. **测试运行**: 集成测试现在在 `tests/integration/` 目录下

## 总结

此次项目结构重组是 XTool MCP Server 迈向专业化的重要里程碑。新的目录结构不仅提高了项目的专业性和可维护性，同时通过保留便捷脚本确保了向后兼容性，为项目的长期发展奠定了坚实基础。