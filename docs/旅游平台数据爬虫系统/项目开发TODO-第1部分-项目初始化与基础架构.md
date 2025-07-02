# 旅游平台数据爬虫系统 - 项目开发TODO详细指南
## 第1部分：项目初始化与基础架构

> 本文档设计为Claude Code可以逐步执行的详细任务清单，每个任务都包含具体的实现代码和验证步骤

## 项目概要
- **目标**：构建双引擎（Crawl4AI + MediaCrawl）的旅游数据爬虫系统
- **平台覆盖**：高德地图、马蜂窝、大众点评、携程、小红书、抖音、微博、B站
- **核心技术**：Python 3.11+、FastAPI、PostgreSQL、Redis、Docker

---

## Phase 1: 项目初始化（Day 1）

### Task 1.1: 创建项目基础结构
```bash
# 1. 创建项目根目录
mkdir -p /Users/xiao/Documents/BaiduNetSyncDownload/CodeDev/CrawlPOIData/travel-crawler-system
cd /Users/xiao/Documents/BaiduNetSyncDownload/CodeDev/CrawlPOIData/travel-crawler-system

# 2. 初始化Git仓库
git init
echo "# Travel Crawler System - 双引擎旅游数据爬虫系统" > README.md

# 3. 创建完整的项目目录结构
mkdir -p src/{__pycache__}
mkdir -p src/core/{engines,scheduler,anti_detection,models,config}
mkdir -p src/engines/{crawl4ai,mediacrawl,base}
mkdir -p src/anti_detection/{proxy,fingerprint,behavior}
mkdir -p src/adapters/{amap,mafengwo,dianping,ctrip,xiaohongshu,douyin,weibo,bilibili}
mkdir -p src/processors/{cleaner,deduplicator,enhancer}
mkdir -p src/api/{v1,middleware,dependencies}
mkdir -p src/utils/{logger,validators,helpers}
mkdir -p tests/{unit,integration,e2e,fixtures}
mkdir -p docker/{development,production,scripts}
mkdir -p config/{engines,platforms,environments}
mkdir -p scripts/{setup,deploy,test,monitoring}
mkdir -p docs/{api,architecture,deployment,development}
mkdir -p logs/{api,crawl4ai,mediacrawl,scheduler}
mkdir -p data/{fingerprints,proxies,cache}
```

**验证步骤**：
```bash
# 验证目录结构创建成功
find . -type d | wc -l  # 应该显示 50+ 个目录
tree -d -L 3  # 查看目录树结构
```

### Task 1.2: 创建Python虚拟环境和项目配置

#### 1.2.1 创建pyproject.toml
```toml
# pyproject.toml
[tool.poetry]
name = "travel-crawler-system"
version = "1.0.0"
description = "双引擎旅游数据爬虫系统 - 支持Crawl4AI和MediaCrawl"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
crawl4ai = "^0.2.0"
playwright = "^1.40.0"
httpx = "^0.25.0"
redis = "^5.0.0"
asyncpg = "^0.29.0"
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
alembic = "^1.12.0"
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"
python-multipart = "^0.0.6"
aiofiles = "^23.0.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.0"}
tenacity = "^8.2.0"
loguru = "^0.7.0"
prometheus-client = "^0.19.0"
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.0.0"
isort = "^5.12.0"
mypy = "^1.7.0"
ruff = "^0.1.0"
pre-commit = "^3.5.0"

[tool.poetry.group.dev.dependencies]
jupyter = "^1.0.0"
ipython = "^8.17.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/migrations/*"]
```

#### 1.2.2 创建.gitignore
```gitignore
# .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/
dist/
build/

# IDE
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Logs
logs/
*.log

# Environment
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3

# Test coverage
.coverage
.pytest_cache/
htmlcov/

# Docker
docker-compose.override.yml

# Data
data/cache/
data/temp/
```

#### 1.2.3 初始化Python环境
```bash
# 安装Poetry（如果未安装）
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell

# 安装Playwright浏览器
playwright install chromium firefox webkit
```

**验证步骤**：
```bash
# 验证Python版本
python --version  # 应该显示 Python 3.11.x

# 验证主要包安装
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import crawl4ai; print('Crawl4AI installed')"
python -c "from playwright.async_api import async_playwright; print('Playwright ready')"
```

### Task 1.3: 创建核心配置系统

