# 旅游平台数据爬虫系统 - 项目开发TODO详细指南
## 第5部分：数据处理与API服务

> 本部分实现数据处理管道、去重系统、增强器和对外API服务

---

## Phase 5: 数据处理与API服务（Day 13-15）

### Task 5.1: 实现数据处理管道

#### 5.1.1 数据处理基础模型
```python
# src/processors/base/processor_interface.py
"""数据处理器接口定义"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from src.adapters.base.adapter_interface import POI, Review, Article
from src.utils.logger.logger import get_logger

logger = get_logger("processor.interface")

T = TypeVar('T', bound=BaseModel)

# 处理状态枚举
class ProcessStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

# 处理结果模型
class ProcessResult(BaseModel, Generic[T]):
    """处理结果"""
    status: ProcessStatus = Field(..., description="处理状态")
    input_count: int = Field(..., description="输入数据量")
    output_count: int = Field(..., description="输出数据量")
    processed_count: int = Field(default=0, description="已处理数量")
    failed_count: int = Field(default=0, description="失败数量")
    skipped_count: int = Field(default=0, description="跳过数量")
    
    data: List[T] = Field(default_factory=list, description="处理后的数据")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误信息")
    
    processing_time: float = Field(..., description="处理耗时(秒)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

# 数据处理器基类
class DataProcessor(ABC, Generic[T]):
    """数据处理器抽象基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def process(self, data: List[T]) -> ProcessResult[T]:
        """处理数据"""
        pass
    
    @abstractmethod
    async def validate(self, item: T) -> bool:
        """验证单个数据项"""
        pass
    
    async def process_batch(self, data: List[T], batch_size: int = 100) -> ProcessResult[T]:
        """批量处理数据"""
        start_time = datetime.utcnow()
        result = ProcessResult[T](
            status=ProcessStatus.PROCESSING,
            input_count=len(data),
            output_count=0,
            processing_time=0
        )
        
        try:
            # 分批处理
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                batch_result = await self.process(batch)
                
                # 合并结果
                result.data.extend(batch_result.data)
                result.processed_count += batch_result.processed_count
                result.failed_count += batch_result.failed_count
                result.skipped_count += batch_result.skipped_count
                result.errors.extend(batch_result.errors)
            
            result.output_count = len(result.data)
            result.status = ProcessStatus.COMPLETED
        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            result.status = ProcessStatus.FAILED
            result.errors.append({
                "error": str(e),
                "type": type(e).__name__
            })
        finally:
            result.processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return result
```

#### 5.1.2 数据清洗器实现
```python
# src/processors/cleaner/data_cleaner.py
"""数据清洗器实现"""
import re
import html
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, unquote
import unicodedata

from src.processors.base.processor_interface import DataProcessor, ProcessResult, ProcessStatus
from src.adapters.base.adapter_interface import POI, Review, Article
from src.utils.logger.logger import get_logger

logger = get_logger("data.cleaner")

class TextCleaner:
    """文本清洗工具类"""
    
    @staticmethod
    def clean_html(text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        
        # 解码HTML实体
        text = html.unescape(text)
        
        # 移除script和style标签内容
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """规范化文本"""
        if not text:
            return ""
        
        # Unicode规范化
        text = unicodedata.normalize('NFKC', text)
        
        # 全角转半角
        text = text.translate({
            ord('　'): ord(' '),
            ord('！'): ord('!'),
            ord('？'): ord('?'),
            ord('，'): ord(','),
            ord('。'): ord('.'),
            ord('；'): ord(';'),
            ord('：'): ord(':'),
            ord('''): ord("'"),
            ord('''): ord("'"),
            ord('"'): ord('"'),
            ord('"'): ord('"'),
        })
        
        # 移除零宽字符
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        
        # 移除控制字符
        text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
        
        return text.strip()
    
    @staticmethod
    def clean_url(url: str) -> str:
        """清理URL"""
        if not url:
            return ""
        
        try:
            # 解码URL
            url = unquote(url)
            
            # 解析URL
            parsed = urlparse(url)
            
            # 重建干净的URL
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                # 移除跟踪参数
                params = []
                for param in parsed.query.split('&'):
                    key = param.split('=')[0]
                    if key not in ['utm_source', 'utm_medium', 'utm_campaign', 'fbclid', 'gclid']:
                        params.append(param)
                if params:
                    clean += '?' + '&'.join(params)
            
            return clean
        except Exception:
            return url
    
    @staticmethod
    def clean_phone(phone: str) -> str:
        """清理电话号码"""
        if not phone:
            return ""
        
        # 移除非数字字符
        phone = re.sub(r'[^\d\+\-\(\)\s]', '', phone)
        
        # 规范化格式
        phone = re.sub(r'\s+', ' ', phone)
        
        return phone.strip()

class POICleaner(DataProcessor[POI]):
    """POI数据清洗器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.text_cleaner = TextCleaner()
    
    async def process(self, data: List[POI]) -> ProcessResult[POI]:
        """处理POI数据"""
        result = ProcessResult[POI](
            status=ProcessStatus.PROCESSING,
            input_count=len(data),
            output_count=0,
            processing_time=0
        )
        
        cleaned_data = []
        
        for poi in data:
            try:
                # 验证数据
                if not await self.validate(poi):
                    result.skipped_count += 1
                    continue
                
                # 清洗数据
                cleaned_poi = await self._clean_poi(poi)
                cleaned_data.append(cleaned_poi)
                result.processed_count += 1
                
            except Exception as e:
                result.failed_count += 1
                result.errors.append({
                    "poi_id": poi.poi_id,
                    "error": str(e)
                })
                logger.error(f"Failed to clean POI {poi.poi_id}: {str(e)}")
        
        result.data = cleaned_data
        result.output_count = len(cleaned_data)
        result.status = ProcessStatus.COMPLETED
        
        return result
    
    async def validate(self, item: POI) -> bool:
        """验证POI数据"""
        # 必须有名称和ID
        if not item.name or not item.poi_id:
            return False
        
        # 名称长度检查
        if len(item.name) < 2 or len(item.name) > 100:
            return False
        
        # 坐标范围检查
        if item.latitude:
            if not (-90 <= item.latitude <= 90):
                return False
        
        if item.longitude:
            if not (-180 <= item.longitude <= 180):
                return False
        
        return True
    
    async def _clean_poi(self, poi: POI) -> POI:
        """清洗单个POI"""
        # 复制POI
        cleaned = poi.model_copy()
        
        # 清洗文本字段
        cleaned.name = self.text_cleaner.normalize_text(cleaned.name)
        
        if cleaned.description:
            cleaned.description = self.text_cleaner.clean_html(cleaned.description)
            cleaned.description = self.text_cleaner.normalize_text(cleaned.description)
        
        if cleaned.address:
            cleaned.address = self.text_cleaner.normalize_text(cleaned.address)
        
        # 清洗电话
        if cleaned.phone:
            cleaned.phone = self.text_cleaner.clean_phone(cleaned.phone)
        
        # 清洗URL
        if cleaned.website:
            cleaned.website = self.text_cleaner.clean_url(cleaned.website)
        
        # 清洗图片URL
        if cleaned.cover_image:
            cleaned.cover_image = self.text_cleaner.clean_url(cleaned.cover_image)
        
        cleaned.images = [
            self.text_cleaner.clean_url(img) 
            for img in cleaned.images 
            if img
        ]
        
        # 去重标签
        if cleaned.tags:
            cleaned.tags = list(set(
                self.text_cleaner.normalize_text(tag) 
                for tag in cleaned.tags 
                if tag
            ))
        
        return cleaned

class ReviewCleaner(DataProcessor[Review]):
    """评论数据清洗器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.text_cleaner = TextCleaner()
        self.min_content_length = config.get('min_content_length', 10) if config else 10
        self.max_content_length = config.get('max_content_length', 5000) if config else 5000
    
    async def process(self, data: List[Review]) -> ProcessResult[Review]:
        """处理评论数据"""
        result = ProcessResult[Review](
            status=ProcessStatus.PROCESSING,
            input_count=len(data),
            output_count=0,
            processing_time=0
        )
        
        cleaned_data = []
        
        for review in data:
            try:
                # 验证数据
                if not await self.validate(review):
                    result.skipped_count += 1
                    continue
                
                # 清洗数据
                cleaned_review = await self._clean_review(review)
                cleaned_data.append(cleaned_review)
                result.processed_count += 1
                
            except Exception as e:
                result.failed_count += 1
                result.errors.append({
                    "review_id": review.review_id,
                    "error": str(e)
                })
                logger.error(f"Failed to clean review {review.review_id}: {str(e)}")
        
        result.data = cleaned_data
        result.output_count = len(cleaned_data)
        result.status = ProcessStatus.COMPLETED
        
        return result
    
    async def validate(self, item: Review) -> bool:
        """验证评论数据"""
        # 必须有内容
        if not item.content:
            return False
        
        # 内容长度检查
        if len(item.content) < self.min_content_length:
            return False
        
        if len(item.content) > self.max_content_length:
            return False
        
        # 评分范围检查
        if item.rating is not None:
            if not (0 <= item.rating <= 5):
                return False
        
        return True
    
    async def _clean_review(self, review: Review) -> Review:
        """清洗单个评论"""
        # 复制评论
        cleaned = review.model_copy()
        
        # 清洗内容
        cleaned.content = self.text_cleaner.clean_html(cleaned.content)
        cleaned.content = self.text_cleaner.normalize_text(cleaned.content)
        
        # 清洗标题
        if cleaned.title:
            cleaned.title = self.text_cleaner.normalize_text(cleaned.title)
        
        # 清洗作者信息
        if cleaned.author_name:
            cleaned.author_name = self.text_cleaner.normalize_text(cleaned.author_name)
        
        # 清洗图片URL
        cleaned.images = [
            self.text_cleaner.clean_url(img) 
            for img in cleaned.images 
            if img
        ]
        
        return cleaned
```

