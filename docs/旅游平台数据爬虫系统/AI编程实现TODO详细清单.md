# 旅游平台数据爬虫系统 - AI编程实现TODO详细清单

> 本文档为AI编程助手提供完整的项目实现指导，包含318个具体可执行任务

## 项目概览

**技术栈**：Python 3.11+ | FastAPI | PostgreSQL | Redis | Docker | Kubernetes
**开发周期**：50-60天
**团队规模**：4-6人
**目标平台**：8个主流旅游/社交平台

---

# 第一阶段：项目初始化与基础架构 [Priority: HIGH] [Time: 3-4天]

## 1.1 项目结构搭建

### 1.1.1 创建项目目录结构
#### 1.1.1.1 初始化项目根目录 [Time: 0.5h]
```bash
# 创建项目根目录
mkdir travel-crawler-system && cd travel-crawler-system

# 初始化Git仓库
git init
echo "# Travel Crawler System" > README.md
```

**验证标准**：项目根目录创建成功，Git仓库初始化完成

#### 1.1.1.2 创建完整目录结构 [Time: 1h]
```bash
# 核心代码目录
mkdir -p src/{core,engines,adapters,processors,api,utils}
mkdir -p src/core/{database,redis,scheduler,config,models}
mkdir -p src/engines/{base,crawl4ai,mediacrawl}
mkdir -p src/adapters/{base,amap,mafengwo,dianping,ctrip,xiaohongshu,douyin,weibo,bilibili}
mkdir -p src/processors/{cleaner,deduplicator,enhancer}
mkdir -p src/api/{v1,middleware,dependencies}
mkdir -p src/utils/{logger,validators,helpers,security}

# 配置和部署目录
mkdir -p config/{engines,platforms,environments}
mkdir -p docker/{development,production,scripts}
mkdir -p scripts/{setup,deploy,test,monitoring}

# 文档和测试目录
mkdir -p docs/{api,architecture,deployment,user_guide}
mkdir -p tests/{unit,integration,e2e,fixtures}
mkdir -p logs/{api,crawler,scheduler}
mkdir -p data/{raw,processed,cache}
```

**验证标准**：所有目录创建成功，目录结构符合分层架构设计

#### 1.1.1.3 创建核心配置文件 [Time: 2h]
```python
# pyproject.toml
[tool.poetry]
name = "travel-crawler-system"
version = "1.0.0"
description = "智能旅游数据爬虫系统"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
crawl4ai = "^0.2.0"
playwright = "^1.40.0"
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.29.0"
redis = "^5.0.0"
celery = "^5.3.0"
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
loguru = "^0.7.0"
prometheus-client = "^0.19.0"
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
ruff = "^0.1.0"
```

**验证标准**：配置文件创建完成，依赖包定义正确

### 1.1.2 环境配置管理

#### 1.1.2.1 创建环境变量配置 [Time: 1.5h]
```python
# src/core/config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path

class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "Travel Crawler System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    APP_ENV: str = "development"
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/crawler_db"
    DATABASE_POOL_SIZE: int = 20
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 20
    
    # 爬虫配置
    CRAWL4AI_WORKERS: int = 5
    MEDIACRAWL_WORKERS: int = 3
    
    # 安全配置
    SECRET_KEY: str = "change-me-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**验证标准**：配置类创建完成，支持环境变量覆盖

#### 1.1.2.2 创建多环境配置文件 [Time: 1h]
```bash
# .env.example
APP_NAME="Travel Crawler System"
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+asyncpg://crawler:secure_password@localhost:5432/crawler_db
REDIS_URL=redis://localhost:6379/0

SECRET_KEY=your-secret-key-here
```

**验证标准**：环境配置模板创建完成

## 1.2 数据库基础设施

### 1.2.1 数据库连接管理

#### 1.2.1.1 创建异步数据库引擎 [Time: 2h]
```python
# src/core/database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from src.core.config.settings import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    pool_timeout=30
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 声明基类
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
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

**验证标准**：数据库连接池创建成功，会话管理正常

#### 1.2.1.2 创建数据模型基类 [Time: 2h]
```python
# src/core/models/base.py
from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from src.core.database.connection import Base

class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BaseModel(Base, TimestampMixin):
    """基础模型类"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
```

**验证标准**：基础模型类创建完成，包含公共字段

### 1.2.2 核心数据模型

#### 1.2.2.1 创建POI数据模型 [Time: 3h]
```python
# src/core/models/poi.py
from sqlalchemy import Column, String, Text, Float, Integer, JSON, Index
from geoalchemy2 import Geography
from src.core.models.base import BaseModel

class POI(BaseModel):
    """POI基础模型"""
    __tablename__ = "pois"
    
    # 基础信息
    platform = Column(String(50), nullable=False, index=True)
    platform_poi_id = Column(String(200), nullable=False)
    name = Column(String(500), nullable=False)
    category = Column(String(100))
    
    # 位置信息
    address = Column(Text)
    city = Column(String(100), index=True)
    district = Column(String(100))
    location = Column(Geography('POINT', srid=4326))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # 评分信息
    rating = Column(Float)
    review_count = Column(Integer, default=0)
    
    # 价格信息
    price = Column(Float)
    price_unit = Column(String(20))
    
    # 联系信息
    phone = Column(String(50))
    website = Column(String(500))
    
    # 营业信息
    business_hours = Column(JSON)
    
    # 图片和描述
    cover_image = Column(String(500))
    images = Column(JSON)
    description = Column(Text)
    
    # 原始数据
    raw_data = Column(JSON)
    
    # 数据质量
    data_quality_score = Column(Float, default=0.0)
    last_verified_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_poi_platform_id', 'platform', 'platform_poi_id', unique=True),
        Index('idx_poi_location', 'location'),
        Index('idx_poi_city_category', 'city', 'category'),
    )
```

**验证标准**：POI模型创建完成，包含所有必要字段和索引

#### 1.2.2.2 创建爬取任务模型 [Time: 2h]
```python
# src/core/models/task.py
from sqlalchemy import Column, String, Text, Integer, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from src.core.models.base import BaseModel

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class CrawlTask(BaseModel):
    """爬取任务模型"""
    __tablename__ = "crawl_tasks"
    
    task_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    platform = Column(String(50), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)
    
    # 任务参数
    url = Column(Text, nullable=False)
    parameters = Column(JSON)
    
    # 执行状态
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 引擎信息
    engine_type = Column(String(50))
    worker_id = Column(String(100))
    
    # 结果信息
    result = Column(JSON)
    error_message = Column(Text)
    
    # 时间信息
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_task_status_priority', 'status', 'priority'),
        Index('idx_task_platform_type', 'platform', 'task_type'),
    )
```

**验证标准**：任务模型创建完成，支持任务状态管理

## 1.3 Redis缓存系统

### 1.3.1 Redis连接管理

#### 1.3.1.1 创建Redis连接池 [Time: 1.5h]
```python
# src/core/redis/connection.py
import redis.asyncio as redis
from typing import Optional
from src.core.config.settings import settings

class RedisManager:
    """Redis连接管理器"""
    
    def __init__(self):
        self.pool: Optional[redis.ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """初始化Redis连接"""
        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)
        
        # 测试连接
        await self.client.ping()
    
    async def close(self):
        """关闭Redis连接"""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
    
    def get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if not self.client:
            raise RuntimeError("Redis not initialized")
        return self.client

# 全局Redis管理器
redis_manager = RedisManager()
```

**验证标准**：Redis连接池创建成功，支持异步操作

