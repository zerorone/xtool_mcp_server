# 旅游平台数据爬虫系统 - AI编程实现TODO详细清单（第2部分）

> 本文档为AI编程实现TODO详细清单的第二部分，包含第5-7阶段的详细任务

## 前情提要

第一部分已完成：
- ✅ 第1阶段：项目初始化与基础架构
- ✅ 第2阶段：双引擎核心架构
- ✅ 第3阶段：反爬系统实现
- ✅ 第4阶段：平台适配器实现（第一批）

本文档继续：
- 📝 第5阶段：数据处理与API服务
- 📝 第6阶段：高级平台适配器实现
- 📝 第7阶段：监控运维与部署

---

# 第五阶段：数据处理与API服务 [Priority: HIGH] [Time: 5-6天]

## 5.1 数据清洗系统

### 5.1.1 数据清洗框架

#### 5.1.1.1 创建数据清洗基础类 [Time: 3h]
```python
# src/processors/cleaner/base_cleaner.py
import re
import html
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.utils.logger.logger import get_logger

logger = get_logger("processor.cleaner")

class DataCleaner(ABC):
    """数据清洗基础类"""
    
    def __init__(self):
        self.cleaning_rules = []
        self._init_rules()
    
    @abstractmethod
    def _init_rules(self):
        """初始化清洗规则"""
        pass
    
    async def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据清洗"""
        try:
            # 应用所有清洗规则
            cleaned_data = data.copy()
            
            for rule in self.cleaning_rules:
                cleaned_data = await rule(cleaned_data)
            
            # 基础清洗
            cleaned_data = await self._basic_clean(cleaned_data)
            
            # 特定平台清洗
            cleaned_data = await self._platform_specific_clean(cleaned_data)
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            return data
    
    async def _basic_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """基础清洗"""
        # 清理字符串字段
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = await self._clean_string(value)
            elif isinstance(value, dict):
                data[key] = await self._basic_clean(value)
            elif isinstance(value, list):
                data[key] = [
                    await self._clean_string(item) if isinstance(item, str) else item
                    for item in value
                ]
        
        return data
    
    async def _clean_string(self, text: str) -> str:
        """清理字符串"""
        if not text:
            return ""
        
        # HTML解码
        text = html.unescape(text)
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除控制字符
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    @abstractmethod
    async def _platform_specific_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """平台特定清洗"""
        pass

class POICleaner(DataCleaner):
    """POI数据清洗器"""
    
    def _init_rules(self):
        """初始化POI清洗规则"""
        self.cleaning_rules = [
            self._clean_name,
            self._clean_address,
            self._clean_phone,
            self._normalize_rating,
            self._validate_coordinates
        ]
    
    async def _clean_name(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗名称"""
        if "name" in data:
            # 移除括号内容
            name = re.sub(r'\([^)]*\)', '', data["name"])
            
            # 移除特殊标记
            name = re.sub(r'【[^】]*】', '', name)
            
            # 标准化
            data["name"] = name.strip()
        
        return data
    
    async def _clean_address(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗地址"""
        if "address" in data:
            address = data["address"]
            
            # 移除重复的城市/区域信息
            if "city" in data and data["city"] in address:
                address = address.replace(data["city"], "", 1)
            
            if "district" in data and data["district"] in address:
                address = address.replace(data["district"], "", 1)
            
            data["address"] = address.strip()
        
        return data
    
    async def _clean_phone(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗电话号码"""
        if "phone" in data and data["phone"]:
            phone = data["phone"]
            
            # 移除非数字字符
            phone = re.sub(r'[^\d\-\+\s,;]', '', phone)
            
            # 标准化分隔符
            phone = re.sub(r'[,;]', ' ', phone)
            
            # 验证电话格式
            phones = []
            for p in phone.split():
                p = p.strip()
                if re.match(r'^(\+86)?1[3-9]\d{9}$', p):  # 手机号
                    phones.append(p)
                elif re.match(r'^(\d{3,4}-)?\d{7,8}$', p):  # 座机
                    phones.append(p)
            
            data["phone"] = " ".join(phones)
        
        return data
    
    async def _normalize_rating(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化评分"""
        if "rating" in data:
            try:
                rating = float(data["rating"])
                
                # 统一到5分制
                if rating > 5:
                    rating = rating / 2  # 10分制转5分制
                
                # 保留一位小数
                data["rating"] = round(rating, 1)
                
            except (ValueError, TypeError):
                data["rating"] = 0.0
        
        return data
    
    async def _validate_coordinates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证坐标"""
        if "latitude" in data and "longitude" in data:
            try:
                lat = float(data["latitude"])
                lng = float(data["longitude"])
                
                # 中国地理范围验证
                if not (3.86 <= lat <= 53.55 and 73.66 <= lng <= 135.05):
                    logger.warning(f"Invalid coordinates: {lat}, {lng}")
                    data["latitude"] = None
                    data["longitude"] = None
                
            except (ValueError, TypeError):
                data["latitude"] = None
                data["longitude"] = None
        
        return data
    
    async def _platform_specific_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """平台特定清洗"""
        platform = data.get("platform", "")
        
        if platform == "amap":
            return await self._clean_amap_data(data)
        elif platform == "dianping":
            return await self._clean_dianping_data(data)
        elif platform == "mafengwo":
            return await self._clean_mafengwo_data(data)
        
        return data
    
    async def _clean_amap_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """高德地图数据清洗"""
        # 处理高德特定的类型编码
        if "category" in data:
            category_map = {
                "050000": "餐饮服务",
                "100000": "住宿服务",
                "110000": "风景名胜",
                "060000": "购物服务"
            }
            
            if data["category"] in category_map:
                data["category"] = category_map[data["category"]]
        
        return data
    
    async def _clean_dianping_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """大众点评数据清洗"""
        # 处理评分
        if "rating" in data and isinstance(data["rating"], str):
            # 大众点评可能返回星级描述
            star_map = {
                "五星商户": 5.0,
                "四星商户": 4.0,
                "三星商户": 3.0,
                "准四星商户": 3.5,
                "准五星商户": 4.5
            }
            
            data["rating"] = star_map.get(data["rating"], 0.0)
        
        return data
    
    async def _clean_mafengwo_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """马蜂窝数据清洗"""
        # 处理马蜂窝的特殊字段
        if "poi_type" in data:
            data["category"] = data.pop("poi_type")
        
        return data
```