#### 5.1.3 数据去重器实现
```python
# src/processors/deduplicator/deduplicator.py
"""数据去重器实现"""
import hashlib
import difflib
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import asyncio
from collections import defaultdict

from src.processors.base.processor_interface import DataProcessor, ProcessResult, ProcessStatus
from src.adapters.base.adapter_interface import POI, Review, Article
from src.database.connection import get_redis_client
from src.utils.logger.logger import get_logger

logger = get_logger("data.deduplicator")

class HashGenerator:
    """哈希生成器"""
    
    @staticmethod
    def generate_hash(data: str) -> str:
        """生成数据哈希"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_poi_hash(poi: POI) -> str:
        """生成POI哈希"""
        # 使用名称+地址+坐标生成唯一标识
        key_parts = [
            poi.name.lower().strip(),
            poi.platform,
        ]
        
        if poi.address:
            key_parts.append(poi.address.lower().strip())
        
        if poi.latitude and poi.longitude:
            key_parts.extend([
                f"{poi.latitude:.6f}",
                f"{poi.longitude:.6f}"
            ])
        
        key = "|".join(key_parts)
        return HashGenerator.generate_hash(key)
    
    @staticmethod
    def generate_review_hash(review: Review) -> str:
        """生成评论哈希"""
        # 使用内容+作者+时间生成唯一标识
        key_parts = [
            review.content[:200],  # 使用前200字符
            review.platform,
        ]
        
        if review.author_id:
            key_parts.append(review.author_id)
        
        if review.created_at:
            key_parts.append(review.created_at.isoformat())
        
        key = "|".join(key_parts)
        return HashGenerator.generate_hash(key)
    
    @staticmethod
    def generate_article_hash(article: Article) -> str:
        """生成文章哈希"""
        # 使用标题+内容摘要生成唯一标识
        key_parts = [
            article.title.lower().strip(),
            article.platform,
        ]
        
        if article.content:
            key_parts.append(article.content[:500])  # 使用前500字符
        
        if article.author_id:
            key_parts.append(article.author_id)
        
        key = "|".join(key_parts)
        return HashGenerator.generate_hash(key)

class SimilarityChecker:
    """相似度检查器"""
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """计算文本相似度"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    @staticmethod
    def is_similar_poi(poi1: POI, poi2: POI, threshold: float = 0.85) -> bool:
        """检查POI是否相似"""
        # 名称相似度
        name_sim = SimilarityChecker.calculate_similarity(
            poi1.name.lower().strip(),
            poi2.name.lower().strip()
        )
        
        if name_sim < threshold:
            return False
        
        # 如果有坐标，检查距离
        if all([poi1.latitude, poi1.longitude, poi2.latitude, poi2.longitude]):
            # 简单的欧氏距离（实际应该用地理距离）
            distance = ((poi1.latitude - poi2.latitude) ** 2 + 
                       (poi1.longitude - poi2.longitude) ** 2) ** 0.5
            
            # 如果距离太远（约100米），不是同一个POI
            if distance > 0.001:
                return False
        
        # 地址相似度
        if poi1.address and poi2.address:
            addr_sim = SimilarityChecker.calculate_similarity(
                poi1.address.lower().strip(),
                poi2.address.lower().strip()
            )
            if addr_sim < 0.7:
                return False
        
        return True
    
    @staticmethod
    def is_similar_review(review1: Review, review2: Review, threshold: float = 0.9) -> bool:
        """检查评论是否相似"""
        # 内容相似度
        content_sim = SimilarityChecker.calculate_similarity(
            review1.content,
            review2.content
        )
        
        return content_sim >= threshold

class Deduplicator(DataProcessor[POI]):
    """通用去重器基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.redis_client = None
        self.hash_generator = HashGenerator()
        self.similarity_checker = SimilarityChecker()
        self.cache_ttl = config.get('cache_ttl', 86400) if config else 86400  # 24小时
        self.similarity_threshold = config.get('similarity_threshold', 0.85) if config else 0.85
    
    async def initialize(self):
        """初始化Redis连接"""
        if not self.redis_client:
            self.redis_client = await get_redis_client()
    
    async def _check_duplicate_by_hash(self, hash_key: str, cache_key: str) -> bool:
        """通过哈希检查是否重复"""
        await self.initialize()
        
        # 检查Redis中是否存在
        exists = await self.redis_client.sismember(cache_key, hash_key)
        
        if not exists:
            # 添加到集合中
            await self.redis_client.sadd(cache_key, hash_key)
            await self.redis_client.expire(cache_key, self.cache_ttl)
        
        return exists
    
    async def _get_similar_items(self, item: Any, cache_key: str) -> List[str]:
        """获取相似项"""
        await self.initialize()
        
        # 从Redis获取所有已存在的项
        existing_hashes = await self.redis_client.smembers(cache_key)
        
        similar_items = []
        for hash_key in existing_hashes:
            # 这里简化处理，实际需要存储更多信息进行相似度比较
            similar_items.append(hash_key)
        
        return similar_items

class POIDeduplicator(Deduplicator):
    """POI去重器"""
    
    async def process(self, data: List[POI]) -> ProcessResult[POI]:
        """处理POI数据去重"""
        result = ProcessResult[POI](
            status=ProcessStatus.PROCESSING,
            input_count=len(data),
            output_count=0,
            processing_time=0
        )
        
        unique_data = []
        seen_hashes = set()
        
        for poi in data:
            try:
                # 生成哈希
                poi_hash = self.hash_generator.generate_poi_hash(poi)
                
                # 本地去重
                if poi_hash in seen_hashes:
                    result.skipped_count += 1
                    continue
                
                # Redis去重
                cache_key = f"poi_dedup:{poi.platform}:{poi.city or 'unknown'}"
                is_duplicate = await self._check_duplicate_by_hash(poi_hash, cache_key)
                
                if is_duplicate:
                    result.skipped_count += 1
                    logger.info(f"Duplicate POI found: {poi.name} ({poi.poi_id})")
                    continue
                
                # 相似度检查（可选，更严格的去重）
                if self.config.get('enable_similarity_check', False):
                    is_similar = await self._check_similarity(poi, unique_data)
                    if is_similar:
                        result.skipped_count += 1
                        continue
                
                seen_hashes.add(poi_hash)
                unique_data.append(poi)
                result.processed_count += 1
                
            except Exception as e:
                result.failed_count += 1
                result.errors.append({
                    "poi_id": poi.poi_id,
                    "error": str(e)
                })
                logger.error(f"Failed to deduplicate POI {poi.poi_id}: {str(e)}")
        
        result.data = unique_data
        result.output_count = len(unique_data)
        result.status = ProcessStatus.COMPLETED
        
        logger.info(f"POI deduplication completed: {result.input_count} -> {result.output_count}")
        
        return result
    
    async def validate(self, item: POI) -> bool:
        """验证POI数据"""
        return bool(item.poi_id and item.name)
    
    async def _check_similarity(self, poi: POI, existing_pois: List[POI]) -> bool:
        """检查POI相似度"""
        for existing in existing_pois:
            if self.similarity_checker.is_similar_poi(
                poi, existing, self.similarity_threshold
            ):
                return True
        return False

class ReviewDeduplicator(Deduplicator):
    """评论去重器"""
    
    async def process(self, data: List[Review]) -> ProcessResult[Review]:
        """处理评论数据去重"""
        result = ProcessResult[Review](
            status=ProcessStatus.PROCESSING,
            input_count=len(data),
            output_count=0,
            processing_time=0
        )
        
        unique_data = []
        seen_hashes = set()
        
        # 按POI分组处理
        poi_reviews = defaultdict(list)
        for review in data:
            poi_reviews[review.poi_id].append(review)
        
        for poi_id, reviews in poi_reviews.items():
            cache_key = f"review_dedup:{reviews[0].platform}:{poi_id}"
            
            for review in reviews:
                try:
                    # 生成哈希
                    review_hash = self.hash_generator.generate_review_hash(review)
                    
                    # 本地去重
                    if review_hash in seen_hashes:
                        result.skipped_count += 1
                        continue
                    
                    # Redis去重
                    is_duplicate = await self._check_duplicate_by_hash(review_hash, cache_key)
                    
                    if is_duplicate:
                        result.skipped_count += 1
                        logger.info(f"Duplicate review found: {review.review_id}")
                        continue
                    
                    seen_hashes.add(review_hash)
                    unique_data.append(review)
                    result.processed_count += 1
                    
                except Exception as e:
                    result.failed_count += 1
                    result.errors.append({
                        "review_id": review.review_id,
                        "error": str(e)
                    })
                    logger.error(f"Failed to deduplicate review {review.review_id}: {str(e)}")
        
        result.data = unique_data
        result.output_count = len(unique_data)
        result.status = ProcessStatus.COMPLETED
        
        logger.info(f"Review deduplication completed: {result.input_count} -> {result.output_count}")
        
        return result
    
    async def validate(self, item: Review) -> bool:
        """验证评论数据"""
        return bool(item.review_id and item.content and item.poi_id)
```

