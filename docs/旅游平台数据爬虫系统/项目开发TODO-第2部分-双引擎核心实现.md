# 旅游平台数据爬虫系统 - 项目开发TODO详细指南
## 第2部分：双引擎核心实现

> 本部分实现Crawl4AI和MediaCrawl双引擎的核心功能，建立统一的引擎抽象层

---

## Phase 2: 双引擎核心功能实现（Day 2-4）

### Task 2.1: 创建引擎抽象基类

#### 2.1.1 定义引擎接口
```python
# src/core/engines/base/engine_interface.py
"""爬虫引擎抽象接口定义"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from src.utils.logger.logger import get_logger

logger = get_logger("engine.interface")

# 引擎类型枚举
class EngineType(str, Enum):
    CRAWL4AI = "crawl4ai"
    MEDIACRAWL = "mediacrawl"
    AUTO = "auto"  # 自动选择

# 引擎状态枚举
class EngineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    MAINTENANCE = "maintenance"

# 爬取任务模型
class CrawlTask(BaseModel):
    """爬取任务定义"""
    task_id: str = Field(..., description="任务唯一ID")
    platform: str = Field(..., description="目标平台")
    url: str = Field(..., description="目标URL")
    task_type: str = Field(default="fetch", description="任务类型: fetch/search/detail")
    method: str = Field(default="GET", description="HTTP方法")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    params: Dict[str, Any] = Field(default_factory=dict, description="请求参数")
    data: Optional[Union[str, Dict[str, Any]]] = Field(None, description="请求体数据")
    cookies: Dict[str, str] = Field(default_factory=dict, description="Cookies")
    
    # 引擎特定配置
    engine_type: EngineType = Field(default=EngineType.AUTO, description="指定引擎类型")
    engine_config: Dict[str, Any] = Field(default_factory=dict, description="引擎特定配置")
    
    # 爬取配置
    timeout: int = Field(default=30, description="超时时间(秒)")
    retry_times: int = Field(default=3, description="重试次数")
    retry_delay: int = Field(default=5, description="重试延迟(秒)")
    
    # 解析配置
    wait_selector: Optional[str] = Field(None, description="等待元素选择器")
    wait_timeout: int = Field(default=10, description="等待超时(秒)")
    extraction_rules: Dict[str, Any] = Field(default_factory=dict, description="数据提取规则")
    
    # 反爬配置
    use_proxy: bool = Field(default=True, description="是否使用代理")
    use_fingerprint: bool = Field(default=True, description="是否使用浏览器指纹")
    use_behavior_simulation: bool = Field(default=False, description="是否模拟人类行为")
    
    # 元数据
    priority: int = Field(default=0, description="任务优先级(0-10)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

# 爬取结果模型
class CrawlResult(BaseModel):
    """爬取结果定义"""
    task_id: str = Field(..., description="任务ID")
    success: bool = Field(..., description="是否成功")
    status_code: Optional[int] = Field(None, description="HTTP状态码")
    
    # 响应数据
    url: str = Field(..., description="最终URL(可能有重定向)")
    html: Optional[str] = Field(None, description="原始HTML")
    text: Optional[str] = Field(None, description="提取的文本")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON响应")
    
    # 提取的数据
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="提取的结构化数据")
    
    # 元数据
    response_headers: Dict[str, str] = Field(default_factory=dict, description="响应头")
    cookies: Dict[str, str] = Field(default_factory=dict, description="响应Cookies")
    
    # 性能指标
    elapsed_time: float = Field(..., description="执行时间(秒)")
    retry_count: int = Field(default=0, description="重试次数")
    
    # 错误信息
    error_type: Optional[str] = Field(None, description="错误类型")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_traceback: Optional[str] = Field(None, description="错误堆栈")
    
    # 引擎信息
    engine_type: EngineType = Field(..., description="使用的引擎类型")
    engine_version: str = Field(..., description="引擎版本")
    
    # 代理信息
    proxy_used: Optional[str] = Field(None, description="使用的代理")
    fingerprint_used: Optional[str] = Field(None, description="使用的指纹ID")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# 引擎能力定义
class EngineCapability(BaseModel):
    """引擎能力描述"""
    name: str = Field(..., description="能力名称")
    description: str = Field(..., description="能力描述")
    supported: bool = Field(..., description="是否支持")
    config_options: Dict[str, Any] = Field(default_factory=dict, description="配置选项")

# 抽象引擎基类
class CrawlingEngine(ABC):
    """爬虫引擎抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine_type: EngineType = EngineType.AUTO
        self.engine_version: str = "1.0.0"
        self._status: EngineStatus = EngineStatus.IDLE
        self.logger = logger.bind(engine=self.__class__.__name__)
    
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
    async def health_check(self) -> EngineStatus:
        """健康检查"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[EngineCapability]:
        """获取引擎能力列表"""
        pass
    
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        pass
    
    # 通用方法
    async def validate_task(self, task: CrawlTask) -> bool:
        """验证任务参数"""
        try:
            # 基础验证
            if not task.url:
                raise ValueError("URL is required")
            
            if not task.url.startswith(("http://", "https://")):
                raise ValueError("Invalid URL scheme")
            
            if task.timeout <= 0:
                raise ValueError("Timeout must be positive")
            
            if task.retry_times < 0:
                raise ValueError("Retry times must be non-negative")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Task validation failed: {e}")
            return False
    
    def get_status(self) -> EngineStatus:
        """获取引擎状态"""
        return self._status
    
    def set_status(self, status: EngineStatus) -> None:
        """设置引擎状态"""
        self._status = status
        self.logger.info(f"Engine status changed to: {status}")
```

