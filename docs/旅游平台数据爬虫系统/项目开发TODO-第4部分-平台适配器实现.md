# 旅游平台数据爬虫系统 - 项目开发TODO详细指南
## 第4部分：平台适配器实现

> 本部分实现8个目标平台的适配器，包括高德地图、马蜂窝、大众点评、携程、小红书、抖音、微博、B站

---

## Phase 4: 平台适配器实现（Day 8-12）

### Task 4.1: 创建平台适配器基类

#### 4.1.1 适配器接口定义
```python
# src/adapters/base/adapter_interface.py
"""平台适配器接口定义"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.core.engines.base.engine_interface import CrawlTask, CrawlResult
from src.core.scheduler.coordinator import coordinator
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.interface")

# 数据类型枚举
class DataType(str, Enum):
    POI = "poi"  # 兴趣点
    REVIEW = "review"  # 评论
    ARTICLE = "article"  # 文章/游记
    PRICE = "price"  # 价格
    IMAGE = "image"  # 图片
    VIDEO = "video"  # 视频

# 搜索查询模型
class SearchQuery(BaseModel):
    """搜索查询参数"""
    keyword: str = Field(..., description="搜索关键词")
    city: Optional[str] = Field(None, description="城市")
    category: Optional[str] = Field(None, description="分类")
    sort_by: Optional[str] = Field(None, description="排序方式")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")

# POI基础模型
class POI(BaseModel):
    """兴趣点基础模型"""
    # 基础信息
    poi_id: str = Field(..., description="POI唯一ID")
    platform: str = Field(..., description="来源平台")
    platform_poi_id: str = Field(..., description="平台原始ID")
    
    # 核心信息
    name: str = Field(..., description="名称")
    category: Optional[str] = Field(None, description="分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    
    # 位置信息
    address: Optional[str] = Field(None, description="地址")
    city: Optional[str] = Field(None, description="城市")
    district: Optional[str] = Field(None, description="区域")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")
    
    # 评分信息
    rating: Optional[float] = Field(None, description="评分")
    rating_count: Optional[int] = Field(None, description="评分人数")
    review_count: Optional[int] = Field(None, description="评论数")
    
    # 价格信息
    price: Optional[float] = Field(None, description="价格")
    price_unit: Optional[str] = Field(None, description="价格单位")
    price_desc: Optional[str] = Field(None, description="价格描述")
    
    # 联系信息
    phone: Optional[str] = Field(None, description="电话")
    website: Optional[str] = Field(None, description="网站")
    
    # 营业信息
    business_hours: Optional[Dict[str, str]] = Field(None, description="营业时间")
    is_closed: bool = Field(default=False, description="是否已关闭")
    
    # 图片信息
    cover_image: Optional[str] = Field(None, description="封面图")
    images: List[str] = Field(default_factory=list, description="图片列表")
    
    # 额外信息
    description: Optional[str] = Field(None, description="描述")
    features: Dict[str, Any] = Field(default_factory=dict, description="特色功能")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="原始数据")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_crawled_at: datetime = Field(default_factory=datetime.utcnow)

# 评论模型
class Review(BaseModel):
    """评论模型"""
    review_id: str = Field(..., description="评论ID")
    poi_id: str = Field(..., description="关联的POI ID")
    platform: str = Field(..., description="来源平台")
    
    # 作者信息
    author_id: str = Field(..., description="作者ID")
    author_name: str = Field(..., description="作者名称")
    author_avatar: Optional[str] = Field(None, description="作者头像")
    author_level: Optional[str] = Field(None, description="作者等级")
    
    # 评论内容
    content: str = Field(..., description="评论内容")
    rating: Optional[float] = Field(None, description="评分")
    
    # 图片/视频
    images: List[str] = Field(default_factory=list, description="图片列表")
    videos: List[str] = Field(default_factory=list, description="视频列表")
    
    # 互动数据
    like_count: int = Field(default=0, description="点赞数")
    reply_count: int = Field(default=0, description="回复数")
    
    # 时间信息
    created_at: datetime = Field(..., description="发布时间")
    crawled_at: datetime = Field(default_factory=datetime.utcnow)

# 文章/游记模型
class Article(BaseModel):
    """文章/游记模型"""
    article_id: str = Field(..., description="文章ID")
    platform: str = Field(..., description="来源平台")
    
    # 基础信息
    title: str = Field(..., description="标题")
    summary: Optional[str] = Field(None, description="摘要")
    content: str = Field(..., description="内容")
    
    # 作者信息
    author_id: str = Field(..., description="作者ID")
    author_name: str = Field(..., description="作者名称")
    
    # 关联POI
    related_pois: List[str] = Field(default_factory=list, description="相关POI")
    
    # 统计数据
    view_count: int = Field(default=0, description="浏览数")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    
    # 时间信息
    created_at: datetime = Field(..., description="发布时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    crawled_at: datetime = Field(default_factory=datetime.utcnow)

# 平台适配器基类
class PlatformAdapter(ABC):
    """平台适配器抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_name = "unknown"
        self.logger = logger.bind(platform=self.platform_name)
        
        # 速率限制配置
        self.rate_limit = config.get("rate_limit", 1.0)  # 请求间隔(秒)
        self.max_retries = config.get("max_retries", 3)
        
        # 数据处理配置
        self.enable_cache = config.get("enable_cache", True)
        self.cache_ttl = config.get("cache_ttl", 3600)  # 缓存时间(秒)
    
    @abstractmethod
    async def search_pois(self, query: SearchQuery) -> List[POI]:
        """搜索POI"""
        pass
    
    @abstractmethod
    async def get_poi_detail(self, poi_id: str) -> Optional[POI]:
        """获取POI详情"""
        pass
    
    @abstractmethod
    async def get_poi_reviews(
        self, 
        poi_id: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> List[Review]:
        """获取POI评论"""
        pass
    
    @abstractmethod
    async def search_articles(
        self, 
        keyword: str, 
        page: int = 1
    ) -> List[Article]:
        """搜索文章/游记"""
        pass
    
    # 通用方法
    async def create_crawl_task(
        self,
        url: str,
        task_type: str,
        extraction_rules: Dict[str, Any],
        **kwargs
    ) -> CrawlTask:
        """创建爬取任务"""
        task = CrawlTask(
            task_id=f"{self.platform_name}_{task_type}_{datetime.utcnow().timestamp()}",
            platform=self.platform_name,
            url=url,
            task_type=task_type,
            extraction_rules=extraction_rules,
            retry_times=self.max_retries,
            **kwargs
        )
        
        return task
    
    async def execute_crawl_task(self, task: CrawlTask) -> CrawlResult:
        """执行爬取任务"""
        # 通过协调器执行任务
        result = await coordinator.execute_task(task)
        
        if not result.success:
            self.logger.error(
                f"Crawl task failed: {result.error_message}",
                task_id=task.task_id,
                url=task.url
            )
        
        return result
    
    async def parse_poi_from_html(self, html: str) -> Optional[POI]:
        """从HTML解析POI（子类实现具体逻辑）"""
        raise NotImplementedError
    
    async def parse_reviews_from_html(self, html: str) -> List[Review]:
        """从HTML解析评论（子类实现具体逻辑）"""
        raise NotImplementedError
    
    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """清理文本"""
        if not text:
            return None
        
        # 移除多余空白
        text = " ".join(text.split())
        
        # 移除特殊字符
        text = text.strip()
        
        return text if text else None
    
    def extract_number(self, text: str) -> Optional[float]:
        """从文本提取数字"""
        import re
        
        if not text:
            return None
        
        # 匹配数字
        match = re.search(r'[\d.]+', text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return None
```