### Task 5.2: 实现数据增强器

#### 5.2.1 数据增强器实现
```python
# src/processors/enhancer/data_enhancer.py
"""数据增强器实现"""
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from src.processors.base.processor_interface import DataProcessor, ProcessResult, ProcessStatus
from src.adapters.base.adapter_interface import POI, Review, Article
from src.utils.logger.logger import get_logger

logger = get_logger("data.enhancer")

class GeoEnhancer:
    """地理信息增强器"""
    
    def __init__(self):
        self.geocoding_api = "https://restapi.amap.com/v3/geocode/geo"
        self.reverse_geocoding_api = "https://restapi.amap.com/v3/geocode/regeo"
        self.api_key = None  # 需要配置
    
    async def enhance_with_coordinates(self, address: str, city: str = None) -> Optional[Dict[str, float]]:
        """通过地址获取坐标"""
        if not self.api_key or not address:
            return None
        
        params = {
            "key": self.api_key,
            "address": address,
            "output": "json"
        }
        
        if city:
            params["city"] = city
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.geocoding_api, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("geocodes"):
                            location = data["geocodes"][0]["location"].split(",")
                            return {
                                "longitude": float(location[0]),
                                "latitude": float(location[1])
                            }
        except Exception as e:
            logger.error(f"Failed to get coordinates for {address}: {str(e)}")
        
        return None
    
    async def enhance_with_address(self, latitude: float, longitude: float) -> Optional[Dict[str, str]]:
        """通过坐标获取地址"""
        if not self.api_key:
            return None
        
        params = {
            "key": self.api_key,
            "location": f"{longitude},{latitude}",
            "output": "json",
            "extensions": "all"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.reverse_geocoding_api, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("regeocode"):
                            regeocode = data["regeocode"]
                            address_component = regeocode.get("addressComponent", {})
                            
                            return {
                                "address": regeocode.get("formatted_address", ""),
                                "province": address_component.get("province", ""),
                                "city": address_component.get("city", ""),
                                "district": address_component.get("district", ""),
                                "township": address_component.get("township", ""),
                                "street": address_component.get("streetNumber", {}).get("street", ""),
                                "number": address_component.get("streetNumber", {}).get("number", "")
                            }
        except Exception as e:
            logger.error(f"Failed to get address for ({latitude}, {longitude}): {str(e)}")
        
        return None

class CategoryEnhancer:
    """分类增强器"""
    
    def __init__(self):
        # 分类映射表
        self.category_mapping = {
            # 餐饮
            "餐厅": ["美食", "餐饮"],
            "饭店": ["美食", "餐饮"],
            "火锅": ["美食", "餐饮", "火锅"],
            "烧烤": ["美食", "餐饮", "烧烤"],
            "咖啡": ["美食", "饮品", "咖啡厅"],
            "奶茶": ["美食", "饮品"],
            
            # 住宿
            "酒店": ["住宿", "酒店"],
            "民宿": ["住宿", "民宿"],
            "客栈": ["住宿", "客栈"],
            "青旅": ["住宿", "青年旅社"],
            
            # 景点
            "景区": ["景点", "旅游"],
            "公园": ["景点", "公园"],
            "博物馆": ["景点", "文化", "博物馆"],
            "寺庙": ["景点", "宗教", "寺庙"],
            
            # 购物
            "商场": ["购物", "商场"],
            "超市": ["购物", "超市"],
            "市场": ["购物", "市场"],
            
            # 娱乐
            "KTV": ["娱乐", "KTV"],
            "电影院": ["娱乐", "电影"],
            "游乐园": ["娱乐", "游乐园"]
        }
    
    def enhance_category(self, name: str, category: str = None) -> List[str]:
        """增强分类标签"""
        tags = []
        
        # 从现有分类提取
        if category:
            tags.append(category)
        
        # 从名称提取
        name_lower = name.lower()
        for keyword, category_tags in self.category_mapping.items():
            if keyword in name_lower:
                tags.extend(category_tags)
        
        # 去重并返回
        return list(set(tags))

class SentimentAnalyzer:
    """情感分析器"""
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析文本情感"""
        # 简单的基于关键词的情感分析
        positive_words = ["好", "棒", "赞", "优秀", "推荐", "满意", "不错", "很好", "完美", "喜欢"]
        negative_words = ["差", "糟", "烂", "失望", "不好", "垃圾", "坑", "骗", "难吃", "贵"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total = positive_count + negative_count
        if total == 0:
            sentiment = "neutral"
            score = 0.5
        else:
            score = positive_count / total
            if score > 0.6:
                sentiment = "positive"
            elif score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": score,
            "positive_count": positive_count,
            "negative_count": negative_count
        }

class POIEnhancer(DataProcessor[POI]):
    """POI数据增强器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.geo_enhancer = GeoEnhancer()
        self.category_enhancer = CategoryEnhancer()
        
        # 配置API密钥
        if config and config.get('amap_api_key'):
            self.geo_enhancer.api_key = config['amap_api_key']
    
    async def process(self, data: List[POI]) -> ProcessResult[POI]:
        """处理POI数据增强"""
        result = ProcessResult[POI](
            status=ProcessStatus.PROCESSING,
            input_count=len(data),
            output_count=0,
            processing_time=0
        )
        
        enhanced_data = []
        
        # 批量处理，避免过多并发请求
        batch_size = 10
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_tasks = [self._enhance_poi(poi) for poi in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for poi, enhanced in zip(batch, batch_results):
                if isinstance(enhanced, Exception):
                    result.failed_count += 1
                    result.errors.append({
                        "poi_id": poi.poi_id,
                        "error": str(enhanced)
                    })
                    enhanced_data.append(poi)  # 保留原始数据
                else:
                    enhanced_data.append(enhanced)
                    result.processed_count += 1
        
        result.data = enhanced_data
        result.output_count = len(enhanced_data)
        result.status = ProcessStatus.COMPLETED
        
        return result
    
    async def validate(self, item: POI) -> bool:
        """验证POI数据"""
        return bool(item.poi_id and item.name)
    
    async def _enhance_poi(self, poi: POI) -> POI:
        """增强单个POI"""
        enhanced = poi.model_copy()
        
        # 地理信息增强
        if not enhanced.latitude or not enhanced.longitude:
            # 通过地址获取坐标
            if enhanced.address:
                coords = await self.geo_enhancer.enhance_with_coordinates(
                    enhanced.address, enhanced.city
                )
                if coords:
                    enhanced.latitude = coords["latitude"]
                    enhanced.longitude = coords["longitude"]
                    logger.info(f"Enhanced POI {poi.name} with coordinates")
        
        elif not enhanced.address:
            # 通过坐标获取地址
            addr_info = await self.geo_enhancer.enhance_with_address(
                enhanced.latitude, enhanced.longitude
            )
            if addr_info:
                enhanced.address = addr_info["address"]
                enhanced.city = enhanced.city or addr_info["city"]
                enhanced.district = enhanced.district or addr_info["district"]
                logger.info(f"Enhanced POI {poi.name} with address")
        
        # 分类标签增强
        enhanced_tags = self.category_enhancer.enhance_category(
            enhanced.name, enhanced.category
        )
        if enhanced_tags:
            enhanced.tags = list(set(enhanced.tags + enhanced_tags))
        
        # 评分标准化（统一到0-5分）
        if enhanced.rating:
            if enhanced.rating > 5:
                enhanced.rating = enhanced.rating / 2  # 假设是10分制
            elif enhanced.rating < 0:
                enhanced.rating = 0
        
        # 更新时间戳
        enhanced.updated_at = datetime.utcnow()
        
        return enhanced

class ReviewEnhancer(DataProcessor[Review]):
    """评论数据增强器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.sentiment_analyzer = SentimentAnalyzer()
    
    async def process(self, data: List[Review]) -> ProcessResult[Review]:
        """处理评论数据增强"""
        result = ProcessResult[Review](
            status=ProcessStatus.PROCESSING,
            input_count=len(data),
            output_count=0,
            processing_time=0
        )
        
        enhanced_data = []
        
        for review in data:
            try:
                enhanced = await self._enhance_review(review)
                enhanced_data.append(enhanced)
                result.processed_count += 1
            except Exception as e:
                result.failed_count += 1
                result.errors.append({
                    "review_id": review.review_id,
                    "error": str(e)
                })
                enhanced_data.append(review)  # 保留原始数据
        
        result.data = enhanced_data
        result.output_count = len(enhanced_data)
        result.status = ProcessStatus.COMPLETED
        
        return result
    
    async def validate(self, item: Review) -> bool:
        """验证评论数据"""
        return bool(item.review_id and item.content)
    
    async def _enhance_review(self, review: Review) -> Review:
        """增强单个评论"""
        enhanced = review.model_copy()
        
        # 情感分析
        sentiment_result = self.sentiment_analyzer.analyze_sentiment(enhanced.content)
        enhanced.sentiment = sentiment_result["sentiment"]
        enhanced.sentiment_score = sentiment_result["score"]
        
        # 评分推断（如果没有评分）
        if enhanced.rating is None and enhanced.sentiment:
            if enhanced.sentiment == "positive":
                enhanced.rating = 4.5
            elif enhanced.sentiment == "negative":
                enhanced.rating = 2.0
            else:
                enhanced.rating = 3.0
        
        # 内容长度分类
        content_length = len(enhanced.content)
        if content_length < 50:
            enhanced.review_type = "short"
        elif content_length < 200:
            enhanced.review_type = "medium"
        else:
            enhanced.review_type = "long"
        
        # 添加内容质量标记
        if content_length > 100 and enhanced.images:
            enhanced.quality_score = 0.9  # 高质量评论
        elif content_length > 50:
            enhanced.quality_score = 0.7  # 中等质量
        else:
            enhanced.quality_score = 0.5  # 低质量
        
        # 更新时间戳
        enhanced.updated_at = datetime.utcnow()
        
        return enhanced
```