**验证标准**：数据清洗框架创建完成，支持多规则链式清洗

#### 5.1.1.2 实现批量清洗处理器 [Time: 2h]
```python
# src/processors/cleaner/batch_cleaner.py
import asyncio
from typing import List, Dict, Any, Type
from src.processors.cleaner.base_cleaner import DataCleaner, POICleaner
from src.utils.logger.logger import get_logger

logger = get_logger("processor.batch_cleaner")

class BatchDataCleaner:
    """批量数据清洗器"""
    
    def __init__(self):
        self.cleaner_registry = {
            "poi": POICleaner,
            "review": ReviewCleaner,
            "media": MediaCleaner
        }
        self.batch_size = 100
        self.max_workers = 10
    
    async def clean_batch(
        self, 
        data_list: List[Dict[str, Any]], 
        data_type: str = "poi"
    ) -> List[Dict[str, Any]]:
        """批量清洗数据"""
        try:
            # 获取清洗器
            cleaner_class = self.cleaner_registry.get(data_type, POICleaner)
            cleaner = cleaner_class()
            
            # 分批处理
            cleaned_data = []
            
            for i in range(0, len(data_list), self.batch_size):
                batch = data_list[i:i + self.batch_size]
                
                # 并发清洗
                tasks = [cleaner.clean(data) for data in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Cleaning failed for item {i+j}: {result}")
                        cleaned_data.append(batch[j])  # 返回原数据
                    else:
                        cleaned_data.append(result)
                
                # 进度日志
                progress = min(i + self.batch_size, len(data_list))
                logger.info(f"Cleaned {progress}/{len(data_list)} items")
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Batch cleaning failed: {e}")
            return data_list
    
    def register_cleaner(self, data_type: str, cleaner_class: Type[DataCleaner]):
        """注册新的清洗器"""
        self.cleaner_registry[data_type] = cleaner_class
        logger.info(f"Registered cleaner for {data_type}")

class ReviewCleaner(DataCleaner):
    """评论数据清洗器"""
    
    def _init_rules(self):
        self.cleaning_rules = [
            self._clean_review_content,
            self._clean_reviewer_info,
            self._normalize_rating
        ]
    
    async def _clean_review_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗评论内容"""
        if "content" in data:
            content = data["content"]
            
            # 移除表情符号
            content = re.sub(r'[\U00010000-\U0010ffff]', '', content)
            
            # 移除重复字符
            content = re.sub(r'(.)\1{3,}', r'\1\1\1', content)
            
            # 移除广告链接
            content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
            
            data["content"] = content.strip()
        
        return data
    
    async def _clean_reviewer_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗评论者信息"""
        if "reviewer_name" in data:
            # 脱敏处理
            name = data["reviewer_name"]
            if len(name) > 1:
                data["reviewer_name"] = name[0] + "*" * (len(name) - 1)
        
        return data
    
    async def _normalize_rating(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化评分"""
        if "rating" in data:
            try:
                rating = float(data["rating"])
                data["rating"] = max(0, min(5, rating))  # 限制在0-5范围
            except:
                data["rating"] = 0
        
        return data
    
    async def _platform_specific_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """平台特定清洗"""
        return data

class MediaCleaner(DataCleaner):
    """媒体数据清洗器"""
    
    def _init_rules(self):
        self.cleaning_rules = [
            self._clean_media_url,
            self._clean_media_metadata,
            self._validate_media_type
        ]
    
    async def _clean_media_url(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗媒体URL"""
        if "url" in data:
            url = data["url"]
            
            # 移除查询参数
            if "?" in url:
                url = url.split("?")[0]
            
            # 确保HTTPS
            if url.startswith("http://"):
                url = url.replace("http://", "https://")
            
            data["url"] = url
        
        return data
    
    async def _clean_media_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗媒体元数据"""
        # 标准化尺寸信息
        if "width" in data and "height" in data:
            try:
                data["width"] = int(data["width"])
                data["height"] = int(data["height"])
            except:
                data["width"] = 0
                data["height"] = 0
        
        return data
    
    async def _validate_media_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证媒体类型"""
        valid_types = ["image", "video", "audio"]
        
        if "media_type" in data:
            if data["media_type"] not in valid_types:
                data["media_type"] = "unknown"
        
        return data
    
    async def _platform_specific_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """平台特定清洗"""
        return data
```

