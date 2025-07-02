# 🎯 XTool MCP Server 快速参考指南

## 🚀 快速命令

### 启动服务器
```bash
# 最简单的启动方式（兼容旧命令）
./quick-start.sh

# 查看实时日志
./quick-start.sh -f

# 查看配置说明
./quick-start.sh -c
```

### Docker 构建
```bash
# 构建最新版本
./build.sh

# 构建指定版本
./build.sh v1.0.0
```

### 代码质量检查
```bash
# 运行代码质量检查
build/scripts/code_quality_checks.sh

# 运行集成测试
build/scripts/run_integration_tests.sh
```

## 📁 新的目录结构

| 目录 | 用途 | 说明 |
|------|------|------|
| `build/` | 构建相关 | Docker文件、构建脚本 |
| `deployment/` | 部署配置 | Compose文件、环境配置 |
| `docs/` | 文档 | 按功能分类的文档 |
| `archives/` | 归档 | 备份文件、历史报告 |
| `tests/` | 测试 | 单元测试、集成测试 |

## 🔧 常用文件位置

### 构建和部署
- **Docker构建**: `build/docker/Dockerfile.lightweight`
- **推送脚本**: `build/docker/docker-push.sh`
- **开发环境**: `deployment/compose/docker-compose.dev.yml`
- **生产环境**: `deployment/compose/docker-compose.prod.yml`
- **环境变量示例**: `deployment/configs/.env.example`

### 脚本工具
- **服务器启动**: `build/scripts/run-server.sh`
- **代码检查**: `build/scripts/code_quality_checks.sh`
- **质量测试**: `build/scripts/run_integration_tests.sh`

### 文档
- **Docker部署指南**: `docs/deployment/DOCKER_DEPLOYMENT_GUIDE.md`
- **快速开始**: `docs/deployment/QUICK_START_DOCKER.md`
- **开发指南**: `docs/development/CLAUDE.md`
- **工具说明**: `docs/tools/`

## 🎨 便捷命令（向后兼容）

我们保留了便捷脚本确保向后兼容：

```bash
# 这些命令仍然有效
./quick-start.sh        # 启动服务器
./build.sh             # Docker构建

# 实际调用的是这些
build/scripts/run-server.sh
build/docker/Dockerfile.lightweight
```

## 🔄 迁移说明

如果您有自动化脚本引用了旧路径，请更新：

### 路径更新对照表

| 旧路径 | 新路径 |
|--------|--------|
| `./run-server.sh` | `build/scripts/run-server.sh` |
| `./docker-compose.dev.yml` | `deployment/compose/docker-compose.dev.yml` |
| `./Dockerfile.lightweight` | `build/docker/Dockerfile.lightweight` |
| `./docker-push.sh` | `build/docker/docker-push.sh` |
| `./code_quality_checks.sh` | `build/scripts/code_quality_checks.sh` |

### CI/CD 更新示例

```yaml
# 旧的CI配置
script:
  - ./run-server.sh -c
  - docker build -f Dockerfile.lightweight .

# 新的CI配置  
script:
  - build/scripts/run-server.sh -c
  - docker build -f build/docker/Dockerfile.lightweight .
```

## 💡 为什么重新整理？

1. **更清晰的结构** - 根目录不再混乱
2. **功能分组** - 相关文件放在一起
3. **便于维护** - 构建、部署、文档分离
4. **符合标准** - 遵循现代项目组织规范
5. **向后兼容** - 保留便捷脚本

## 🆘 问题排查

### 脚本找不到？
```bash
# 确保脚本可执行
chmod +x quick-start.sh build.sh
chmod +x build/scripts/*.sh
```

### Docker构建失败？
```bash
# 检查Dockerfile路径
ls -la build/docker/
```

### 找不到配置文件？
```bash
# 查看配置示例
cat deployment/configs/.env.example
```

---

**🎉 现在您的项目结构更加整洁和专业！** 

如有问题，请查看详细文档：`docs/` 目录中有完整的指南。