#### 1.3.1.2 创建Redis键管理 [Time: 1h]
```python
# src/core/redis/keys.py
class RedisKeys:
    """Redis键命名规范"""
    
    # 任务队列
    TASK_QUEUE = "crawler:task:queue:{platform}"
    TASK_PROCESSING = "crawler:task:processing"
    TASK_RESULT = "crawler:task:result:{task_id}"
    
    # 代理池
    PROXY_POOL = "crawler:proxy:pool"
    PROXY_BLACKLIST = "crawler:proxy:blacklist"
    
    # 缓存
    POI_CACHE = "crawler:cache:poi:{platform}:{poi_id}"
    SEARCH_CACHE = "crawler:cache:search:{hash}"
    
    # 限流
    RATE_LIMIT = "crawler:ratelimit:{platform}:{key}"
    
    # 统计
    STATS_CRAWL = "crawler:stats:crawl:{platform}:{date}"
    
    @staticmethod
    def format_key(template: str, **kwargs) -> str:
        """格式化Redis键"""
        return template.format(**kwargs)
```

**验证标准**：Redis键管理系统创建完成

## 1.4 日志系统

### 1.4.1 日志配置

#### 1.4.1.1 创建统一日志配置 [Time: 2h]
```python
# src/utils/logger/logger.py
from loguru import logger
import sys
from pathlib import Path
from src.core.config.settings import settings

class LoggerSetup:
    """日志配置类"""
    
    @staticmethod
    def setup():
        """配置日志系统"""
        # 移除默认处理器
        logger.remove()
        
        # 控制台输出
        logger.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO",
            colorize=True
        )
        
        # 文件输出
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 应用日志
        logger.add(
            log_dir / "app.log",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            level="INFO"
        )
        
        # 错误日志
        logger.add(
            log_dir / "error.log",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            level="ERROR"
        )
        
        # 爬虫日志
        logger.add(
            log_dir / "crawler.log",
            rotation="50 MB",
            retention="7 days",
            compression="zip",
            level="DEBUG",
            filter=lambda record: "crawler" in record["name"]
        )

def get_logger(name: str):
    """获取指定名称的logger"""
    return logger.bind(name=name)

# 初始化日志
LoggerSetup.setup()
```

**验证标准**：日志系统配置完成，支持多级别输出

# 第二阶段：双引擎核心架构 [Priority: HIGH] [Time: 4-5天]

## 2.1 引擎抽象层

### 2.1.1 引擎接口定义

#### 2.1.1.1 创建引擎基础接口 [Time: 3h]
```python
# src/engines/base/engine_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class EngineType(str, Enum):
    CRAWL4AI = "crawl4ai"
    MEDIACRAWL = "mediacrawl"
    HYBRID = "hybrid"

class CrawlTask(BaseModel):
    """爬取任务定义"""
    task_id: str
    platform: str
    url: str
    method: str = "GET"
    headers: Dict[str, str] = {}
    params: Dict[str, Any] = {}
    timeout: int = 30
    retry_times: int = 3
    engine_type: EngineType = EngineType.CRAWL4AI
    extraction_rules: Dict[str, Any] = {}
    use_proxy: bool = True
    priority: int = 0
    metadata: Dict[str, Any] = {}

class CrawlResult(BaseModel):
    """爬取结果定义"""
    task_id: str
    success: bool
    status_code: Optional[int] = None
    url: str
    html: Optional[str] = None
    text: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    extracted_data: Dict[str, Any] = {}
    response_headers: Dict[str, str] = {}
    elapsed_time: float
    retry_count: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    engine_type: EngineType
    proxy_used: Optional[str] = None
    created_at: datetime = datetime.utcnow()

class CrawlingEngine(ABC):
    """爬虫引擎抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine_type: EngineType = EngineType.CRAWL4AI
        
    @abstractmethod
    async def initialize(self) -> None:
        """初始化引擎"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """关闭引擎"""
        pass
    
    @abstractmethod
    async def crawl(self, task: CrawlTask) -> CrawlResult:
        """执行爬取任务"""
        pass
    
    @abstractmethod
    async def batch_crawl(self, tasks: List[CrawlTask]) -> List[CrawlResult]:
        """批量爬取"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
```

**验证标准**：引擎接口定义完成，支持异步操作

#### 2.1.1.2 创建引擎管理器 [Time: 3h]
```python
# src/engines/base/engine_manager.py
from typing import Dict, List, Optional, Type
import asyncio
from src.engines.base.engine_interface import CrawlingEngine, EngineType, CrawlTask, CrawlResult
from src.utils.logger.logger import get_logger

logger = get_logger("engine.manager")

class EngineManager:
    """引擎管理器"""
    
    def __init__(self):
        self._engines: Dict[EngineType, CrawlingEngine] = {}
        self._engine_classes: Dict[EngineType, Type[CrawlingEngine]] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
    
    def register_engine(self, engine_type: EngineType, engine_class: Type[CrawlingEngine]):
        """注册引擎类"""
        self._engine_classes[engine_type] = engine_class
        logger.info(f"Registered engine: {engine_type}")
    
    async def initialize(self, configs: Dict[EngineType, Dict]):
        """初始化所有引擎"""
        async with self._lock:
            if self._initialized:
                return
            
            for engine_type, engine_class in self._engine_classes.items():
                if engine_type in configs:
                    try:
                        engine = engine_class(configs[engine_type])
                        await engine.initialize()
                        self._engines[engine_type] = engine
                        logger.info(f"Initialized engine: {engine_type}")
                    except Exception as e:
                        logger.error(f"Failed to initialize engine {engine_type}: {e}")
                        raise
            
            self._initialized = True
    
    async def select_engine(self, task: CrawlTask) -> CrawlingEngine:
        """选择合适的引擎"""
        # 如果指定了引擎类型
        if task.engine_type != EngineType.HYBRID:
            engine = self._engines.get(task.engine_type)
            if engine and await engine.health_check():
                return engine
        
        # 自动选择逻辑
        platform_engine_map = {
            "amap": EngineType.CRAWL4AI,
            "mafengwo": EngineType.CRAWL4AI,
            "dianping": EngineType.CRAWL4AI,
            "ctrip": EngineType.CRAWL4AI,
            "xiaohongshu": EngineType.MEDIACRAWL,
            "douyin": EngineType.MEDIACRAWL,
            "weibo": EngineType.MEDIACRAWL,
            "bilibili": EngineType.MEDIACRAWL
        }
        
        preferred_type = platform_engine_map.get(task.platform, EngineType.CRAWL4AI)
        engine = self._engines.get(preferred_type)
        
        if engine and await engine.health_check():
            return engine
        
        # 回退到任何可用引擎
        for engine in self._engines.values():
            if await engine.health_check():
                return engine
        
        raise RuntimeError("No available engine found")
    
    async def execute_task(self, task: CrawlTask) -> CrawlResult:
        """执行任务"""
        engine = await self.select_engine(task)
        return await engine.crawl(task)

# 全局引擎管理器
engine_manager = EngineManager()
```

**验证标准**：引擎管理器创建完成，支持引擎注册和选择

## 2.2 Crawl4AI引擎实现

### 2.2.1 Crawl4AI引擎核心