**验证标准**：批量清洗处理器实现完成，支持并发批量处理

## 5.2 数据去重系统

### 5.2.1 去重算法实现

#### 5.2.1.1 实现去重管理器 [Time: 3h]
```python
# src/processors/deduplicator/dedup_manager.py
import hashlib
import difflib
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from src.core.database.connection import get_db
from src.core.redis.connection import redis_manager
from src.utils.logger.logger import get_logger

logger = get_logger("processor.deduplicator")

class DeduplicationManager:
    """去重管理器"""
    
    def __init__(self):
        self.similarity_threshold = 0.85
        self.hash_fields = ["name", "address", "latitude", "longitude"]
        self.cache_ttl = 3600  # 1小时
    
    async def deduplicate(
        self, 
        items: List[Dict[str, Any]], 
        platform: str = None
    ) -> List[Dict[str, Any]]:
        """去重处理"""
        try:
            unique_items = []
            seen_hashes = set()
            
            for item in items:
                # 生成唯一标识
                item_hash = self._generate_hash(item)
                
                # 快速哈希去重
                if item_hash in seen_hashes:
                    continue
                
                # 数据库去重检查
                is_duplicate = await self._check_database_duplicate(item, platform)
                if is_duplicate:
                    continue
                
                # 相似度去重
                is_similar = await self._check_similarity(item, unique_items)
                if is_similar:
                    continue
                
                # 添加到结果
                seen_hashes.add(item_hash)
                unique_items.append(item)
            
            logger.info(f"Deduplication: {len(items)} -> {len(unique_items)} items")
            return unique_items
            
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            return items
    
    def _generate_hash(self, item: Dict[str, Any]) -> str:
        """生成数据哈希"""
        hash_parts = []
        
        for field in self.hash_fields:
            if field in item:
                value = str(item[field]).lower().strip()
                hash_parts.append(value)
        
        hash_string = "|".join(hash_parts)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    async def _check_database_duplicate(
        self, 
        item: Dict[str, Any], 
        platform: str
    ) -> bool:
        """检查数据库中的重复"""
        try:
            # 先检查Redis缓存
            cache_key = f"dedup:{platform}:{item.get('platform_poi_id', '')}"
            cached = await redis_manager.get_client().get(cache_key)
            
            if cached:
                return True
            
            # 数据库查询
            async with get_db() as db:
                # 精确匹配
                if "platform_poi_id" in item:
                    existing = await db.query(POI).filter(
                        POI.platform == platform,
                        POI.platform_poi_id == item["platform_poi_id"]
                    ).first()
                    
                    if existing:
                        # 缓存结果
                        await redis_manager.get_client().setex(
                            cache_key, self.cache_ttl, "1"
                        )
                        return True
                
                # 坐标匹配
                if "latitude" in item and "longitude" in item:
                    lat, lng = item["latitude"], item["longitude"]
                    
                    # 查找附近100米内的POI
                    nearby = await db.query(POI).filter(
                        func.ST_DWithin(
                            POI.location,
                            func.ST_MakePoint(lng, lat),
                            0.001  # 约100米
                        )
                    ).all()
                    
                    for poi in nearby:
                        if self._is_same_poi(item, poi):
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Database duplicate check failed: {e}")
            return False
    
    async def _check_similarity(
        self, 
        item: Dict[str, Any], 
        existing_items: List[Dict[str, Any]]
    ) -> bool:
        """检查相似度"""
        for existing in existing_items:
            similarity = self._calculate_similarity(item, existing)
            
            if similarity >= self.similarity_threshold:
                return True
        
        return False
    
    def _calculate_similarity(
        self, 
        item1: Dict[str, Any], 
        item2: Dict[str, Any]
    ) -> float:
        """计算两个POI的相似度"""
        scores = []
        
        # 名称相似度（权重0.4）
        if "name" in item1 and "name" in item2:
            name_sim = difflib.SequenceMatcher(
                None, 
                item1["name"].lower(), 
                item2["name"].lower()
            ).ratio()
            scores.append(name_sim * 0.4)
        
        # 地址相似度（权重0.3）
        if "address" in item1 and "address" in item2:
            addr_sim = difflib.SequenceMatcher(
                None,
                item1["address"].lower(),
                item2["address"].lower()
            ).ratio()
            scores.append(addr_sim * 0.3)
        
        # 坐标距离（权重0.3）
        if all(k in item1 and k in item2 for k in ["latitude", "longitude"]):
            distance = self._calculate_distance(
                item1["latitude"], item1["longitude"],
                item2["latitude"], item2["longitude"]
            )
            
            # 距离小于100米认为是同一地点
            if distance < 0.1:
                scores.append(0.3)
            else:
                scores.append(0)
        
        return sum(scores)
    
    def _calculate_distance(
        self, 
        lat1: float, 
        lng1: float, 
        lat2: float, 
        lng2: float
    ) -> float:
        """计算两点距离（简化版，单位：公里）"""
        import math
        
        R = 6371  # 地球半径
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _is_same_poi(self, item: Dict[str, Any], poi: POI) -> bool:
        """判断是否为同一POI"""
        # 名称完全相同
        if item.get("name") == poi.name:
            return True
        
        # 计算综合相似度
        poi_dict = {
            "name": poi.name,
            "address": poi.address,
            "latitude": poi.latitude,
            "longitude": poi.longitude
        }
        
        similarity = self._calculate_similarity(item, poi_dict)
        return similarity >= self.similarity_threshold
```