#### 2.1.2 创建引擎管理器
```python
# src/core/engines/base/engine_manager.py
"""引擎管理器"""
from typing import Dict, List, Optional, Type
import asyncio
from contextlib import asynccontextmanager
from src.core.engines.base.engine_interface import (
    CrawlingEngine, EngineType, EngineStatus, CrawlTask, CrawlResult
)
from src.utils.logger.logger import get_logger

logger = get_logger("engine.manager")

class EngineManager:
    """引擎管理器 - 负责引擎的注册、选择和调度"""
    
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
            logger.info("All engines initialized successfully")
    
    async def shutdown(self):
        """关闭所有引擎"""
        async with self._lock:
            for engine_type, engine in self._engines.items():
                try:
                    await engine.shutdown()
                    logger.info(f"Shut down engine: {engine_type}")
                except Exception as e:
                    logger.error(f"Error shutting down engine {engine_type}: {e}")
            
            self._engines.clear()
            self._initialized = False
    
    async def get_engine(self, engine_type: EngineType) -> Optional[CrawlingEngine]:
        """获取指定引擎"""
        return self._engines.get(engine_type)
    
    async def select_engine(self, task: CrawlTask) -> CrawlingEngine:
        """根据任务选择合适的引擎"""
        # 如果任务指定了引擎类型
        if task.engine_type != EngineType.AUTO:
            engine = self._engines.get(task.engine_type)
            if engine and await engine.health_check() == EngineStatus.IDLE:
                return engine
        
        # 自动选择逻辑
        # 基于平台特征选择
        platform_engine_map = {
            "amap": EngineType.CRAWL4AI,      # 高德地图 - 结构化数据
            "mafengwo": EngineType.CRAWL4AI,  # 马蜂窝 - 结构化数据
            "dianping": EngineType.CRAWL4AI,  # 大众点评 - 结构化数据
            "ctrip": EngineType.CRAWL4AI,     # 携程 - 结构化数据
            "xiaohongshu": EngineType.MEDIACRAWL,  # 小红书 - 动态内容
            "douyin": EngineType.MEDIACRAWL,       # 抖音 - 动态内容
            "weibo": EngineType.MEDIACRAWL,        # 微博 - 动态内容
            "bilibili": EngineType.MEDIACRAWL      # B站 - 动态内容
        }
        
        preferred_engine_type = platform_engine_map.get(task.platform, EngineType.CRAWL4AI)
        engine = self._engines.get(preferred_engine_type)
        
        if engine and await engine.health_check() == EngineStatus.IDLE:
            return engine
        
        # 回退策略：选择任何可用的引擎
        for engine in self._engines.values():
            if await engine.health_check() == EngineStatus.IDLE:
                return engine
        
        raise RuntimeError("No available engine found")
    
    async def execute_task(self, task: CrawlTask) -> CrawlResult:
        """执行单个任务"""
        engine = await self.select_engine(task)
        logger.info(f"Selected engine {engine.engine_type} for task {task.task_id}")
        
        # 执行任务
        result = await engine.crawl(task)
        return result
    
    async def execute_batch(self, tasks: List[CrawlTask]) -> List[CrawlResult]:
        """批量执行任务"""
        # 按引擎类型分组
        engine_tasks: Dict[EngineType, List[CrawlTask]] = {}
        
        for task in tasks:
            engine = await self.select_engine(task)
            engine_type = engine.engine_type
            
            if engine_type not in engine_tasks:
                engine_tasks[engine_type] = []
            engine_tasks[engine_type].append(task)
        
        # 并发执行各引擎的批量任务
        results = []
        tasks_list = []
        
        for engine_type, engine_task_list in engine_tasks.items():
            engine = self._engines[engine_type]
            tasks_list.append(engine.batch_crawl(engine_task_list))
        
        # 等待所有批量任务完成
        batch_results = await asyncio.gather(*tasks_list)
        
        # 展平结果
        for batch_result in batch_results:
            results.extend(batch_result)
        
        return results
    
    async def get_engine_status(self) -> Dict[EngineType, EngineStatus]:
        """获取所有引擎状态"""
        status = {}
        for engine_type, engine in self._engines.items():
            status[engine_type] = await engine.health_check()
        return status
    
    async def get_engine_metrics(self) -> Dict[EngineType, Dict]:
        """获取所有引擎指标"""
        metrics = {}
        for engine_type, engine in self._engines.items():
            metrics[engine_type] = await engine.get_metrics()
        return metrics

# 全局引擎管理器实例
engine_manager = EngineManager()

# 引擎管理器上下文
@asynccontextmanager
async def engine_context(configs: Dict[EngineType, Dict]):
    """引擎管理器上下文"""
    await engine_manager.initialize(configs)
    try:
        yield engine_manager
    finally:
        await engine_manager.shutdown()
```

### Task 2.2: 实现Crawl4AI引擎