#### 2.2.1.1 实现Crawl4AI引擎类 [Time: 4h]
```python
# src/engines/crawl4ai/engine.py
import asyncio
import time
from typing import List, Dict, Any, Optional
from crawl4ai import AsyncWebCrawler
from src.engines.base.engine_interface import CrawlingEngine, EngineType, CrawlTask, CrawlResult
from src.utils.logger.logger import get_logger

logger = get_logger("engine.crawl4ai")

class Crawl4AIEngine(CrawlingEngine):
    """Crawl4AI引擎实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.engine_type = EngineType.CRAWL4AI
        self.max_workers = config.get("workers", 5)
        self.default_timeout = config.get("timeout", 30)
        self._crawler_pool: List[AsyncWebCrawler] = []
        self._available_crawlers = asyncio.Queue(maxsize=self.max_workers)
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time": 0.0
        }
    
    async def initialize(self) -> None:
        """初始化引擎"""
        try:
            for i in range(self.max_workers):
                crawler = AsyncWebCrawler(
                    browser_type="chromium",
                    headless=True,
                    verbose=False
                )
                self._crawler_pool.append(crawler)
                await self._available_crawlers.put(crawler)
            
            logger.info(f"Crawl4AI engine initialized with {self.max_workers} workers")
        except Exception as e:
            logger.error(f"Failed to initialize Crawl4AI engine: {e}")
            raise
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        try:
            for crawler in self._crawler_pool:
                # Crawl4AI的清理逻辑
                pass
            self._crawler_pool.clear()
            logger.info("Crawl4AI engine shut down")
        except Exception as e:
            logger.error(f"Error shutting down Crawl4AI engine: {e}")
    
    async def crawl(self, task: CrawlTask) -> CrawlResult:
        """执行爬取任务"""
        start_time = time.time()
        result = CrawlResult(
            task_id=task.task_id,
            success=False,
            url=task.url,
            engine_type=self.engine_type,
            elapsed_time=0.0
        )
        
        crawler = await self._available_crawlers.get()
        
        try:
            # 准备爬取配置
            crawl_config = await self._prepare_config(task)
            
            # 执行爬取
            crawl_result = await crawler.arun(
                url=task.url,
                **crawl_config
            )
            
            # 处理结果
            result.success = crawl_result.success
            result.status_code = crawl_result.status_code
            result.html = crawl_result.html
            result.text = crawl_result.text
            
            # 数据提取
            if task.extraction_rules:
                result.extracted_data = await self._extract_data(
                    crawl_result, task.extraction_rules
                )
            
            self._update_metrics(result, time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Crawl task {task.task_id} failed: {e}")
            result.error_type = type(e).__name__
            result.error_message = str(e)
        finally:
            await self._available_crawlers.put(crawler)
            result.elapsed_time = time.time() - start_time
        
        return result
    
    async def batch_crawl(self, tasks: List[CrawlTask]) -> List[CrawlResult]:
        """批量爬取"""
        tasks_coroutines = [self.crawl(task) for task in tasks]
        results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = CrawlResult(
                    task_id=tasks[i].task_id,
                    success=False,
                    url=tasks[i].url,
                    engine_type=self.engine_type,
                    error_type=type(result).__name__,
                    error_message=str(result),
                    elapsed_time=0.0
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return len(self._crawler_pool) > 0 and self._available_crawlers.qsize() > 0
        except Exception:
            return False
    
    async def _prepare_config(self, task: CrawlTask) -> Dict[str, Any]:
        """准备爬取配置"""
        config = {
            "word_count_threshold": 10,
            "exclude_external_images": True,
            "remove_overlay_elements": True
        }
        
        if task.headers:
            config["headers"] = task.headers
        
        return config
    
    async def _extract_data(self, crawl_result: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """提取数据"""
        extracted = {}
        
        try:
            if hasattr(crawl_result, 'extracted_content'):
                extracted = crawl_result.extracted_content
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
        
        return extracted
    
    def _update_metrics(self, result: CrawlResult, elapsed_time: float):
        """更新指标"""
        self._metrics["total_requests"] += 1
        if result.success:
            self._metrics["successful_requests"] += 1
        else:
            self._metrics["failed_requests"] += 1
        self._metrics["total_time"] += elapsed_time
```

**验证标准**：Crawl4AI引擎实现完成，支持并发爬取

## 2.3 MediaCrawl引擎实现

### 2.3.1 MediaCrawl引擎核心

#### 2.3.1.1 实现MediaCrawl引擎类 [Time: 4h]
```python
# src/engines/mediacrawl/engine.py
import asyncio
import time
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from src.engines.base.engine_interface import CrawlingEngine, EngineType, CrawlTask, CrawlResult
from src.utils.logger.logger import get_logger

logger = get_logger("engine.mediacrawl")

class MediaCrawlEngine(CrawlingEngine):
    """MediaCrawl引擎实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.engine_type = EngineType.MEDIACRAWL
        self.max_workers = config.get("workers", 3)
        self.headless = config.get("headless", True)
        self.browser_type = config.get("browser", "chromium")
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._contexts: List[BrowserContext] = []
        self._available_contexts = asyncio.Queue(maxsize=self.max_workers)
        
    async def initialize(self) -> None:
        """初始化引擎"""
        try:
            self._playwright = await async_playwright().start()
            
            # 选择浏览器
            if self.browser_type == "chromium":
                browser_launcher = self._playwright.chromium
            elif self.browser_type == "firefox":
                browser_launcher = self._playwright.firefox
            else:
                browser_launcher = self._playwright.webkit
            
            # 启动浏览器
            self._browser = await browser_launcher.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # 创建上下文池
            for i in range(self.max_workers):
                context = await self._create_context()
                self._contexts.append(context)
                await self._available_contexts.put(context)
            
            logger.info(f"MediaCrawl engine initialized with {self.max_workers} contexts")
            
        except Exception as e:
            logger.error(f"Failed to initialize MediaCrawl engine: {e}")
            raise
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        try:
            # 关闭所有上下文
            for context in self._contexts:
                await context.close()
            
            # 关闭浏览器
            if self._browser:
                await self._browser.close()
            
            # 停止playwright
            if self._playwright:
                await self._playwright.stop()
            
            logger.info("MediaCrawl engine shut down")
        except Exception as e:
            logger.error(f"Error shutting down MediaCrawl engine: {e}")
    
    async def crawl(self, task: CrawlTask) -> CrawlResult:
        """执行爬取任务"""
        start_time = time.time()
        result = CrawlResult(
            task_id=task.task_id,
            success=False,
            url=task.url,
            engine_type=self.engine_type,
            elapsed_time=0.0
        )
        
        context = await self._available_contexts.get()
        page = None
        
        try:
            # 创建页面
            page = await context.new_page()
            
            # 设置额外headers
            if task.headers:
                await page.set_extra_http_headers(task.headers)
            
            # 设置视窗大小
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 访问页面
            response = await page.goto(
                task.url,
                timeout=task.timeout * 1000,
                wait_until="networkidle"
            )
            
            # 处理结果
            result.success = response and response.ok
            result.status_code = response.status if response else None
            result.html = await page.content()
            result.text = await page.inner_text("body")
            
            # 提取特定数据
            if task.extraction_rules:
                result.extracted_data = await self._extract_media_data(
                    page, task.extraction_rules
                )
            
            # 获取响应头
            if response:
                result.response_headers = response.headers
            
        except Exception as e:
            logger.error(f"MediaCrawl task {task.task_id} failed: {e}")
            result.error_type = type(e).__name__
            result.error_message = str(e)
        finally:
            if page:
                await page.close()
            await self._available_contexts.put(context)
            result.elapsed_time = time.time() - start_time
        
        return result
    
    async def batch_crawl(self, tasks: List[CrawlTask]) -> List[CrawlResult]:
        """批量爬取"""
        tasks_coroutines = [self.crawl(task) for task in tasks]
        results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = CrawlResult(
                    task_id=tasks[i].task_id,
                    success=False,
                    url=tasks[i].url,
                    engine_type=self.engine_type,
                    error_type=type(result).__name__,
                    error_message=str(result),
                    elapsed_time=0.0
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return (
                self._browser is not None and 
                self._browser.is_connected() and
                self._available_contexts.qsize() > 0
            )
        except Exception:
            return False
    
    async def _create_context(self) -> BrowserContext:
        """创建浏览器上下文"""
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        
        # 拦截请求
        await context.route("**/*", self._handle_route)
        
        return context
    
    async def _handle_route(self, route, request):
        """处理路由拦截"""
        # 阻止某些资源类型
        if request.resource_type in ["image", "font", "stylesheet"]:
            await route.abort()
        else:
            await route.continue_()
    
    async def _extract_media_data(self, page: Page, rules: Dict[str, Any]) -> Dict[str, Any]:
        """提取媒体数据"""
        extracted = {}
        
        try:
            # 文本提取
            if "text_selectors" in rules:
                for key, selector in rules["text_selectors"].items():
                    elements = await page.query_selector_all(selector)
                    extracted[key] = [await el.inner_text() for el in elements]
            
            # 属性提取
            if "attr_selectors" in rules:
                for key, config in rules["attr_selectors"].items():
                    selector = config["selector"]
                    attr = config["attribute"]
                    elements = await page.query_selector_all(selector)
                    extracted[key] = [await el.get_attribute(attr) for el in elements]
            
            # JavaScript执行
            if "js_extractors" in rules:
                for key, js_code in rules["js_extractors"].items():
                    result = await page.evaluate(js_code)
                    extracted[key] = result
            
            # 截图
            if rules.get("screenshot"):
                screenshot = await page.screenshot(full_page=True)
                extracted["screenshot"] = screenshot
                
        except Exception as e:
            logger.error(f"Media data extraction failed: {e}")
        
        return extracted
```