**验证标准**：去重管理器实现完成，支持多维度去重策略

#### 5.2.1.2 实现增量去重处理 [Time: 2h]
```python
# src/processors/deduplicator/incremental_dedup.py
import asyncio
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
from src.processors.deduplicator.dedup_manager import DeduplicationManager
from src.core.models.poi import POI
from src.utils.logger.logger import get_logger

logger = get_logger("processor.incremental_dedup")

class IncrementalDeduplicator:
    """增量去重处理器"""
    
    def __init__(self):
        self.dedup_manager = DeduplicationManager()
        self.bloom_filter_size = 1000000  # 布隆过滤器大小
        self.bloom_filter_error_rate = 0.01
        self._init_bloom_filter()
    
    def _init_bloom_filter(self):
        """初始化布隆过滤器"""
        try:
            from pybloom_live import BloomFilter
            self.bloom_filter = BloomFilter(
                capacity=self.bloom_filter_size,
                error_rate=self.bloom_filter_error_rate
            )
            logger.info("Bloom filter initialized")
        except ImportError:
            logger.warning("pybloom_live not installed, using set instead")
            self.bloom_filter = set()
    
    async def process_incremental(
        self, 
        new_items: List[Dict[str, Any]], 
        platform: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """处理增量数据"""
        try:
            unique_items = []
            duplicate_items = []
            
            # 批量检查
            for item in new_items:
                item_id = self._get_item_id(item)
                
                # 布隆过滤器快速检查
                if self._bloom_filter_check(item_id):
                    # 可能重复，需要进一步验证
                    is_duplicate = await self._verify_duplicate(item, platform)
                    
                    if is_duplicate:
                        duplicate_items.append(item)
                        continue
                
                # 添加到布隆过滤器
                self._bloom_filter_add(item_id)
                unique_items.append(item)
            
            # 二次去重
            unique_items = await self.dedup_manager.deduplicate(unique_items, platform)
            
            logger.info(
                f"Incremental dedup: {len(new_items)} items, "
                f"{len(unique_items)} unique, {len(duplicate_items)} duplicates"
            )
            
            return unique_items, duplicate_items
            
        except Exception as e:
            logger.error(f"Incremental deduplication failed: {e}")
            return new_items, []
    
    def _get_item_id(self, item: Dict[str, Any]) -> str:
        """获取项目标识"""
        # 优先使用平台ID
        if "platform_poi_id" in item:
            return f"{item.get('platform', '')}:{item['platform_poi_id']}"
        
        # 使用名称和坐标
        parts = [
            item.get("name", ""),
            str(item.get("latitude", "")),
            str(item.get("longitude", ""))
        ]
        
        return ":".join(parts)
    
    def _bloom_filter_check(self, item_id: str) -> bool:
        """布隆过滤器检查"""
        if isinstance(self.bloom_filter, set):
            return item_id in self.bloom_filter
        else:
            return item_id in self.bloom_filter
    
    def _bloom_filter_add(self, item_id: str):
        """添加到布隆过滤器"""
        if isinstance(self.bloom_filter, set):
            self.bloom_filter.add(item_id)
        else:
            self.bloom_filter.add(item_id)
    
    async def _verify_duplicate(
        self, 
        item: Dict[str, Any], 
        platform: str
    ) -> bool:
        """验证是否真的重复"""
        # 使用去重管理器的数据库检查
        return await self.dedup_manager._check_database_duplicate(item, platform)
    
    async def sync_bloom_filter(self, platform: str = None):
        """同步布隆过滤器与数据库"""
        try:
            async with get_db() as db:
                # 查询现有POI
                query = db.query(POI.platform, POI.platform_poi_id)
                
                if platform:
                    query = query.filter(POI.platform == platform)
                
                # 批量处理
                offset = 0
                batch_size = 10000
                
                while True:
                    pois = await query.offset(offset).limit(batch_size).all()
                    
                    if not pois:
                        break
                    
                    # 添加到布隆过滤器
                    for poi in pois:
                        item_id = f"{poi.platform}:{poi.platform_poi_id}"
                        self._bloom_filter_add(item_id)
                    
                    offset += batch_size
                    logger.info(f"Synced {offset} POIs to bloom filter")
            
            logger.info("Bloom filter sync completed")
            
        except Exception as e:
            logger.error(f"Bloom filter sync failed: {e}")
```

