#!/usr/bin/env python3
"""
旅游平台数据爬虫系统 - 增强版脚手架生成器
提供交互式项目创建体验，支持模块化选择和配置
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from datetime import datetime

# ANSI颜色代码
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message: str, color: str = Colors.WHITE, bold: bool = False):
    """打印带颜色的消息"""
    prefix = f"{color}{Colors.BOLD if bold else ''}"
    suffix = Colors.RESET
    print(f"{prefix}{message}{suffix}")

def print_banner():
    """打印横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║          旅游平台数据爬虫系统 - 智能脚手架生成器              ║
    ║                     Travel Crawler Scaffold                  ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print_colored(banner, Colors.CYAN, bold=True)

class ProjectConfig:
    """项目配置类"""
    def __init__(self):
        self.project_name = "travel-crawler-system"
        self.python_version = "3.11"
        self.selected_platforms = []
        self.selected_features = []
        self.deployment_options = []
        self.database_type = "postgresql"
        self.use_docker = True
        self.use_k8s = False
        self.author_name = ""
        self.author_email = ""

class ScaffoldGenerator:
    """脚手架生成器"""
    
    # 支持的平台
    PLATFORMS = {
        "amap": "高德地图",
        "mafengwo": "马蜂窝",
        "dianping": "大众点评",
        "ctrip": "携程",
        "xiaohongshu": "小红书",
        "douyin": "抖音",
        "weibo": "微博",
        "bilibili": "B站"
    }
    
    # 可选特性
    FEATURES = {
        "dual_engine": "双引擎架构 (Crawl4AI + MediaCrawl)",
        "anti_detection": "三层反爬系统",
        "data_processing": "数据处理流水线",
        "api_service": "RESTful API服务",
        "jwt_auth": "JWT认证系统",
        "monitoring": "Prometheus + Grafana监控",
        "scheduler": "分布式任务调度",
        "export": "数据导出功能"
    }
    
    # 部署选项
    DEPLOYMENT = {
        "docker": "Docker容器化",
        "docker_compose": "Docker Compose编排",
        "kubernetes": "Kubernetes部署",
        "helm": "Helm Chart",
        "ci_cd": "CI/CD流水线"
    }
    
    def __init__(self):
        self.config = ProjectConfig()
        self.project_path = None
    
    def run(self):
        """运行脚手架生成器"""
        print_banner()
        
        # 交互式配置
        if not self.parse_arguments():
            self.interactive_config()
        
        # 确认配置
        if not self.confirm_config():
            print_colored("已取消创建项目", Colors.YELLOW)
            return
        
        # 创建项目
        self.create_project()
        
        # 显示完成信息
        self.show_completion_info()
    
    def parse_arguments(self) -> bool:
        """解析命令行参数"""
        parser = argparse.ArgumentParser(description="旅游平台数据爬虫系统脚手架生成器")
        parser.add_argument("--name", help="项目名称")
        parser.add_argument("--platforms", nargs="+", choices=list(self.PLATFORMS.keys()), 
                          help="选择平台")
        parser.add_argument("--all-platforms", action="store_true", help="选择所有平台")
        parser.add_argument("--features", nargs="+", choices=list(self.FEATURES.keys()),
                          help="选择特性")
        parser.add_argument("--all-features", action="store_true", help="选择所有特性")
        parser.add_argument("--no-docker", action="store_true", help="不使用Docker")
        parser.add_argument("--with-k8s", action="store_true", help="包含Kubernetes配置")
        parser.add_argument("--quick", action="store_true", help="快速模式，使用默认配置")
        
        args = parser.parse_args()
        
        if args.quick:
            # 快速模式：使用所有默认配置
            self.config.selected_platforms = list(self.PLATFORMS.keys())
            self.config.selected_features = list(self.FEATURES.keys())
            self.config.deployment_options = ["docker", "docker_compose"]
            return True
        
        if args.name:
            self.config.project_name = args.name
        
        if args.all_platforms:
            self.config.selected_platforms = list(self.PLATFORMS.keys())
        elif args.platforms:
            self.config.selected_platforms = args.platforms
        
        if args.all_features:
            self.config.selected_features = list(self.FEATURES.keys())
        elif args.features:
            self.config.selected_features = args.features
        
        if args.no_docker:
            self.config.use_docker = False
        
        if args.with_k8s:
            self.config.use_k8s = True
            self.config.deployment_options.extend(["kubernetes", "helm"])
        
        # 如果有命令行参数，返回True跳过交互式配置
        return any([args.name, args.platforms, args.all_platforms, 
                   args.features, args.all_features])
    
    def interactive_config(self):
        """交互式配置"""
        # 项目基本信息
        print_colored("\n📋 项目基本信息", Colors.BLUE, bold=True)
        self.config.project_name = input(f"项目名称 [{self.config.project_name}]: ") or self.config.project_name
        self.config.author_name = input("作者姓名: ") or "Your Name"
        self.config.author_email = input("作者邮箱: ") or "your.email@example.com"
        
        # 选择平台
        print_colored("\n🔌 选择要支持的平台", Colors.BLUE, bold=True)
        print("0. 全选")
        for i, (key, name) in enumerate(self.PLATFORMS.items(), 1):
            print(f"{i}. {name} ({key})")
        
        platform_choices = input("请选择平台（多个用空格分隔，如: 1 2 3）: ").strip()
        if platform_choices == "0":
            self.config.selected_platforms = list(self.PLATFORMS.keys())
        else:
            indices = [int(x) - 1 for x in platform_choices.split() if x.isdigit()]
            platform_keys = list(self.PLATFORMS.keys())
            self.config.selected_platforms = [platform_keys[i] for i in indices if 0 <= i < len(platform_keys)]
        
        # 选择特性
        print_colored("\n✨ 选择项目特性", Colors.BLUE, bold=True)
        print("0. 全选（推荐）")
        for i, (key, name) in enumerate(self.FEATURES.items(), 1):
            print(f"{i}. {name}")
        
        feature_choices = input("请选择特性（多个用空格分隔）: ").strip()
        if feature_choices == "0":
            self.config.selected_features = list(self.FEATURES.keys())
        else:
            indices = [int(x) - 1 for x in feature_choices.split() if x.isdigit()]
            feature_keys = list(self.FEATURES.keys())
            self.config.selected_features = [feature_keys[i] for i in indices if 0 <= i < len(feature_keys)]
        
        # 部署选项
        print_colored("\n🚀 部署配置", Colors.BLUE, bold=True)
        use_docker = input("使用Docker？(Y/n): ").strip().lower()
        self.config.use_docker = use_docker != 'n'
        
        if self.config.use_docker:
            self.config.deployment_options.append("docker")
            use_compose = input("使用Docker Compose？(Y/n): ").strip().lower()
            if use_compose != 'n':
                self.config.deployment_options.append("docker_compose")
        
        use_k8s = input("包含Kubernetes配置？(y/N): ").strip().lower()
        if use_k8s == 'y':
            self.config.use_k8s = True
            self.config.deployment_options.extend(["kubernetes", "helm"])
    
    def confirm_config(self) -> bool:
        """确认配置"""
        print_colored("\n📝 配置确认", Colors.GREEN, bold=True)
        print(f"项目名称: {self.config.project_name}")
        print(f"作者: {self.config.author_name} <{self.config.author_email}>")
        print(f"Python版本: {self.config.python_version}")
        print(f"选择的平台: {', '.join([self.PLATFORMS[p] for p in self.config.selected_platforms])}")
        print(f"选择的特性: {', '.join([self.FEATURES[f] for f in self.config.selected_features])}")
        print(f"部署选项: {', '.join(self.config.deployment_options)}")
        
        confirm = input("\n确认创建项目？(Y/n): ").strip().lower()
        return confirm != 'n'
    
    def create_project(self):
        """创建项目"""
        self.project_path = Path(self.config.project_name)
        
        # 检查目录是否存在
        if self.project_path.exists():
            overwrite = input(f"\n⚠️  目录 {self.config.project_name} 已存在，是否覆盖？(y/N): ").strip().lower()
            if overwrite != 'y':
                print_colored("已取消创建", Colors.YELLOW)
                sys.exit(0)
            shutil.rmtree(self.project_path)
        
        print_colored(f"\n🔨 开始创建项目: {self.config.project_name}", Colors.GREEN, bold=True)
        
        # 创建目录结构
        self._create_directory_structure()
        
        # 创建配置文件
        self._create_config_files()
        
        # 创建源代码
        self._create_source_code()
        
        # 创建Docker文件
        if self.config.use_docker:
            self._create_docker_files()
        
        # 创建Kubernetes文件
        if self.config.use_k8s:
            self._create_k8s_files()
        
        # 创建文档
        self._create_documentation()
        
        # 初始化Git
        self._init_git()
        
        print_colored("✅ 项目创建完成！", Colors.GREEN, bold=True)
    
    def _create_directory_structure(self):
        """创建目录结构"""
        print("  📁 创建目录结构...")
        
        # 基础目录
        directories = [
            "src/core/config",
            "src/core/database",
            "src/core/redis",
            "src/core/models",
            "src/utils/logger",
            "src/utils/validators",
            "src/utils/helpers",
            "src/api/v1/endpoints",
            "src/api/v1/schemas",
            "src/api/middleware",
            "tests/unit",
            "tests/integration",
            "tests/fixtures",
            "docs/api",
            "docs/guides",
            "scripts/setup",
            "scripts/deploy",
            "logs",
            "data/raw",
            "data/processed",
            "data/cache",
        ]
        
        # 根据选择的特性添加目录
        if "dual_engine" in self.config.selected_features:
            directories.extend([
                "src/engines/base",
                "src/engines/crawl4ai",
                "src/engines/mediacrawl"
            ])
        
        if "anti_detection" in self.config.selected_features:
            directories.extend([
                "src/core/anti_detection/proxy_pool",
                "src/core/anti_detection/fingerprint",
                "src/core/anti_detection/behavior"
            ])
        
        if "data_processing" in self.config.selected_features:
            directories.extend([
                "src/processors/cleaner",
                "src/processors/deduplicator",
                "src/processors/enhancer"
            ])
        
        if "scheduler" in self.config.selected_features:
            directories.append("src/core/scheduler")
        
        if "monitoring" in self.config.selected_features:
            directories.extend([
                "monitoring/prometheus",
                "monitoring/grafana/dashboards"
            ])
        
        # 平台适配器目录
        directories.append("src/adapters/base")
        for platform in self.config.selected_platforms:
            directories.append(f"src/adapters/{platform}")
        
        # Docker目录
        if self.config.use_docker:
            directories.extend([
                "docker/development",
                "docker/production"
            ])
        
        # Kubernetes目录
        if self.config.use_k8s:
            directories.extend([
                "k8s/base",
                "k8s/overlays/dev",
                "k8s/overlays/prod",
                "k8s/charts"
            ])
        
        # 创建所有目录
        for directory in directories:
            (self.project_path / directory).mkdir(parents=True, exist_ok=True)
        
        # 创建__init__.py文件
        for root, dirs, _ in os.walk(self.project_path / "src"):
            for dir_name in dirs:
                init_file = Path(root) / dir_name / "__init__.py"
                init_file.touch()
        
        # 创建.gitkeep文件
        for data_dir in ["raw", "processed", "cache"]:
            gitkeep = self.project_path / "data" / data_dir / ".gitkeep"
            gitkeep.touch()
    
    def _create_config_files(self):
        """创建配置文件"""
        print("  📄 创建配置文件...")
        
        # pyproject.toml
        dependencies = {
            "python": "^3.11",
            "fastapi": "^0.104.0",
            "uvicorn": {"extras": ["standard"], "version": "^0.24.0"},
            "sqlalchemy": {"extras": ["asyncio"], "version": "^2.0.0"},
            "asyncpg": "^0.29.0",
            "redis": "^5.0.0",
            "pydantic": "^2.5.0",
            "pydantic-settings": "^2.1.0",
            "loguru": "^0.7.0",
            "httpx": "^0.25.0",
            "beautifulsoup4": "^4.12.0",
            "lxml": "^5.0.0"
        }
        
        # 根据选择的特性添加依赖
        if "dual_engine" in self.config.selected_features:
            dependencies["crawl4ai"] = "^0.2.0"
            dependencies["playwright"] = "^1.40.0"
        
        if "jwt_auth" in self.config.selected_features:
            dependencies["python-jose"] = {"extras": ["cryptography"], "version": "^3.3.0"}
            dependencies["passlib"] = {"extras": ["bcrypt"], "version": "^1.7.4"}
            dependencies["python-multipart"] = "^0.0.6"
        
        if "scheduler" in self.config.selected_features:
            dependencies["celery"] = {"extras": ["redis"], "version": "^5.3.0"}
        
        if "monitoring" in self.config.selected_features:
            dependencies["prometheus-client"] = "^0.19.0"
        
        if "anti_detection" in self.config.selected_features:
            dependencies["fake-useragent"] = "^1.4.0"
            dependencies["cloudscraper"] = "^1.2.0"
        
        pyproject_content = {
            "tool": {
                "poetry": {
                    "name": self.config.project_name,
                    "version": "1.0.0",
                    "description": "智能旅游平台数据爬虫系统",
                    "authors": [f"{self.config.author_name} <{self.config.author_email}>"],
                    "readme": "README.md",
                    "packages": [{"include": "src"}],
                    "dependencies": dependencies,
                    "group": {
                        "dev": {
                            "dependencies": {
                                "pytest": "^7.4.0",
                                "pytest-asyncio": "^0.21.0",
                                "pytest-cov": "^4.1.0",
                                "black": "^23.0.0",
                                "ruff": "^0.1.0",
                                "mypy": "^1.7.0",
                                "pre-commit": "^3.5.0"
                            }
                        }
                    }
                },
                "black": {
                    "line-length": 100,
                    "target-version": ["py311"]
                },
                "ruff": {
                    "line-length": 100,
                    "select": ["E", "F", "I", "N", "W"],
                    "ignore": ["E501"]
                },
                "pytest": {
                    "ini_options": {
                        "testpaths": ["tests"],
                        "python_files": ["test_*.py", "*_test.py"],
                        "addopts": "-ra -q --strict-markers",
                        "asyncio_mode": "auto"
                    }
                }
            },
            "build-system": {
                "requires": ["poetry-core"],
                "build-backend": "poetry.core.masonry.api"
            }
        }
        
        with open(self.project_path / "pyproject.toml", "w") as f:
            # 简化的TOML写入（实际应使用toml库）
            f.write("[tool.poetry]\n")
            f.write(f'name = "{pyproject_content["tool"]["poetry"]["name"]}"\n')
            f.write(f'version = "{pyproject_content["tool"]["poetry"]["version"]}"\n')
            f.write(f'description = "{pyproject_content["tool"]["poetry"]["description"]}"\n')
            f.write(f'authors = {pyproject_content["tool"]["poetry"]["authors"]}\n')
            f.write('readme = "README.md"\n')
            f.write('packages = [{include = "src"}]\n\n')
            
            f.write("[tool.poetry.dependencies]\n")
            for dep, version in dependencies.items():
                if isinstance(version, dict):
                    extras = version.get("extras", [])
                    ver = version["version"]
                    if extras:
                        f.write(f'{dep} = {{extras = {extras}, version = "{ver}"}}\n')
                    else:
                        f.write(f'{dep} = "{ver}"\n')
                else:
                    f.write(f'{dep} = "{version}"\n')
            
            f.write("\n[tool.poetry.group.dev.dependencies]\n")
            for dep, version in pyproject_content["tool"]["poetry"]["group"]["dev"]["dependencies"].items():
                f.write(f'{dep} = "{version}"\n')
            
            f.write("\n[build-system]\n")
            f.write('requires = ["poetry-core"]\n')
            f.write('build-backend = "poetry.core.masonry.api"\n')
        
        # .env.example
        self._create_env_example()
        
        # .gitignore
        self._create_gitignore()
        
        # README.md
        self._create_readme()
    
    def _create_env_example(self):
        """创建.env.example文件"""
        env_content = f"""# 应用配置
APP_NAME={self.config.project_name}
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=postgresql+asyncpg://crawler:password@localhost:5432/crawler_db
DATABASE_POOL_SIZE=20

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=100

# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
"""
        
        if "dual_engine" in self.config.selected_features:
            env_content += """
# 爬虫引擎配置
CRAWLER_MAX_WORKERS=10
CRAWLER_TIMEOUT=30
CRAWLER_RETRY_TIMES=3
"""
        
        if "anti_detection" in self.config.selected_features:
            env_content += """
# 反爬配置
PROXY_POOL_ENABLE=true
PROXY_POOL_MIN_SIZE=100
USER_AGENT_POOL_SIZE=1000
"""
        
        if "jwt_auth" in self.config.selected_features:
            env_content += """
# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
"""
        
        if "monitoring" in self.config.selected_features:
            env_content += """
# 监控配置
METRICS_ENABLE=true
METRICS_PORT=9090
"""
        
        # 平台API密钥
        env_content += "\n# 平台API密钥\n"
        for platform in self.config.selected_platforms:
            env_content += f"{platform.upper()}_API_KEY=\n"
        
        with open(self.project_path / ".env.example", "w") as f:
            f.write(env_content)
    
    def _create_gitignore(self):
        """创建.gitignore文件"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/

# Poetry
poetry.lock

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/

# Logs
logs/
*.log

# Environment
.env
.env.*

# Data
data/raw/*
data/processed/*
data/cache/*
!data/*/.gitkeep

# OS
.DS_Store
Thumbs.db

# Project specific
*.db
*.sqlite
"""
        
        with open(self.project_path / ".gitignore", "w") as f:
            f.write(gitignore_content)
    
    def _create_readme(self):
        """创建README.md"""
        platforms_list = "\n".join([f"- {self.PLATFORMS[p]}" for p in self.config.selected_platforms])
        features_list = "\n".join([f"- {self.FEATURES[f]}" for f in self.config.selected_features])
        
        readme_content = f"""# {self.config.project_name}

智能旅游平台数据爬虫系统，支持多平台数据采集与处理。

## 支持的平台

{platforms_list}

## 核心特性

{features_list}

## 快速开始

### 环境要求

- Python {self.config.python_version}+
- PostgreSQL 15+
- Redis 7+
"""
        
        if self.config.use_docker:
            readme_content += """
### Docker部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```
"""
        
        readme_content += """
### 本地开发

```bash
# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行数据库迁移
poetry run alembic upgrade head

# 启动开发服务器
poetry run uvicorn src.main:app --reload
```

## API文档

启动服务后访问: http://localhost:8000/docs

## 项目结构

```
{}/
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   ├── engines/           # 爬虫引擎
│   ├── adapters/          # 平台适配器
│   ├── processors/        # 数据处理
│   ├── api/              # API接口
│   └── utils/            # 工具函数
├── tests/                 # 测试代码
├── docs/                  # 文档
├── scripts/               # 脚本工具
└── docker/                # Docker配置
```

## 贡献指南

欢迎提交Issue和Pull Request！

## License

MIT License

---

Created with ❤️ by {}
""".format(self.config.project_name, self.config.author_name)
        
        with open(self.project_path / "README.md", "w") as f:
            f.write(readme_content)
    
    def _create_source_code(self):
        """创建源代码"""
        print("  💻 创建源代码...")
        
        # 主应用入口
        self._create_main_app()
        
        # 配置管理
        self._create_settings()
        
        # 日志模块
        self._create_logger()
        
        # 数据库连接
        self._create_database()
        
        # API路由
        self._create_api_router()
        
        # 根据选择的特性创建相应代码
        if "dual_engine" in self.config.selected_features:
            self._create_engine_base()
        
        if "anti_detection" in self.config.selected_features:
            self._create_anti_detection_base()
        
        # 创建平台适配器基类
        self._create_adapter_base()
        
        # 创建测试文件
        self._create_test_files()
    
    def _create_main_app(self):
        """创建主应用文件"""
        imports = [
            "from fastapi import FastAPI",
            "from fastapi.middleware.cors import CORSMiddleware",
            "from contextlib import asynccontextmanager",
            "from src.core.config.settings import get_settings",
            "from src.core.database.connection import init_db",
            "from src.api.v1.router import api_router",
            "from src.utils.logger.logger import setup_logger"
        ]
        
        if "monitoring" in self.config.selected_features:
            imports.append("from prometheus_client import make_asgi_app")
        
        main_content = f"""\"\"\"
{self.config.project_name} - 主应用入口
\"\"\"
{chr(10).join(imports)}

settings = get_settings()
logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"应用生命周期管理\"\"\"
    logger.info("Starting {self.config.project_name}...")
    await init_db()
    yield
    logger.info("Shutting down {self.config.project_name}...")

app = FastAPI(
    title="{self.config.project_name}",
    description="智能旅游数据采集与处理平台",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")
"""
        
        if "monitoring" in self.config.selected_features:
            main_content += """
# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
"""
        
        main_content += """
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
"""
        
        with open(self.project_path / "src" / "main.py", "w") as f:
            f.write(main_content)
    
    def _create_settings(self):
        """创建配置文件"""
        settings_content = f'''"""配置管理模块"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""
    # 基础配置
    app_name: str = "{self.config.project_name}"
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    
    # 数据库
    database_url: str
    database_pool_size: int = 20
    
    # Redis
    redis_url: str
    redis_max_connections: int = 100
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
'''
        
        if "dual_engine" in self.config.selected_features:
            settings_content += '''
    # 爬虫配置
    crawler_max_workers: int = 10
    crawler_timeout: int = 30
    crawler_retry_times: int = 3
'''
        
        if "jwt_auth" in self.config.selected_features:
            settings_content += '''
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
'''
        
        settings_content += '''
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
'''
        
        with open(self.project_path / "src" / "core" / "config" / "settings.py", "w") as f:
            f.write(settings_content)
    
    def _create_logger(self):
        """创建日志模块"""
        logger_content = '''"""日志管理模块"""
from loguru import logger
import sys
from pathlib import Path

def setup_logger():
    """配置日志"""
    logger.remove()
    
    # 控制台日志
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 文件日志
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG"
    )
    
    return logger

def get_logger(name: str):
    return logger.bind(name=name)
'''
        
        with open(self.project_path / "src" / "utils" / "logger" / "logger.py", "w") as f:
            f.write(logger_content)
    
    def _create_database(self):
        """创建数据库模块"""
        db_content = '''"""数据库连接管理"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.core.config.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
'''
        
        with open(self.project_path / "src" / "core" / "database" / "connection.py", "w") as f:
            f.write(db_content)
    
    def _create_api_router(self):
        """创建API路由"""
        router_content = '''"""API路由配置"""
from fastapi import APIRouter
from src.api.v1.endpoints import crawler, data, platform

api_router = APIRouter()

# 爬虫相关路由
api_router.include_router(
    crawler.router,
    prefix="/crawler",
    tags=["爬虫管理"]
)

# 数据相关路由
api_router.include_router(
    data.router,
    prefix="/data",
    tags=["数据管理"]
)

# 平台相关路由
api_router.include_router(
    platform.router,
    prefix="/platform",
    tags=["平台管理"]
)
'''
        
        with open(self.project_path / "src" / "api" / "v1" / "router.py", "w") as f:
            f.write(router_content)
        
        # 创建示例端点
        crawler_endpoint = '''"""爬虫管理端点"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.post("/task")
async def create_crawl_task(task_data: Dict[str, Any]):
    """创建爬取任务"""
    return {"task_id": "example-task-id", "status": "pending"}

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    return {"task_id": task_id, "status": "running", "progress": 50}
'''
        
        with open(self.project_path / "src" / "api" / "v1" / "endpoints" / "crawler.py", "w") as f:
            f.write(crawler_endpoint)
        
        # 创建空的其他端点文件
        for endpoint in ["data", "platform"]:
            endpoint_content = f'''"""ￄ{endpoint.capitalize()}管理端点"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_{endpoint}_list():
    """获取{endpoint}列表"""
    return []
'''
            with open(self.project_path / "src" / "api" / "v1" / "endpoints" / f"{endpoint}.py", "w") as f:
                f.write(endpoint_content)
    
    def _create_engine_base(self):
        """创建引擎基类"""
        engine_base = '''"""爬虫引擎基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class EngineType(Enum):
    CRAWL4AI = "crawl4ai"
    MEDIACRAWL = "mediacrawl"

@dataclass
class CrawlTask:
    """爬取任务"""
    task_id: str
    url: str
    platform: str
    engine_type: EngineType
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    timeout: int = 30

class BaseEngine(ABC):
    """引擎基类"""
    
    @abstractmethod
    async def crawl(self, task: CrawlTask) -> Dict[str, Any]:
        """执行爬取"""
        pass
    
    @abstractmethod
    async def init(self):
        """初始化引擎"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭引擎"""
        pass
'''
        
        with open(self.project_path / "src" / "engines" / "base" / "engine_interface.py", "w") as f:
            f.write(engine_base)
    
    def _create_anti_detection_base(self):
        """创建反爬基础模块"""
        proxy_manager = '''"""代理池管理器"""
from typing import List, Optional
import random

class ProxyPoolManager:
    """代理池管理"""
    
    def __init__(self):
        self.proxies: List[str] = []
        self.failed_proxies: set = set()
    
    async def get_proxy(self) -> Optional[str]:
        """获取可用代理"""
        available = [p for p in self.proxies if p not in self.failed_proxies]
        return random.choice(available) if available else None
    
    async def mark_failed(self, proxy: str):
        """标记失败代理"""
        self.failed_proxies.add(proxy)
    
    async def refresh_pool(self):
        """刷新代理池"""
        # 实现代理池刷新逻辑
        pass
'''
        
        with open(self.project_path / "src" / "core" / "anti_detection" / "proxy_pool" / "manager.py", "w") as f:
            f.write(proxy_manager)
    
    def _create_adapter_base(self):
        """创建适配器基类"""
        adapter_base = '''"""平台适配器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    def __init__(self):
        self.platform_name = ""
        self.base_url = ""
    
    @abstractmethod
    async def search(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """搜索数据"""
        pass
    
    @abstractmethod
    async def get_detail(self, item_id: str) -> Dict[str, Any]:
        """获取详情"""
        pass
    
    @abstractmethod
    async def parse_data(self, raw_data: Any) -> Dict[str, Any]:
        """解析数据"""
        pass
'''
        
        with open(self.project_path / "src" / "adapters" / "base" / "adapter_interface.py", "w") as f:
            f.write(adapter_base)
    
    def _create_test_files(self):
        """创建测试文件"""
        test_main = '''"""主应用测试"""
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
'''
        
        with open(self.project_path / "tests" / "test_main.py", "w") as f:
            f.write(test_main)
    
    def _create_docker_files(self):
        """创建Docker文件"""
        print("  🐳 创建Docker配置...")
        
        # Docker Compose
        compose_content = f"""version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: crawler
      POSTGRES_PASSWORD: password
      POSTGRES_DB: crawler_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  app:
    build:
      context: .
      dockerfile: docker/development/Dockerfile
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://crawler:password@postgres:5432/crawler_db
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./src:/app/src
    ports:
      - "8000:8000"
"""
        
        if "monitoring" in self.config.selected_features:
            compose_content += """
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    depends_on:
      - prometheus
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
"""
        
        compose_content += """
volumes:
  postgres_data:
  redis_data:"""
        
        if "monitoring" in self.config.selected_features:
            compose_content += """
  prometheus_data:
  grafana_data:"""
        
        with open(self.project_path / "docker-compose.yml", "w") as f:
            f.write(compose_content)
        
        # Development Dockerfile
        dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装依赖