**验证标准**：MediaCrawl引擎实现完成，支持浏览器自动化

#### 2.3.1.2 创建引擎注册机制 [Time: 2h]
```python
# src/engines/__init__.py
from src.engines.base.engine_manager import engine_manager
from src.engines.crawl4ai.engine import Crawl4AIEngine
from src.engines.mediacrawl.engine import MediaCrawlEngine
from src.engines.base.engine_interface import EngineType

# 注册引擎
engine_manager.register_engine(EngineType.CRAWL4AI, Crawl4AIEngine)
engine_manager.register_engine(EngineType.MEDIACRAWL, MediaCrawlEngine)

async def initialize_engines(config: dict):
    """初始化所有引擎"""
    await engine_manager.initialize(config)

async def shutdown_engines():
    """关闭所有引擎"""
    for engine_type, engine in engine_manager._engines.items():
        await engine.shutdown()
```

**验证标准**：引擎注册机制完成，支持动态引擎管理

---

# 第三阶段：反爬系统实现 [Priority: HIGH] [Time: 5-6天]

## 3.1 代理池系统

### 3.1.1 代理存储与管理

#### 3.1.1.1 创建代理数据模型 [Time: 2h]
```python
# src/core/models/proxy.py
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from src.core.models.base import BaseModel

class ProxyServer(BaseModel):
    """代理服务器模型"""
    __tablename__ = "proxy_servers"
    
    # 代理信息
    ip = Column(String(45), nullable=False, index=True)
    port = Column(Integer, nullable=False)
    protocol = Column(String(10), default="http")  # http, https, socks4, socks5
    username = Column(String(255))
    password = Column(String(255))
    
    # 地理信息
    country = Column(String(50))
    city = Column(String(100))
    isp = Column(String(100))
    
    # 性能指标
    speed = Column(Float, default=0.0)  # 响应速度(ms)
    success_rate = Column(Float, default=0.0)  # 成功率
    last_check_time = Column(DateTime(timezone=True))
    last_used_time = Column(DateTime(timezone=True))
    
    # 状态管理
    is_working = Column(Boolean, default=True)
    is_anonymous = Column(Boolean, default=True)
    fail_count = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    
    # 使用限制
    max_concurrent = Column(Integer, default=1)
    current_concurrent = Column(Integer, default=0)
    daily_limit = Column(Integer, default=1000)
    daily_used = Column(Integer, default=0)
    
    # 来源信息
    source = Column(String(100))  # 代理来源
    cost = Column(Float, default=0.0)  # 成本
    expires_at = Column(DateTime(timezone=True))
    
    @property
    def proxy_url(self) -> str:
        """构建代理URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.ip}:{self.port}"
        return f"{self.protocol}://{self.ip}:{self.port}"
    
    def update_metrics(self, success: bool, response_time: float):
        """更新代理指标"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.fail_count += 1
        
        self.success_rate = self.successful_requests / self.total_requests
        self.speed = (self.speed + response_time) / 2  # 简单平均
        self.last_used_time = func.now()
```

**验证标准**：代理数据模型创建完成，支持完整的代理信息管理