**验证标准**：增量去重处理实现完成，支持布隆过滤器优化

## 5.3 数据增强系统

### 5.3.1 数据增强处理

#### 5.3.1.1 实现数据增强器 [Time: 3h]
```python
# src/processors/enhancer/data_enhancer.py
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.utils.logger.logger import get_logger

logger = get_logger("processor.enhancer")

class DataEnhancer:
    """数据增强器"""
    
    def __init__(self):
        self.enhancement_rules = [
            self._enhance_category,
            self._enhance_business_hours,
            self._enhance_price_level,
            self._enhance_tags,
            self._calculate_popularity_score
        ]
    
    async def enhance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """增强数据"""
        try:
            enhanced_data = data.copy()
            
            # 应用所有增强规则
            for rule in self.enhancement_rules:
                enhanced_data = await rule(enhanced_data)
            
            # 添加增强元数据
            enhanced_data["enhanced_at"] = datetime.utcnow().isoformat()
            enhanced_data["enhancement_version"] = "1.0"
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Data enhancement failed: {e}")
            return data
    
    async def _enhance_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """增强分类信息"""
        if "category" in data:
            # 标准化分类
            category_mapping = {
                "餐饮": ["restaurant", "food", "dining"],
                "住宿": ["hotel", "accommodation", "lodging"],
                "景点": ["attraction", "scenic_spot", "tourist_attraction"],
                "购物": ["shopping", "mall", "store"],
                "娱乐": ["entertainment", "recreation", "leisure"]
            }
            
            # 添加英文标签
            for cn_cat, en_cats in category_mapping.items():
                if cn_cat in data["category"]:
                    if "category_tags" not in data:
                        data["category_tags"] = []
                    data["category_tags"].extend(en_cats)
                    break
        
        return data
    
    async def _enhance_business_hours(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """增强营业时间"""
        if "business_hours" in data and data["business_hours"]:
            try:
                # 解析营业时间
                hours = data["business_hours"]
                
                # 判断是否24小时营业
                if "24" in hours or "全天" in hours:
                    data["is_24_hours"] = True
                else:
                    data["is_24_hours"] = False
                
                # 判断当前是否营业
                data["is_open_now"] = await self._check_if_open(hours)
                
            except Exception as e:
                logger.debug(f"Failed to enhance business hours: {e}")
        
        return data
    
    async def _enhance_price_level(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """增强价格等级"""
        if "price" in data:
            try:
                price = float(data["price"])
                
                # 根据价格判断等级
                if price < 50:
                    data["price_level"] = 1  # 经济
                elif price < 100:
                    data["price_level"] = 2  # 适中
                elif price < 200:
                    data["price_level"] = 3  # 偏贵
                else:
                    data["price_level"] = 4  # 昂贵
                    
            except (ValueError, TypeError):
                pass
        
        return data
    
    async def _enhance_tags(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """增强标签"""
        tags = []
        
        # 基于评分的标签
        if "rating" in data:
            rating = data.get("rating", 0)
            if rating >= 4.5:
                tags.append("highly_rated")
            elif rating >= 4.0:
                tags.append("well_rated")
        
        # 基于评论数的标签
        if "review_count" in data:
            count = data.get("review_count", 0)
            if count >= 1000:
                tags.append("popular")
            elif count >= 500:
                tags.append("trending")
        
        # 基于位置的标签
        if "district" in data:
            if any(area in data["district"] for area in ["市中心", "商业区", "CBD"]):
                tags.append("city_center")
        
        # 合并标签
        if "tags" in data:
            data["tags"].extend(tags)
        else:
            data["tags"] = tags
        
        # 去重
        data["tags"] = list(set(data["tags"]))
        
        return data
    
    async def _calculate_popularity_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算人气分数"""
        score = 0.0
        
        # 基于评分（权重0.4）
        if "rating" in data:
            rating = data.get("rating", 0)
            score += (rating / 5.0) * 0.4
        
        # 基于评论数（权重0.3）
        if "review_count" in data:
            count = data.get("review_count", 0)
            # 对数缩放
            import math
            normalized_count = math.log10(count + 1) / 4  # 假设10000为最高
            score += min(normalized_count, 1.0) * 0.3
        
        # 基于图片数（权重0.2）
        if "images" in data:
            image_count = len(data.get("images", []))
            normalized_images = min(image_count / 20, 1.0)  # 20张图片为满分
            score += normalized_images * 0.2
        
        # 基于标签数（权重0.1）
        if "tags" in data:
            tag_count = len(data.get("tags", []))
            normalized_tags = min(tag_count / 10, 1.0)  # 10个标签为满分
            score += normalized_tags * 0.1
        
        data["popularity_score"] = round(score, 2)
        
        return data
    
    async def _check_if_open(self, business_hours: str) -> bool:
        """检查是否营业中"""
        # 简化实现，实际应该解析营业时间并对比当前时间
        from datetime import datetime
        
        current_hour = datetime.now().hour
        
        # 简单判断
        if "24" in business_hours or "全天" in business_hours:
            return True
        
        # 一般营业时间
        if 9 <= current_hour <= 22:
            return True
        
        return False

class POIEnhancer(DataEnhancer):
    """POI数据增强器"""
    
    def __init__(self):
        super().__init__()
        # 添加POI特定的增强规则
        self.enhancement_rules.extend([
            self._enhance_location_info,
            self._enhance_nearby_info
        ])
    
    async def _enhance_location_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """增强位置信息"""
        if "latitude" in data and "longitude" in data:
            # 添加geohash
            try:
                import geohash2
                data["geohash"] = geohash2.encode(
                    data["latitude"], 
                    data["longitude"], 
                    precision=7
                )
            except ImportError:
                pass
            
            # 添加坐标系信息
            data["coordinate_system"] = "WGS84"
        
        return data
    
    async def _enhance_nearby_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """增强周边信息"""
        # 这里可以调用地图API获取周边信息
        # 简化实现，添加占位信息
        
        data["nearby_facilities"] = {
            "subway_stations": [],
            "bus_stops": [],
            "parking_lots": [],
            "landmarks": []
        }
        
        return data
```

