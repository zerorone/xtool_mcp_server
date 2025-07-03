#!/bin/bash

# 旅游平台数据爬虫系统 - 一键脚手架脚本
# 功能：自动创建项目结构、安装依赖、初始化配置
# 使用：bash scaffold.sh [项目名称] [--full]

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认项目名称
PROJECT_NAME=${1:-"travel-crawler-system"}
FULL_INSTALL=${2:-""}

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要的工具
check_requirements() {
    print_info "检查系统环境..."
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.11"
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python 版本必须 >= 3.11，当前版本: $PYTHON_VERSION"
        exit 1
    fi
    
    # 检查Poetry
    if ! command -v poetry &> /dev/null; then
        print_warning "Poetry 未安装，正在安装..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # 检查Docker（可选）
    if command -v docker &> /dev/null; then
        print_success "Docker 已安装"
    else
        print_warning "Docker 未安装，部署功能将不可用"
    fi
    
    print_success "环境检查完成"
}

# 创建项目目录结构
create_project_structure() {
    print_info "创建项目目录结构..."
    
    # 创建根目录
    mkdir -p "$PROJECT_NAME"
    cd "$PROJECT_NAME"
    
    # 创建核心代码目录
    mkdir -p src/{core,engines,adapters,processors,api,utils}
    mkdir -p src/core/{database,redis,scheduler,config,models,anti_detection}
    mkdir -p src/core/anti_detection/{proxy_pool,fingerprint,behavior}
    mkdir -p src/engines/{base,crawl4ai,mediacrawl}
    mkdir -p src/adapters/{base,amap,mafengwo,dianping,ctrip,xiaohongshu,douyin,weibo,bilibili}
    mkdir -p src/processors/{cleaner,deduplicator,enhancer}
    mkdir -p src/api/{v1,middleware,dependencies}
    mkdir -p src/api/v1/{endpoints,schemas,services}
    mkdir -p src/utils/{logger,validators,helpers,security}
    
    # 创建配置和部署目录
    mkdir -p config/{engines,platforms,environments}
    mkdir -p docker/{development,production,scripts}
    mkdir -p scripts/{setup,deploy,test,monitoring}
    mkdir -p k8s/{base,overlays,charts}
    
    # 创建文档和测试目录
    mkdir -p docs/{api,architecture,deployment,user_guide}
    mkdir -p tests/{unit,integration,e2e,fixtures}
    mkdir -p tests/unit/{engines,adapters,processors,api}
    mkdir -p tests/integration/{crawling,data_processing}
    
    # 创建其他必要目录
    mkdir -p logs/{api,crawler,scheduler}
    mkdir -p data/{raw,processed,cache,exports}
    mkdir -p monitoring/{prometheus,grafana}
    
    # 创建 __init__.py 文件
    find src tests -type d -exec touch {}/__init__.py \;
    
    print_success "目录结构创建完成"
}