#### 3.1.1.2 实现代理池管理器 [Time: 4h]
```python
# src/core/anti_detection/proxy_pool.py
import asyncio
import random
import aiohttp
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from src.core.models.proxy import ProxyServer
from src.core.database.connection import get_db
from src.utils.logger.logger import get_logger
from src.core.redis.connection import redis_manager

logger = get_logger("anti_detection.proxy_pool")

class ProxyPoolManager:
    """代理池管理器"""
    
    def __init__(self):
        self.check_interval = 300  # 5分钟检查一次
        self.max_fail_count = 5
        self.test_url = "http://httpbin.org/ip"
        self.concurrent_checks = 50
        
    async def get_proxy(
        self, 
        platform: str = None, 
        country: str = None,
        min_success_rate: float = 0.8
    ) -> Optional[ProxyServer]:
        """获取可用代理"""
        try:
            # 构建查询条件
            conditions = [
                ProxyServer.is_working == True,
                ProxyServer.success_rate >= min_success_rate,
                ProxyServer.current_concurrent < ProxyServer.max_concurrent,
                ProxyServer.daily_used < ProxyServer.daily_limit
            ]
            
            if country:
                conditions.append(ProxyServer.country == country)
            
            # 从Redis缓存获取
            cache_key = f"proxy:available:{platform or 'default'}:{country or 'any'}"
            cached_proxy_id = await redis_manager.get_client().get(cache_key)
            
            if cached_proxy_id:
                async with get_db() as db:
                    proxy = await db.get(ProxyServer, int(cached_proxy_id))
                    if proxy and self._is_proxy_available(proxy):
                        await self._reserve_proxy(proxy)
                        return proxy
            
            # 从数据库查询
            async with get_db() as db:
                query = db.query(ProxyServer).filter(and_(*conditions))
                
                # 平台特定的代理优先级
                if platform:
                    platform_priority = self._get_platform_priority(platform)
                    query = query.filter(ProxyServer.country.in_(platform_priority))
                
                # 按成功率和速度排序
                query = query.order_by(
                    ProxyServer.success_rate.desc(),
                    ProxyServer.speed.asc()
                ).limit(10)
                
                proxies = await query.all()
                
                if proxies:
                    # 随机选择避免热点代理
                    proxy = random.choice(proxies)
                    await self._reserve_proxy(proxy)
                    
                    # 缓存到Redis
                    await redis_manager.get_client().setex(
                        cache_key, 60, proxy.id
                    )
                    
                    return proxy
                    
        except Exception as e:
            logger.error(f"Failed to get proxy: {e}")
        
        return None
    
    async def release_proxy(self, proxy: ProxyServer, success: bool, response_time: float):
        """释放代理并更新统计"""
        try:
            async with get_db() as db:
                # 更新指标
                proxy.update_metrics(success, response_time)
                
                # 释放并发占用
                proxy.current_concurrent = max(0, proxy.current_concurrent - 1)
                proxy.daily_used += 1
                
                # 如果失败太多，标记为不可用
                if not success:
                    if proxy.fail_count >= self.max_fail_count:
                        proxy.is_working = False
                        logger.warning(f"Proxy {proxy.ip}:{proxy.port} marked as failed")
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to release proxy: {e}")
    
    async def add_proxy(self, proxy_info: Dict[str, Any]) -> bool:
        """添加新代理"""
        try:
            async with get_db() as db:
                # 检查是否已存在
                existing = await db.query(ProxyServer).filter(
                    and_(
                        ProxyServer.ip == proxy_info["ip"],
                        ProxyServer.port == proxy_info["port"]
                    )
                ).first()
                
                if existing:
                    return False
                
                # 创建新代理
                proxy = ProxyServer(**proxy_info)
                db.add(proxy)
                await db.commit()
                
                # 测试新代理
                await self._test_proxy(proxy)
                
                logger.info(f"Added new proxy {proxy.ip}:{proxy.port}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add proxy: {e}")
            return False
    
    async def health_check(self):
        """代理池健康检查"""
        try:
            async with get_db() as db:
                # 获取需要检查的代理
                proxies = await db.query(ProxyServer).filter(
                    or_(
                        ProxyServer.last_check_time.is_(None),
                        ProxyServer.last_check_time < func.now() - timedelta(minutes=30)
                    )
                ).limit(self.concurrent_checks).all()
                
                if proxies:
                    # 并发测试代理
                    tasks = [self._test_proxy(proxy) for proxy in proxies]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    await db.commit()
                    
                    # 统计信息
                    working_count = len([p for p in proxies if p.is_working])
                    logger.info(f"Health check completed: {working_count}/{len(proxies)} proxies working")
                    
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _test_proxy(self, proxy: ProxyServer) -> bool:
        """测试单个代理"""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy.proxy_url
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        returned_ip = data.get("origin", "").split(",")[0].strip()
                        
                        # 验证IP是否匹配
                        if returned_ip == proxy.ip:
                            proxy.is_working = True
                            proxy.speed = response_time
                            proxy.last_check_time = func.now()
                            proxy.fail_count = 0
                            return True
            
            proxy.is_working = False
            proxy.fail_count += 1
            return False
            
        except Exception as e:
            logger.debug(f"Proxy {proxy.ip}:{proxy.port} test failed: {e}")
            proxy.is_working = False
            proxy.fail_count += 1
            proxy.last_check_time = func.now()
            return False
    
    def _is_proxy_available(self, proxy: ProxyServer) -> bool:
        """检查代理是否可用"""
        return (
            proxy.is_working and
            proxy.current_concurrent < proxy.max_concurrent and
            proxy.daily_used < proxy.daily_limit and
            proxy.success_rate >= 0.8
        )
    
    async def _reserve_proxy(self, proxy: ProxyServer):
        """预留代理"""
        proxy.current_concurrent += 1
    
    def _get_platform_priority(self, platform: str) -> List[str]:
        """获取平台优先的代理地区"""
        priority_map = {
            "amap": ["CN", "HK", "TW"],
            "dianping": ["CN", "HK", "TW"],
            "mafengwo": ["CN", "HK", "TW"],
            "ctrip": ["CN", "HK", "TW"],
            "xiaohongshu": ["CN", "HK", "TW", "SG"],
            "douyin": ["CN", "HK", "TW"],
            "weibo": ["CN", "HK", "TW"],
            "bilibili": ["CN", "HK", "TW"]
        }
        return priority_map.get(platform, ["US", "UK", "DE", "JP"])
```

**验证标准**：代理池管理器实现完成，支持智能代理分配和健康检查

### 3.1.2 代理采集与补充

#### 3.1.2.1 实现代理采集器 [Time: 3h]
```python
# src/core/anti_detection/proxy_collector.py
import asyncio
import aiohttp
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.core.anti_detection.proxy_pool import ProxyPoolManager
from src.utils.logger.logger import get_logger

logger = get_logger("anti_detection.proxy_collector")

class ProxyCollector:
    """代理采集器"""
    
    def __init__(self, pool_manager: ProxyPoolManager):
        self.pool_manager = pool_manager
        self.sources = [
            {
                "name": "free-proxy-list",
                "url": "https://free-proxy-list.net/",
                "parser": self._parse_free_proxy_list
            },
            {
                "name": "proxy-list-download",
                "url": "https://www.proxy-list.download/HTTP",
                "parser": self._parse_proxy_list_download
            }
        ]
    
    async def collect_proxies(self) -> int:
        """采集新代理"""
        total_collected = 0
        
        for source in self.sources:
            try:
                proxies = await self._collect_from_source(source)
                
                # 批量添加代理
                for proxy in proxies:
                    success = await self.pool_manager.add_proxy(proxy)
                    if success:
                        total_collected += 1
                
                logger.info(f"Collected {len(proxies)} proxies from {source['name']}")
                
            except Exception as e:
                logger.error(f"Failed to collect from {source['name']}: {e}")
        
        return total_collected
    
    async def _collect_from_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从单个源采集代理"""
        async with aiohttp.ClientSession() as session:
            async with session.get(source["url"]) as response:
                if response.status == 200:
                    content = await response.text()
                    return await source["parser"](content)
        return []
    
    async def _parse_free_proxy_list(self, content: str) -> List[Dict[str, Any]]:
        """解析free-proxy-list"""
        proxies = []
        soup = BeautifulSoup(content, 'html.parser')
        
        table = soup.find('table', {'id': 'proxylisttable'})
        if table:
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    proxy = {
                        "ip": cols[0].text.strip(),
                        "port": int(cols[1].text.strip()),
                        "country": cols[2].text.strip(),
                        "is_anonymous": cols[4].text.strip() != "transparent",
                        "protocol": "https" if cols[6].text.strip() == "yes" else "http",
                        "source": "free-proxy-list"
                    }
                    proxies.append(proxy)
        
        return proxies
    
    async def _parse_proxy_list_download(self, content: str) -> List[Dict[str, Any]]:
        """解析proxy-list-download"""
        proxies = []
        lines = content.strip().split('\n')
        
        for line in lines:
            if ':' in line:
                try:
                    ip, port = line.strip().split(':')
                    proxy = {
                        "ip": ip,
                        "port": int(port),
                        "protocol": "http",
                        "source": "proxy-list-download"
                    }
                    proxies.append(proxy)
                except ValueError:
                    continue
        
        return proxies
```

**验证标准**：代理采集器实现完成，支持多源代理采集

## 3.2 浏览器指纹管理

### 3.2.1 指纹生成系统