**验证标准**：数据增强器实现完成，支持多维度数据增强

## 5.4 RESTful API服务

### 5.4.1 API框架搭建

#### 5.4.1.1 创建API路由结构 [Time: 3h]
```python
# src/api/v1/routers/base.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "Success"
    data: Any = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginatedResponse(BaseResponse):
    """分页响应模型"""
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0

# 基础查询参数
class BaseQueryParams(BaseModel):
    """基础查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: Optional[str] = Field(default="desc", regex="^(asc|desc)$")

# src/api/v1/routers/poi.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
from sqlalchemy.orm import Session
from src.api.v1.routers.base import BaseResponse, PaginatedResponse, BaseQueryParams
from src.api.v1.schemas.poi import POICreate, POIUpdate, POIResponse, POISearchParams
from src.api.v1.services.poi_service import POIService
from src.api.v1.dependencies import get_db, get_current_user
from src.utils.logger.logger import get_logger

logger = get_logger("api.poi")

router = APIRouter(prefix="/pois", tags=["POI"])

@router.get("/search", response_model=PaginatedResponse)
async def search_pois(
    keyword: str = Query(..., description="搜索关键词"),
    city: Optional[str] = Query(None, description="城市"),
    category: Optional[str] = Query(None, description="分类"),
    platforms: List[str] = Query(default=[], description="平台列表"),
    query_params: BaseQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """搜索POI"""
    try:
        service = POIService(db)
        
        # 构建搜索参数
        search_params = POISearchParams(
            keyword=keyword,
            city=city,
            category=category,
            platforms=platforms,
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        # 执行搜索
        results, total = await service.search_pois(search_params)
        
        # 构建响应
        return PaginatedResponse(
            data=results,
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            total_pages=(total + query_params.page_size - 1) // query_params.page_size
        )
        
    except Exception as e:
        logger.error(f"POI search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{poi_id}", response_model=BaseResponse)
async def get_poi(
    poi_id: int = Path(..., description="POI ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取POI详情"""
    try:
        service = POIService(db)
        poi = await service.get_poi_by_id(poi_id)
        
        if not poi:
            raise HTTPException(status_code=404, detail="POI not found")
        
        return BaseResponse(data=poi)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get POI failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=BaseResponse)
async def create_poi(
    poi_data: POICreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建POI"""
    try:
        service = POIService(db)
        poi = await service.create_poi(poi_data.dict())
        
        return BaseResponse(
            data=poi,
            message="POI created successfully"
        )
        
    except Exception as e:
        logger.error(f"Create POI failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{poi_id}", response_model=BaseResponse)
async def update_poi(
    poi_id: int = Path(..., description="POI ID"),
    poi_data: POIUpdate = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新POI"""
    try:
        service = POIService(db)
        poi = await service.update_poi(poi_id, poi_data.dict(exclude_unset=True))
        
        if not poi:
            raise HTTPException(status_code=404, detail="POI not found")
        
        return BaseResponse(
            data=poi,
            message="POI updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update POI failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{poi_id}", response_model=BaseResponse)
async def delete_poi(
    poi_id: int = Path(..., description="POI ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除POI"""
    try:
        service = POIService(db)
        success = await service.delete_poi(poi_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="POI not found")
        
        return BaseResponse(message="POI deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete POI failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nearby", response_model=PaginatedResponse)
async def get_nearby_pois(
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    radius: int = Query(default=1000, description="半径（米）"),
    category: Optional[str] = Query(None, description="分类"),
    query_params: BaseQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取附近POI"""
    try:
        service = POIService(db)
        
        # 执行附近搜索
        results, total = await service.search_nearby(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            category=category,
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        return PaginatedResponse(
            data=results,
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            total_pages=(total + query_params.page_size - 1) // query_params.page_size
        )
        
    except Exception as e:
        logger.error(f"Nearby POI search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**验证标准**：API路由结构创建完成，支持完整的CRUD操作

#### 5.4.1.2 实现API服务层 [Time: 3h]
```python
# src/api/v1/services/poi_service.py
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from src.core.models.poi import POI
from src.api.v1.schemas.poi import POISearchParams
from src.processors.cleaner.base_cleaner import POICleaner
from src.processors.enhancer.data_enhancer import POIEnhancer
from src.utils.logger.logger import get_logger