#### 4.1.2 适配器工厂
```python
# src/adapters/base/adapter_factory.py
"""平台适配器工厂"""
from typing import Dict, Type, Optional
from src.adapters.base.adapter_interface import PlatformAdapter
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.factory")

class AdapterFactory:
    """适配器工厂"""
    
    _adapters: Dict[str, Type[PlatformAdapter]] = {}
    _instances: Dict[str, PlatformAdapter] = {}
    
    @classmethod
    def register(cls, platform: str, adapter_class: Type[PlatformAdapter]):
        """注册适配器"""
        cls._adapters[platform] = adapter_class
        logger.info(f"Registered adapter for platform: {platform}")
    
    @classmethod
    def create(cls, platform: str, config: Dict) -> Optional[PlatformAdapter]:
        """创建适配器实例"""
        if platform not in cls._adapters:
            logger.error(f"No adapter registered for platform: {platform}")
            return None
        
        # 单例模式
        if platform not in cls._instances:
            adapter_class = cls._adapters[platform]
            cls._instances[platform] = adapter_class(config)
            logger.info(f"Created adapter instance for platform: {platform}")
        
        return cls._instances[platform]
    
    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        """获取支持的平台列表"""
        return list(cls._adapters.keys())
```

### Task 4.2: 实现高德地图适配器