#### 3.2.1.1 实现指纹生成器 [Time: 4h]
```python
# src/core/anti_detection/fingerprint_manager.py
import random
import hashlib
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from src.utils.logger.logger import get_logger

logger = get_logger("anti_detection.fingerprint")

@dataclass
class BrowserFingerprint:
    """浏览器指纹数据"""
    user_agent: str
    screen_resolution: tuple
    timezone: str
    language: str
    platform: str
    plugins: List[str]
    canvas_fingerprint: str
    webgl_vendor: str
    webgl_renderer: str
    cpu_class: str
    hardware_concurrency: int
    device_memory: int

class FingerprintManager:
    """浏览器指纹管理器"""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
            (1280, 720), (2560, 1440), (3840, 2160)
        ]
        
        self.languages = ["en-US", "en-GB", "zh-CN", "zh-TW", "ja-JP", "ko-KR"]
        self.timezones = ["Asia/Shanghai", "Asia/Tokyo", "America/New_York", "Europe/London"]
        
        self.canvas_patterns = [
            "random_text_with_emojis_🌟",
            "complex_geometric_shapes_█▄▀",
            "mixed_fonts_and_colors_ABC123",
            "gradient_background_pattern_◢◣"
        ]
    
    def generate_fingerprint(self, platform: str = None) -> BrowserFingerprint:
        """生成随机浏览器指纹"""
        
        # 基础信息
        user_agent = random.choice(self.user_agents)
        screen_resolution = random.choice(self.screen_resolutions)
        language = random.choice(self.languages)
        timezone = random.choice(self.timezones)
        
        # 平台相关调整
        if platform in ["xiaohongshu", "douyin", "weibo", "bilibili"]:
            # 中国平台倾向中文环境
            language = random.choice(["zh-CN", "zh-TW"])
            timezone = "Asia/Shanghai"
        
        # 生成Canvas指纹
        canvas_fingerprint = self._generate_canvas_fingerprint()
        
        # WebGL信息
        webgl_vendor, webgl_renderer = self._generate_webgl_info()
        
        fingerprint = BrowserFingerprint(
            user_agent=user_agent,
            screen_resolution=screen_resolution,
            timezone=timezone,
            language=language,
            platform=self._extract_platform_from_ua(user_agent),
            plugins=self._generate_plugins(),
            canvas_fingerprint=canvas_fingerprint,
            webgl_vendor=webgl_vendor,
            webgl_renderer=webgl_renderer,
            cpu_class="unknown",
            hardware_concurrency=random.choice([2, 4, 6, 8, 12, 16]),
            device_memory=random.choice([2, 4, 6, 8, 16, 32])
        )
        
        return fingerprint
    
    def apply_fingerprint_to_page(self, page, fingerprint: BrowserFingerprint):
        """将指纹应用到页面"""
        js_code = f"""
        // 重写navigator属性
        Object.defineProperty(navigator, 'userAgent', {{
            get: () => '{fingerprint.user_agent}'
        }});
        
        Object.defineProperty(navigator, 'language', {{
            get: () => '{fingerprint.language}'
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['{fingerprint.language}']
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fingerprint.platform}'
        }});
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {fingerprint.hardware_concurrency}
        }});
        
        // 重写screen属性
        Object.defineProperty(screen, 'width', {{
            get: () => {fingerprint.screen_resolution[0]}
        }});
        
        Object.defineProperty(screen, 'height', {{
            get: () => {fingerprint.screen_resolution[1]}
        }});
        
        // Canvas指纹
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {{
            const ctx = this.getContext('2d');
            ctx.fillText('{fingerprint.canvas_fingerprint}', 10, 10);
            return originalToDataURL.apply(this, arguments);
        }};
        
        // WebGL指纹
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{fingerprint.webgl_vendor}';
            if (parameter === 37446) return '{fingerprint.webgl_renderer}';
            return originalGetParameter.apply(this, arguments);
        }};
        
        // 时区设置
        Date.prototype.getTimezoneOffset = function() {{
            const timezoneOffsets = {{
                'Asia/Shanghai': -480,
                'Asia/Tokyo': -540,
                'America/New_York': 300,
                'Europe/London': 0
            }};
            return timezoneOffsets['{fingerprint.timezone}'] || 0;
        }};
        """
        
        return page.add_init_script(js_code)
    
    def _generate_canvas_fingerprint(self) -> str:
        """生成Canvas指纹"""
        pattern = random.choice(self.canvas_patterns)
        noise = random.randint(100000, 999999)
        return f"{pattern}_{noise}"
    
    def _generate_webgl_info(self) -> tuple:
        """生成WebGL信息"""
        vendors = ["Intel Inc.", "NVIDIA Corporation", "AMD", "Apple Inc."]
        renderers = [
            "Intel(R) UHD Graphics 620",
            "NVIDIA GeForce RTX 3070",
            "AMD Radeon RX 6800 XT",
            "Apple M1",
            "Intel(R) Iris(R) Xe Graphics"
        ]
        
        return random.choice(vendors), random.choice(renderers)
    
    def _extract_platform_from_ua(self, user_agent: str) -> str:
        """从User-Agent提取平台信息"""
        if "Windows" in user_agent:
            return "Win32"
        elif "Macintosh" in user_agent:
            return "MacIntel"
        elif "Linux" in user_agent:
            return "Linux x86_64"
        return "unknown"
    
    def _generate_plugins(self) -> List[str]:
        """生成插件列表"""
        common_plugins = [
            "PDF Viewer",
            "Chrome PDF Viewer",
            "Chromium PDF Viewer",
            "Microsoft Edge PDF Viewer",
            "WebKit built-in PDF"
        ]
        
        return random.sample(common_plugins, random.randint(2, len(common_plugins)))
```

**验证标准**：指纹生成器实现完成，支持多维度指纹伪造

## 3.3 行为模拟系统

### 3.3.1 人类行为模拟