#### 2.2.1 Crawl4AI引擎实现
```python
# src/engines/crawl4ai/engine.py
"""Crawl4AI引擎实现"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy

from src.core.engines.base.engine_interface import (
    CrawlingEngine, EngineType, EngineStatus, 
    CrawlTask, CrawlResult, EngineCapability
)
from src.anti_detection.proxy.manager import proxy_manager
from src.anti_detection.fingerprint.manager import fingerprint_manager
from src.utils.logger.logger import get_logger

logger = get_logger("engine.crawl4ai")

class Crawl4AIEngine(CrawlingEngine):
    """Crawl4AI引擎 - 专注于结构化数据抓取"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.engine_type = EngineType.CRAWL4AI
        self.engine_version = "0.2.0"
        
        # 配置参数
        self.max_workers = config.get("workers", 5)
        self.default_timeout = config.get("timeout", 30)
        self.retry_times = config.get("retry_times", 3)
        
        # 爬虫池
        self._crawler_pool: List[AsyncWebCrawler] = []
        self._available_crawlers = asyncio.Queue(maxsize=self.max_workers)
        
        # 性能指标
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time": 0.0,
            "average_time": 0.0
        }
    
    async def initialize(self) -> None:
        """初始化引擎"""
        try:
            # 创建爬虫实例池
            for i in range(self.max_workers):
                crawler = AsyncWebCrawler(
                    browser_type="chromium",
                    headless=True,
                    verbose=False
                )
                self._crawler_pool.append(crawler)
                await self._available_crawlers.put(crawler)
            
            self.set_status(EngineStatus.IDLE)
            logger.info(f"Crawl4AI engine initialized with {self.max_workers} workers")
            
        except Exception as e:
            self.set_status(EngineStatus.ERROR)
            logger.error(f"Failed to initialize Crawl4AI engine: {e}")
            raise
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        try:
            # 清理爬虫池
            for crawler in self._crawler_pool:
                try:
                    # Crawl4AI的清理逻辑
                    pass
                except Exception as e:
                    logger.warning(f"Error closing crawler: {e}")
            
            self._crawler_pool.clear()
            self.set_status(EngineStatus.IDLE)
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
            engine_version=self.engine_version,
            elapsed_time=0.0
        )
        
        # 获取可用的爬虫实例
        crawler = await self._available_crawlers.get()
        
        try:
            self.set_status(EngineStatus.RUNNING)
            
            # 验证任务
            if not await self.validate_task(task):
                raise ValueError("Invalid task parameters")
            
            # 准备爬取配置
            crawl_config = await self._prepare_crawl_config(task)
            
            # 执行爬取
            retry_count = 0
            last_error = None
            
            while retry_count <= task.retry_times:
                try:
                    # 调用Crawl4AI
                    crawl_result = await crawler.arun(
                        url=task.url,
                        **crawl_config
                    )
                    
                    # 处理结果
                    result.success = crawl_result.success
                    result.status_code = crawl_result.status_code
                    result.html = crawl_result.html
                    result.text = crawl_result.text
                    
                    # 提取数据
                    if task.extraction_rules:
                        result.extracted_data = await self._extract_data(
                            crawl_result, task.extraction_rules
                        )
                    
                    # 成功则退出重试循环
                    if result.success:
                        break
                        
                except Exception as e:
                    last_error = e
                    logger.warning(f"Crawl attempt {retry_count + 1} failed: {e}")
                    
                retry_count += 1
                if retry_count <= task.retry_times:
                    await asyncio.sleep(task.retry_delay)
            
            result.retry_count = retry_count - 1
            
            # 记录错误信息
            if not result.success and last_error:
                result.error_type = type(last_error).__name__
                result.error_message = str(last_error)
            
            # 更新指标
            self._update_metrics(result, time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Crawl task {task.task_id} failed: {e}")
            result.error_type = type(e).__name__
            result.error_message = str(e)
            
        finally:
            # 归还爬虫实例
            await self._available_crawlers.put(crawler)
            self.set_status(EngineStatus.IDLE)
            
            result.elapsed_time = time.time() - start_time
        
        return result
    
    async def batch_crawl(self, tasks: List[CrawlTask]) -> List[CrawlResult]:
        """批量爬取"""
        # 并发执行任务
        tasks_coroutines = [self.crawl(task) for task in tasks]
        results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 创建错误结果
                error_result = CrawlResult(
                    task_id=tasks[i].task_id,
                    success=False,
                    url=tasks[i].url,
                    engine_type=self.engine_type,
                    engine_version=self.engine_version,
                    error_type=type(result).__name__,
                    error_message=str(result),
                    elapsed_time=0.0
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def health_check(self) -> EngineStatus:
        """健康检查"""
        try:
            # 检查爬虫池
            if not self._crawler_pool:
                return EngineStatus.ERROR
            
            # 检查可用爬虫数量
            available_count = self._available_crawlers.qsize()
            if available_count == 0 and self.get_status() == EngineStatus.IDLE:
                return EngineStatus.ERROR
            
            return self.get_status()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return EngineStatus.ERROR
    
    async def get_capabilities(self) -> List[EngineCapability]:
        """获取引擎能力"""
        return [
            EngineCapability(
                name="structured_extraction",
                description="Extract structured data from HTML",
                supported=True,
                config_options={
                    "css_selector": "CSS selector based extraction",
                    "json_css": "JSON + CSS combined extraction",
                    "llm_extraction": "LLM based extraction"
                }
            ),
            EngineCapability(
                name="javascript_rendering",
                description="Render JavaScript generated content",
                supported=True,
                config_options={
                    "wait_for": "Wait for specific elements",
                    "execute_js": "Execute custom JavaScript"
                }
            ),
            EngineCapability(
                name="proxy_support",
                description="HTTP/HTTPS/SOCKS proxy support",
                supported=True,
                config_options={}
            ),
            EngineCapability(
                name="custom_headers",
                description="Custom HTTP headers",
                supported=True,
                config_options={}
            ),
            EngineCapability(
                name="concurrent_crawling",
                description="Concurrent request handling",
                supported=True,
                config_options={
                    "max_workers": f"1-{self.max_workers}"
                }
            )
        ]
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self._metrics,
            "available_workers": self._available_crawlers.qsize(),
            "total_workers": self.max_workers,
            "engine_status": self.get_status().value
        }
    
    async def _prepare_crawl_config(self, task: CrawlTask) -> Dict[str, Any]:
        """准备爬取配置"""
        config = {
            "word_count_threshold": 10,
            "exclude_external_images": True,
            "remove_overlay_elements": True,
            "process_iframes": True
        }
        
        # 添加代理
        if task.use_proxy:
            proxy = await proxy_manager.get_proxy(task.platform)
            if proxy:
                config["proxy"] = proxy.to_dict()
                task.metadata["proxy_used"] = proxy.proxy_url
        
        # 添加自定义headers
        if task.headers:
            config["headers"] = task.headers
        
        # 添加等待选择器
        if task.wait_selector:
            config["wait_for"] = task.wait_selector
        
        # 添加提取策略
        if task.extraction_rules:
            if "css_rules" in task.extraction_rules:
                config["extraction_strategy"] = JsonCssExtractionStrategy(
                    schema=task.extraction_rules["css_rules"]
                )
            elif "llm_prompt" in task.extraction_rules:
                config["extraction_strategy"] = LLMExtractionStrategy(
                    provider="openai",
                    api_token=self.config.get("openai_api_key"),
                    instruction=task.extraction_rules["llm_prompt"]
                )
        
        # 合并引擎特定配置
        config.update(task.engine_config)
        
        return config
    
    async def _extract_data(self, crawl_result: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """提取数据"""
        extracted = {}
        
        try:
            # 如果有extraction_strategy返回的数据
            if hasattr(crawl_result, 'extracted_content'):
                extracted = crawl_result.extracted_content
            
            # 额外的自定义提取逻辑
            if "custom_extractors" in rules:
                # TODO: 实现自定义提取器
                pass
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
        
        return extracted
    
    def _update_metrics(self, result: CrawlResult, elapsed_time: float):
        """更新性能指标"""
        self._metrics["total_requests"] += 1
        
        if result.success:
            self._metrics["successful_requests"] += 1
        else:
            self._metrics["failed_requests"] += 1
        
        self._metrics["total_time"] += elapsed_time
        self._metrics["average_time"] = (
            self._metrics["total_time"] / self._metrics["total_requests"]
        )
```

#### 2.2.2 创建Crawl4AI配置
```python
# src/engines/crawl4ai/config.py
"""Crawl4AI引擎配置"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Crawl4AIConfig(BaseModel):
    """Crawl4AI配置模型"""
    # 基础配置
    workers: int = Field(default=5, ge=1, le=20, description="工作线程数")
    timeout: int = Field(default=30, ge=5, le=300, description="默认超时时间(秒)")
    retry_times: int = Field(default=3, ge=0, le=10, description="默认重试次数")
    
    # 浏览器配置
    browser_type: str = Field(default="chromium", description="浏览器类型")
    headless: bool = Field(default=True, description="是否无头模式")
    
    # 内容处理配置
    word_count_threshold: int = Field(default=10, description="最小字数阈值")
    exclude_external_images: bool = Field(default=True, description="排除外部图片")
    remove_overlay_elements: bool = Field(default=True, description="移除覆盖元素")
    process_iframes: bool = Field(default=True, description="处理iframe")
    
    # 性能配置
    cache_enabled: bool = Field(default=True, description="启用缓存")
    cache_ttl: int = Field(default=3600, description="缓存过期时间(秒)")
    
    # API配置(用于LLM提取)
    openai_api_key: Optional[str] = Field(None, description="OpenAI API密钥")
    
    @classmethod
    def from_env(cls) -> "Crawl4AIConfig":
        """从环境变量创建配置"""
        from src.core.config.settings import settings
        
        return cls(
            workers=settings.CRAWL4AI_WORKERS,
            timeout=settings.CRAWL4AI_TIMEOUT,
            retry_times=settings.CRAWL4AI_RETRY_TIMES
        )
```

### Task 2.3: 实现MediaCrawl引擎