logger = get_logger("api.service.poi")

class POIService:
    """POI服务层"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cleaner = POICleaner()
        self.enhancer = POIEnhancer()
    
    async def search_pois(
        self, 
        params: POISearchParams
    ) -> Tuple[List[Dict[str, Any]], int]:
        """搜索POI"""
        try:
            # 构建查询
            query = self.db.query(POI)
            
            # 关键词搜索
            if params.keyword:
                query = query.filter(
                    or_(
                        POI.name.ilike(f"%{params.keyword}%"),
                        POI.address.ilike(f"%{params.keyword}%"),
                        POI.description.ilike(f"%{params.keyword}%")
                    )
                )
            
            # 城市过滤
            if params.city:
                query = query.filter(POI.city == params.city)
            
            # 分类过滤
            if params.category:
                query = query.filter(POI.category.ilike(f"%{params.category}%"))
            
            # 平台过滤
            if params.platforms:
                query = query.filter(POI.platform.in_(params.platforms))
            
            # 只返回激活的POI
            query = query.filter(POI.is_active == True)
            
            # 获取总数
            total = query.count()
            
            # 分页
            offset = (params.page - 1) * params.page_size
            pois = query.offset(offset).limit(params.page_size).all()
            
            # 转换为字典并增强
            results = []
            for poi in pois:
                poi_dict = self._poi_to_dict(poi)
                enhanced = await self.enhancer.enhance(poi_dict)
                results.append(enhanced)
            
            return results, total
            
        except Exception as e:
            logger.error(f"POI search failed: {e}")
            raise
    
    async def get_poi_by_id(self, poi_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取POI"""
        try:
            poi = self.db.query(POI).filter(
                POI.id == poi_id,
                POI.is_active == True
            ).first()
            
            if not poi:
                return None
            
            # 转换并增强
            poi_dict = self._poi_to_dict(poi)
            enhanced = await self.enhancer.enhance(poi_dict)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Get POI by ID failed: {e}")
            raise
    
    async def create_poi(self, poi_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建POI"""
        try:
            # 清洗数据
            cleaned_data = await self.cleaner.clean(poi_data)
            
            # 创建POI对象
            poi = POI(**cleaned_data)
            
            # 保存到数据库
            self.db.add(poi)
            self.db.commit()
            self.db.refresh(poi)
            
            # 返回增强后的数据
            poi_dict = self._poi_to_dict(poi)
            enhanced = await self.enhancer.enhance(poi_dict)
            
            return enhanced
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Create POI failed: {e}")
            raise
    
    async def update_poi(
        self, 
        poi_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新POI"""
        try:
            poi = self.db.query(POI).filter(POI.id == poi_id).first()
            
            if not poi:
                return None
            
            # 清洗更新数据
            cleaned_data = await self.cleaner.clean(update_data)
            
            # 更新字段
            for key, value in cleaned_data.items():
                if hasattr(poi, key):
                    setattr(poi, key, value)
            
            # 保存
            self.db.commit()
            self.db.refresh(poi)
            
            # 返回增强后的数据
            poi_dict = self._poi_to_dict(poi)
            enhanced = await self.enhancer.enhance(poi_dict)
            
            return enhanced
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Update POI failed: {e}")
            raise
    
    async def delete_poi(self, poi_id: int) -> bool:
        """删除POI（软删除）"""
        try:
            poi = self.db.query(POI).filter(POI.id == poi_id).first()
            
            if not poi:
                return False
            
            # 软删除
            poi.is_active = False
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Delete POI failed: {e}")
            raise
    
    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """搜索附近POI"""
        try:
            # 使用PostGIS的ST_DWithin进行地理查询
            point = func.ST_MakePoint(longitude, latitude)
            
            query = self.db.query(POI).filter(
                func.ST_DWithin(
                    POI.location,
                    point,
                    radius / 111000.0  # 转换为度
                ),
                POI.is_active == True
            )
            
            # 分类过滤
            if category:
                query = query.filter(POI.category.ilike(f"%{category}%"))
            
            # 按距离排序
            query = query.order_by(func.ST_Distance(POI.location, point))
            
            # 获取总数
            total = query.count()
            
            # 分页
            offset = (page - 1) * page_size
            pois = query.offset(offset).limit(page_size).all()
            
            # 转换并增强
            results = []
            for poi in pois:
                poi_dict = self._poi_to_dict(poi)
                
                # 添加距离信息
                distance = self.db.scalar(
                    func.ST_Distance(poi.location, point) * 111000  # 转换为米
                )
                poi_dict["distance"] = round(distance, 2)
                
                enhanced = await self.enhancer.enhance(poi_dict)
                results.append(enhanced)
            
            return results, total
            
        except Exception as e:
            logger.error(f"Nearby search failed: {e}")
            raise
    
    def _poi_to_dict(self, poi: POI) -> Dict[str, Any]:
        """POI对象转字典"""
        return {
            "id": poi.id,
            "platform": poi.platform,
            "platform_poi_id": poi.platform_poi_id,
            "name": poi.name,
            "category": poi.category,
            "address": poi.address,
            "city": poi.city,
            "district": poi.district,
            "latitude": poi.latitude,
            "longitude": poi.longitude,
            "rating": poi.rating,
            "review_count": poi.review_count,
            "price": poi.price,
            "price_unit": poi.price_unit,
            "phone": poi.phone,
            "website": poi.website,
            "business_hours": poi.business_hours,
            "cover_image": poi.cover_image,
            "images": poi.images,
            "description": poi.description,
            "created_at": poi.created_at.isoformat() if poi.created_at else None,
            "updated_at": poi.updated_at.isoformat() if poi.updated_at else None
        }
```

**验证标准**：API服务层实现完成，支持业务逻辑处理

## 5.5 认证授权系统

### 5.5.1 JWT认证实现

#### 5.5.1.1 实现认证管理器 [Time: 3h]
```python
# src/api/v1/auth/auth_manager.py
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from src.core.config.settings import settings
from src.utils.logger.logger import get_logger

logger = get_logger("api.auth")

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

class TokenData(BaseModel):
    """Token数据模型"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600

class UserCredentials(BaseModel):
    """用户凭证模型"""
    username: str
    password: str

class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 7
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 验证令牌类型
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    async def authenticate_user(
        self, 
        username: str, 
        password: str
    ) -> Optional[Dict[str, Any]]:
        """认证用户"""
        # 这里应该查询数据库
        # 简化示例
        if username == "admin" and password == "admin123":
            return {
                "user_id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin"
            }
        
        return None
    
    def create_token_response(self, user_data: Dict[str, Any]) -> TokenData:
        """创建令牌响应"""
        # 创建访问令牌
        access_token = self.create_access_token(
            data={"sub": str(user_data["user_id"]), "username": user_data["username"]}
        )
        
        # 创建刷新令牌
        refresh_token = self.create_refresh_token(
            data={"sub": str(user_data["user_id"])}
        )
        
        return TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60
        )

# 全局认证管理器
auth_manager = AuthManager()

# src/api/v1/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any
from src.api.v1.auth.auth_manager import auth_manager, oauth2_scheme
from src.core.models.user import User
from src.core.database.connection import get_db

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
) -> User:
    """获取当前用户"""
    # 验证令牌
    payload = auth_manager.verify_token(token)
    
    # 获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # 查询用户
    user = await db.query(User).filter(User.id == int(user_id)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """需要管理员权限"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
    
    return current_user
```

**验证标准**：JWT认证系统实现完成，支持令牌生成和验证

---

## 验证和测试要求

### 阶段五验证清单
- [ ] 数据清洗功能测试通过
- [ ] 去重算法准确率 > 95%
- [ ] 数据增强功能正常
- [ ] API接口响应时间 < 1秒
- [ ] 认证授权系统安全

### 代码质量要求
- 代码覆盖率 > 85%
- API文档完整
- 错误处理完善
- 日志记录详细

### 性能要求
- 批量数据处理 > 1000条/秒
- API并发支持 > 100 QPS
- 响应时间 P95 < 500ms

---

**注意**：本文档为第二部分，包含第5阶段的详细实现。第6-7阶段将继续在后续部分中详细说明。

每个任务都包含具体的实现代码、验证标准和预估工时，可以直接用于指导AI编程助手进行开发工作。