#### 1.3.1 创建环境变量配置
```python
# src/core/config/settings.py
"""应用配置管理"""
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn, validator
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    """全局配置类"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 基础配置
    APP_NAME: str = "Travel Crawler System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    APP_ENV: str = Field(default="development", pattern="^(development|staging|production)$")
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    API_TITLE: str = "Travel Crawler API"
    API_DESCRIPTION: str = "双引擎旅游数据爬虫系统API"
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=1)
    
    # 数据库配置
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://crawler:password@localhost:5432/crawler_db"
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    
    # Redis配置
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0"
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_POOL_SIZE: int = Field(default=20)
    REDIS_DECODE_RESPONSES: bool = Field(default=True)
    
    # 爬虫引擎配置
    CRAWL4AI_WORKERS: int = Field(default=5)
    CRAWL4AI_TIMEOUT: int = Field(default=30)
    CRAWL4AI_RETRY_TIMES: int = Field(default=3)
    
    MEDIACRAWL_WORKERS: int = Field(default=3)
    MEDIACRAWL_BROWSER_COUNT: int = Field(default=3)
    MEDIACRAWL_HEADLESS: bool = Field(default=True)
    
    # 调度器配置
    SCHEDULER_MAX_CONCURRENT_TASKS: int = Field(default=50)
    SCHEDULER_TASK_TIMEOUT: int = Field(default=300)
    SCHEDULER_CHECK_INTERVAL: int = Field(default=10)
    
    # 反爬配置
    PROXY_POOL_MIN_SIZE: int = Field(default=100)
    PROXY_CHECK_INTERVAL: int = Field(default=300)
    PROXY_SCORE_THRESHOLD: int = Field(default=70)
    
    FINGERPRINT_POOL_SIZE: int = Field(default=5000)
    FINGERPRINT_ROTATION_INTERVAL: int = Field(default=3600)
    
    # 安全配置
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    LOG_ROTATION: str = Field(default="10 MB")
    LOG_RETENTION: str = Field(default="7 days")
    
    # 项目路径
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    CONFIG_DIR: Path = PROJECT_ROOT / "config"
    
    @validator("LOGS_DIR", "DATA_DIR", "CONFIG_DIR", pre=True)
    def create_dirs(cls, v):
        """自动创建必要的目录"""
        if isinstance(v, Path):
            v.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        """Pydantic配置"""
        case_sensitive = True
        
@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()

# 导出配置实例
settings = get_settings()
```

#### 1.3.2 创建日志系统
```python
# src/utils/logger/logger.py
"""统一日志管理系统"""
from loguru import logger
from pathlib import Path
import sys
from typing import Optional
from src.core.config.settings import settings

class LoggerSetup:
    """日志配置类"""
    
    @staticmethod
    def setup():
        """配置日志系统"""
        # 移除默认的日志处理器
        logger.remove()
        
        # 控制台输出
        logger.add(
            sys.stderr,
            format=settings.LOG_FORMAT,
            level=settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # 通用日志文件
        logger.add(
            settings.LOGS_DIR / "app.log",
            format=settings.LOG_FORMAT,
            level=settings.LOG_LEVEL,
            rotation=settings.LOG_ROTATION,
            retention=settings.LOG_RETENTION,
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # 错误日志文件
        logger.add(
            settings.LOGS_DIR / "error.log",
            format=settings.LOG_FORMAT,
            level="ERROR",
            rotation=settings.LOG_ROTATION,
            retention=settings.LOG_RETENTION,
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # 爬虫专用日志
        logger.add(
            settings.LOGS_DIR / "crawler.log",
            format=settings.LOG_FORMAT,
            level="DEBUG",
            rotation=settings.LOG_ROTATION,
            retention=settings.LOG_RETENTION,
            compression="zip",
            filter=lambda record: "crawler" in record["name"]
        )
        
        logger.info(f"Logger initialized for {settings.APP_NAME}")
        
# 初始化日志
LoggerSetup.setup()

# 创建专用logger
def get_logger(name: str):
    """获取指定名称的logger"""
    return logger.bind(name=name)

# 导出
crawler_logger = get_logger("crawler")
api_logger = get_logger("api")
scheduler_logger = get_logger("scheduler")
```