#### 4.2.1 高德地图适配器实现
```python
# src/adapters/amap/adapter.py
"""高德地图适配器"""
import re
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode, quote

from src.adapters.base.adapter_interface import (
    PlatformAdapter, POI, Review, Article, SearchQuery, DataType
)
from src.adapters.base.adapter_factory import AdapterFactory
from src.core.engines.base.engine_interface import CrawlTask
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.amap")

class AMapAdapter(PlatformAdapter):
    """高德地图适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.platform_name = "amap"
        self.base_url = "https://www.amap.com"
        self.search_url = "https://www.amap.com/search"
        
        # API配置（如果有）
        self.api_key = config.get("api_key")
        self.use_api = config.get("use_api", False) and self.api_key
        
        # 提取规则
        self.extraction_rules = {
            "search_results": {
                "css_selectors": {
                    "items": ".poilist-item",
                    "name": ".poi-title",
                    "address": ".poi-address",
                    "rating": ".poi-rating",
                    "category": ".poi-category",
                    "tel": ".poi-tel"
                }
            },
            "poi_detail": {
                "css_selectors": {
                    "name": "h1.detail-title",
                    "address": ".detail-address",
                    "tel": ".detail-tel",
                    "hours": ".business-hours",
                    "rating": ".rating-score",
                    "review_count": ".review-count",
                    "images": ".photo-list img"
                },
                "attribute_extractors": {
                    "images": {
                        "selector": ".photo-list img",
                        "attribute": "src"
                    }
                }
            }
        }
    
    async def search_pois(self, query: SearchQuery) -> List[POI]:
        """搜索POI"""
        try:
            # 构建搜索URL
            params = {
                "query": query.keyword,
                "city": query.city or "全国",
                "pagenum": query.page,
                "pagesize": query.page_size
            }
            
            url = f"{self.search_url}?{urlencode(params)}"
            
            # 创建爬取任务
            task = await self.create_crawl_task(
                url=url,
                task_type="search",
                extraction_rules=self.extraction_rules["search_results"],
                wait_selector=".poilist-item"
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return []
            
            # 解析结果
            pois = await self._parse_search_results(result)
            
            return pois
            
        except Exception as e:
            logger.error(f"Search POIs error: {e}")
            return []
    
    async def get_poi_detail(self, poi_id: str) -> Optional[POI]:
        """获取POI详情"""
        try:
            # 构建详情URL
            url = f"{self.base_url}/detail/{poi_id}"
            
            # 创建爬取任务
            task = await self.create_crawl_task(
                url=url,
                task_type="detail",
                extraction_rules=self.extraction_rules["poi_detail"],
                wait_selector=".detail-title"
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return None
            
            # 解析详情
            poi = await self._parse_poi_detail(result, poi_id)
            
            return poi
            
        except Exception as e:
            logger.error(f"Get POI detail error: {e}")
            return None
    
    async def get_poi_reviews(
        self, 
        poi_id: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> List[Review]:
        """获取POI评论"""
        try:
            # 构建评论URL
            url = f"{self.base_url}/detail/{poi_id}/review?page={page}"
            
            # 创建爬取任务
            task = await self.create_crawl_task(
                url=url,
                task_type="reviews",
                extraction_rules={
                    "css_selectors": {
                        "items": ".review-item",
                        "author": ".review-author",
                        "content": ".review-content",
                        "rating": ".review-rating",
                        "date": ".review-date",
                        "images": ".review-images img"
                    }
                },
                wait_selector=".review-item"
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return []
            
            # 解析评论
            reviews = await self._parse_reviews(result, poi_id)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Get POI reviews error: {e}")
            return []
    
    async def search_articles(
        self, 
        keyword: str, 
        page: int = 1
    ) -> List[Article]:
        """搜索文章/游记"""
        # 高德地图主要是地图服务，没有游记功能
        return []
    
    async def _parse_search_results(self, crawl_result) -> List[POI]:
        """解析搜索结果"""
        pois = []
        
        try:
            # 从提取的数据中解析
            items = crawl_result.extracted_data.get("items", [])
            
            for idx, item in enumerate(items):
                # 解析每个POI
                poi_data = {
                    "platform": self.platform_name,
                    "platform_poi_id": f"amap_{idx}_{datetime.utcnow().timestamp()}",
                    "name": self.clean_text(item.get("name")),
                    "address": self.clean_text(item.get("address")),
                    "category": self.clean_text(item.get("category")),
                    "phone": self.clean_text(item.get("tel")),
                    "raw_data": item
                }
                
                # 解析评分
                rating_text = item.get("rating", "")
                if rating_text:
                    rating = self.extract_number(rating_text)
                    if rating:
                        poi_data["rating"] = rating
                
                # 创建POI对象
                if poi_data["name"]:
                    poi = POI(
                        poi_id=f"{self.platform_name}_{poi_data['platform_poi_id']}",
                        **poi_data
                    )
                    pois.append(poi)
            
            # 如果没有从提取数据中获取，尝试从HTML解析
            if not pois and crawl_result.html:
                pois = await self._parse_search_results_from_html(crawl_result.html)
            
        except Exception as e:
            logger.error(f"Parse search results error: {e}")
        
        return pois
    
    async def _parse_search_results_from_html(self, html: str) -> List[POI]:
        """从HTML解析搜索结果"""
        pois = []
        
        try:
            # 使用BeautifulSoup解析（需要安装）
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找POI列表项
            items = soup.select('.poilist-item')
            
            for item in items:
                # 提取信息
                name_elem = item.select_one('.poi-title')
                address_elem = item.select_one('.poi-address')
                
                if name_elem:
                    poi_data = {
                        "platform": self.platform_name,
                        "platform_poi_id": item.get('data-id', ''),
                        "name": self.clean_text(name_elem.text),
                        "address": self.clean_text(address_elem.text) if address_elem else None,
                    }
                    
                    # 提取其他信息
                    category_elem = item.select_one('.poi-category')
                    if category_elem:
                        poi_data["category"] = self.clean_text(category_elem.text)
                    
                    tel_elem = item.select_one('.poi-tel')
                    if tel_elem:
                        poi_data["phone"] = self.clean_text(tel_elem.text)
                    
                    rating_elem = item.select_one('.poi-rating')
                    if rating_elem:
                        rating = self.extract_number(rating_elem.text)
                        if rating:
                            poi_data["rating"] = rating
                    
                    # 创建POI
                    poi = POI(
                        poi_id=f"{self.platform_name}_{poi_data['platform_poi_id']}",
                        **poi_data
                    )
                    pois.append(poi)
                    
        except Exception as e:
            logger.error(f"Parse HTML error: {e}")
        
        return pois
    
    async def _parse_poi_detail(self, crawl_result, poi_id: str) -> Optional[POI]:
        """解析POI详情"""
        try:
            data = crawl_result.extracted_data
            
            poi_data = {
                "poi_id": f"{self.platform_name}_{poi_id}",
                "platform": self.platform_name,
                "platform_poi_id": poi_id,
                "name": self.clean_text(data.get("name")),
                "address": self.clean_text(data.get("address")),
                "phone": self.clean_text(data.get("tel")),
                "images": data.get("images", []),
                "raw_data": data
            }
            
            # 解析营业时间
            hours_text = data.get("hours")
            if hours_text:
                poi_data["business_hours"] = self._parse_business_hours(hours_text)
            
            # 解析评分
            rating_text = data.get("rating")
            if rating_text:
                rating = self.extract_number(rating_text)
                if rating:
                    poi_data["rating"] = rating
            
            # 解析评论数
            review_count_text = data.get("review_count")
            if review_count_text:
                count = self.extract_number(review_count_text)
                if count:
                    poi_data["review_count"] = int(count)
            
            # 设置封面图
            if poi_data["images"]:
                poi_data["cover_image"] = poi_data["images"][0]
            
            return POI(**poi_data)
            
        except Exception as e:
            logger.error(f"Parse POI detail error: {e}")
            return None
    
    async def _parse_reviews(self, crawl_result, poi_id: str) -> List[Review]:
        """解析评论"""
        reviews = []
        
        try:
            items = crawl_result.extracted_data.get("items", [])
            
            for item in items:
                review_data = {
                    "review_id": f"amap_review_{datetime.utcnow().timestamp()}",
                    "poi_id": f"{self.platform_name}_{poi_id}",
                    "platform": self.platform_name,
                    "author_id": "unknown",
                    "author_name": self.clean_text(item.get("author", "匿名用户")),
                    "content": self.clean_text(item.get("content", "")),
                    "images": item.get("images", [])
                }
                
                # 解析评分
                rating_text = item.get("rating")
                if rating_text:
                    rating = self.extract_number(rating_text)
                    if rating:
                        review_data["rating"] = rating
                
                # 解析时间
                date_text = item.get("date")
                if date_text:
                    review_data["created_at"] = self._parse_date(date_text)
                else:
                    review_data["created_at"] = datetime.utcnow()
                
                if review_data["content"]:
                    review = Review(**review_data)
                    reviews.append(review)
                    
        except Exception as e:
            logger.error(f"Parse reviews error: {e}")
        
        return reviews
    
    def _parse_business_hours(self, hours_text: str) -> Dict[str, str]:
        """解析营业时间"""
        # 简单实现，实际需要根据高德的格式调整
        return {"default": self.clean_text(hours_text)}
    
    def _parse_date(self, date_text: str) -> datetime:
        """解析日期"""
        # 简单实现，实际需要根据高德的日期格式调整
        try:
            # 尝试几种常见格式
            from dateutil import parser
            return parser.parse(date_text)
        except:
            return datetime.utcnow()

# 注册适配器
AdapterFactory.register("amap", AMapAdapter)
```

### Task 4.3: 实现马蜂窝适配器