#### 2.3.1 MediaCrawl引擎实现
```python
# src/engines/mediacrawl/engine.py
"""MediaCrawl引擎实现 - 基于Playwright的动态内容爬虫"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from src.core.engines.base.engine_interface import (
    CrawlingEngine, EngineType, EngineStatus,
    CrawlTask, CrawlResult, EngineCapability
)
from src.anti_detection.proxy.manager import proxy_manager
from src.anti_detection.fingerprint.manager import fingerprint_manager
from src.anti_detection.behavior.simulator import BehaviorSimulator
from src.utils.logger.logger import get_logger

logger = get_logger("engine.mediacrawl")

class MediaCrawlEngine(CrawlingEngine):
    """MediaCrawl引擎 - 专注于动态内容和社交媒体抓取"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.engine_type = EngineType.MEDIACRAWL
        self.engine_version = "1.0.0"
        
        # 配置参数
        self.max_browsers = config.get("browser_count", 3)
        self.max_contexts_per_browser = config.get("contexts_per_browser", 5)
        self.headless = config.get("headless", True)
        self.default_timeout = config.get("timeout", 30) * 1000  # 转换为毫秒
        
        # 浏览器池
        self._playwright = None
        self._browsers: List[Browser] = []
        self._context_pool = asyncio.Queue()
        
        # 行为模拟器
        self._behavior_simulator = BehaviorSimulator()
        
        # 性能指标
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time": 0.0,
            "average_time": 0.0,
            "browser_crashes": 0
        }
    
    async def initialize(self) -> None:
        """初始化引擎"""
        try:
            # 启动Playwright
            self._playwright = await async_playwright().start()
            
            # 创建浏览器实例
            for i in range(self.max_browsers):
                browser = await self._create_browser()
                self._browsers.append(browser)
                
                # 为每个浏览器创建多个上下文
                for j in range(self.max_contexts_per_browser):
                    context = await self._create_context(browser)
                    await self._context_pool.put((browser, context))
            
            self.set_status(EngineStatus.IDLE)
            logger.info(
                f"MediaCrawl engine initialized with {self.max_browsers} browsers, "
                f"{self.max_contexts_per_browser} contexts each"
            )
            
        except Exception as e:
            self.set_status(EngineStatus.ERROR)
            logger.error(f"Failed to initialize MediaCrawl engine: {e}")
            raise
    
    async def shutdown(self) -> None:
        """关闭引擎"""
        try:
            # 关闭所有浏览器
            for browser in self._browsers:
                try:
                    await browser.close()
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
            
            # 停止Playwright
            if self._playwright:
                await self._playwright.stop()
            
            self._browsers.clear()
            self.set_status(EngineStatus.IDLE)
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
            engine_version=self.engine_version,
            elapsed_time=0.0
        )
        
        # 获取可用的浏览器上下文
        browser, context = await self._context_pool.get()
        page = None
        
        try:
            self.set_status(EngineStatus.RUNNING)
            
            # 验证任务
            if not await self.validate_task(task):
                raise ValueError("Invalid task parameters")
            
            # 创建新页面
            page = await context.new_page()
            
            # 配置页面
            await self._configure_page(page, task)
            
            # 执行爬取
            retry_count = 0
            last_error = None
            
            while retry_count <= task.retry_times:
                try:
                    # 导航到目标URL
                    response = await page.goto(
                        task.url,
                        wait_until="networkidle",
                        timeout=task.timeout * 1000
                    )
                    
                    # 记录响应信息
                    if response:
                        result.status_code = response.status
                        result.response_headers = dict(response.headers)
                    
                    # 等待特定元素
                    if task.wait_selector:
                        await page.wait_for_selector(
                            task.wait_selector,
                            timeout=task.wait_timeout * 1000
                        )
                    
                    # 模拟人类行为
                    if task.use_behavior_simulation:
                        await self._behavior_simulator.simulate_human_behavior(page)
                    
                    # 获取页面内容
                    result.html = await page.content()
                    result.text = await page.evaluate("() => document.body.innerText")
                    result.url = page.url  # 可能有重定向
                    
                    # 提取数据
                    if task.extraction_rules:
                        result.extracted_data = await self._extract_data(page, task.extraction_rules)
                    
                    # 获取cookies
                    cookies = await context.cookies()
                    result.cookies = {c["name"]: c["value"] for c in cookies}
                    
                    result.success = True
                    break
                    
                except PlaywrightTimeout as e:
                    last_error = e
                    logger.warning(f"Page timeout for task {task.task_id}: {e}")
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"Crawl attempt {retry_count + 1} failed: {e}")
                
                retry_count += 1
                if retry_count <= task.retry_times:
                    await asyncio.sleep(task.retry_delay)
            
            result.retry_count = retry_count - 1
            
            # 记录错误信息
            if not result.success and last_error:
                result.error_type = type(last_error).__name__
                result.error_message = str(last_error)
                
                # 截图用于调试
                try:
                    screenshot = await page.screenshot()
                    result.metadata["error_screenshot"] = screenshot.hex()
                except:
                    pass
            
            # 更新指标
            self._update_metrics(result, time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Crawl task {task.task_id} failed: {e}")
            result.error_type = type(e).__name__
            result.error_message = str(e)
            
        finally:
            # 清理页面
            if page:
                try:
                    await page.close()
                except:
                    pass
            
            # 归还上下文
            await self._context_pool.put((browser, context))
            self.set_status(EngineStatus.IDLE)
            
            result.elapsed_time = time.time() - start_time
        
        return result
    
    async def batch_crawl(self, tasks: List[CrawlTask]) -> List[CrawlResult]:
        """批量爬取"""
        # 限制并发数
        semaphore = asyncio.Semaphore(self._context_pool.qsize())
        
        async def crawl_with_semaphore(task: CrawlTask) -> CrawlResult:
            async with semaphore:
                return await self.crawl(task)
        
        # 并发执行
        results = await asyncio.gather(
            *[crawl_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = CrawlResult(
                    task_id=tasks[i].task_id,
                    success=False,
                    url=tasks[i].url,
                    engine_type=self.engine_type,
                    engine_version=self.engine_version,
                    error_type=type(result).__name__,
                    error_message=str(result),
                    elapsed_time=0.0
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def health_check(self) -> EngineStatus:
        """健康检查"""
        try:
            # 检查浏览器状态
            for browser in self._browsers:
                if not browser.is_connected():
                    return EngineStatus.ERROR
            
            # 检查上下文池
            if self._context_pool.empty() and self.get_status() == EngineStatus.IDLE:
                return EngineStatus.ERROR
            
            return self.get_status()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return EngineStatus.ERROR
    
    async def get_capabilities(self) -> List[EngineCapability]:
        """获取引擎能力"""
        return [
            EngineCapability(
                name="dynamic_content",
                description="Handle JavaScript rendered content",
                supported=True,
                config_options={
                    "wait_until": ["load", "domcontentloaded", "networkidle"],
                    "wait_for_selector": "CSS selector to wait for"
                }
            ),
            EngineCapability(
                name="browser_automation",
                description="Full browser automation capabilities",
                supported=True,
                config_options={
                    "click": "Click elements",
                    "type": "Type text",
                    "scroll": "Scroll page",
                    "screenshot": "Take screenshots"
                }
            ),
            EngineCapability(
                name="behavior_simulation",
                description="Simulate human behavior patterns",
                supported=True,
                config_options={
                    "mouse_movement": "Natural mouse movements",
                    "typing_delays": "Human-like typing",
                    "random_actions": "Random browsing patterns"
                }
            ),
            EngineCapability(
                name="fingerprint_rotation",
                description="Browser fingerprint management",
                supported=True,
                config_options={
                    "user_agent": "Custom user agents",
                    "screen_resolution": "Various resolutions",
                    "timezone": "Different timezones"
                }
            ),
            EngineCapability(
                name="media_download",
                description="Download images and videos",
                supported=True,
                config_options={}
            )
        ]
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self._metrics,
            "available_contexts": self._context_pool.qsize(),
            "total_contexts": self.max_browsers * self.max_contexts_per_browser,
            "browser_count": len(self._browsers),
            "engine_status": self.get_status().value
        }
    
    async def _create_browser(self) -> Browser:
        """创建浏览器实例"""
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-features=IsolateOrigins,site-per-process"
        ]
        
        browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )
        
        return browser
    
    async def _create_context(self, browser: Browser) -> BrowserContext:
        """创建浏览器上下文"""
        # 获取浏览器指纹
        fingerprint = await fingerprint_manager.get_fingerprint()
        
        context_options = {
            "user_agent": fingerprint.user_agent,
            "viewport": {
                "width": fingerprint.screen_width,
                "height": fingerprint.screen_height
            },
            "locale": fingerprint.language,
            "timezone_id": fingerprint.timezone,
            "device_scale_factor": fingerprint.device_scale_factor,
            "is_mobile": fingerprint.is_mobile,
            "has_touch": fingerprint.has_touch
        }
        
        # 添加额外的权限
        context_options["permissions"] = ["geolocation", "notifications"]
        
        # 创建上下文
        context = await browser.new_context(**context_options)
        
        # 注入反检测脚本
        await context.add_init_script("""
            // 覆盖 navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 覆盖 navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // 覆盖 navigator.languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            
            // 修改 chrome 对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        """)
        
        return context
    
    async def _configure_page(self, page: Page, task: CrawlTask):
        """配置页面"""
        # 设置超时
        page.set_default_timeout(self.default_timeout)
        
        # 设置额外的headers
        if task.headers:
            await page.set_extra_http_headers(task.headers)
        
        # 设置代理认证（如果需要）
        if task.use_proxy:
            proxy = await proxy_manager.get_proxy(task.platform)
            if proxy and proxy.username and proxy.password:
                await page.context.route("**/*", lambda route: route.continue_(
                    headers={
                        **route.request.headers,
                        "Proxy-Authorization": f"Basic {proxy.get_auth_string()}"
                    }
                ))
        
        # 拦截和修改请求
        async def handle_route(route):
            # 可以在这里修改请求
            await route.continue_()
        
        # 可选：拦截特定请求
        if task.engine_config.get("intercept_requests"):
            await page.route("**/*", handle_route)
    
    async def _extract_data(self, page: Page, rules: Dict[str, Any]) -> Dict[str, Any]:
        """从页面提取数据"""
        extracted = {}
        
        try:
            # CSS选择器提取
            if "css_selectors" in rules:
                for key, selector in rules["css_selectors"].items():
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            if len(elements) == 1:
                                extracted[key] = await elements[0].text_content()
                            else:
                                extracted[key] = [
                                    await el.text_content() for el in elements
                                ]
                    except Exception as e:
                        logger.warning(f"Failed to extract {key}: {e}")
            
            # JavaScript提取
            if "js_extractors" in rules:
                for key, js_code in rules["js_extractors"].items():
                    try:
                        extracted[key] = await page.evaluate(js_code)
                    except Exception as e:
                        logger.warning(f"Failed to execute JS for {key}: {e}")
            
            # 属性提取
            if "attribute_extractors" in rules:
                for key, config in rules["attribute_extractors"].items():
                    selector = config["selector"]
                    attribute = config["attribute"]
                    try:
                        elements = await page.query_selector_all(selector)
                        values = []
                        for el in elements:
                            value = await el.get_attribute(attribute)
                            if value:
                                values.append(value)
                        extracted[key] = values if len(values) > 1 else (values[0] if values else None)
                    except Exception as e:
                        logger.warning(f"Failed to extract attribute {key}: {e}")
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
        
        return extracted
    
    def _update_metrics(self, result: CrawlResult, elapsed_time: float):
        """更新性能指标"""
        self._metrics["total_requests"] += 1
        
        if result.success:
            self._metrics["successful_requests"] += 1
        else:
            self._metrics["failed_requests"] += 1
            
            # 检查是否是浏览器崩溃
            if "browser" in str(result.error_message).lower():
                self._metrics["browser_crashes"] += 1
        
        self._metrics["total_time"] += elapsed_time
        self._metrics["average_time"] = (
            self._metrics["total_time"] / self._metrics["total_requests"]
        )
```