#### 1.3.3 创建环境变量文件
```bash
# .env
# 基础配置
APP_NAME="Travel Crawler System"
APP_ENV=development
DEBUG=true

# API配置
API_V1_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql+asyncpg://crawler:secure_password@localhost:5432/crawler_db
DATABASE_POOL_SIZE=20

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20

# 爬虫引擎配置
CRAWL4AI_WORKERS=5
CRAWL4AI_TIMEOUT=30
MEDIACRAWL_WORKERS=3
MEDIACRAWL_HEADLESS=true

# 调度器配置
SCHEDULER_MAX_CONCURRENT_TASKS=50
SCHEDULER_TASK_TIMEOUT=300

# 反爬配置
PROXY_POOL_MIN_SIZE=100
FINGERPRINT_POOL_SIZE=5000

# 安全配置
SECRET_KEY=your-secret-key-change-in-production-$(openssl rand -hex 32)

# 日志配置
LOG_LEVEL=INFO
```

### Task 1.4: 创建Docker基础环境

#### 1.4.1 创建Docker Compose配置
```yaml
# docker-compose.yml
version: '3.9'

services:
  # PostgreSQL + PostGIS
  postgres:
    image: postgis/postgis:15-3.4-alpine
    container_name: crawler_postgres
    environment:
      POSTGRES_USER: crawler
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: crawler_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U crawler -d crawler_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - crawler_network

  # Redis
  redis:
    image: redis:7-alpine
    container_name: crawler_redis
    command: redis-server --appendonly yes --requirepass redis_secure_pass
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - crawler_network

  # 应用服务（开发模式）
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
      - DATABASE_URL=postgresql+asyncpg://crawler:secure_password@postgres:5432/crawler_db
      - REDIS_URL=redis://:redis_secure_pass@redis:6379/0
      - PYTHONPATH=/app
      - APP_ENV=development
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src
      - ./config:/app/config
      - ./logs:/app/logs
      - ./data:/app/data
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - crawler_network

volumes:
  postgres_data:
  redis_data:

networks:
  crawler_network:
    driver: bridge
```

#### 1.4.2 创建Dockerfile
```dockerfile
# docker/development/Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    postgresql-client \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 复制项目文件
COPY pyproject.toml poetry.lock* ./

# 安装Python依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# 安装Playwright浏览器
RUN playwright install chromium firefox webkit

# 复制源代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs data/fingerprints data/proxies data/cache

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

#### 1.4.3 创建数据库初始化脚本
```sql
-- scripts/init-db.sql
-- 创建PostGIS扩展
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- 创建基础表结构
-- POI基础信息表
CREATE TABLE IF NOT EXISTS pois (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    platform_id VARCHAR(200) NOT NULL,
    name VARCHAR(500) NOT NULL,
    type VARCHAR(100),
    address TEXT,
    location GEOGRAPHY(POINT, 4326),
    city VARCHAR(100),
    district VARCHAR(100),
    rating DECIMAL(3,2),
    review_count INTEGER DEFAULT 0,
    price_level INTEGER,
    phone VARCHAR(50),
    website VARCHAR(500),
    business_hours JSONB,
    tags TEXT[],
    images JSONB,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(platform, platform_id)
);

-- 创建索引
CREATE INDEX idx_pois_platform ON pois(platform);
CREATE INDEX idx_pois_location ON pois USING GIST(location);
CREATE INDEX idx_pois_city ON pois(city);
CREATE INDEX idx_pois_tags ON pois USING GIN(tags);

-- 爬取任务表
CREATE TABLE IF NOT EXISTS crawl_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    parameters JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    engine_type VARCHAR(50),
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 创建索引
CREATE INDEX idx_tasks_status ON crawl_tasks(status);
CREATE INDEX idx_tasks_platform ON crawl_tasks(platform);
CREATE INDEX idx_tasks_created_at ON crawl_tasks(created_at);