#### 4.3.1 马蜂窝适配器实现
```python
# src/adapters/mafengwo/adapter.py
"""马蜂窝适配器"""
import re
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode, quote

from src.adapters.base.adapter_interface import (
    PlatformAdapter, POI, Review, Article, SearchQuery, DataType
)
from src.adapters.base.adapter_factory import AdapterFactory
from src.core.engines.base.engine_interface import CrawlTask, EngineType
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.mafengwo")

class MafengwoAdapter(PlatformAdapter):
    """马蜂窝适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.platform_name = "mafengwo"
        self.base_url = "https://www.mafengwo.cn"
        
        # 马蜂窝需要登录态才能获取完整数据
        self.cookies = config.get("cookies", {})
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.base_url
        }
        
        # 提取规则
        self.extraction_rules = {
            "search_results": {
                "css_selectors": {
                    "items": "li.item",
                    "name": ".title a",
                    "url": ".title a",
                    "type": ".type",
                    "location": ".location",
                    "info": ".info"
                },
                "attribute_extractors": {
                    "url": {
                        "selector": ".title a",
                        "attribute": "href"
                    }
                }
            },
            "poi_detail": {
                "css_selectors": {
                    "name": "h1",
                    "address": ".address",
                    "tel": ".tel",
                    "intro": ".intro .content",
                    "score": ".score em",
                    "comment_count": ".comment-count",
                    "rank": ".rank",
                    "tips": ".tips-list li",
                    "images": ".photo-list img"
                },
                "js_extractors": {
                    "location": """
                    (() => {
                        if (window.PageData && window.PageData.poi) {
                            return {
                                lat: window.PageData.poi.lat,
                                lng: window.PageData.poi.lng
                            };
                        }
                        return null;
                    })()
                    """
                }
            },
            "articles": {
                "css_selectors": {
                    "items": ".post-list li",
                    "title": ".title a",
                    "author": ".author",
                    "summary": ".abstract",
                    "stats": ".stats span",
                    "url": ".title a"
                }
            }
        }
    
    async def search_pois(self, query: SearchQuery) -> List[POI]:
        """搜索POI"""
        try:
            # 马蜂窝搜索API
            search_api = f"{self.base_url}/search/s.php"
            
            params = {
                "q": query.keyword,
                "t": "poi",  # 搜索类型：poi
                "p": query.page,
                "n": query.page_size
            }
            
            if query.city:
                params["mdd"] = query.city
            
            url = f"{search_api}?{urlencode(params)}"
            
            # 创建爬取任务
            task = await self.create_crawl_task(
                url=url,
                task_type="search",
                extraction_rules=self.extraction_rules["search_results"],
                headers=self.headers,
                cookies=self.cookies,
                engine_type=EngineType.CRAWL4AI  # 马蜂窝适合结构化爬取
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return []
            
            # 解析结果
            pois = await self._parse_search_results(result)
            
            # 获取详情（马蜂窝搜索结果信息较少）
            detailed_pois = []
            for poi in pois[:5]:  # 限制并发数
                if poi.platform_poi_id:
                    detail = await self.get_poi_detail(poi.platform_poi_id)
                    if detail:
                        detailed_pois.append(detail)
                    else:
                        detailed_pois.append(poi)
                    
                    # 控制速率
                    await asyncio.sleep(self.rate_limit)
            
            return detailed_pois
            
        except Exception as e:
            logger.error(f"Search POIs error: {e}")
            return []
    
    async def get_poi_detail(self, poi_id: str) -> Optional[POI]:
        """获取POI详情"""
        try:
            # 构建详情URL
            url = f"{self.base_url}/poi/{poi_id}.html"
            
            # 创建爬取任务
            task = await self.create_crawl_task(
                url=url,
                task_type="detail",
                extraction_rules=self.extraction_rules["poi_detail"],
                headers=self.headers,
                cookies=self.cookies,
                wait_selector="h1",
                engine_type=EngineType.CRAWL4AI
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return None
            
            # 解析详情
            poi = await self._parse_poi_detail(result, poi_id)
            
            return poi
            
        except Exception as e:
            logger.error(f"Get POI detail error: {e}")
            return None
    
    async def get_poi_reviews(
        self, 
        poi_id: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> List[Review]:
        """获取POI评论"""
        try:
            # 马蜂窝评论需要AJAX请求
            url = f"{self.base_url}/poi/comment/list"
            
            # 构建请求参数
            params = {
                "poi_id": poi_id,
                "page": page,
                "page_size": page_size,
                "type": 3  # 评论类型
            }
            
            # 创建爬取任务
            task = await self.create_crawl_task(
                url=url,
                task_type="reviews",
                method="POST",
                data=params,
                headers={**self.headers, "X-Requested-With": "XMLHttpRequest"},
                cookies=self.cookies,
                engine_type=EngineType.CRAWL4AI
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return []
            
            # 解析评论
            reviews = await self._parse_reviews(result, poi_id)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Get POI reviews error: {e}")
            return []
    
    async def search_articles(
        self, 
        keyword: str, 
        page: int = 1
    ) -> List[Article]:
        """搜索文章/游记"""
        try:
            # 马蜂窝游记搜索
            search_api = f"{self.base_url}/search/s.php"
            
            params = {
                "q": keyword,
                "t": "notes",  # 搜索类型：游记
                "p": page
            }
            
            url = f"{search_api}?{urlencode(params)}"
            
            # 创建爬取任务
            task = await self.create_crawl_task(
                url=url,
                task_type="articles",
                extraction_rules=self.extraction_rules["articles"],
                headers=self.headers,
                engine_type=EngineType.CRAWL4AI
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return []
            
            # 解析文章
            articles = await self._parse_articles(result)
            
            return articles
            
        except Exception as e:
            logger.error(f"Search articles error: {e}")
            return []
    
    async def _parse_search_results(self, crawl_result) -> List[POI]:
        """解析搜索结果"""
        pois = []
        
        try:
            items = crawl_result.extracted_data.get("items", [])
            urls = crawl_result.extracted_data.get("url", [])
            
            for idx, item in enumerate(items):
                # 提取POI ID
                poi_id = None
                if idx < len(urls):
                    url = urls[idx]
                    match = re.search(r'/poi/(\d+)\.html', url)
                    if match:
                        poi_id = match.group(1)
                
                poi_data = {
                    "platform": self.platform_name,
                    "platform_poi_id": poi_id or f"mfw_{idx}",
                    "name": self.clean_text(item.get("name")),
                    "category": self.clean_text(item.get("type")),
                    "address": self.clean_text(item.get("location")),
                    "description": self.clean_text(item.get("info")),
                    "raw_data": item
                }
                
                if poi_data["name"]:
                    poi = POI(
                        poi_id=f"{self.platform_name}_{poi_data['platform_poi_id']}",
                        **poi_data
                    )
                    pois.append(poi)
                    
        except Exception as e:
            logger.error(f"Parse search results error: {e}")
        
        return pois
    
    async def _parse_poi_detail(self, crawl_result, poi_id: str) -> Optional[POI]:
        """解析POI详情"""
        try:
            data = crawl_result.extracted_data
            
            poi_data = {
                "poi_id": f"{self.platform_name}_{poi_id}",
                "platform": self.platform_name,
                "platform_poi_id": poi_id,
                "name": self.clean_text(data.get("name")),
                "address": self.clean_text(data.get("address")),
                "phone": self.clean_text(data.get("tel")),
                "description": self.clean_text(data.get("intro")),
                "images": data.get("images", []),
                "raw_data": data
            }
            
            # 解析评分
            score_text = data.get("score")
            if score_text:
                score = self.extract_number(score_text)
                if score:
                    poi_data["rating"] = score
            
            # 解析评论数
            comment_count_text = data.get("comment_count")
            if comment_count_text:
                count = self.extract_number(comment_count_text)
                if count:
                    poi_data["review_count"] = int(count)
            
            # 解析坐标
            location = data.get("location")
            if location and isinstance(location, dict):
                poi_data["latitude"] = location.get("lat")
                poi_data["longitude"] = location.get("lng")
            
            # 解析排名
            rank_text = data.get("rank")
            if rank_text:
                poi_data["features"]["rank"] = self.clean_text(rank_text)
            
            # 解析贴士
            tips = data.get("tips", [])
            if tips:
                poi_data["features"]["tips"] = [self.clean_text(tip) for tip in tips if tip]
            
            # 设置封面图
            if poi_data["images"]:
                poi_data["cover_image"] = poi_data["images"][0]
            
            return POI(**poi_data)
            
        except Exception as e:
            logger.error(f"Parse POI detail error: {e}")
            return None
    
    async def _parse_reviews(self, crawl_result, poi_id: str) -> List[Review]:
        """解析评论"""
        reviews = []
        
        try:
            # 马蜂窝评论通常返回JSON
            if crawl_result.json_data:
                data = crawl_result.json_data
                comment_list = data.get("data", {}).get("list", [])
                
                for comment in comment_list:
                    review_data = {
                        "review_id": str(comment.get("id", "")),
                        "poi_id": f"{self.platform_name}_{poi_id}",
                        "platform": self.platform_name,
                        "author_id": str(comment.get("user", {}).get("id", "")),
                        "author_name": comment.get("user", {}).get("name", "匿名用户"),
                        "author_avatar": comment.get("user", {}).get("avatar", ""),
                        "content": self.clean_text(comment.get("content", "")),
                        "images": comment.get("images", []),
                        "like_count": comment.get("like_count", 0),
                        "created_at": self._parse_timestamp(comment.get("time", 0))
                    }
                    
                    # 解析评分
                    score = comment.get("score")
                    if score:
                        review_data["rating"] = float(score) / 10  # 马蜂窝评分是0-50
                    
                    if review_data["content"] and review_data["review_id"]:
                        review = Review(**review_data)
                        reviews.append(review)
                        
        except Exception as e:
            logger.error(f"Parse reviews error: {e}")
        
        return reviews
    
    async def _parse_articles(self, crawl_result) -> List[Article]:
        """解析文章列表"""
        articles = []
        
        try:
            items = crawl_result.extracted_data.get("items", [])
            
            for item in items:
                # 提取文章ID
                article_id = None
                url = item.get("url")
                if url:
                    match = re.search(r'/i/(\d+)\.html', url)
                    if match:
                        article_id = match.group(1)
                
                article_data = {
                    "article_id": article_id or f"mfw_article_{datetime.utcnow().timestamp()}",
                    "platform": self.platform_name,
                    "title": self.clean_text(item.get("title")),
                    "author_name": self.clean_text(item.get("author", "").replace("作者：", "")),
                    "author_id": "unknown",
                    "summary": self.clean_text(item.get("summary")),
                    "content": "",  # 需要进入详情页获取
                    "created_at": datetime.utcnow()  # 需要从详情页获取
                }
                
                # 解析统计数据
                stats = item.get("stats", [])
                for stat in stats:
                    stat_text = self.clean_text(stat)
                    if "浏览" in stat_text:
                        count = self.extract_number(stat_text)
                        if count:
                            article_data["view_count"] = int(count)
                    elif "评论" in stat_text:
                        count = self.extract_number(stat_text)
                        if count:
                            article_data["comment_count"] = int(count)
                    elif "赞" in stat_text or "顶" in stat_text:
                        count = self.extract_number(stat_text)
                        if count:
                            article_data["like_count"] = int(count)
                
                if article_data["title"]:
                    article = Article(**article_data)
                    articles.append(article)
                    
        except Exception as e:
            logger.error(f"Parse articles error: {e}")
        
        return articles
    
    def _parse_timestamp(self, timestamp: int) -> datetime:
        """解析时间戳"""
        try:
            # 马蜂窝使用毫秒时间戳
            return datetime.fromtimestamp(timestamp / 1000)
        except:
            return datetime.utcnow()

# 注册适配器
AdapterFactory.register("mafengwo", MafengwoAdapter)
```