#### 2.3.2 行为模拟器实现
```python
# src/anti_detection/behavior/simulator.py
"""人类行为模拟器"""
import asyncio
import random
import math
from typing import Optional, Tuple
from playwright.async_api import Page
from src.utils.logger.logger import get_logger

logger = get_logger("behavior.simulator")

class BehaviorSimulator:
    """模拟人类浏览行为"""
    
    def __init__(self):
        self.min_mouse_speed = 100  # 像素/秒
        self.max_mouse_speed = 500
        self.min_scroll_delay = 0.5  # 秒
        self.max_scroll_delay = 2.0
        self.min_type_delay = 0.05  # 秒
        self.max_type_delay = 0.3
    
    async def simulate_human_behavior(self, page: Page):
        """执行一系列人类行为"""
        try:
            # 随机选择行为组合
            behaviors = [
                self.random_mouse_movement,
                self.random_scrolling,
                self.random_hover,
                self.check_page_elements
            ]
            
            # 执行2-4个随机行为
            num_behaviors = random.randint(2, 4)
            selected_behaviors = random.sample(behaviors, num_behaviors)
            
            for behavior in selected_behaviors:
                await behavior(page)
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            logger.warning(f"Behavior simulation error: {e}")
    
    async def random_mouse_movement(self, page: Page):
        """随机鼠标移动"""
        viewport = page.viewport_size
        if not viewport:
            return
        
        # 生成随机路径点
        num_points = random.randint(3, 7)
        points = []
        
        for _ in range(num_points):
            x = random.randint(100, viewport["width"] - 100)
            y = random.randint(100, viewport["height"] - 100)
            points.append((x, y))
        
        # 沿路径移动鼠标
        for i in range(len(points) - 1):
            await self._smooth_mouse_move(
                page,
                points[i],
                points[i + 1]
            )
    
    async def random_scrolling(self, page: Page):
        """随机页面滚动"""
        # 获取页面高度
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = page.viewport_size["height"]
        
        if page_height <= viewport_height:
            return
        
        # 随机滚动3-5次
        num_scrolls = random.randint(3, 5)
        
        for _ in range(num_scrolls):
            # 随机滚动距离
            scroll_distance = random.randint(100, 500)
            
            # 随机方向
            if random.random() > 0.3:  # 70%概率向下滚动
                scroll_distance = abs(scroll_distance)
            else:
                scroll_distance = -abs(scroll_distance)
            
            # 平滑滚动
            await self._smooth_scroll(page, scroll_distance)
            
            # 随机停留
            await asyncio.sleep(random.uniform(
                self.min_scroll_delay,
                self.max_scroll_delay
            ))
    
    async def random_hover(self, page: Page):
        """随机悬停在元素上"""
        try:
            # 获取可交互元素
            elements = await page.query_selector_all(
                "a, button, input, [onclick], [onmouseover]"
            )
            
            if not elements:
                return
            
            # 随机选择1-3个元素悬停
            num_hovers = min(len(elements), random.randint(1, 3))
            selected_elements = random.sample(elements, num_hovers)
            
            for element in selected_elements:
                try:
                    # 悬停
                    await element.hover()
                    
                    # 停留一会儿
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                except Exception:
                    # 元素可能已经不存在
                    pass
                    
        except Exception as e:
            logger.debug(f"Random hover error: {e}")
    
    async def check_page_elements(self, page: Page):
        """检查页面元素（模拟阅读）"""
        try:
            # 模拟视线扫描
            viewport = page.viewport_size
            
            # 生成扫描路径（Z字形）
            scan_points = []
            rows = 3
            cols = 3
            
            for row in range(rows):
                if row % 2 == 0:  # 从左到右
                    for col in range(cols):
                        x = int(viewport["width"] * (col + 0.5) / cols)
                        y = int(viewport["height"] * (row + 0.5) / rows)
                        scan_points.append((x, y))
                else:  # 从右到左
                    for col in range(cols - 1, -1, -1):
                        x = int(viewport["width"] * (col + 0.5) / cols)
                        y = int(viewport["height"] * (row + 0.5) / rows)
                        scan_points.append((x, y))
            
            # 沿扫描路径移动鼠标
            for point in scan_points:
                await page.mouse.move(point[0], point[1])
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
        except Exception as e:
            logger.debug(f"Check elements error: {e}")
    
    async def human_type(self, page: Page, selector: str, text: str):
        """模拟人类打字"""
        element = await page.query_selector(selector)
        if not element:
            return
        
        # 点击元素
        await element.click()
        
        # 逐字符输入
        for char in text:
            await page.keyboard.type(char)
            
            # 随机延迟
            delay = random.uniform(self.min_type_delay, self.max_type_delay)
            
            # 偶尔有更长的停顿（思考）
            if random.random() < 0.1:
                delay *= random.uniform(2, 5)
            
            await asyncio.sleep(delay)
    
    async def _smooth_mouse_move(self, page: Page, start: Tuple[int, int], end: Tuple[int, int]):
        """平滑鼠标移动"""
        # 计算距离
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        # 计算步数
        speed = random.uniform(self.min_mouse_speed, self.max_mouse_speed)
        duration = distance / speed
        steps = int(duration * 60)  # 60 FPS
        steps = max(steps, 5)
        
        # 生成贝塞尔曲线控制点
        control_x = (start[0] + end[0]) / 2 + random.randint(-50, 50)
        control_y = (start[1] + end[1]) / 2 + random.randint(-50, 50)
        
        # 沿曲线移动
        for i in range(steps + 1):
            t = i / steps
            
            # 二次贝塞尔曲线
            x = int((1-t)**2 * start[0] + 2*(1-t)*t * control_x + t**2 * end[0])
            y = int((1-t)**2 * start[1] + 2*(1-t)*t * control_y + t**2 * end[1])
            
            await page.mouse.move(x, y)
            await asyncio.sleep(duration / steps)
    
    async def _smooth_scroll(self, page: Page, distance: int):
        """平滑滚动"""
        # 分多次小幅度滚动
        steps = random.randint(5, 10)
        step_distance = distance / steps
        
        for _ in range(steps):
            await page.evaluate(f"window.scrollBy(0, {step_distance})")
            await asyncio.sleep(random.uniform(0.05, 0.15))
```