### Task 5.3: 实现API服务层

#### 5.3.1 API路由实现
```python
# src/api/v1/endpoints/crawler.py
"""爬虫API端点"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.rate_limit import rate_limit
from src.core.scheduler.task_queue import TaskQueue
from src.core.scheduler.coordinator import coordinator
from src.adapters.factory import adapter_factory
from src.models.schemas import (
    CrawlTaskCreate, CrawlTaskResponse, CrawlTaskStatus,
    SearchRequest, SearchResponse,
    POIResponse, ReviewResponse, ArticleResponse
)
from src.utils.logger.logger import get_logger

logger = get_logger("api.crawler")
router = APIRouter()

# 任务队列
task_queue = TaskQueue()

@router.post("/tasks", response_model=CrawlTaskResponse)
@rate_limit(calls=10, period=60)
async def create_crawl_task(
    task: CrawlTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """创建爬取任务"""
    try:
        # 验证平台
        if task.platform not in adapter_factory.get_supported_platforms():
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform: {task.platform}"
            )
        
        # 创建任务
        task_id = await task_queue.create_task(
            platform=task.platform,
            task_type=task.task_type,
            config=task.config,
            user_id=current_user["user_id"]
        )
        
        # 后台执行任务
        background_tasks.add_task(
            coordinator.execute_task,
            task_id
        )
        
        return CrawlTaskResponse(
            task_id=task_id,
            status=CrawlTaskStatus.PENDING,
            created_at=datetime.utcnow(),
            message="Task created successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}", response_model=CrawlTaskResponse)
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取任务状态"""
    try:
        task = await task_queue.get_task(task_id)
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found: {task_id}"
            )
        
        # 权限检查
        if task["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        
        return CrawlTaskResponse(
            task_id=task_id,
            status=task["status"],
            created_at=task["created_at"],
            updated_at=task["updated_at"],
            progress=task.get("progress", 0),
            result=task.get("result"),
            error=task.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """取消任务"""
    try:
        task = await task_queue.get_task(task_id)
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found: {task_id}"
            )
        
        # 权限检查
        if task["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        
        # 取消任务
        await task_queue.cancel_task(task_id)
        
        return JSONResponse(
            content={"message": "Task cancelled successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchResponse)
@rate_limit(calls=30, period=60)
async def search_pois(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """搜索POI"""
    try:
        # 获取适配器
        adapter = adapter_factory.get_adapter(request.platform)
        
        if not adapter:
            raise HTTPException(
                status_code=400,
                detail=f"Platform not available: {request.platform}"
            )
        
        # 执行搜索
        search_query = request.to_search_query()
        pois = await adapter.search_pois(search_query)
        
        # 转换响应
        return SearchResponse(
            platform=request.platform,
            keyword=request.keyword,
            total=len(pois),
            page=request.page,
            page_size=request.page_size,
            data=[POIResponse.from_poi(poi) for poi in pois]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pois/{platform}/{poi_id}", response_model=POIResponse)
@rate_limit(calls=60, period=60)
async def get_poi_detail(
    platform: str,
    poi_id: str,
    include_reviews: bool = Query(False, description="是否包含评论"),
    review_limit: int = Query(10, ge=1, le=50, description="评论数量限制"),
    current_user: dict = Depends(get_current_user)
):
    """获取POI详情"""
    try:
        # 获取适配器
        adapter = adapter_factory.get_adapter(platform)
        
        if not adapter:
            raise HTTPException(
                status_code=400,
                detail=f"Platform not available: {platform}"
            )
        
        # 获取POI详情
        poi = await adapter.get_poi_detail(poi_id)
        
        if not poi:
            raise HTTPException(
                status_code=404,
                detail=f"POI not found: {poi_id}"
            )
        
        response = POIResponse.from_poi(poi)
        
        # 获取评论
        if include_reviews:
            reviews = await adapter.get_poi_reviews(
                poi_id, 
                limit=review_limit
            )
            response.reviews = [
                ReviewResponse.from_review(review) 
                for review in reviews
            ]
            response.review_count = len(reviews)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get POI detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms", response_model=List[Dict[str, Any]])
async def get_platforms():
    """获取支持的平台列表"""
    platforms = []
    
    for platform_id in adapter_factory.get_supported_platforms():
        adapter = adapter_factory.get_adapter(platform_id)
        platforms.append({
            "id": platform_id,
            "name": adapter.platform_name,
            "supported_types": adapter.supported_types,
            "features": adapter.get_features(),
            "status": "active"
        })
    
    return platforms

@router.get("/stats")
@rate_limit(calls=10, period=60)
async def get_crawler_stats(
    platform: Optional[str] = Query(None, description="平台筛选"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: dict = Depends(get_current_user)
):
    """获取爬虫统计信息"""
    try:
        stats = await coordinator.get_statistics(
            platform=platform,
            days=days
        )
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 5.3.2 数据API端点
```python
# src/api/v1/endpoints/data.py
"""数据API端点"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
import csv
import io
import json

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.database import get_db
from src.models.database import POI as POIModel, Review as ReviewModel
from src.models.schemas import (
    POIResponse, ReviewResponse, ArticleResponse,
    DataExportRequest, DataStatistics
)
from src.utils.logger.logger import get_logger
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("api.data")
router = APIRouter()

@router.get("/pois", response_model=List[POIResponse])
async def list_pois(
    platform: Optional[str] = Query(None, description="平台筛选"),
    city: Optional[str] = Query(None, description="城市筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="最低评分"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("updated_at", description="排序字段"),
    order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取POI列表"""
    try:
        # 构建查询
        query = select(POIModel)
        
        # 应用过滤条件
        filters = []
        if platform:
            filters.append(POIModel.platform == platform)
        if city:
            filters.append(POIModel.city == city)
        if category:
            filters.append(POIModel.category == category)
        if keyword:
            filters.append(
                or_(
                    POIModel.name.ilike(f"%{keyword}%"),
                    POIModel.description.ilike(f"%{keyword}%")
                )
            )
        if min_rating is not None:
            filters.append(POIModel.rating >= min_rating)
        
        if filters:
            query = query.where(and_(*filters))
        
        # 排序
        order_column = getattr(POIModel, sort_by, POIModel.updated_at)
        if order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 执行查询
        result = await db.execute(query)
        pois = result.scalars().all()
        
        return [POIResponse.from_orm(poi) for poi in pois]
        
    except Exception as e:
        logger.error(f"Failed to list POIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reviews", response_model=List[ReviewResponse])