### Task 4.4: 实现小红书适配器

#### 4.4.1 小红书适配器实现
```python
# src/adapters/xiaohongshu/adapter.py
"""小红书适配器"""
import re
import json
import asyncio
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode, quote

from src.adapters.base.adapter_interface import (
    PlatformAdapter, POI, Review, Article, SearchQuery, DataType
)
from src.adapters.base.adapter_factory import AdapterFactory
from src.core.engines.base.engine_interface import CrawlTask, EngineType
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.xiaohongshu")

class XiaohongshuAdapter(PlatformAdapter):
    """小红书适配器 - 需要处理复杂的反爬机制"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.platform_name = "xiaohongshu"
        self.base_url = "https://www.xiaohongshu.com"
        self.api_base = "https://edith.xiaohongshu.com/api/sns/web/v1"
        
        # 小红书需要特殊的请求头和签名
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.base_url,
            "Origin": self.base_url,
            "X-S": "",  # 需要动态生成
            "X-T": ""   # 需要动态生成
        }
        
        # 提取规则
        self.extraction_rules = {
            "search_notes": {
                "js_extractors": {
                    "data": """
                    (() => {
                        // 小红书数据通常在__INITIAL_STATE__中
                        if (window.__INITIAL_STATE__) {
                            return window.__INITIAL_STATE__.search.notes;
                        }
                        return null;
                    })()
                    """
                }
            },
            "note_detail": {
                "js_extractors": {
                    "data": """
                    (() => {
                        if (window.__INITIAL_STATE__) {
                            return window.__INITIAL_STATE__.note.noteDetail;
                        }
                        return null;
                    })()
                    """
                },
                "css_selectors": {
                    "images": ".note-image img",
                    "content": ".note-content",
                    "tags": ".tag-item"
                }
            }
        }
    
    async def search_pois(self, query: SearchQuery) -> List[POI]:
        """搜索POI - 小红书主要是笔记内容"""
        # 小红书不是传统的POI平台，而是社交内容平台
        # 这里将搜索笔记并提取其中的地点信息
        try:
            articles = await self.search_articles(query.keyword, query.page)
            
            # 从笔记中提取POI信息
            pois = []
            for article in articles:
                poi = await self._extract_poi_from_article(article)
                if poi:
                    pois.append(poi)
            
            return pois
            
        except Exception as e:
            logger.error(f"Search POIs error: {e}")
            return []
    
    async def get_poi_detail(self, poi_id: str) -> Optional[POI]:
        """获取POI详情 - 小红书没有独立的POI页面"""
        # 小红书的"POI"实际上是从笔记中提取的
        return None
    
    async def get_poi_reviews(
        self, 
        poi_id: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> List[Review]:
        """获取POI评论 - 实际是获取相关笔记"""
        # 搜索包含该POI的笔记作为"评论"
        try:
            # 使用POI名称搜索相关笔记
            articles = await self.search_articles(poi_id, page)
            
            # 转换为评论格式
            reviews = []
            for article in articles:
                review = Review(
                    review_id=f"xhs_note_{article.article_id}",
                    poi_id=poi_id,
                    platform=self.platform_name,
                    author_id=article.author_id,
                    author_name=article.author_name,
                    content=article.content or article.summary,
                    images=[],  # 从article中提取
                    like_count=article.like_count,
                    created_at=article.created_at
                )
                reviews.append(review)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Get POI reviews error: {e}")
            return []
    
    async def search_articles(
        self, 
        keyword: str, 
        page: int = 1
    ) -> List[Article]:
        """搜索文章/笔记"""
        try:
            # 小红书搜索需要特殊处理
            url = f"{self.base_url}/search_result"
            
            # 创建爬取任务 - 使用MediaCrawl处理动态内容
            task = await self.create_crawl_task(
                url=url,
                task_type="search",
                extraction_rules=self.extraction_rules["search_notes"],
                headers=self.headers,
                engine_type=EngineType.MEDIACRAWL,  # 小红书需要动态渲染
                wait_selector=".note-item",
                engine_config={
                    "execute_js": f"""
                    // 模拟搜索
                    const searchInput = document.querySelector('input[type="search"]');
                    if (searchInput) {{
                        searchInput.value = '{keyword}';
                        searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        
                        // 触发搜索
                        const searchBtn = document.querySelector('.search-button');
                        if (searchBtn) {{
                            searchBtn.click();
                        }} else {{
                            // 或者按回车
                            searchInput.dispatchEvent(new KeyboardEvent('keypress', {{
                                key: 'Enter',
                                keyCode: 13,
                                bubbles: true
                            }}));
                        }}
                    }}
                    """
                }
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return []
            
            # 解析笔记
            articles = await self._parse_notes(result)
            
            return articles
            
        except Exception as e:
            logger.error(f"Search articles error: {e}")
            return []
    
    async def get_note_detail(self, note_id: str) -> Optional[Article]:
        """获取笔记详情"""
        try:
            url = f"{self.base_url}/explore/{note_id}"
            
            # 创建爬取任务
            task = await self.create_crawl_task(
                url=url,
                task_type="note_detail",
                extraction_rules=self.extraction_rules["note_detail"],
                headers=self.headers,
                engine_type=EngineType.MEDIACRAWL,
                wait_selector=".note-content",
                use_behavior_simulation=True  # 模拟人类行为
            )
            
            # 执行爬取
            result = await self.execute_crawl_task(task)
            
            if not result.success:
                return None
            
            # 解析详情
            article = await self._parse_note_detail(result, note_id)
            
            return article
            
        except Exception as e:
            logger.error(f"Get note detail error: {e}")
            return None
    
    async def _parse_notes(self, crawl_result) -> List[Article]:
        """解析笔记列表"""
        articles = []
        
        try:
            # 尝试从JS提取的数据解析
            data = crawl_result.extracted_data.get("data")
            
            if data and isinstance(data, list):
                for note_data in data:
                    article = await self._parse_note_item(note_data)
                    if article:
                        articles.append(article)
            else:
                # 降级到HTML解析
                articles = await self._parse_notes_from_html(crawl_result.html)
                
        except Exception as e:
            logger.error(f"Parse notes error: {e}")
        
        return articles
    
    async def _parse_note_item(self, note_data: Dict) -> Optional[Article]:
        """解析单个笔记数据"""
        try:
            article_data = {
                "article_id": note_data.get("id", ""),
                "platform": self.platform_name,
                "title": self.clean_text(note_data.get("title", "")),
                "summary": self.clean_text(note_data.get("desc", "")),
                "content": "",  # 需要进入详情页获取
                "author_id": note_data.get("user", {}).get("id", ""),
                "author_name": note_data.get("user", {}).get("nickname", ""),
                "view_count": note_data.get("view_count", 0),
                "like_count": note_data.get("liked_count", 0),
                "comment_count": note_data.get("comment_count", 0),
                "created_at": self._parse_timestamp(note_data.get("time", 0))
            }
            
            # 提取相关地点
            if "poi" in note_data:
                poi_info = note_data["poi"]
                article_data["related_pois"] = [poi_info.get("name", "")]
            
            if article_data["article_id"] and (article_data["title"] or article_data["summary"]):
                return Article(**article_data)
                
        except Exception as e:
            logger.error(f"Parse note item error: {e}")
        
        return None
    
    async def _parse_notes_from_html(self, html: str) -> List[Article]:
        """从HTML解析笔记"""
        articles = []
        
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找笔记卡片
            note_items = soup.select('.note-item, .feed-item')
            
            for item in note_items:
                # 提取笔记ID
                note_id = item.get('data-note-id') or item.get('data-id')
                
                # 提取标题
                title_elem = item.select_one('.title, .note-title')
                title = self.clean_text(title_elem.text) if title_elem else ""
                
                # 提取作者
                author_elem = item.select_one('.author-name, .user-name')
                author_name = self.clean_text(author_elem.text) if author_elem else ""
                
                # 提取统计
                like_elem = item.select_one('.like-count, .likes')
                like_count = self.extract_number(like_elem.text) if like_elem else 0
                
                if note_id and (title or author_name):
                    article = Article(
                        article_id=note_id,
                        platform=self.platform_name,
                        title=title,
                        summary="",
                        content="",
                        author_id="unknown",
                        author_name=author_name,
                        like_count=int(like_count) if like_count else 0,
                        created_at=datetime.utcnow()
                    )
                    articles.append(article)
                    
        except Exception as e:
            logger.error(f"Parse HTML error: {e}")
        
        return articles
    
    async def _parse_note_detail(self, crawl_result, note_id: str) -> Optional[Article]:
        """解析笔记详情"""
        try:
            # 优先从JS数据解析
            data = crawl_result.extracted_data.get("data")
            
            if data:
                article_data = {
                    "article_id": note_id,
                    "platform": self.platform_name,
                    "title": self.clean_text(data.get("title", "")),
                    "content": self.clean_text(data.get("content", "")),
                    "author_id": data.get("user", {}).get("userId", ""),
                    "author_name": data.get("user", {}).get("nickname", ""),
                    "view_count": data.get("viewCount", 0),
                    "like_count": data.get("likedCount", 0),
                    "comment_count": data.get("commentCount", 0),
                    "created_at": self._parse_timestamp(data.get("time", 0))
                }
                
                # 提取图片
                images = []
                for img in data.get("imageList", []):
                    if img.get("url"):
                        images.append(img["url"])
                
                # 提取标签
                tags = []
                for tag in data.get("tagList", []):
                    if tag.get("name"):
                        tags.append(tag["name"])
                
                # 如果没有content，使用summary
                if not article_data["content"]:
                    article_data["content"] = article_data.get("summary", "")
                
                return Article(**article_data)
            else:
                # 从HTML提取
                content_elem = crawl_result.extracted_data.get("content")
                if content_elem:
                    return Article(
                        article_id=note_id,
                        platform=self.platform_name,
                        title="",
                        content=self.clean_text(content_elem),
                        author_id="unknown",
                        author_name="",
                        created_at=datetime.utcnow()
                    )
                    
        except Exception as e:
            logger.error(f"Parse note detail error: {e}")
        
        return None
    
    async def _extract_poi_from_article(self, article: Article) -> Optional[POI]:
        """从笔记中提取POI信息"""
        try:
            # 简单实现：如果笔记标题或内容中包含地点信息
            # 实际应该使用NLP或正则提取
            
            # 查找相关POI
            if article.related_pois:
                poi_name = article.related_pois[0]
                
                return POI(
                    poi_id=f"{self.platform_name}_poi_{hashlib.md5(poi_name.encode()).hexdigest()[:8]}",
                    platform=self.platform_name,
                    platform_poi_id=poi_name,
                    name=poi_name,
                    description=f"提取自小红书笔记：{article.title}",
                    review_count=1,
                    raw_data={
                        "source_article_id": article.article_id,
                        "source_article_title": article.title
                    }
                )
                
        except Exception as e:
            logger.error(f"Extract POI from article error: {e}")
        
        return None
    
    def _parse_timestamp(self, timestamp: int) -> datetime:
        """解析时间戳"""
        try:
            # 小红书使用毫秒时间戳
            return datetime.fromtimestamp(timestamp / 1000)
        except:
            return datetime.utcnow()
    
    def _generate_signature(self, url: str, data: Dict = None) -> Dict[str, str]:
        """生成小红书签名（简化版，实际需要逆向工程）"""
        # 实际的签名算法需要通过逆向工程获得
        # 这里只是示例
        timestamp = str(int(datetime.utcnow().timestamp() * 1000))
        
        # 简化的签名生成
        sign_str = f"{url}{timestamp}"
        if data:
            sign_str += json.dumps(data, sort_keys=True)
        
        signature = hashlib.md5(sign_str.encode()).hexdigest()
        
        return {
            "X-S": signature,
            "X-T": timestamp
        }

# 注册适配器
AdapterFactory.register("xiaohongshu", XiaohongshuAdapter)
```