### Task 2.4: 实现引擎协调器

#### 2.4.1 智能调度协调器
```python
# src/core/scheduler/coordinator.py
"""引擎协调器 - 负责任务分配和引擎选择"""
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import hashlib

from src.core.engines.base.engine_interface import (
    EngineType, CrawlTask, CrawlResult
)
from src.core.engines.base.engine_manager import engine_manager
from src.core.redis import get_redis, RedisKeys
from src.utils.logger.logger import get_logger

logger = get_logger("scheduler.coordinator")

class EngineCoordinator:
    """引擎协调器"""
    
    def __init__(self):
        self.redis = get_redis()
        self._platform_stats: Dict[str, Dict] = {}
        self._engine_load: Dict[EngineType, int] = {
            EngineType.CRAWL4AI: 0,
            EngineType.MEDIACRAWL: 0
        }
        self._running_tasks: Set[str] = set()
        self._lock = asyncio.Lock()
    
    async def analyze_platform(self, platform: str) -> Dict[str, any]:
        """分析平台特征"""
        # 平台特征定义
        platform_features = {
            "amap": {
                "content_type": "static",
                "js_render_required": False,
                "api_available": True,
                "anti_bot_level": "low",
                "rate_limit": "medium",
                "preferred_engine": EngineType.CRAWL4AI
            },
            "mafengwo": {
                "content_type": "mixed",
                "js_render_required": True,
                "api_available": False,
                "anti_bot_level": "medium",
                "rate_limit": "medium",
                "preferred_engine": EngineType.CRAWL4AI
            },
            "dianping": {
                "content_type": "mixed",
                "js_render_required": True,
                "api_available": False,
                "anti_bot_level": "high",
                "rate_limit": "strict",
                "preferred_engine": EngineType.CRAWL4AI
            },
            "ctrip": {
                "content_type": "mixed",
                "js_render_required": True,
                "api_available": True,
                "anti_bot_level": "medium",
                "rate_limit": "medium",
                "preferred_engine": EngineType.CRAWL4AI
            },
            "xiaohongshu": {
                "content_type": "dynamic",
                "js_render_required": True,
                "api_available": False,
                "anti_bot_level": "very_high",
                "rate_limit": "very_strict",
                "preferred_engine": EngineType.MEDIACRAWL
            },
            "douyin": {
                "content_type": "dynamic",
                "js_render_required": True,
                "api_available": False,
                "anti_bot_level": "very_high",
                "rate_limit": "strict",
                "preferred_engine": EngineType.MEDIACRAWL
            },
            "weibo": {
                "content_type": "dynamic",
                "js_render_required": True,
                "api_available": True,
                "anti_bot_level": "medium",
                "rate_limit": "medium",
                "preferred_engine": EngineType.MEDIACRAWL
            },
            "bilibili": {
                "content_type": "dynamic",
                "js_render_required": True,
                "api_available": True,
                "anti_bot_level": "low",
                "rate_limit": "low",
                "preferred_engine": EngineType.MEDIACRAWL
            }
        }
        
        return platform_features.get(platform, {
            "content_type": "unknown",
            "js_render_required": True,
            "api_available": False,
            "anti_bot_level": "medium",
            "rate_limit": "medium",
            "preferred_engine": EngineType.MEDIACRAWL
        })
    
    async def select_engine_for_task(self, task: CrawlTask) -> EngineType:
        """为任务选择最佳引擎"""
        # 如果任务明确指定了引擎
        if task.engine_type != EngineType.AUTO:
            return task.engine_type
        
        # 分析平台特征
        platform_features = await self.analyze_platform(task.platform)
        
        # 获取引擎负载
        async with self._lock:
            crawl4ai_load = self._engine_load[EngineType.CRAWL4AI]
            mediacrawl_load = self._engine_load[EngineType.MEDIACRAWL]
        
        # 决策逻辑
        preferred_engine = platform_features["preferred_engine"]
        
        # 考虑负载均衡
        if preferred_engine == EngineType.CRAWL4AI:
            # 如果Crawl4AI负载过高，考虑使用MediaCrawl
            if crawl4ai_load > mediacrawl_load * 2:
                logger.info(f"Load balancing: switching to MediaCrawl for task {task.task_id}")
                return EngineType.MEDIACRAWL
        else:
            # 如果MediaCrawl负载过高，考虑使用Crawl4AI（如果内容支持）
            if mediacrawl_load > crawl4ai_load * 2 and not platform_features["js_render_required"]:
                logger.info(f"Load balancing: switching to Crawl4AI for task {task.task_id}")
                return EngineType.CRAWL4AI
        
        return preferred_engine
    
    async def execute_task(self, task: CrawlTask) -> CrawlResult:
        """执行任务"""
        # 检查任务是否已在运行
        async with self._lock:
            if task.task_id in self._running_tasks:
                raise ValueError(f"Task {task.task_id} is already running")
            self._running_tasks.add(task.task_id)
        
        try:
            # 选择引擎
            engine_type = await self.select_engine_for_task(task)
            task.engine_type = engine_type
            
            # 更新引擎负载
            async with self._lock:
                self._engine_load[engine_type] += 1
            
            # 应用速率限制
            await self._apply_rate_limit(task.platform)
            
            # 执行任务
            logger.info(f"Executing task {task.task_id} with engine {engine_type}")
            result = await engine_manager.execute_task(task)
            
            # 更新平台统计
            await self._update_platform_stats(task.platform, result)
            
            return result
            
        finally:
            # 清理
            async with self._lock:
                self._running_tasks.discard(task.task_id)
                self._engine_load[engine_type] -= 1
    
    async def execute_batch(self, tasks: List[CrawlTask]) -> List[CrawlResult]:
        """批量执行任务"""
        # 按平台分组以更好地控制速率
        platform_tasks: Dict[str, List[CrawlTask]] = {}
        
        for task in tasks:
            if task.platform not in platform_tasks:
                platform_tasks[task.platform] = []
            platform_tasks[task.platform].append(task)
        
        # 并发执行各平台的任务
        all_results = []
        
        for platform, platform_task_list in platform_tasks.items():
            # 为每个平台的任务创建执行计划
            platform_results = await self._execute_platform_batch(
                platform, platform_task_list
            )
            all_results.extend(platform_results)
        
        return all_results
    
    async def _execute_platform_batch(self, platform: str, tasks: List[CrawlTask]) -> List[CrawlResult]:
        """执行单个平台的批量任务"""
        results = []
        
        # 获取平台特征
        platform_features = await self.analyze_platform(platform)
        
        # 根据速率限制确定并发数
        rate_limit = platform_features["rate_limit"]
        concurrency = {
            "low": 10,
            "medium": 5,
            "strict": 3,
            "very_strict": 1
        }.get(rate_limit, 3)
        
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(concurrency)
        
        async def execute_with_limit(task: CrawlTask):
            async with semaphore:
                return await self.execute_task(task)
        
        # 执行任务
        batch_results = await asyncio.gather(
            *[execute_with_limit(task) for task in tasks],
            return_exceptions=True
        )
        
        # 处理结果
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                # 创建错误结果
                error_result = CrawlResult(
                    task_id=tasks[i].task_id,
                    success=False,
                    url=tasks[i].url,
                    engine_type=tasks[i].engine_type,
                    engine_version="1.0.0",
                    error_type=type(result).__name__,
                    error_message=str(result),
                    elapsed_time=0.0
                )
                results.append(error_result)
            else:
                results.append(result)
        
        return results
    
    async def _apply_rate_limit(self, platform: str):
        """应用平台速率限制"""
        platform_features = await self.analyze_platform(platform)
        rate_limit = platform_features["rate_limit"]
        
        # 速率限制配置（请求间隔，秒）
        rate_intervals = {
            "low": 0.5,
            "medium": 1.0,
            "strict": 2.0,
            "very_strict": 5.0
        }
        
        interval = rate_intervals.get(rate_limit, 1.0)
        
        # 使用Redis实现分布式速率限制
        rate_key = RedisKeys.RATE_LIMIT.format(platform=platform, key="global")
        
        while True:
            # 获取上次请求时间
            last_request = await self.redis.get(rate_key)
            
            if not last_request:
                # 第一次请求
                await self.redis.setex(rate_key, 60, str(time.time()))
                break
            
            # 计算需要等待的时间
            elapsed = time.time() - float(last_request)
            if elapsed >= interval:
                # 更新时间戳
                await self.redis.setex(rate_key, 60, str(time.time()))
                break
            
            # 等待
            wait_time = interval - elapsed
            await asyncio.sleep(wait_time)
    
    async def _update_platform_stats(self, platform: str, result: CrawlResult):
        """更新平台统计信息"""
        # 更新Redis统计
        today = datetime.now().strftime("%Y-%m-%d")
        
        if result.success:
            stats_key = RedisKeys.STATS_CRAWL.format(platform=platform, date=today)
            await self.redis.hincrby(stats_key, "success", 1)
            await self.redis.hincrbyfloat(stats_key, "total_time", result.elapsed_time)
        else:
            stats_key = RedisKeys.STATS_ERROR.format(platform=platform, date=today)
            await self.redis.hincrby(stats_key, result.error_type or "unknown", 1)
        
        # 设置过期时间（7天）
        await self.redis.expire(stats_key, 7 * 24 * 3600)
        
        # 更新内存统计
        if platform not in self._platform_stats:
            self._platform_stats[platform] = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "avg_time": 0.0
            }
        
        stats = self._platform_stats[platform]
        stats["total"] += 1
        
        if result.success:
            stats["success"] += 1
            # 更新平均时间
            stats["avg_time"] = (
                (stats["avg_time"] * (stats["success"] - 1) + result.elapsed_time) 
                / stats["success"]
            )
        else:
            stats["failed"] += 1
    
    async def get_platform_stats(self, platform: Optional[str] = None) -> Dict:
        """获取平台统计信息"""
        if platform:
            return self._platform_stats.get(platform, {})
        return self._platform_stats
    
    async def get_engine_load(self) -> Dict[EngineType, int]:
        """获取引擎负载"""
        async with self._lock:
            return self._engine_load.copy()

# 创建全局协调器实例
coordinator = EngineCoordinator()
```