async def list_reviews(
    platform: Optional[str] = Query(None, description="平台筛选"),
    poi_id: Optional[str] = Query(None, description="POI ID筛选"),
    author_id: Optional[str] = Query(None, description="作者ID筛选"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="最低评分"),
    sentiment: Optional[str] = Query(None, regex="^(positive|negative|neutral)$", description="情感筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取评论列表"""
    try:
        # 构建查询
        query = select(ReviewModel)
        
        # 应用过滤条件
        filters = []
        if platform:
            filters.append(ReviewModel.platform == platform)
        if poi_id:
            filters.append(ReviewModel.poi_id == poi_id)
        if author_id:
            filters.append(ReviewModel.author_id == author_id)
        if min_rating is not None:
            filters.append(ReviewModel.rating >= min_rating)
        if sentiment:
            filters.append(ReviewModel.sentiment == sentiment)
        if start_date:
            filters.append(ReviewModel.created_at >= start_date)
        if end_date:
            filters.append(ReviewModel.created_at <= end_date)
        
        if filters:
            query = query.where(and_(*filters))
        
        # 排序（按时间倒序）
        query = query.order_by(ReviewModel.created_at.desc())
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 执行查询
        result = await db.execute(query)
        reviews = result.scalars().all()
        
        return [ReviewResponse.from_orm(review) for review in reviews]
        
    except Exception as e:
        logger.error(f"Failed to list reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", response_model=DataStatistics)
async def get_data_statistics(
    platform: Optional[str] = Query(None, description="平台筛选"),
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取数据统计"""
    try:
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 基础过滤条件
        time_filter = and_(
            POIModel.created_at >= start_date,
            POIModel.created_at <= end_date
        )
        
        if platform:
            platform_filter = POIModel.platform == platform
            filters = and_(time_filter, platform_filter)
        else:
            filters = time_filter
        
        # POI统计
        poi_count = await db.scalar(
            select(func.count(POIModel.id)).where(filters)
        )
        
        # 评论统计
        review_filters = and_(
            ReviewModel.created_at >= start_date,
            ReviewModel.created_at <= end_date
        )
        if platform:
            review_filters = and_(review_filters, ReviewModel.platform == platform)
        
        review_count = await db.scalar(
            select(func.count(ReviewModel.id)).where(review_filters)
        )
        
        # 平台分布
        platform_stats = await db.execute(
            select(
                POIModel.platform,
                func.count(POIModel.id).label("count")
            ).where(time_filter).group_by(POIModel.platform)
        )
        
        platform_distribution = {
            row.platform: row.count 
            for row in platform_stats
        }
        
        # 城市分布（前10）
        city_stats = await db.execute(
            select(
                POIModel.city,
                func.count(POIModel.id).label("count")
            ).where(filters).group_by(POIModel.city)
            .order_by(func.count(POIModel.id).desc())
            .limit(10)
        )
        
        city_distribution = {
            row.city: row.count 
            for row in city_stats
            if row.city
        }
        
        # 每日趋势
        daily_stats = await db.execute(
            select(
                func.date(POIModel.created_at).label("date"),
                func.count(POIModel.id).label("count")
            ).where(filters)
            .group_by(func.date(POIModel.created_at))
            .order_by(func.date(POIModel.created_at))
        )
        
        daily_trend = [
            {
                "date": row.date.isoformat(),
                "count": row.count
            }
            for row in daily_stats
        ]
        
        return DataStatistics(
            total_pois=poi_count,
            total_reviews=review_count,
            platform_distribution=platform_distribution,
            city_distribution=city_distribution,
            daily_trend=daily_trend,
            time_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_data(
    request: DataExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """导出数据"""
    try:
        # 根据数据类型查询
        if request.data_type == "poi":
            query = select(POIModel)
            
            # 应用过滤
            filters = []
            if request.filters.get("platform"):
                filters.append(POIModel.platform == request.filters["platform"])
            if request.filters.get("city"):
                filters.append(POIModel.city == request.filters["city"])
            if request.filters.get("start_date"):
                filters.append(POIModel.created_at >= request.filters["start_date"])
            if request.filters.get("end_date"):
                filters.append(POIModel.created_at <= request.filters["end_date"])
            
            if filters:
                query = query.where(and_(*filters))
            
            result = await db.execute(query.limit(request.limit))
            data = result.scalars().all()
            
        elif request.data_type == "review":
            query = select(ReviewModel)
            
            # 应用过滤
            filters = []
            if request.filters.get("platform"):
                filters.append(ReviewModel.platform == request.filters["platform"])
            if request.filters.get("poi_id"):
                filters.append(ReviewModel.poi_id == request.filters["poi_id"])
            if request.filters.get("start_date"):
                filters.append(ReviewModel.created_at >= request.filters["start_date"])
            if request.filters.get("end_date"):
                filters.append(ReviewModel.created_at <= request.filters["end_date"])
            
            if filters:
                query = query.where(and_(*filters))
            
            result = await db.execute(query.limit(request.limit))
            data = result.scalars().all()
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported data type: {request.data_type}"
            )
        
        # 根据格式导出
        if request.format == "csv":
            return _export_csv(data, request.data_type)
        elif request.format == "json":
            return _export_json(data, request.data_type)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {request.format}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _export_csv(data: List[Any], data_type: str) -> StreamingResponse:
    """导出CSV格式"""
    output = io.StringIO()
    
    if data_type == "poi":
        fieldnames = [
            "poi_id", "name", "platform", "city", "address",
            "latitude", "longitude", "rating", "review_count",
            "category", "tags", "created_at"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for poi in data:
            writer.writerow({
                "poi_id": poi.poi_id,
                "name": poi.name,
                "platform": poi.platform,
                "city": poi.city,
                "address": poi.address,
                "latitude": poi.latitude,
                "longitude": poi.longitude,
                "rating": poi.rating,
                "review_count": poi.review_count,
                "category": poi.category,
                "tags": ",".join(poi.tags) if poi.tags else "",
                "created_at": poi.created_at.isoformat()
            })
            
    elif data_type == "review":
        fieldnames = [
            "review_id", "poi_id", "platform", "rating",
            "content", "author_name", "sentiment", "created_at"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for review in data:
            writer.writerow({
                "review_id": review.review_id,
                "poi_id": review.poi_id,
                "platform": review.platform,
                "rating": review.rating,
                "content": review.content,
                "author_name": review.author_name,
                "sentiment": review.sentiment,
                "created_at": review.created_at.isoformat()
            })
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

def _export_json(data: List[Any], data_type: str) -> StreamingResponse:
    """导出JSON格式"""
    if data_type == "poi":
        export_data = [
            {
                "poi_id": poi.poi_id,
                "name": poi.name,
                "platform": poi.platform,
                "city": poi.city,
                "address": poi.address,
                "location": {
                    "latitude": poi.latitude,
                    "longitude": poi.longitude
                },
                "rating": poi.rating,
                "review_count": poi.review_count,
                "category": poi.category,
                "tags": poi.tags,
                "created_at": poi.created_at.isoformat(),
                "updated_at": poi.updated_at.isoformat()
            }
            for poi in data
        ]
    elif data_type == "review":
        export_data = [
            {
                "review_id": review.review_id,
                "poi_id": review.poi_id,
                "platform": review.platform,
                "rating": review.rating,
                "content": review.content,
                "author": {
                    "id": review.author_id,
                    "name": review.author_name
                },
                "sentiment": review.sentiment,
                "images": review.images,
                "created_at": review.created_at.isoformat()
            }
            for review in data
        ]
    
    json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    return StreamingResponse(
        io.BytesIO(json_data.encode('utf-8')),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )
```

### Task 5.4: 实现管道验证脚本

#### 5.4.1 数据处理管道验证
```python
# scripts/test/test_data_pipeline.py
"""数据处理管道测试脚本"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.processors.cleaner.data_cleaner import POICleaner, ReviewCleaner
from src.processors.deduplicator.deduplicator import POIDeduplicator, ReviewDeduplicator
from src.processors.enhancer.data_enhancer import POIEnhancer, ReviewEnhancer
from src.adapters.base.adapter_interface import POI, Review
from src.utils.logger.logger import get_logger
from datetime import datetime

logger = get_logger("test.pipeline")

async def test_poi_pipeline():
    """测试POI处理管道"""
    logger.info("Testing POI processing pipeline...")
    
    # 创建测试数据
    test_pois = [
        POI(
            poi_id="test_001",
            platform="amap",
            platform_poi_id="B001",
            name="测试餐厅",
            address="北京市朝阳区测试路1号",
            city="北京",
            category="餐饮",
            rating=4.5,
            review_count=100
        ),
        POI(
            poi_id="test_002",
            platform="amap",
            platform_poi_id="B002",
            name="测试餐厅",  # 重复名称
            address="北京市朝阳区测试路1号",  # 重复地址
            city="北京",
            category="餐饮",
            rating=4.3,
            review_count=80
        ),
        POI(
            poi_id="test_003",
            platform="amap",
            platform_poi_id="B003",
            name="<b>测试酒店</b>",  # 需要清洗的HTML
            address="上海市浦东新区测试大道99号",
            city="上海",
            rating=4.8,
            review_count=200
        )
    ]
    
    # 1. 数据清洗
    logger.info("Step 1: Data cleaning")
    cleaner = POICleaner()
    clean_result = await cleaner.process(test_pois)
    logger.info(f"Cleaned: {clean_result.input_count} -> {clean_result.output_count}")
    
    # 2. 数据去重
    logger.info("Step 2: Data deduplication")
    deduplicator = POIDeduplicator()
    dedup_result = await deduplicator.process(clean_result.data)
    logger.info(f"Deduplicated: {dedup_result.input_count} -> {dedup_result.output_count}")
    
    # 3. 数据增强
    logger.info("Step 3: Data enhancement")
    enhancer = POIEnhancer()
    enhance_result = await enhancer.process(dedup_result.data)
    logger.info(f"Enhanced: {enhance_result.input_count} -> {enhance_result.output_count}")
    
    # 显示最终结果
    logger.info("\nFinal POIs:")
    for poi in enhance_result.data:
        logger.info(f"- {poi.name} ({poi.poi_id})")
        logger.info(f"  Address: {poi.address}")
        logger.info(f"  Tags: {poi.tags}")
        logger.info(f"  Location: ({poi.latitude}, {poi.longitude})")

async def test_review_pipeline():
    """测试评论处理管道"""
    logger.info("\nTesting Review processing pipeline...")
    
    # 创建测试数据
    test_reviews = [
        Review(
            review_id="r001",
            poi_id="test_001",
            platform="amap",
            platform_review_id="R001",
            content="这家餐厅真的很棒！环境优雅，服务态度好，菜品美味。强烈推荐！",
            rating=5.0,
            author_id="u001",
            author_name="测试用户1",
            created_at=datetime.utcnow()
        ),
        Review(
            review_id="r002",
            poi_id="test_001",
            platform="amap",
            platform_review_id="R002",
            content="<p>食物一般般，价格偏贵，性价比不高。</p>",  # 需要清洗的HTML
            rating=2.5,
            author_id="u002",
            author_name="测试用户2",
            created_at=datetime.utcnow()
        ),
        Review(
            review_id="r003",
            poi_id="test_001",
            platform="amap",
            platform_review_id="R003",
            content="还不错",  # 短评论
            rating=3.5,
            author_id="u003",
            author_name="测试用户3",
            created_at=datetime.utcnow()
        )
    ]
    
    # 1. 数据清洗
    logger.info("Step 1: Data cleaning")
    cleaner = ReviewCleaner()
    clean_result = await cleaner.process(test_reviews)
    logger.info(f"Cleaned: {clean_result.input_count} -> {clean_result.output_count}")
    
    # 2. 数据去重
    logger.info("Step 2: Data deduplication")
    deduplicator = ReviewDeduplicator()
    dedup_result = await deduplicator.process(clean_result.data)
    logger.info(f"Deduplicated: {dedup_result.input_count} -> {dedup_result.output_count}")
    
    # 3. 数据增强
    logger.info("Step 3: Data enhancement")
    enhancer = ReviewEnhancer()
    enhance_result = await enhancer.process(dedup_result.data)
    logger.info(f"Enhanced: {enhance_result.input_count} -> {enhance_result.output_count}")
    
    # 显示最终结果
    logger.info("\nFinal Reviews:")
    for review in enhance_result.data:
        logger.info(f"- Review {review.review_id}")
        logger.info(f"  Content: {review.content[:50]}...")
        logger.info(f"  Sentiment: {review.sentiment} (score: {review.sentiment_score})")
        logger.info(f"  Quality: {review.quality_score}")

async def main():
    """主测试函数"""
    try:
        # 测试POI管道
        await test_poi_pipeline()
        
        # 测试评论管道
        await test_review_pipeline()
        
        logger.info("\n✅ All pipeline tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

#### 5.4.2 API服务验证
```python
# scripts/test/test_api_service.py
"""API服务测试脚本"""
import asyncio
import httpx
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger.logger import get_logger

logger = get_logger("test.api")

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 测试用户凭证
TEST_USER = {
    "username": "test_user",
    "password": "test_password"
}

async def get_auth_token():
    """获取认证令牌"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            logger.error(f"Failed to login: {response.text}")
            return None

async def test_crawler_endpoints(token: str):
    """测试爬虫API端点"""
    logger.info("Testing crawler endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. 获取支持的平台
        logger.info("1. Get supported platforms")
        response = await client.get(
            f"{BASE_URL}/crawler/platforms",
            headers=headers
        )
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            platforms = response.json()
            logger.info(f"Platforms: {[p['id'] for p in platforms]}")
        
        # 2. 创建爬取任务
        logger.info("\n2. Create crawl task")
        task_data = {
            "platform": "amap",
            "task_type": "search",
            "config": {
                "keyword": "北京烤鸭",
                "city": "北京",
                "page_size": 10
            }
        }
        
        response = await client.post(
            f"{BASE_URL}/crawler/tasks",
            json=task_data,
            headers=headers
        )
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            task = response.json()
            task_id = task["task_id"]
            logger.info(f"Task created: {task_id}")
            
            # 3. 获取任务状态
            await asyncio.sleep(2)  # 等待任务执行
            
            logger.info("\n3. Get task status")
            response = await client.get(
                f"{BASE_URL}/crawler/tasks/{task_id}",
                headers=headers
            )
            logger.info(f"Status: {response.status_code}")
            if response.status_code == 200:
                status = response.json()
                logger.info(f"Task status: {status['status']}")
        
        # 4. 搜索POI
        logger.info("\n4. Search POIs")
        search_data = {
            "platform": "amap",
            "keyword": "故宫",
            "city": "北京",
            "page": 1,
            "page_size": 5
        }
        
        response = await client.post(
            f"{BASE_URL}/crawler/search",
            json=search_data,
            headers=headers
        )
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Found {result['total']} POIs")

async def test_data_endpoints(token: str):
    """测试数据API端点"""
    logger.info("\nTesting data endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. 获取POI列表
        logger.info("1. Get POI list")
        response = await client.get(
            f"{BASE_URL}/data/pois",
            params={
                "city": "北京",
                "page": 1,
                "page_size": 10
            },
            headers=headers
        )
        logger.info(f"Status: {response.status_code}")
        
        # 2. 获取数据统计
        logger.info("\n2. Get data statistics")
        response = await client.get(
            f"{BASE_URL}/data/statistics",
            params={"days": 7},
            headers=headers
        )
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            logger.info(f"Total POIs: {stats['total_pois']}")
            logger.info(f"Total Reviews: {stats['total_reviews']}")
        
        # 3. 导出数据
        logger.info("\n3. Export data")
        export_data = {
            "data_type": "poi",
            "format": "json",
            "filters": {
                "platform": "amap",
                "city": "北京"
            },
            "limit": 100
        }
        
        response = await client.post(
            f"{BASE_URL}/data/export",
            json=export_data,
            headers=headers
        )
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            logger.info("Export successful")

async def test_health_check():
    """测试健康检查端点"""
    logger.info("Testing health check...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        logger.info(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            health = response.json()
            logger.info(f"Health: {health}")

async def main():
    """主测试函数"""
    try:
        # 健康检查
        await test_health_check()
        
        # 获取认证令牌
        logger.info("\nGetting auth token...")
        token = await get_auth_token()
        
        if not token:
            logger.error("Failed to get auth token")
            return
        
        logger.info("Auth token obtained")
        
        # 测试爬虫端点
        await test_crawler_endpoints(token)
        
        # 测试数据端点
        await test_data_endpoints(token)
        
        logger.info("\n✅ All API tests completed!")
        
    except Exception as e:
        logger.error(f"❌ API test failed: {str(e)}")
        raise

if __name__ == "__main__":
    # 确保API服务正在运行
    logger.info("Make sure the API service is running on http://localhost:8000")
    logger.info("Starting API tests in 3 seconds...")
    asyncio.run(asyncio.sleep(3))
    
    asyncio.run(main())
```

---

## 执行验证

### Claude Code执行步骤：

1. **验证数据处理管道**：
```bash
cd /Users/xiao/Documents/BaiduNetSyncDownload/CodeDev/CrawlPOIData/travel-crawler-system
python scripts/test/test_data_pipeline.py
```

预期输出：
- POI清洗、去重、增强成功
- 评论清洗、去重、增强成功
- 显示处理后的数据样例

2. **启动API服务**：
```bash
# 在一个终端中
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

3. **验证API服务**：
```bash
# 在另一个终端中
python scripts/test/test_api_service.py
```

预期输出：
- 健康检查通过
- 认证成功
- 爬虫端点测试通过
- 数据端点测试通过

## 下一步

完成数据处理与API服务后，后续还需要实现：
- 监控与日志系统
- 部署配置（Docker Compose/K8s）
- 性能优化与缓存策略
- 更多平台适配器（大众点评、携程、抖音、微博、B站）

数据处理管道和API服务是整个系统的核心部分，确保数据质量和对外服务能力。