### Task 4.5: 创建平台适配器测试脚本

#### 4.5.1 测试平台适配器
```python
# scripts/test_adapters.py
"""测试平台适配器"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.adapters.base.adapter_factory import AdapterFactory
from src.adapters.base.adapter_interface import SearchQuery
from src.core.engines.base.engine_manager import engine_manager
from src.engines.crawl4ai.engine import Crawl4AIEngine
from src.engines.mediacrawl.engine import MediaCrawlEngine
from src.core.scheduler.coordinator import coordinator
from src.anti_detection.proxy.manager import proxy_manager
from src.anti_detection.fingerprint.manager import fingerprint_manager
from src.utils.logger.logger import get_logger

# 导入适配器
from src.adapters.amap.adapter import AMapAdapter
from src.adapters.mafengwo.adapter import MafengwoAdapter
from src.adapters.xiaohongshu.adapter import XiaohongshuAdapter

logger = get_logger("test.adapters")

async def test_amap_adapter():
    """测试高德地图适配器"""
    logger.info("Testing AMap adapter...")
    
    # 创建适配器
    adapter = AdapterFactory.create("amap", {
        "rate_limit": 2.0,
        "enable_cache": True
    })
    
    if not adapter:
        logger.error("Failed to create AMap adapter")
        return False
    
    # 测试搜索
    query = SearchQuery(
        keyword="故宫",
        city="北京",
        page=1,
        page_size=5
    )
    
    pois = await adapter.search_pois(query)
    logger.info(f"Found {len(pois)} POIs")
    
    if pois:
        # 显示第一个结果
        poi = pois[0]
        logger.info(f"First POI: {poi.name}")
        logger.info(f"  Address: {poi.address}")
        logger.info(f"  Category: {poi.category}")
        logger.info(f"  Rating: {poi.rating}")
        
        # 测试获取详情
        if poi.platform_poi_id:
            detail = await adapter.get_poi_detail(poi.platform_poi_id)
            if detail:
                logger.info(f"✓ Got POI detail: {detail.name}")
            else:
                logger.warning("Failed to get POI detail")
    
    return len(pois) > 0

async def test_mafengwo_adapter():
    """测试马蜂窝适配器"""
    logger.info("Testing Mafengwo adapter...")
    
    # 创建适配器
    adapter = AdapterFactory.create("mafengwo", {
        "rate_limit": 2.0,
        "enable_cache": True,
        "cookies": {}  # 实际使用需要提供cookies
    })
    
    if not adapter:
        logger.error("Failed to create Mafengwo adapter")
        return False
    
    # 测试搜索POI
    query = SearchQuery(
        keyword="外滩",
        city="上海",
        page=1,
        page_size=3
    )
    
    pois = await adapter.search_pois(query)
    logger.info(f"Found {len(pois)} POIs")
    
    # 测试搜索游记
    articles = await adapter.search_articles("上海旅游", page=1)
    logger.info(f"Found {len(articles)} articles")
    
    if articles:
        article = articles[0]
        logger.info(f"First article: {article.title}")
        logger.info(f"  Author: {article.author_name}")
        logger.info(f"  Views: {article.view_count}")
        logger.info(f"  Likes: {article.like_count}")
    
    return len(pois) > 0 or len(articles) > 0

async def test_xiaohongshu_adapter():
    """测试小红书适配器"""
    logger.info("Testing Xiaohongshu adapter...")
    
    # 创建适配器
    adapter = AdapterFactory.create("xiaohongshu", {
        "rate_limit": 3.0,
        "enable_cache": True
    })
    
    if not adapter:
        logger.error("Failed to create Xiaohongshu adapter")
        return False
    
    # 测试搜索笔记
    articles = await adapter.search_articles("北京美食", page=1)
    logger.info(f"Found {len(articles)} notes")
    
    if articles:
        article = articles[0]
        logger.info(f"First note: {article.title or article.summary[:50]}")
        logger.info(f"  Author: {article.author_name}")
        logger.info(f"  Likes: {article.like_count}")
        
        # 尝试获取详情
        if article.article_id:
            detail = await adapter.get_note_detail(article.article_id)
            if detail:
                logger.info(f"✓ Got note detail")
            else:
                logger.warning("Failed to get note detail")
    
    # 测试从笔记提取POI
    query = SearchQuery(keyword="上海迪士尼")
    pois = await adapter.search_pois(query)
    logger.info(f"Extracted {len(pois)} POIs from notes")
    
    return len(articles) > 0

async def test_adapter_integration():
    """测试适配器集成"""
    logger.info("Testing adapter integration...")
    
    # 测试多平台搜索
    keyword = "长城"
    platforms = ["amap", "mafengwo"]
    
    all_results = {}
    
    for platform in platforms:
        adapter = AdapterFactory.create(platform, {"rate_limit": 2.0})
        if adapter:
            query = SearchQuery(keyword=keyword, page=1, page_size=3)
            pois = await adapter.search_pois(query)
            all_results[platform] = len(pois)
            logger.info(f"{platform}: Found {len(pois)} POIs")
    
    # 显示汇总
    logger.info(f"Total results for '{keyword}':")
    for platform, count in all_results.items():
        logger.info(f"  {platform}: {count}")
    
    return sum(all_results.values()) > 0

async def init_systems():
    """初始化系统"""
    # 注册引擎
    engine_manager.register_engine(EngineType.CRAWL4AI, Crawl4AIEngine)
    engine_manager.register_engine(EngineType.MEDIACRAWL, MediaCrawlEngine)
    
    # 初始化引擎
    configs = {
        EngineType.CRAWL4AI: {
            "workers": 2,
            "timeout": 30
        },
        EngineType.MEDIACRAWL: {
            "browser_count": 1,
            "contexts_per_browser": 2,
            "headless": True
        }
    }
    
    await engine_manager.initialize(configs)
    
    # 初始化反爬系统
    await proxy_manager.initialize()
    await fingerprint_manager.initialize()

async def cleanup_systems():
    """清理系统"""
    await proxy_manager.shutdown()
    await engine_manager.shutdown()

async def main():
    """主测试流程"""
    logger.info("Starting adapter tests...")
    
    # 初始化系统
    await init_systems()
    
    try:
        tests = [
            ("AMap Adapter", test_amap_adapter),
            ("Mafengwo Adapter", test_mafengwo_adapter),
            ("Xiaohongshu Adapter", test_xiaohongshu_adapter),
            ("Adapter Integration", test_adapter_integration)
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
            
            # 测试间隔
            await asyncio.sleep(2)
        
        # 输出总结
        logger.info(f"\n{'='*50}")
        logger.info("Test Summary:")
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{test_name}: {status}")
        
        all_passed = all(result for _, result in results)
        if all_passed:
            logger.info("\n✅ All adapter tests passed!")
        else:
            logger.error("\n❌ Some adapter tests failed!")
        
        return all_passed
        
    finally:
        # 清理
        await cleanup_systems()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
```

