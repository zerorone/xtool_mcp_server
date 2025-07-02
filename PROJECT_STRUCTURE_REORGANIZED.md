# 🗂️ XTool MCP Server 项目结构重组说明

## 概述

为了提高项目的可维护性和可读性，我们对根目录进行了重新整理，将文件按功能分门别类。

## 新的目录结构

```
xtool-mcp-server/
├── 📁 build/                      # 构建相关文件
│   ├── docker/                     # Docker构建文件
│   │   ├── Dockerfile              # 标准Dockerfile
│   │   ├── Dockerfile.lightweight  # 轻量级Dockerfile
│   │   ├── docker-push.sh          # Docker镜像推送脚本
│   │   ├── docker-start.sh         # Docker启动脚本
│   │   └── core/                   # Docker核心脚本
│   └── scripts/                    # 构建和部署脚本
│       ├── build_and_publish.sh    # 构建发布脚本
│       ├── deploy_to_project.sh    # 项目部署脚本
│       ├── prepare_release.sh      # 发布准备脚本
│       ├── code_quality_checks.*   # 代码质量检查
│       ├── run-server.*            # 服务器运行脚本
│       └── setup-claude-code.sh    # Claude Code 设置
│
├── 📁 deployment/                  # 部署配置
│   ├── compose/                    # Docker Compose文件
│   │   ├── docker-compose.yml      # 标准compose配置
│   │   ├── docker-compose.dev.yml  # 开发环境配置
│   │   ├── docker-compose.prod.yml # 生产环境配置
│   │   └── docker-compose.enhanced.yml # 增强配置
│   └── configs/                    # 配置文件
│       ├── .env.example            # 环境变量示例
│       ├── claude_code_config.json # Claude Code配置
│       ├── claude_config_example.json # Claude配置示例
│       ├── pyproject.toml          # Python项目配置
│       └── pytest.ini              # 测试配置
│
├── 📁 archives/                    # 归档文件
│   ├── backups/                    # 备份文件
│   │   └── *.zen_backup            # 所有备份文件
│   ├── reports/                    # 各种报告
│   │   ├── *REPORT*.md             # 项目报告
│   │   ├── CHANGELOG*.md           # 变更日志
│   │   └── comprehensive_test_results.json # 测试结果
│   └── global_zen_to_xtool_rename.py # 重命名脚本
│
├── 📁 core/                        # 核心代码（保持不变）
│   ├── server.py                   # 主服务器
│   ├── config.py                   # 配置模块
│   ├── tools/                      # 工具模块
│   ├── providers/                  # AI提供者
│   ├── utils/                      # 工具函数
│   ├── systemprompts/              # 系统提示
│   └── config_data/                # 配置数据
│
├── 📁 tests/                       # 测试文件（重新整理）
│   ├── integration/                # 集成测试
│   │   ├── test_*.py               # 从根目录移动的测试
│   │   └── ...
│   ├── simulator_tests/            # 模拟器测试
│   └── test_simulation_files/      # 测试文件
│
├── 📁 docs/                        # 文档（重新整理）
│   ├── deployment/                 # 部署相关文档
│   │   ├── DOCKER_DEPLOYMENT_GUIDE.md # Docker部署指南
│   │   ├── QUICK_START_DOCKER.md   # 快速开始指南
│   │   └── ...
│   ├── development/                # 开发相关文档
│   │   ├── CLAUDE.md               # Claude使用指南
│   │   ├── CLAUDE_CODE_SETUP.md    # Claude Code设置
│   │   ├── PROJECT_STRUCTURE.md    # 项目结构说明
│   │   └── ...
│   └── tools/                      # 工具文档
│
├── 📁 examples/                    # 示例文件（保持不变）
├── 📁 patch/                       # 补丁文件（保持不变）
├── 📁 conf/                        # 运行时配置（保持不变）
├── 📁 logs/                        # 日志文件（保持不变）
│
├── 📄 README.md                    # 主要说明文件
├── 📄 LICENSE                      # 许可证
├── 📄 requirements.txt             # Python依赖
├── 📄 requirements-dev.txt         # 开发依赖
└── 📄 PROJECT_STRUCTURE_REORGANIZED.md # 本文档
```

## 文件移动映射

### 🐳 Docker相关文件
- `Dockerfile*` → `build/docker/`
- `docker-*.sh` → `build/docker/`
- `docker-*.yml` → `deployment/compose/`
- `docker/` → `build/docker/core/`

### 🔧 脚本文件
- `*.sh` → `build/scripts/`
- `*.ps1` → `build/scripts/`
- `scripts/*` → `build/scripts/`

### ⚙️ 配置文件
- `claude_*.json` → `deployment/configs/`
- `.env.example` → `deployment/configs/`
- `pyproject.toml` → `deployment/configs/`
- `pytest.ini` → `deployment/configs/`

### 📦 备份和报告
- `*.zen_backup` → `archives/backups/`
- `*REPORT*.md` → `archives/reports/`
- `CHANGELOG*.md` → `archives/reports/`
- `*.json` (测试结果等) → `archives/reports/`

### 🧪 测试文件
- `test_*.py` (根目录) → `tests/integration/`

### 📚 文档重组
- `DOCKER_DEPLOYMENT_GUIDE.md` → `docs/deployment/`
- `QUICK_START_DOCKER.md` → `docs/deployment/`
- `CLAUDE*.md` → `docs/development/`
- `PROJECT_STRUCTURE.md` → `docs/development/`

## 更新的引用路径

### Docker构建命令更新
```bash
# 旧命令
docker build -f Dockerfile .
docker build -f Dockerfile.lightweight .

# 新命令
docker build -f build/docker/Dockerfile .
docker build -f build/docker/Dockerfile.lightweight .
```

### Docker Compose 命令更新
```bash
# 旧命令
docker-compose -f docker-compose.dev.yml up

# 新命令
docker-compose -f deployment/compose/docker-compose.dev.yml up
```

### 脚本运行更新
```bash
# 旧命令
./run-server.sh
./code_quality_checks.sh

# 新命令
build/scripts/run-server.sh
build/scripts/code_quality_checks.sh
```

## 好处

### ✅ 提高可维护性
- 根目录更简洁，核心文件清晰可见
- 相关文件分组管理，便于查找
- 构建、部署、文档分离

### ✅ 更好的组织结构
- Docker相关文件集中管理
- 配置文件统一存放
- 历史文件归档处理

### ✅ 便于自动化
- 构建脚本集中在 `build/` 目录
- 部署配置集中在 `deployment/` 目录
- CI/CD 流程更清晰

### ✅ 文档结构优化
- 部署文档与开发文档分离
- 工具文档独立维护
- 便于文档查找和维护

## 注意事项

1. **CI/CD 更新**: 如果有 CI/CD 流程，需要更新相关路径
2. **脚本引用**: 更新其他脚本中的文件路径引用
3. **文档链接**: 更新文档中的内部链接
4. **Docker 构建**: 更新 Dockerfile 和 compose 文件的路径

## 后续工作

- [ ] 更新 CI/CD 配置文件
- [ ] 更新 README.md 中的路径引用
- [ ] 检查并更新脚本中的相对路径
- [ ] 更新文档中的链接引用
- [ ] 测试所有构建和部署流程

## 回滚说明

如果需要回滚到原来的结构，可以使用以下脚本：
```bash
# 将所有文件移回根目录（不推荐）
find build/ deployment/ archives/ -type f -exec mv {} . \;
```

但建议保持新的结构，因为它更符合现代项目的组织规范。