RUN poetry config virtualenvs.create false \\
    && poetry install --no-interaction
"""
        
        if "dual_engine" in self.config.selected_features:
            dockerfile_content += """
# 安装Playwright
RUN playwright install chromium
RUN playwright install-deps chromium
"""
        
        dockerfile_content += """
# 复制源代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
"""
        
        with open(self.project_path / "docker" / "development" / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
    
    def _create_k8s_files(self):
        """创建Kubernetes文件"""
        print("  ☸️  创建Kubernetes配置...")
        
        # Deployment
        deployment_content = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {self.config.project_name}-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {self.config.project_name}-api
  template:
    metadata:
      labels:
        app: {self.config.project_name}-api
    spec:
      containers:
      - name: api
        image: {self.config.project_name}:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {self.config.project_name}-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
"""
        
        with open(self.project_path / "k8s" / "base" / "deployment.yaml", "w") as f:
            f.write(deployment_content)
        
        # Service
        service_content = f"""apiVersion: v1
kind: Service
metadata:
  name: {self.config.project_name}-api
spec:
  selector:
    app: {self.config.project_name}-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
"""
        
        with open(self.project_path / "k8s" / "base" / "service.yaml", "w") as f:
            f.write(service_content)
    
    def _create_documentation(self):
        """创建文档"""
        print("  📚 创建文档...")
        
        # API文档说明
        api_doc = f"""# {self.config.project_name} API文档

## 概述

本文档描述了{self.config.project_name}的API接口。

## 认证

"""
        
        if "jwt_auth" in self.config.selected_features:
            api_doc += """所有API请求需要在Header中包含JWT Token：

```
Authorization: Bearer <token>
```

### 获取Token

POST /api/v1/auth/login
"""
        else:
            api_doc += "当前API不需要认证。"
        
        api_doc += """

## 接口列表

### 爬虫管理

- POST /api/v1/crawler/task - 创建爬取任务
- GET /api/v1/crawler/task/{task_id} - 获取任务状态

### 数据管理

- GET /api/v1/data - 获取数据列表
- GET /api/v1/data/{id} - 获取数据详情

### 平台管理

- GET /api/v1/platform - 获取支持的平台列表
"""
        
        with open(self.project_path / "docs" / "api" / "README.md", "w") as f:
            f.write(api_doc)
        
        # 部署指南
        deploy_guide = f"""# 部署指南

## 环境要求

- Python {self.config.python_version}+
- PostgreSQL 15+
- Redis 7+
"""
        
        if self.config.use_docker:
            deploy_guide += """
## Docker部署

### 开发环境

```bash
docker-compose up -d
```

### 生产环境

```bash
docker build -f docker/production/Dockerfile -t {project_name}:latest .
docker run -d -p 8000:8000 --env-file .env {project_name}:latest
```
""".format(project_name=self.config.project_name)
        
        if self.config.use_k8s:
            deploy_guide += """
## Kubernetes部署

### 使用kubectl

```bash
kubectl apply -k k8s/base
```

### 使用Helm

```bash
helm install {project_name} ./k8s/charts/{project_name}
```
""".format(project_name=self.config.project_name)
        
        with open(self.project_path / "docs" / "guides" / "deployment.md", "w") as f:
            f.write(deploy_guide)
    
    def _init_git(self):
        """初始化Git仓库"""
        print("  📦 初始化Git仓库...")
        
        try:
            subprocess.run(["git", "init"], cwd=self.project_path, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=self.project_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit: Project scaffold"], 
                cwd=self.project_path, 
                check=True, 
                capture_output=True
            )
        except subprocess.CalledProcessError:
            print_colored("    ⚠️  Git初始化失败，请手动初始化", Colors.YELLOW)
    
    def show_completion_info(self):
        """显示完成信息"""
        print()
        print_colored("="*60, Colors.GREEN)
        print_colored(f"🎉 项目 {self.config.project_name} 创建成功！", Colors.GREEN, bold=True)
        print_colored("="*60, Colors.GREEN)
        print()
        
        print_colored("📋 项目信息", Colors.BLUE, bold=True)
        print(f"  路径: {self.project_path.absolute()}")
        print(f"  平台: {len(self.config.selected_platforms)}个")
        print(f"  特性: {len(self.config.selected_features)}个")
        print()
        
        print_colored("🚀 快速开始", Colors.BLUE, bold=True)
        print(f"  1. cd {self.config.project_name}")
        print("  2. cp .env.example .env")
        print("  3. # 编辑 .env 文件配置数据库等信息")
        
        if self.config.use_docker:
            print("  4. docker-compose up -d")
            print("  5. 访问 http://localhost:8000/docs")
        else:
            print("  4. poetry install")
            print("  5. poetry run uvicorn src.main:app --reload")
            print("  6. 访问 http://localhost:8000/docs")
        
        print()
        print_colored("📚 相关文档", Colors.BLUE, bold=True)
        print("  - API文档: docs/api/README.md")
        print("  - 部署指南: docs/guides/deployment.md")
        print("  - 项目说明: README.md")
        
        if "monitoring" in self.config.selected_features and self.config.use_docker:
            print()
            print_colored("📊 监控服务", Colors.BLUE, bold=True)
            print("  - Prometheus: http://localhost:9090")
            print("  - Grafana: http://localhost:3000")
        
        print()
        print_colored("祝您开发愉快！🚀", Colors.GREEN, bold=True)

def main():
    """主函数"""
    generator = ScaffoldGenerator()
    generator.run()

if __name__ == "__main__":
    main()