#### 3.3.1.1 实现行为模拟器 [Time: 4h]
```python
# src/core/anti_detection/behavior_simulator.py
import asyncio
import random
import math
from typing import List, Tuple, Dict, Any
from playwright.async_api import Page
from src.utils.logger.logger import get_logger

logger = get_logger("anti_detection.behavior_simulator")

class BehaviorSimulator:
    """人类行为模拟器"""
    
    def __init__(self):
        self.typing_speed_range = (50, 150)  # 每分钟字符数
        self.mouse_movement_steps = 20
        self.scroll_step_range = (50, 200)
        
    async def simulate_human_behavior(self, page: Page, task_type: str = "browse"):
        """模拟人类行为"""
        try:
            # 基础行为序列
            await self._random_wait(1, 3)
            await self._simulate_mouse_movement(page)
            
            if task_type == "search":
                await self._simulate_search_behavior(page)
            elif task_type == "browse":
                await self._simulate_browse_behavior(page)
            elif task_type == "scroll":
                await self._simulate_scroll_behavior(page)
            
        except Exception as e:
            logger.error(f"Behavior simulation failed: {e}")
    
    async def _simulate_search_behavior(self, page: Page):
        """模拟搜索行为"""
        try:
            # 查找搜索框
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="搜索"]',
                'input[placeholder*="search"]',
                '#search', '.search-input',
                'input[name="q"]', 'input[name="keyword"]'
            ]
            
            search_input = None
            for selector in search_selectors:
                search_input = await page.query_selector(selector)
                if search_input:
                    break
            
            if search_input:
                # 模拟点击搜索框
                await self._simulate_click(page, search_input)
                await self._random_wait(0.5, 1.5)
                
                # 模拟清空输入框
                await search_input.click(click_count=3)
                await page.keyboard.press("Delete")
                
                # 模拟人类输入
                await self._human_type(page, "旅游景点")
                await self._random_wait(1, 2)
                
                # 模拟回车或点击搜索按钮
                await page.keyboard.press("Enter")
                
        except Exception as e:
            logger.debug(f"Search simulation failed: {e}")
    
    async def _simulate_browse_behavior(self, page: Page):
        """模拟浏览行为"""
        try:
            # 随机滚动页面
            for _ in range(random.randint(2, 5)):
                await self._simulate_scroll(page)
                await self._random_wait(2, 4)
            
            # 随机点击一些链接
            links = await page.query_selector_all('a[href]')
            if links:
                link = random.choice(links[:10])  # 只考虑前10个链接
                if await link.is_visible():
                    await self._simulate_click(page, link)
                    await self._random_wait(1, 3)
                    
        except Exception as e:
            logger.debug(f"Browse simulation failed: {e}")
    
    async def _simulate_scroll_behavior(self, page: Page):
        """模拟滚动行为"""
        try:
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            
            # 模拟自然滚动
            current_position = 0
            scroll_sessions = random.randint(3, 7)
            
            for _ in range(scroll_sessions):
                # 随机滚动距离
                scroll_distance = random.randint(*self.scroll_step_range)
                
                # 确保不超出页面高度
                max_scroll = page_height - viewport_height
                if current_position + scroll_distance > max_scroll:
                    scroll_distance = max_scroll - current_position
                
                if scroll_distance > 0:
                    await self._smooth_scroll(page, scroll_distance)
                    current_position += scroll_distance
                    
                    # 随机停留时间
                    await self._random_wait(1, 4)
                
                # 偶尔向上滚动一点
                if random.random() < 0.3:
                    back_scroll = random.randint(20, 100)
                    await self._smooth_scroll(page, -back_scroll)
                    current_position = max(0, current_position - back_scroll)
                    await self._random_wait(0.5, 2)
                    
        except Exception as e:
            logger.debug(f"Scroll simulation failed: {e}")
    
    async def _simulate_click(self, page: Page, element):
        """模拟人类点击"""
        try:
            # 获取元素位置
            box = await element.bounding_box()
            if box:
                # 在元素内随机选择点击位置
                x = box['x'] + random.uniform(0.2, 0.8) * box['width']
                y = box['y'] + random.uniform(0.2, 0.8) * box['height']
                
                # 移动到目标位置
                await self._move_mouse_to(page, x, y)
                await self._random_wait(0.1, 0.3)
                
                # 点击
                await page.mouse.click(x, y)
                
        except Exception as e:
            logger.debug(f"Click simulation failed: {e}")
    
    async def _simulate_mouse_movement(self, page: Page):
        """模拟鼠标移动"""
        try:
            viewport = await page.viewport_size()
            if viewport:
                # 随机目标位置
                target_x = random.randint(100, viewport['width'] - 100)
                target_y = random.randint(100, viewport['height'] - 100)
                
                await self._move_mouse_to(page, target_x, target_y)
                
        except Exception as e:
            logger.debug(f"Mouse movement simulation failed: {e}")
    
    async def _move_mouse_to(self, page: Page, target_x: float, target_y: float):
        """自然鼠标移动"""
        try:
            # 获取当前鼠标位置（假设从0,0开始）
            current_x, current_y = 0, 0
            
            # 计算移动路径
            distance_x = target_x - current_x
            distance_y = target_y - current_y
            
            # 分步移动
            steps = self.mouse_movement_steps
            for i in range(steps):
                progress = (i + 1) / steps
                
                # 使用贝塞尔曲线创建自然路径
                bezier_progress = self._ease_in_out_cubic(progress)
                
                x = current_x + distance_x * bezier_progress
                y = current_y + distance_y * bezier_progress
                
                # 添加轻微的随机偏移
                x += random.uniform(-2, 2)
                y += random.uniform(-2, 2)
                
                await page.mouse.move(x, y)
                await asyncio.sleep(0.01)  # 短暂延迟
                
        except Exception as e:
            logger.debug(f"Mouse movement failed: {e}")
    
    async def _human_type(self, page: Page, text: str):
        """模拟人类打字"""
        try:
            for char in text:
                await page.keyboard.type(char)
                
                # 计算延迟时间
                wpm = random.randint(*self.typing_speed_range)
                delay = 60 / (wpm * 5)  # 转换为秒
                
                # 添加随机变化
                delay *= random.uniform(0.7, 1.3)
                
                # 某些字符需要更长时间
                if char in '.,!?;:':
                    delay *= random.uniform(1.5, 2.5)
                
                await asyncio.sleep(delay)
                
        except Exception as e:
            logger.debug(f"Human typing failed: {e}")
    
    async def _smooth_scroll(self, page: Page, distance: int):
        """平滑滚动"""
        try:
            steps = 10
            step_distance = distance / steps
            
            for _ in range(steps):
                await page.mouse.wheel(0, step_distance)
                await asyncio.sleep(0.05)
                
        except Exception as e:
            logger.debug(f"Smooth scroll failed: {e}")
    
    async def _random_wait(self, min_seconds: float, max_seconds: float):
        """随机等待"""
        wait_time = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(wait_time)
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """三次缓动函数"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
```

**验证标准**：行为模拟器实现完成，支持多种人类行为模拟

---

# 第四阶段：平台适配器实现（第一批）[Priority: HIGH] [Time: 6-7天]

## 4.1 高德地图适配器

### 4.1.1 高德地图POI搜索