# 创建基础配置文件
create_base_configs() {
    print_info "创建基础配置文件..."
    
    # 创建 pyproject.toml
    cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "travel-crawler-system"
version = "1.0.0"
description = "智能旅游平台数据爬虫系统"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
packages = [{include = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
crawl4ai = "^0.2.0"
playwright = "^1.40.0"
beautifulsoup4 = "^4.12.0"
lxml = "^5.0.0"
httpx = "^0.25.0"
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.29.0"
alembic = "^1.13.0"
redis = "^5.0.0"
celery = {extras = ["redis"], version = "^5.3.0"}
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
loguru = "^0.7.0"
prometheus-client = "^0.19.0"
tenacity = "^8.2.0"
fake-useragent = "^1.4.0"
cloudscraper = "^1.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
black = "^23.0.0"
ruff = "^0.1.0"
mypy = "^1.7.0"
pre-commit = "^3.5.0"
ipython = "^8.17.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = "-ra -q --strict-markers --cov=src --cov-report=html"
asyncio_mode = "auto"
EOF

    # 创建 .env.example
    cat > .env.example << 'EOF'
# 应用配置
APP_NAME=travel-crawler-system
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=postgresql+asyncpg://crawler:password@localhost:5432/crawler_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=100

# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# 爬虫配置
CRAWLER_MAX_WORKERS=10
CRAWLER_TIMEOUT=30
CRAWLER_RETRY_TIMES=3
CRAWLER_USER_AGENT_POOL_SIZE=1000

# 代理配置
PROXY_POOL_ENABLE=true
PROXY_POOL_MIN_SIZE=100
PROXY_VALIDATION_INTERVAL=300

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_ROTATION=1 day
LOG_RETENTION=30 days

# 监控配置
METRICS_ENABLE=true
METRICS_PORT=9090

# 平台API密钥（根据需要填写）
AMAP_API_KEY=
MAFENGWO_API_KEY=
CTRIP_API_KEY=
EOF

    # 创建 .gitignore
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
.venv/

# Poetry
poetry.lock

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
.coverage.*
*.cover
.hypothesis/

# Logs
logs/
*.log

# Environment
.env
.env.local
.env.*.local

# Data
data/raw/*
data/processed/*
data/cache/*
!data/*/.gitkeep

# Docker
.docker/

# OS
.DS_Store
Thumbs.db

# Project specific
*.db
*.sqlite
*.pid
EOF

    # 创建 README.md
    cat > README.md << 'EOF'
# 旅游平台数据爬虫系统

智能旅游平台数据爬虫系统，支持8大主流平台的数据采集。

## 特性

- 🚀 双引擎架构：Crawl4AI + MediaCrawl
- 🛡️ 三层反爬系统
- 🔌 8大平台支持
- 📊 完整数据处理流程
- 🔍 生产级监控

## 快速开始

```bash
# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 初始化数据库
poetry run alembic upgrade head

# 启动服务
poetry run uvicorn src.main:app --reload
```

## 文档

详细文档请查看 `docs/` 目录。

## License

MIT
EOF

    # 创建 docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.3
    container_name: crawler_postgres
    environment:
      POSTGRES_USER: crawler
      POSTGRES_PASSWORD: password
      POSTGRES_DB: crawler_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U crawler"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: crawler_redis
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: docker/development/Dockerfile
    container_name: crawler_app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://crawler:password@postgres:5432/crawler_db
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  redis_data:
EOF

    print_success "配置文件创建完成"
}

# 创建核心源代码文件
create_source_files() {
    print_info "创建核心源代码文件..."
    
    # 创建主应用文件
    cat > src/main.py << 'EOF'
"""
旅游平台数据爬虫系统 - 主应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config.settings import get_settings
from src.core.database.connection import init_db
from src.core.redis.connection import init_redis
from src.api.v1.router import api_router
from src.utils.logger.logger import setup_logger
from prometheus_client import make_asgi_app

settings = get_settings()
logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Travel Crawler System...")
    await init_db()
    await init_redis()
    yield
    # 关闭时
    logger.info("Shutting down Travel Crawler System...")

# 创建FastAPI应用
app = FastAPI(
    title="旅游平台数据爬虫系统",
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

# 添加Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Travel Crawler System",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
EOF

    # 创建配置管理
    cat > src/core/config/settings.py << 'EOF'
"""配置管理模块"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""
    # 基础配置
    app_name: str = "travel-crawler-system"
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    
    # 数据库
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 40
    
    # Redis
    redis_url: str
    redis_max_connections: int = 100
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # 爬虫配置
    crawler_max_workers: int = 10
    crawler_timeout: int = 30
    crawler_retry_times: int = 3
    
    # 代理池
    proxy_pool_enable: bool = True
    proxy_pool_min_size: int = 100
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
EOF

    # 创建日志模块
    cat > src/utils/logger/logger.py << 'EOF'
"""日志管理模块"""
from loguru import logger
import sys
from pathlib import Path

def setup_logger():
    """配置日志"""
    # 移除默认处理器
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
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    return logger

def get_logger(name: str):
    """获取logger实例"""
    return logger.bind(name=name)
EOF

    # 创建数据库连接模块
    cat > src/core/database/connection.py << 'EOF'
"""数据库连接管理"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.core.config.settings import get_settings

settings = get_settings()

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)

# 声明基类
Base = declarative_base()

async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 在生产环境中应该使用Alembic管理
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
EOF

    # 创建测试文件
    cat > tests/test_main.py << 'EOF'
"""主应用测试"""
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to Travel Crawler System"

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
EOF

    print_success "源代码文件创建完成"
}

# 创建Docker文件
create_docker_files() {
    print_info "创建Docker配置文件..."
    
    # 开发环境Dockerfile
    cat > docker/development/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装Python依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# 安装Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# 复制源代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

    # 生产环境Dockerfile
    cat > docker/production/Dockerfile << 'EOF'
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 导出requirements.txt
RUN poetry export -f requirements.txt > requirements.txt

# 最终镜像
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements并安装
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# 复制源代码
COPY src ./src
COPY alembic.ini ./

# 创建非root用户
RUN useradd -m -u 1000 crawler && chown -R crawler:crawler /app

USER crawler

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    print_success "Docker文件创建完成"
}

# 创建Kubernetes配置
create_k8s_files() {
    if [[ "$FULL_INSTALL" != "--full" ]]; then
        return
    fi
    
    print_info "创建Kubernetes配置文件..."
    
    # Deployment
    cat > k8s/base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawler-api
  labels:
    app: crawler-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crawler-api
  template:
    metadata:
      labels:
        app: crawler-api
    spec:
      containers:
      - name: api
        image: travel-crawler:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: crawler-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: crawler-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

    # Service
    cat > k8s/base/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: crawler-api
spec:
  selector:
    app: crawler-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
EOF

    print_success "Kubernetes配置创建完成"
}

# 创建启动脚本
create_scripts() {
    print_info "创建便捷脚本..."
    
    # 开发环境启动脚本
    cat > scripts/dev.sh << 'EOF'
#!/bin/bash
# 开发环境启动脚本

echo "启动开发环境..."

# 检查依赖
if ! command -v docker-compose &> /dev/null; then
    echo "请先安装 docker-compose"
    exit 1
fi

# 启动服务
docker-compose up -d

# 等待服务就绪
echo "等待服务启动..."
sleep 10

# 运行数据库迁移
docker-compose exec app alembic upgrade head

echo "开发环境启动完成！"
echo "API文档: http://localhost:8000/docs"
echo "监控指标: http://localhost:8000/metrics"
EOF

    # 测试脚本
    cat > scripts/test.sh << 'EOF'
#!/bin/bash
# 运行测试脚本

echo "运行测试..."

# 运行单元测试
poetry run pytest tests/unit -v

# 运行集成测试
poetry run pytest tests/integration -v

# 生成覆盖率报告
poetry run pytest --cov=src --cov-report=html

echo "测试完成！覆盖率报告: htmlcov/index.html"
EOF

    # 设置脚本可执行权限
    chmod +x scripts/*.sh
    
    print_success "脚本创建完成"
}

# 初始化Git仓库
init_git() {
    print_info "初始化Git仓库..."
    
    git init
    git add .
    git commit -m "Initial commit: Travel Crawler System scaffold"
    
    print_success "Git仓库初始化完成"
}

# 安装依赖
install_dependencies() {
    print_info "安装项目依赖..."
    
    poetry install
    
    # 安装Playwright浏览器
    poetry run playwright install chromium
    
    print_success "依赖安装完成"
}

# 显示完成信息
show_completion_message() {
    echo ""
    echo "======================================"
    print_success "🎉 项目脚手架创建完成！"
    echo "======================================"
    echo ""
    echo "项目名称: $PROJECT_NAME"
    echo "项目路径: $(pwd)"
    echo ""
    echo "下一步操作:"
    echo "1. 配置环境变量:"
    echo "   cp .env.example .env"
    echo "   # 编辑 .env 文件"
    echo ""
    echo "2. 启动开发环境:"
    echo "   bash scripts/dev.sh"
    echo ""
    echo "3. 访问服务:"
    echo "   - API文档: http://localhost:8000/docs"
    echo "   - 健康检查: http://localhost:8000/health"
    echo "   - 监控指标: http://localhost:8000/metrics"
    echo ""
    echo "4. 运行测试:"
    echo "   bash scripts/test.sh"
    echo ""
    if [[ "$FULL_INSTALL" == "--full" ]]; then
        echo "5. Kubernetes部署:"
        echo "   kubectl apply -k k8s/base"
    fi
    echo ""
    echo "详细文档请查看 docs/ 目录"
    echo "======================================"
}

# 主函数
main() {
    echo "======================================"
    echo "旅游平台数据爬虫系统 - 脚手架生成器"
    echo "======================================"
    echo ""
    
    # 检查是否已存在同名目录
    if [ -d "$PROJECT_NAME" ]; then
        print_error "目录 $PROJECT_NAME 已存在！"
        read -p "是否删除并重新创建？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_NAME"
        else
            exit 1
        fi
    fi
    
    # 执行各步骤
    check_requirements
    create_project_structure
    create_base_configs
    create_source_files
    create_docker_files
    create_k8s_files
    create_scripts
    
    # 可选步骤
    read -p "是否初始化Git仓库？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        init_git
    fi
    
    read -p "是否立即安装依赖？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_dependencies
    fi
    
    # 显示完成信息
    show_completion_message
}

# 执行主函数
main
EOF