-- 代理池表
CREATE TABLE IF NOT EXISTS proxies (
    id SERIAL PRIMARY KEY,
    proxy_url VARCHAR(500) UNIQUE NOT NULL,
    proxy_type VARCHAR(20) NOT NULL,
    location VARCHAR(100),
    provider VARCHAR(100),
    score INTEGER DEFAULT 100,
    last_check_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    response_time DECIMAL(10,3),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_proxies_score ON proxies(score);
CREATE INDEX idx_proxies_active ON proxies(is_active);

-- 浏览器指纹表
CREATE TABLE IF NOT EXISTS browser_fingerprints (
    id SERIAL PRIMARY KEY,
    fingerprint_id VARCHAR(100) UNIQUE NOT NULL,
    user_agent TEXT NOT NULL,
    screen_resolution VARCHAR(20),
    timezone VARCHAR(50),
    languages VARCHAR(100)[],
    webgl_vendor VARCHAR(200),
    webgl_renderer VARCHAR(200),
    canvas_fingerprint TEXT,
    fonts TEXT[],
    plugins JSONB,
    hardware_concurrency INTEGER,
    device_memory INTEGER,
    platform VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    use_count INTEGER DEFAULT 0
);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pois_updated_at
    BEFORE UPDATE ON pois
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### Task 1.5: 创建主应用入口

#### 1.5.1 创建FastAPI主应用
```python
# src/main.py
"""主应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app
import uvicorn

from src.core.config.settings import settings
from src.utils.logger.logger import api_logger
from src.api.v1.router import api_router
from src.core.database import init_db, close_db
from src.core.redis import init_redis, close_redis
from src.core.scheduler import init_scheduler, close_scheduler

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    api_logger.info(f"Starting {settings.APP_NAME}...")
    
    # 初始化数据库
    await init_db()
    api_logger.info("Database initialized")
    
    # 初始化Redis
    await init_redis()
    api_logger.info("Redis initialized")
    
    # 初始化调度器
    await init_scheduler()
    api_logger.info("Scheduler initialized")
    
    api_logger.info(f"{settings.APP_NAME} started successfully!")
    
    yield
    
    # 关闭时执行
    api_logger.info(f"Shutting down {settings.APP_NAME}...")
    
    # 关闭调度器
    await close_scheduler()
    
    # 关闭Redis
    await close_redis()
    
    # 关闭数据库
    await close_db()
    
    api_logger.info(f"{settings.APP_NAME} shut down successfully!")

# 创建FastAPI应用
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# 添加中间件
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }

# 开发模式启动
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
```

#### 1.5.2 创建数据库连接管理
```python
# src/core/database.py
"""数据库连接管理"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from src.core.config.settings import settings
from src.utils.logger.logger import get_logger

logger = get_logger("database")

# 创建异步引擎
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    poolclass=NullPool if settings.DEBUG else None
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# 声明基类
Base = declarative_base()

# 数据库初始化
async def init_db():
    """初始化数据库"""
    try:
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# 关闭数据库连接
async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("Database connections closed")

# 获取数据库会话
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 事务管理上下文
@asynccontextmanager
async def db_transaction():
    """数据库事务上下文管理器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### 1.5.3 创建Redis连接管理
```python
# src/core/redis.py
"""Redis连接管理"""
import redis.asyncio as redis
from typing import Optional
from src.core.config.settings import settings
from src.utils.logger.logger import get_logger

logger = get_logger("redis")

# 全局Redis连接池
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None

async def init_redis():
    """初始化Redis连接池"""
    global redis_pool, redis_client
    
    try:
        # 创建连接池
        redis_pool = redis.ConnectionPool.from_url(
            str(settings.REDIS_URL),
            password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=settings.REDIS_DECODE_RESPONSES
        )
        
        # 创建Redis客户端
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # 测试连接
        await redis_client.ping()
        logger.info("Redis connection established successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

async def close_redis():
    """关闭Redis连接"""
    global redis_pool, redis_client
    
    if redis_client:
        await redis_client.close()
    
    if redis_pool:
        await redis_pool.disconnect()
    
    logger.info("Redis connections closed")

def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    return redis_client

# Redis键前缀
class RedisKeys:
    """Redis键定义"""
    # 任务相关
    TASK_QUEUE = "crawler:task:queue:{platform}"
    TASK_PROCESSING = "crawler:task:processing"
    TASK_RESULT = "crawler:task:result:{task_id}"
    
    # 代理相关
    PROXY_POOL = "crawler:proxy:pool"
    PROXY_BLACKLIST = "crawler:proxy:blacklist"
    PROXY_STATS = "crawler:proxy:stats:{proxy_id}"
    
    # 指纹相关
    FINGERPRINT_POOL = "crawler:fingerprint:pool"
    FINGERPRINT_USED = "crawler:fingerprint:used"
    
    # 缓存相关
    CACHE_POI = "crawler:cache:poi:{platform}:{poi_id}"
    CACHE_SEARCH = "crawler:cache:search:{platform}:{query_hash}"
    
    # 限流相关
    RATE_LIMIT = "crawler:ratelimit:{platform}:{key}"
    
    # 统计相关
    STATS_CRAWL = "crawler:stats:crawl:{platform}:{date}"
    STATS_ERROR = "crawler:stats:error:{platform}:{date}"
```

### Task 1.6: 创建基础验证脚本

#### 1.6.1 创建快速验证脚本
```python
# scripts/verify_setup.py
"""项目设置验证脚本"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config.settings import settings
from src.core.database import init_db, close_db, engine
from src.core.redis import init_redis, close_redis, get_redis
from src.utils.logger.logger import get_logger

logger = get_logger("verify")

async def verify_database():
    """验证数据库连接"""
    try:
        await init_db()
        
        # 测试查询
        async with engine.connect() as conn:
            result = await conn.execute("SELECT version()")
            version = result.scalar()
            logger.info(f"PostgreSQL version: {version}")
            
            # 检查PostGIS
            result = await conn.execute("SELECT PostGIS_version()")
            postgis_version = result.scalar()
            logger.info(f"PostGIS version: {postgis_version}")
        
        await close_db()
        return True
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

async def verify_redis():
    """验证Redis连接"""
    try:
        await init_redis()
        redis = get_redis()
        
        # 测试操作
        await redis.set("test:key", "test_value", ex=10)
        value = await redis.get("test:key")
        assert value == "test_value"
        
        # 获取信息
        info = await redis.info()
        logger.info(f"Redis version: {info['server']['redis_version']}")
        
        await close_redis()
        return True
    except Exception as e:
        logger.error(f"Redis verification failed: {e}")
        return False

async def verify_crawl4ai():
    """验证Crawl4AI"""
    try:
        from crawl4ai import AsyncWebCrawler
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url="https://example.com")
            logger.info(f"Crawl4AI test: Status {result.status_code}")
        
        return True
    except Exception as e:
        logger.error(f"Crawl4AI verification failed: {e}")
        return False

async def verify_playwright():
    """验证Playwright"""
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://example.com")
            title = await page.title()
            logger.info(f"Playwright test: Page title '{title}'")
            await browser.close()
        
        return True
    except Exception as e:
        logger.error(f"Playwright verification failed: {e}")
        return False

async def main():
    """主验证流程"""
    logger.info("Starting project setup verification...")
    
    # 验证配置
    logger.info(f"App Name: {settings.APP_NAME}")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    # 验证目录结构
    required_dirs = [
        settings.LOGS_DIR,
        settings.DATA_DIR,
        settings.CONFIG_DIR,
        settings.PROJECT_ROOT / "src",
        settings.PROJECT_ROOT / "tests"
    ]
    
    for dir_path in required_dirs:
        if dir_path.exists():
            logger.info(f"✓ Directory exists: {dir_path}")
        else:
            logger.error(f"✗ Directory missing: {dir_path}")
    
    # 验证组件
    components = [
        ("Database", verify_database),
        ("Redis", verify_redis),
        ("Crawl4AI", verify_crawl4ai),
        ("Playwright", verify_playwright)
    ]
    
    results = []
    for name, verify_func in components:
        logger.info(f"Verifying {name}...")
        result = await verify_func()
        results.append((name, result))
        if result:
            logger.info(f"✓ {name} verification passed")
        else:
            logger.error(f"✗ {name} verification failed")
    
    # 总结
    logger.info("\n" + "="*50)
    logger.info("Verification Summary:")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        logger.info("\n✅ All verifications passed! Project is ready.")
    else:
        logger.error("\n❌ Some verifications failed. Please check the logs.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
```

### 验证步骤汇总

执行以下命令验证整个Phase 1的设置：

```bash
# 1. 启动Docker服务
docker-compose up -d postgres redis

# 2. 等待服务启动
sleep 10

# 3. 运行验证脚本
poetry run python scripts/verify_setup.py

# 4. 检查API服务
poetry run python src/main.py &
sleep 5
curl http://localhost:8000/health

# 5. 查看日志
tail -f logs/app.log
```

如果所有验证都通过，说明项目基础架构已经成功搭建！

---

## 下一步

完成Phase 1后，我们将进入Phase 2：实现双引擎核心功能。请确保：
1. 所有验证步骤都通过
2. Docker服务正常运行
3. 日志系统工作正常
4. 可以访问API健康检查接口

准备好后，继续执行第2部分的任务。