### Task 2.5: 创建引擎测试脚本

#### 2.5.1 引擎功能测试
```python
# scripts/test_engines.py
"""测试双引擎功能"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.core.engines.base.engine_interface import (
    EngineType, CrawlTask, EngineStatus
)
from src.core.engines.base.engine_manager import engine_manager
from src.engines.crawl4ai.engine import Crawl4AIEngine
from src.engines.mediacrawl.engine import MediaCrawlEngine
from src.core.scheduler.coordinator import coordinator
from src.utils.logger.logger import get_logger

logger = get_logger("test.engines")

async def test_crawl4ai_engine():
    """测试Crawl4AI引擎"""
    logger.info("Testing Crawl4AI Engine...")
    
    # 创建测试任务
    task = CrawlTask(
        task_id="test_crawl4ai_001",
        platform="test",
        url="https://example.com",
        engine_type=EngineType.CRAWL4AI,
        use_proxy=False,
        use_fingerprint=False
    )
    
    # 执行任务
    result = await engine_manager.execute_task(task)
    
    # 验证结果
    assert result.success, f"Crawl4AI test failed: {result.error_message}"
    assert result.html is not None
    assert result.status_code == 200
    
    logger.info(f"✓ Crawl4AI test passed. Elapsed: {result.elapsed_time:.2f}s")
    return True

async def test_mediacrawl_engine():
    """测试MediaCrawl引擎"""
    logger.info("Testing MediaCrawl Engine...")
    
    # 创建测试任务
    task = CrawlTask(
        task_id="test_mediacrawl_001",
        platform="test",
        url="https://example.com",
        engine_type=EngineType.MEDIACRAWL,
        wait_selector="h1",
        use_proxy=False,
        use_fingerprint=True,
        use_behavior_simulation=True
    )
    
    # 执行任务
    result = await engine_manager.execute_task(task)
    
    # 验证结果
    assert result.success, f"MediaCrawl test failed: {result.error_message}"
    assert result.html is not None
    assert "Example Domain" in result.text
    
    logger.info(f"✓ MediaCrawl test passed. Elapsed: {result.elapsed_time:.2f}s")
    return True

async def test_engine_selection():
    """测试引擎自动选择"""
    logger.info("Testing engine selection...")
    
    # 测试不同平台的引擎选择
    test_cases = [
        ("amap", EngineType.CRAWL4AI),
        ("xiaohongshu", EngineType.MEDIACRAWL),
        ("douyin", EngineType.MEDIACRAWL),
        ("mafengwo", EngineType.CRAWL4AI)
    ]
    
    for platform, expected_engine in test_cases:
        task = CrawlTask(
            task_id=f"test_selection_{platform}",
            platform=platform,
            url="https://example.com",
            engine_type=EngineType.AUTO
        )
        
        selected_engine = await coordinator.select_engine_for_task(task)
        assert selected_engine == expected_engine, \
            f"Wrong engine selected for {platform}: {selected_engine}"
        
        logger.info(f"✓ Correct engine selected for {platform}: {selected_engine}")
    
    return True

async def test_batch_crawl():
    """测试批量爬取"""
    logger.info("Testing batch crawl...")
    
    # 创建批量任务
    tasks = []
    for i in range(5):
        task = CrawlTask(
            task_id=f"test_batch_{i:03d}",
            platform="test",
            url=f"https://httpbin.org/delay/{i}",
            engine_type=EngineType.AUTO,
            timeout=10,
            use_proxy=False
        )
        tasks.append(task)
    
    # 执行批量任务
    results = await coordinator.execute_batch(tasks)
    
    # 验证结果
    assert len(results) == len(tasks)
    success_count = sum(1 for r in results if r.success)
    logger.info(f"✓ Batch crawl completed: {success_count}/{len(tasks)} successful")
    
    return True

async def test_engine_metrics():
    """测试引擎指标"""
    logger.info("Testing engine metrics...")
    
    # 获取引擎状态
    engine_status = await engine_manager.get_engine_status()
    logger.info(f"Engine status: {engine_status}")
    
    # 获取引擎指标
    engine_metrics = await engine_manager.get_engine_metrics()
    for engine_type, metrics in engine_metrics.items():
        logger.info(f"{engine_type} metrics: {metrics}")
    
    # 获取引擎负载
    engine_load = await coordinator.get_engine_load()
    logger.info(f"Engine load: {engine_load}")
    
    return True

async def main():
    """主测试流程"""
    logger.info("Starting engine tests...")
    
    # 注册引擎
    engine_manager.register_engine(EngineType.CRAWL4AI, Crawl4AIEngine)
    engine_manager.register_engine(EngineType.MEDIACRAWL, MediaCrawlEngine)
    
    # 初始化引擎
    configs = {
        EngineType.CRAWL4AI: {
            "workers": 3,
            "timeout": 30,
            "retry_times": 2
        },
        EngineType.MEDIACRAWL: {
            "browser_count": 2,
            "contexts_per_browser": 3,
            "headless": True,
            "timeout": 30
        }
    }
    
    await engine_manager.initialize(configs)
    
    try:
        # 运行测试
        tests = [
            ("Crawl4AI Engine", test_crawl4ai_engine),
            ("MediaCrawl Engine", test_mediacrawl_engine),
            ("Engine Selection", test_engine_selection),
            ("Batch Crawl", test_batch_crawl),
            ("Engine Metrics", test_engine_metrics)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                logger.info(f"\n{'='*50}")
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"{test_name} failed: {e}")
                results.append((test_name, False))
        
        # 输出总结
        logger.info(f"\n{'='*50}")
        logger.info("Test Summary:")
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{test_name}: {status}")
        
        all_passed = all(result for _, result in results)
        if all_passed:
            logger.info("\n✅ All engine tests passed!")
        else:
            logger.error("\n❌ Some engine tests failed!")
        
        return all_passed
        
    finally:
        # 清理
        await engine_manager.shutdown()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
```

### 验证步骤汇总

执行以下命令验证Phase 2的实现：

```bash
# 1. 确保Docker服务运行
docker-compose ps

# 2. 安装浏览器（如果还没安装）
poetry run playwright install

# 3. 运行引擎测试
poetry run python scripts/test_engines.py

# 4. 检查日志
tail -f logs/crawler.log
```

如果所有测试都通过，说明双引擎核心功能已经成功实现！

---

## 下一步

完成Phase 2后，我们将进入Phase 3：实现平台适配器。请确保：
1. 双引擎都能正常工作
2. 引擎选择逻辑正确
3. 批量爬取功能正常
4. 性能指标收集正常

准备好后，继续执行第3部分的任务。