### 验证步骤汇总

执行以下命令验证Phase 4的实现：

```bash
# 1. 确保所有系统运行正常
docker-compose ps

# 2. 运行适配器测试
poetry run python scripts/test_adapters.py

# 3. 测试单个适配器
poetry run python -c "
import asyncio
from src.adapters.base.adapter_factory import AdapterFactory
from src.adapters.base.adapter_interface import SearchQuery

async def test():
    adapter = AdapterFactory.create('amap', {})
    query = SearchQuery(keyword='颐和园', city='北京')
    pois = await adapter.search_pois(query)
    print(f'Found {len(pois)} POIs')
    for poi in pois[:3]:
        print(f'- {poi.name}: {poi.address}')

asyncio.run(test())
"

# 4. 查看日志
tail -f logs/crawler.log | grep adapter
```

如果测试通过，说明平台适配器已经成功实现！

---

## 下一步

完成Phase 4后，我们将进入Phase 5：实现数据处理和API服务。请确保：
1. 至少3个平台适配器能正常工作
2. 适配器能正确使用双引擎
3. 数据解析正确
4. 反爬系统正常集成

剩余的5个平台（大众点评、携程、抖音、微博、B站）的适配器实现方式类似，主要区别在于：
- 大众点评：需要处理复杂的加密和设备绑定
- 携程：有API但限制严格，需要混合模式
- 抖音：纯动态内容，需要MediaCrawl和特殊处理
- 微博：需要处理登录态和API限制
- B站：视频内容为主，需要处理多媒体数据

准备好后，继续执行第5部分的任务。