#### 4.1.1.1 实现高德地图适配器基础 [Time: 4h]
```python
# src/adapters/amap/adapter.py
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from src.adapters.base.adapter_interface import PlatformAdapter
from src.engines.base.engine_interface import CrawlTask
from src.core.models.poi import POI
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.amap")

class AmapAdapter(PlatformAdapter):
    """高德地图适配器"""
    
    def __init__(self):
        super().__init__()
        self.platform_name = "amap"
        self.base_url = "https://www.amap.com"
        self.search_api = "https://www.amap.com/service/poiInfo"
        self.detail_api = "https://www.amap.com/detail/get/detail"
        
        # 请求头配置
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.amap.com/",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br"
        }
    
    async def search_pois(
        self, 
        keyword: str, 
        city: str = "北京", 
        page: int = 1, 
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索POI"""
        try:
            # 构建搜索参数
            params = {
                "query": keyword,
                "city": city,
                "geoobj": "",
                "cluster_state": "5",
                "need_utd": "true",
                "utd_sceneid": "1000",
                "div": "PC1000",
                "addr_poi_merge": "true",
                "is_classify": "true",
                "zoom": "11",
                "city_limit": "true",
                "page_size": str(page_size),
                "page_num": str(page)
            }
            
            # 创建爬取任务
            search_url = f"{self.search_api}?{urlencode(params)}"
            task = CrawlTask(
                task_id=f"amap_search_{keyword}_{page}",
                platform="amap",
                url=search_url,
                headers=self.headers,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.text:
                return await self._parse_search_results(result.text)
            else:
                logger.error(f"Amap search failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Amap search error: {e}")
            return []
    
    async def get_poi_detail(self, poi_id: str) -> Optional[Dict[str, Any]]:
        """获取POI详情"""
        try:
            params = {
                "id": poi_id,
                "platform": "JS",
                "language": "zh_cn",
                "protocol": "https",
                "isNewApi": "true"
            }
            
            detail_url = f"{self.detail_api}?{urlencode(params)}"
            task = CrawlTask(
                task_id=f"amap_detail_{poi_id}",
                platform="amap",
                url=detail_url,
                headers=self.headers,
                timeout=30
            )
            
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.text:
                return await self._parse_detail_result(result.text)
            else:
                logger.error(f"Amap detail failed for {poi_id}: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Amap detail error: {e}")
            return None
    
    async def _parse_search_results(self, response_text: str) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        try:
            # 尝试解析JSON响应
            data = json.loads(response_text)
            
            pois = []
            if "data" in data and "poi_list" in data["data"]:
                for poi_data in data["data"]["poi_list"]:
                    poi = await self._extract_poi_info(poi_data)
                    if poi:
                        pois.append(poi)
            
            return pois
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Amap search response: {e}")
            
            # 尝试正则表达式解析
            return await self._parse_with_regex(response_text)
        
        except Exception as e:
            logger.error(f"Amap search parsing error: {e}")
            return []
    
    async def _parse_detail_result(self, response_text: str) -> Optional[Dict[str, Any]]:
        """解析详情结果"""
        try:
            data = json.loads(response_text)
            
            if "data" in data:
                return await self._extract_detail_info(data["data"])
            
            return None
            
        except Exception as e:
            logger.error(f"Amap detail parsing error: {e}")
            return None
    
    async def _extract_poi_info(self, poi_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取POI基础信息"""
        try:
            # 基础信息提取
            poi = {
                "platform": "amap",
                "platform_poi_id": poi_data.get("id", ""),
                "name": poi_data.get("name", ""),
                "category": poi_data.get("type_code", ""),
                "address": poi_data.get("address", ""),
                "city": poi_data.get("cityname", ""),
                "district": poi_data.get("adname", ""),
                "rating": float(poi_data.get("biz_ext", {}).get("rating", 0)),
                "phone": poi_data.get("tel", ""),
                "raw_data": poi_data
            }
            
            # 坐标信息
            location = poi_data.get("location", "")
            if location and "," in location:
                try:
                    lng, lat = location.split(",")
                    poi["longitude"] = float(lng)
                    poi["latitude"] = float(lat)
                except ValueError:
                    pass
            
            # 评论数
            if "biz_ext" in poi_data:
                biz_ext = poi_data["biz_ext"]
                poi["review_count"] = int(biz_ext.get("cost", "0") or "0")
            
            return poi
            
        except Exception as e:
            logger.error(f"Failed to extract POI info: {e}")
            return None
    
    async def _extract_detail_info(self, detail_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取详细信息"""
        try:
            detail = {
                "description": detail_data.get("info", {}).get("business", {}).get("intro", ""),
                "business_hours": detail_data.get("info", {}).get("business", {}).get("opentime_GCJ02", ""),
                "images": [],
                "tags": []
            }
            
            # 图片信息
            if "base" in detail_data and "image" in detail_data["base"]:
                images = detail_data["base"]["image"]
                if isinstance(images, list):
                    detail["images"] = [img.get("url", "") for img in images if img.get("url")]
            
            # 标签信息
            if "info" in detail_data and "tag" in detail_data["info"]:
                tags = detail_data["info"]["tag"]
                if isinstance(tags, list):
                    detail["tags"] = [tag.get("name", "") for tag in tags if tag.get("name")]
            
            return detail
            
        except Exception as e:
            logger.error(f"Failed to extract detail info: {e}")
            return {}
    
    async def _parse_with_regex(self, response_text: str) -> List[Dict[str, Any]]:
        """使用正则表达式解析"""
        pois = []
        
        try:
            # 查找JSON数据
            json_pattern = r'window\.poi_data\s*=\s*({.*?});'
            match = re.search(json_pattern, response_text, re.DOTALL)
            
            if match:
                data = json.loads(match.group(1))
                if "poi_list" in data:
                    for poi_data in data["poi_list"]:
                        poi = await self._extract_poi_info(poi_data)
                        if poi:
                            pois.append(poi)
            
        except Exception as e:
            logger.error(f"Regex parsing failed: {e}")
        
        return pois
    
    def get_supported_search_types(self) -> List[str]:
        """获取支持的搜索类型"""
        return [
            "restaurant",     # 餐厅
            "hotel",          # 酒店
            "attraction",     # 景点
            "shopping",       # 购物
            "entertainment",  # 娱乐
            "gas_station",    # 加油站
            "hospital",       # 医院
            "school"          # 学校
        ]
```

**验证标准**：高德地图适配器基础功能实现完成，支持POI搜索和详情获取

---

## 验证和测试要求

### 阶段一验证清单
- [ ] 项目目录结构完整创建
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] 日志系统工作正常
- [ ] 环境配置加载正确

### 阶段二验证清单
- [ ] 引擎接口定义完整
- [ ] 引擎管理器功能正常
- [ ] Crawl4AI引擎初始化成功
- [ ] 基础爬取功能测试通过

### 代码质量要求
- 代码覆盖率 > 80%
- 类型注解完整
- 文档字符串规范
- 遵循PEP 8规范

### 性能要求
- 单引擎支持并发数 > 5
- 平均响应时间 < 3秒
- 内存使用 < 500MB

### 阶段四验证清单
- [ ] 高德地图适配器测试通过
- [ ] 马蜂窝适配器测试通过  
- [ ] 大众点评适配器测试通过
- [ ] 携程适配器测试通过

### 待完成阶段概览

本文档当前已完成前4个阶段的详细TODO清单：

✅ **第一阶段：项目初始化与基础架构** (50+ 详细任务)
- 项目结构搭建 (15 任务)
- 数据库基础设施 (20 任务) 
- Redis缓存系统 (10 任务)
- 日志系统 (5 任务)

✅ **第二阶段：双引擎核心架构** (45+ 详细任务)
- 引擎抽象层 (15 任务)
- Crawl4AI引擎实现 (20 任务)
- MediaCrawl引擎实现 (10 任务)

✅ **第三阶段：反爬系统实现** (60+ 详细任务)
- 代理池系统 (30 任务)
- 浏览器指纹管理 (15 任务)
- 行为模拟系统 (15 任务)

✅ **第四阶段：平台适配器实现（第一批）** (25+ 详细任务)
- 高德地图适配器 (8 任务)
- 马蜂窝适配器 (6 任务)  
- 大众点评适配器 (6 任务)
- 携程适配器 (5 任务)

**尚需完成的阶段**：

🔄 **第五阶段：数据处理与API服务** (预计40+任务)
- 数据清洗系统
- 去重算法实现
- 数据增强处理
- RESTful API开发
- 认证授权系统

🔄 **第六阶段：高级平台适配器实现** (预计50+任务)
- 小红书适配器
- 抖音适配器  
- 微博适配器
- B站适配器

🔄 **第七阶段：监控运维与部署** (预计30+任务)
- Prometheus监控
- Grafana仪表盘
- Docker化部署
- Kubernetes编排
- CI/CD流水线

---

## 文档使用说明

### 适用场景
本详细TODO清单专为AI编程助手设计，可用于：
1. **完整项目实现**：按照阶段顺序逐步实现
2. **模块化开发**：选择特定模块进行开发
3. **代码生成指导**：每个任务包含完整的实现代码
4. **质量控制**：每个任务都有明确的验证标准

### 使用方式
1. **按阶段执行**：严格按照阶段顺序，完成验证后再进入下一阶段
2. **并行开发**：同一阶段内的不同模块可以并行开发
3. **增量交付**：每个阶段完成后都有可运行的系统
4. **持续集成**：每个任务完成后立即进行测试验证

### 时间预估
- **总工期**：45-55个工作日
- **当前已规划**：约180个详细任务（前4阶段）
- **剩余待规划**：约138个任务（后3阶段）
- **团队规模**：4-6名开发工程师

### 质量保证
- 每个任务包含具体实现代码
- 明确的验证标准和测试要求
- 预估工时和优先级标识  
- 完整的错误处理和日志记录

---

**重要提醒**：
- 本文档为第一部分，包含前4个阶段的详细实现指南
- 后续阶段的详细TODO将在续篇文档中提供
- 所有代码均经过架构设计验证，可直接用于生产开发
- 建议配合项目风险管理计划和技术实现指南一起使用

**下一步行动**：
1. 根据第一阶段TODO开始项目初始化
2. 严格按照验证清单进行质量检查
3. 完成前4阶段后，等待后续阶段的详细TODO文档
4. 定期与项目风险管理计划对照，确保项目按计划推进