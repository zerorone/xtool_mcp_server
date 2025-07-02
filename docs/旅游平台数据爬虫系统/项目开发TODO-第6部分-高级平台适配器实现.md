# 旅游平台数据爬虫系统 - 项目开发TODO详细指南
## 第6部分：高级平台适配器实现

> 本部分实现大众点评、携程、抖音、微博、B站等高级平台适配器

---

## Phase 6: 高级平台适配器实现（Day 16-20）

### Task 6.1: 大众点评适配器实现

#### 6.1.1 大众点评适配器
```python
# src/adapters/dianping/dianping_adapter.py
"""大众点评适配器实现"""
import re
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
from urllib.parse import urlencode, quote

from src.adapters.base.adapter_interface import (
    PlatformAdapter, POI, Review, Article,
    SearchQuery, DataType
)
from src.core.engines.base.engine_interface import CrawlTask, EngineType
from src.core.scheduler.coordinator import coordinator
from src.anti_detection.fingerprint.generator import FingerprintGenerator
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.dianping")

class DianpingAdapter(PlatformAdapter):
    """大众点评适配器"""
    
    def __init__(self):
        super().__init__()
        self.platform = "dianping"
        self.platform_name = "大众点评"
        self.base_url = "https://www.dianping.com"
        self.supported_types = [DataType.POI, DataType.REVIEW, DataType.IMAGE]
        
        # 大众点评特定配置
        self.city_map = {
            "北京": "2", "上海": "1", "广州": "4", "深圳": "7",
            "成都": "8", "杭州": "3", "南京": "5", "西安": "17",
            "重庆": "9", "武汉": "16", "苏州": "6", "天津": "10"
        }
        
        # 分类映射
        self.category_map = {
            "美食": "10", "酒店": "60", "景点": "35",
            "购物": "20", "休闲娱乐": "30", "丽人": "50"
        }
    
    async def search_pois(self, query: SearchQuery) -> List[POI]:
        """搜索POI"""
        logger.info(f"Searching POIs on Dianping: {query.keyword}")
        
        # 构建搜索URL
        city_id = self.city_map.get(query.city, "1")
        search_url = f"{self.base_url}/search/keyword/{city_id}/0_{quote(query.keyword)}"
        
        # 添加分页参数
        if query.page > 1:
            search_url += f"/p{query.page}"
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"dianping_search_{query.keyword}_{query.page}",
            platform=self.platform,
            url=search_url,
            task_type="search",
            engine_type=EngineType.MEDIACRAWL,  # 使用MediaCrawl处理动态内容
            engine_config={
                "wait_selector": ".shop-list",
                "wait_timeout": 10,
                "screenshot": True,
                "scroll_to_bottom": True
            },
            extraction_rules={
                "shops": {
                    "selector": ".shop-list li",
                    "multiple": True,
                    "fields": {
                        "shop_id": {"selector": "[data-shopid]", "attribute": "data-shopid"},
                        "name": {"selector": ".tit h4", "text": True},
                        "url": {"selector": ".tit a", "attribute": "href"},
                        "rating": {"selector": ".star-level", "attribute": "class", "regex": r"star-(\d+)"},
                        "review_count": {"selector": ".review-num b", "text": True},
                        "avg_price": {"selector": ".mean-price b", "text": True},
                        "category": {"selector": ".tag-addr .tag", "text": True},
                        "area": {"selector": ".tag-addr .addr", "text": True},
                        "image": {"selector": ".pic img", "attribute": "src"}
                    }
                }
            },
            use_fingerprint=True,
            use_behavior_simulation=True,
            metadata={"query": query.model_dump()}
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to search on Dianping: {result.error_message}")
            return []
        
        # 解析结果
        pois = []
        shops = result.extracted_data.get("shops", [])
        
        for shop in shops:
            try:
                poi = await self._parse_search_result(shop, query.city)
                if poi:
                    pois.append(poi)
            except Exception as e:
                logger.error(f"Failed to parse shop: {str(e)}")
                continue
        
        logger.info(f"Found {len(pois)} POIs on Dianping")
        return pois
    
    async def get_poi_detail(self, poi_id: str) -> Optional[POI]:
        """获取POI详情"""
        logger.info(f"Getting POI detail from Dianping: {poi_id}")
        
        # 构建详情URL
        detail_url = f"{self.base_url}/shop/{poi_id}"
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"dianping_detail_{poi_id}",
            platform=self.platform,
            url=detail_url,
            task_type="detail",
            engine_type=EngineType.MEDIACRAWL,
            engine_config={
                "wait_selector": ".shop-name",
                "wait_timeout": 10,
                "screenshot": True,
                "execute_script": """
                    // 展开更多信息
                    const moreBtn = document.querySelector('.more-info');
                    if (moreBtn) moreBtn.click();
                """
            },
            extraction_rules={
                "name": {"selector": ".shop-name", "text": True},
                "rating": {"selector": ".star-level", "attribute": "class", "regex": r"star-(\d+)"},
                "review_count": {"selector": ".review-count", "text": True},
                "avg_price": {"selector": ".price .num", "text": True},
                "address": {"selector": ".address-info", "text": True},
                "phone": {"selector": ".phone-info", "text": True},
                "business_hours": {"selector": ".business-hours", "text": True},
                "description": {"selector": ".shop-intro", "text": True},
                "features": {
                    "selector": ".feature-item",
                    "multiple": True,
                    "text": True
                },
                "images": {
                    "selector": ".photo-list img",
                    "multiple": True,
                    "attribute": "src"
                },
                "breadcrumb": {
                    "selector": ".breadcrumb a",
                    "multiple": True,
                    "text": True
                }
            },
            use_fingerprint=True,
            use_behavior_simulation=True
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to get POI detail from Dianping: {result.error_message}")
            return None
        
        # 解析详情
        return await self._parse_poi_detail(poi_id, result.extracted_data)
    
    async def get_poi_reviews(
        self, 
        poi_id: str, 
        page: int = 1,
        limit: int = 20
    ) -> List[Review]:
        """获取POI评论"""
        logger.info(f"Getting reviews for POI {poi_id} from Dianping")
        
        # 评论API URL（需要处理反爬）
        review_url = f"{self.base_url}/shop/{poi_id}/review_all/p{page}"
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"dianping_reviews_{poi_id}_p{page}",
            platform=self.platform,
            url=review_url,
            task_type="review",
            engine_type=EngineType.MEDIACRAWL,
            engine_config={
                "wait_selector": ".reviews-items",
                "wait_timeout": 10,
                "execute_script": """
                    // 处理CSS加密的评论内容
                    const reviews = document.querySelectorAll('.review-item');
                    reviews.forEach(review => {
                        // 这里需要根据实际的CSS加密规则解密
                        // 大众点评使用了SVG字体加密
                    });
                """
            },
            extraction_rules={
                "reviews": {
                    "selector": ".reviews-items > li",
                    "multiple": True,
                    "fields": {
                        "review_id": {"selector": "[data-id]", "attribute": "data-id"},
                        "author_name": {"selector": ".name", "text": True},
                        "author_id": {"selector": ".name", "attribute": "data-user-id"},
                        "rating": {"selector": ".star", "attribute": "class", "regex": r"star-(\d+)"},
                        "content": {"selector": ".review-words", "text": True},
                        "date": {"selector": ".time", "text": True},
                        "useful_count": {"selector": ".useful-num", "text": True},
                        "reply_count": {"selector": ".reply-num", "text": True},
                        "images": {
                            "selector": ".review-pictures img",
                            "multiple": True,
                            "attribute": "src"
                        }
                    }
                }
            },
            use_fingerprint=True,
            use_behavior_simulation=True
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to get reviews from Dianping: {result.error_message}")
            return []
        
        # 解析评论
        reviews = []
        review_items = result.extracted_data.get("reviews", [])
        
        for item in review_items[:limit]:
            try:
                review = await self._parse_review(item, poi_id)
                if review:
                    reviews.append(review)
            except Exception as e:
                logger.error(f"Failed to parse review: {str(e)}")
                continue
        
        return reviews
    
    async def _parse_search_result(self, shop: Dict[str, Any], city: str) -> Optional[POI]:
        """解析搜索结果"""
        try:
            # 解析评分
            rating_class = shop.get("rating", "")
            rating_match = re.search(r"star-(\d+)", rating_class)
            rating = float(rating_match.group(1)) / 10 if rating_match else None
            
            # 解析评论数
            review_text = shop.get("review_count", "0")
            review_count = int(re.findall(r"\d+", review_text)[0]) if re.findall(r"\d+", review_text) else 0
            
            # 解析均价
            price_text = shop.get("avg_price", "")
            price = float(re.findall(r"\d+", price_text)[0]) if re.findall(r"\d+", price_text) else None
            
            # 构建POI
            poi = POI(
                poi_id=f"dianping_{shop['shop_id']}",
                platform=self.platform,
                platform_poi_id=shop["shop_id"],
                name=shop["name"],
                category=shop.get("category"),
                city=city,
                district=shop.get("area"),
                rating=rating,
                rating_count=review_count,
                review_count=review_count,
                price=price,
                price_unit="元/人" if price else None,
                cover_image=shop.get("image"),
                tags=[shop.get("category")] if shop.get("category") else []
            )
            
            return poi
            
        except Exception as e:
            logger.error(f"Error parsing search result: {str(e)}")
            return None
    
    async def _parse_poi_detail(self, poi_id: str, data: Dict[str, Any]) -> Optional[POI]:
        """解析POI详情"""
        try:
            # 解析评分
            rating_class = data.get("rating", "")
            rating_match = re.search(r"star-(\d+)", rating_class)
            rating = float(rating_match.group(1)) / 10 if rating_match else None
            
            # 解析评论数
            review_text = data.get("review_count", "0")
            review_count = int(re.findall(r"\d+", review_text)[0]) if re.findall(r"\d+", review_text) else 0
            
            # 解析均价
            price_text = data.get("avg_price", "")
            price = float(re.findall(r"\d+", price_text)[0]) if re.findall(r"\d+", price_text) else None
            
            # 解析营业时间
            business_hours = {}
            hours_text = data.get("business_hours", "")
            if hours_text:
                # 简单解析，实际可能需要更复杂的逻辑
                business_hours["default"] = hours_text
            
            # 解析特色
            features = {}
            feature_list = data.get("features", [])
            for i, feature in enumerate(feature_list):
                features[f"feature_{i+1}"] = feature
            
            # 从面包屑获取分类
            breadcrumb = data.get("breadcrumb", [])
            category = breadcrumb[-2] if len(breadcrumb) > 2 else None
            
            # 构建POI
            poi = POI(
                poi_id=f"dianping_{poi_id}",
                platform=self.platform,
                platform_poi_id=poi_id,
                name=data["name"],
                category=category,
                address=data.get("address"),
                phone=data.get("phone"),
                rating=rating,
                rating_count=review_count,
                review_count=review_count,
                price=price,
                price_unit="元/人" if price else None,
                business_hours=business_hours,
                description=data.get("description"),
                features=features,
                images=data.get("images", []),
                cover_image=data.get("images", [""])[0] if data.get("images") else None
            )
            
            return poi
            
        except Exception as e:
            logger.error(f"Error parsing POI detail: {str(e)}")
            return None
    
    async def _parse_review(self, item: Dict[str, Any], poi_id: str) -> Optional[Review]:
        """解析评论"""
        try:
            # 解析评分
            rating_class = item.get("rating", "")
            rating_match = re.search(r"star-(\d+)", rating_class)
            rating = float(rating_match.group(1)) / 10 if rating_match else None
            
            # 解析日期
            date_text = item.get("date", "")
            # 大众点评的日期格式可能是"2024-01-15"或"3天前"等
            created_at = self._parse_date(date_text)
            
            # 解析点赞数
            useful_text = item.get("useful_count", "0")
            useful_count = int(re.findall(r"\d+", useful_text)[0]) if re.findall(r"\d+", useful_text) else 0
            
            # 构建评论
            review = Review(
                review_id=f"dianping_{item['review_id']}",
                poi_id=f"dianping_{poi_id}",
                platform=self.platform,
                platform_review_id=item["review_id"],
                content=item.get("content", ""),
                rating=rating,
                author_id=item.get("author_id"),
                author_name=item.get("author_name"),
                useful_count=useful_count,
                reply_count=int(item.get("reply_count", 0)),
                images=item.get("images", []),
                created_at=created_at
            )
            
            return review
            
        except Exception as e:
            logger.error(f"Error parsing review: {str(e)}")
            return None
    
    def _parse_date(self, date_text: str) -> datetime:
        """解析日期文本"""
        import re
        from datetime import datetime, timedelta
        
        # 处理相对时间
        if "分钟前" in date_text:
            minutes = int(re.findall(r"\d+", date_text)[0])
            return datetime.utcnow() - timedelta(minutes=minutes)
        elif "小时前" in date_text:
            hours = int(re.findall(r"\d+", date_text)[0])
            return datetime.utcnow() - timedelta(hours=hours)
        elif "天前" in date_text:
            days = int(re.findall(r"\d+", date_text)[0])
            return datetime.utcnow() - timedelta(days=days)
        elif "月前" in date_text:
            months = int(re.findall(r"\d+", date_text)[0])
            return datetime.utcnow() - timedelta(days=months*30)
        
        # 处理绝对时间
        try:
            # 尝试多种日期格式
            for fmt in ["%Y-%m-%d", "%Y年%m月%d日", "%m-%d", "%m月%d日"]:
                try:
                    date = datetime.strptime(date_text, fmt)
                    # 如果只有月日，补充年份
                    if date.year == 1900:
                        date = date.replace(year=datetime.utcnow().year)
                    return date
                except ValueError:
                    continue
        except:
            pass
        
        # 默认返回当前时间
        return datetime.utcnow()
```

### Task 6.2: 携程适配器实现

#### 6.2.1 携程适配器
```python
# src/adapters/ctrip/ctrip_adapter.py
"""携程适配器实现"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.adapters.base.adapter_interface import (
    PlatformAdapter, POI, Review, Article,
    SearchQuery, DataType
)
from src.core.engines.base.engine_interface import CrawlTask, EngineType
from src.core.scheduler.coordinator import coordinator
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.ctrip")

class CtripAdapter(PlatformAdapter):
    """携程适配器"""
    
    def __init__(self):
        super().__init__()
        self.platform = "ctrip"
        self.platform_name = "携程"
        self.base_url = "https://www.ctrip.com"
        self.api_base = "https://m.ctrip.com/restapi"
        self.supported_types = [DataType.POI, DataType.REVIEW, DataType.PRICE]
        
        # 城市编码映射
        self.city_map = {
            "北京": "1", "上海": "2", "广州": "32", "深圳": "30",
            "成都": "28", "杭州": "17", "南京": "12", "西安": "10",
            "重庆": "4", "武汉": "477", "苏州": "14", "天津": "3"
        }
    
    async def search_pois(self, query: SearchQuery) -> List[POI]:
        """搜索POI - 使用携程移动端API"""
        logger.info(f"Searching POIs on Ctrip: {query.keyword}")
        
        # 构建API请求
        city_id = self.city_map.get(query.city, "2")
        
        # 携程的搜索API
        api_url = f"{self.api_base}/soa2/18254/json/getPoiListByKeyword"
        
        # 请求体
        request_body = {
            "keyword": query.keyword,
            "cityId": city_id,
            "pageIndex": query.page,
            "pageSize": query.page_size,
            "sortType": 0,  # 0: 推荐排序
            "poiType": 0,   # 0: 全部类型
            "head": {
                "cid": "09031037211035410190",
                "ctok": "",
                "cver": "1.0",
                "lang": "01",
                "sid": "8888",
                "syscode": "09",
                "auth": "",
                "extension": []
            }
        }
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"ctrip_search_{query.keyword}_{query.page}",
            platform=self.platform,
            url=api_url,
            task_type="api",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "Referer": "https://m.ctrip.com/"
            },
            data=json.dumps(request_body),
            engine_type=EngineType.CRAWL4AI,  # API请求使用Crawl4AI
            use_proxy=True,
            metadata={"query": query.model_dump()}
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to search on Ctrip: {result.error_message}")
            return []
        
        # 解析API响应
        try:
            data = json.loads(result.text)
            if data.get("ResponseStatus", {}).get("Ack") != "Success":
                logger.error(f"Ctrip API error: {data.get('ResponseStatus')}")
                return []
            
            pois = []
            poi_list = data.get("poiList", [])
            
            for poi_data in poi_list:
                poi = await self._parse_api_poi(poi_data, query.city)
                if poi:
                    pois.append(poi)
            
            logger.info(f"Found {len(pois)} POIs on Ctrip")
            return pois
            
        except Exception as e:
            logger.error(f"Failed to parse Ctrip response: {str(e)}")
            return []
    
    async def get_poi_detail(self, poi_id: str) -> Optional[POI]:
        """获取POI详情"""
        logger.info(f"Getting POI detail from Ctrip: {poi_id}")
        
        # 构建详情API请求
        api_url = f"{self.api_base}/soa2/18254/json/getPoiDetailById"
        
        request_body = {
            "poiId": poi_id.replace("ctrip_", ""),
            "needReview": True,
            "needImage": True,
            "head": {
                "cid": "09031037211035410190",
                "ctok": "",
                "cver": "1.0",
                "lang": "01",
                "sid": "8888",
                "syscode": "09"
            }
        }
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"ctrip_detail_{poi_id}",
            platform=self.platform,
            url=api_url,
            task_type="api",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "Referer": "https://m.ctrip.com/"
            },
            data=json.dumps(request_body),
            engine_type=EngineType.CRAWL4AI,
            use_proxy=True
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to get POI detail from Ctrip: {result.error_message}")
            return None
        
        # 解析详情
        try:
            data = json.loads(result.text)
            if data.get("ResponseStatus", {}).get("Ack") != "Success":
                return None
            
            poi_detail = data.get("poiDetail", {})
            return await self._parse_detail_api_poi(poi_detail)
            
        except Exception as e:
            logger.error(f"Failed to parse Ctrip detail: {str(e)}")
            return None
    
    async def get_poi_reviews(
        self, 
        poi_id: str, 
        page: int = 1,
        limit: int = 20
    ) -> List[Review]:
        """获取POI评论"""
        logger.info(f"Getting reviews for POI {poi_id} from Ctrip")
        
        # 构建评论API请求
        api_url = f"{self.api_base}/soa2/18254/json/getPoiCommentList"
        
        request_body = {
            "poiId": poi_id.replace("ctrip_", ""),
            "pageIndex": page,
            "pageSize": limit,
            "sortType": 0,  # 0: 推荐排序
            "head": {
                "cid": "09031037211035410190",
                "ctok": "",
                "cver": "1.0",
                "lang": "01",
                "sid": "8888",
                "syscode": "09"
            }
        }
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"ctrip_reviews_{poi_id}_p{page}",
            platform=self.platform,
            url=api_url,
            task_type="api",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "Referer": "https://m.ctrip.com/"
            },
            data=json.dumps(request_body),
            engine_type=EngineType.CRAWL4AI,
            use_proxy=True
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to get reviews from Ctrip: {result.error_message}")
            return []
        
        # 解析评论
        try:
            data = json.loads(result.text)
            if data.get("ResponseStatus", {}).get("Ack") != "Success":
                return []
            
            reviews = []
            comment_list = data.get("commentList", [])
            
            for comment_data in comment_list:
                review = await self._parse_api_review(comment_data, poi_id)
                if review:
                    reviews.append(review)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Failed to parse Ctrip reviews: {str(e)}")
            return []
    
    async def _parse_api_poi(self, data: Dict[str, Any], city: str) -> Optional[POI]:
        """解析API返回的POI数据"""
        try:
            poi = POI(
                poi_id=f"ctrip_{data['poiId']}",
                platform=self.platform,
                platform_poi_id=str(data["poiId"]),
                name=data["poiName"],
                category=data.get("poiType"),
                tags=data.get("tags", []),
                city=city,
                district=data.get("districtName"),
                address=data.get("address"),
                latitude=data.get("lat"),
                longitude=data.get("lon"),
                rating=data.get("score"),
                rating_count=data.get("commentCount", 0),
                review_count=data.get("commentCount", 0),
                price=data.get("price"),
                price_unit="元" if data.get("price") else None,
                cover_image=data.get("imageUrl"),
                description=data.get("introduce")
            )
            
            return poi
            
        except Exception as e:
            logger.error(f"Error parsing API POI: {str(e)}")
            return None
    
    async def _parse_detail_api_poi(self, data: Dict[str, Any]) -> Optional[POI]:
        """解析详情API返回的POI数据"""
        try:
            # 解析营业时间
            business_hours = {}
            if data.get("openTime"):
                business_hours["default"] = data["openTime"]
            
            # 解析特色
            features = {}
            if data.get("features"):
                for i, feature in enumerate(data["features"]):
                    features[f"feature_{i+1}"] = feature
            
            # 解析图片
            images = []
            if data.get("imageList"):
                images = [img.get("imageUrl") for img in data["imageList"] if img.get("imageUrl")]
            
            poi = POI(
                poi_id=f"ctrip_{data['poiId']}",
                platform=self.platform,
                platform_poi_id=str(data["poiId"]),
                name=data["poiName"],
                category=data.get("poiType"),
                tags=data.get("tags", []),
                city=data.get("cityName"),
                district=data.get("districtName"),
                address=data.get("address"),
                latitude=data.get("lat"),
                longitude=data.get("lon"),
                rating=data.get("score"),
                rating_count=data.get("commentCount", 0),
                review_count=data.get("commentCount", 0),
                price=data.get("price"),
                price_unit="元" if data.get("price") else None,
                phone=data.get("phone"),
                website=data.get("website"),
                business_hours=business_hours,
                description=data.get("introduce"),
                features=features,
                images=images,
                cover_image=images[0] if images else None
            )
            
            return poi
            
        except Exception as e:
            logger.error(f"Error parsing detail API POI: {str(e)}")
            return None
    
    async def _parse_api_review(self, data: Dict[str, Any], poi_id: str) -> Optional[Review]:
        """解析API返回的评论数据"""
        try:
            # 解析时间
            created_at = datetime.fromisoformat(
                data["commentTime"].replace("Z", "+00:00")
            ) if data.get("commentTime") else datetime.utcnow()
            
            # 解析图片
            images = []
            if data.get("imageList"):
                images = [img.get("imageUrl") for img in data["imageList"] if img.get("imageUrl")]
            
            review = Review(
                review_id=f"ctrip_{data['commentId']}",
                poi_id=poi_id,
                platform=self.platform,
                platform_review_id=str(data["commentId"]),
                content=data.get("content", ""),
                rating=data.get("score"),
                author_id=str(data.get("userId")),
                author_name=data.get("userNick"),
                useful_count=data.get("usefulCount", 0),
                reply_count=data.get("replyCount", 0),
                images=images,
                created_at=created_at
            )
            
            return review
            
        except Exception as e:
            logger.error(f"Error parsing API review: {str(e)}")
            return None
```

### Task 6.3: 抖音适配器实现

#### 6.3.1 抖音适配器
```python
# src/adapters/douyin/douyin_adapter.py
"""抖音适配器实现"""
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote

from src.adapters.base.adapter_interface import (
    PlatformAdapter, POI, Review, Article,
    SearchQuery, DataType
)
from src.core.engines.base.engine_interface import CrawlTask, EngineType
from src.core.scheduler.coordinator import coordinator
from src.anti_detection.behavior.simulator import BehaviorSimulator
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.douyin")

class DouyinAdapter(PlatformAdapter):
    """抖音适配器"""
    
    def __init__(self):
        super().__init__()
        self.platform = "douyin"
        self.platform_name = "抖音"
        self.base_url = "https://www.douyin.com"
        self.supported_types = [DataType.POI, DataType.VIDEO, DataType.ARTICLE]
        
        # 抖音需要特殊的请求签名
        self.api_params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "version_code": "170400",
            "version_name": "17.4.0",
            "cookie_enabled": "true",
            "screen_width": "1920",
            "screen_height": "1080",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "120.0.0.0"
        }
    
    async def search_pois(self, query: SearchQuery) -> List[POI]:
        """搜索POI - 抖音位置搜索"""
        logger.info(f"Searching POIs on Douyin: {query.keyword}")
        
        # 抖音搜索URL
        search_url = f"{self.base_url}/aweme/v1/web/search/item/"
        
        # 搜索参数
        params = {
            **self.api_params,
            "keyword": query.keyword,
            "search_channel": "aweme_poi",
            "sort_type": "0",
            "publish_time": "0",
            "offset": (query.page - 1) * query.page_size,
            "count": query.page_size
        }
        
        # 需要生成签名
        params["_signature"] = await self._generate_signature(params)
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"douyin_search_{query.keyword}_{query.page}",
            platform=self.platform,
            url=search_url,
            task_type="api",
            method="GET",
            params=params,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.douyin.com/search",
                "Cookie": await self._get_cookie()
            },
            engine_type=EngineType.CRAWL4AI,
            use_proxy=True,
            use_fingerprint=True,
            metadata={"query": query.model_dump()}
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to search on Douyin: {result.error_message}")
            return []
        
        # 解析结果
        try:
            data = json.loads(result.text)
            if data.get("status_code") != 0:
                logger.error(f"Douyin API error: {data.get('status_msg')}")
                return []
            
            pois = []
            poi_list = data.get("data", [])
            
            for item in poi_list:
                if item.get("type") == 1:  # POI类型
                    poi = await self._parse_search_poi(item, query.city)
                    if poi:
                        pois.append(poi)
            
            logger.info(f"Found {len(pois)} POIs on Douyin")
            return pois
            
        except Exception as e:
            logger.error(f"Failed to parse Douyin response: {str(e)}")
            return []
    
    async def get_poi_detail(self, poi_id: str) -> Optional[POI]:
        """获取POI详情"""
        logger.info(f"Getting POI detail from Douyin: {poi_id}")
        
        # POI详情页面URL
        detail_url = f"{self.base_url}/location/{poi_id.replace('douyin_', '')}"
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"douyin_detail_{poi_id}",
            platform=self.platform,
            url=detail_url,
            task_type="detail",
            engine_type=EngineType.MEDIACRAWL,
            engine_config={
                "wait_selector": ".location-info",
                "wait_timeout": 10,
                "execute_script": """
                    // 滚动加载更多内容
                    window.scrollTo(0, document.body.scrollHeight);
                    await new Promise(r => setTimeout(r, 2000));
                    
                    // 提取数据
                    const data = window.__INITIAL_STATE__ || {};
                    return JSON.stringify(data);
                """
            },
            use_fingerprint=True,
            use_behavior_simulation=True
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to get POI detail from Douyin: {result.error_message}")
            return None
        
        # 解析详情
        try:
            # 从页面中提取初始数据
            initial_data_match = re.search(
                r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?})</script>',
                result.html,
                re.DOTALL
            )
            
            if initial_data_match:
                data = json.loads(initial_data_match.group(1))
                location_data = data.get("locationDetail", {})
                return await self._parse_detail_poi(location_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse Douyin detail: {str(e)}")
            return None
    
    async def get_poi_reviews(
        self, 
        poi_id: str, 
        page: int = 1,
        limit: int = 20
    ) -> List[Review]:
        """获取POI相关视频作为评论"""
        logger.info(f"Getting videos for POI {poi_id} from Douyin")
        
        # 获取位置相关视频
        api_url = f"{self.base_url}/aweme/v1/web/poi/detail/video"
        
        params = {
            **self.api_params,
            "poi_id": poi_id.replace("douyin_", ""),
            "cursor": (page - 1) * limit,
            "count": limit
        }
        
        params["_signature"] = await self._generate_signature(params)
        
        # 创建爬取任务
        task = CrawlTask(
            task_id=f"douyin_videos_{poi_id}_p{page}",
            platform=self.platform,
            url=api_url,
            task_type="api",
            method="GET",
            params=params,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": f"https://www.douyin.com/location/{poi_id.replace('douyin_', '')}",
                "Cookie": await self._get_cookie()
            },
            engine_type=EngineType.CRAWL4AI,
            use_proxy=True
        )
        
        # 执行爬取
        result = await coordinator.execute_task(task)
        
        if not result.success:
            logger.error(f"Failed to get videos from Douyin: {result.error_message}")
            return []
        
        # 解析视频作为评论
        try:
            data = json.loads(result.text)
            if data.get("status_code") != 0:
                return []
            
            reviews = []
            video_list = data.get("aweme_list", [])
            
            for video_data in video_list:
                review = await self._parse_video_as_review(video_data, poi_id)
                if review:
                    reviews.append(review)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Failed to parse Douyin videos: {str(e)}")
            return []
    
    async def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成抖音API签名"""
        # 这里需要实现抖音的签名算法
        # 实际实现较复杂，涉及JS逆向
        # 这里返回一个占位符
        return "signature_placeholder"
    
    async def _get_cookie(self) -> str:
        """获取有效的Cookie"""
        # 需要维护有效的Cookie池
        return "ttwid=xxx; s_v_web_id=xxx"
    
    async def _parse_search_poi(self, data: Dict[str, Any], city: str) -> Optional[POI]:
        """解析搜索结果中的POI"""
        try:
            poi_info = data.get("poi_info", {})
            
            poi = POI(
                poi_id=f"douyin_{poi_info['poi_id']}",
                platform=self.platform,
                platform_poi_id=poi_info["poi_id"],
                name=poi_info["poi_name"],
                category=poi_info.get("type_name"),
                tags=[poi_info.get("type_name")] if poi_info.get("type_name") else [],
                city=city or poi_info.get("city_name"),
                district=poi_info.get("district"),
                address=poi_info.get("address"),
                latitude=poi_info.get("latitude"),
                longitude=poi_info.get("longitude"),
                cover_image=poi_info.get("cover", {}).get("url_list", [""])[0],
                description=poi_info.get("poi_detail_desc")
            )
            
            # 从相关视频统计评论数
            if data.get("aweme_info"):
                poi.review_count = data["aweme_info"].get("aweme_count", 0)
            
            return poi
            
        except Exception as e:
            logger.error(f"Error parsing search POI: {str(e)}")
            return None
    
    async def _parse_detail_poi(self, data: Dict[str, Any]) -> Optional[POI]:
        """解析POI详情"""
        try:
            poi = POI(
                poi_id=f"douyin_{data['poi_id']}",
                platform=self.platform,
                platform_poi_id=data["poi_id"],
                name=data["poi_name"],
                category=data.get("type_name"),
                tags=data.get("tags", []),
                city=data.get("city_name"),
                district=data.get("district"),
                address=data.get("address"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                phone=data.get("contact_phone"),
                business_hours={
                    "default": data.get("open_time", "")
                } if data.get("open_time") else {},
                description=data.get("poi_detail_desc"),
                features={
                    "video_count": data.get("video_count", 0),
                    "visitor_count": data.get("visitor_count", 0),
                    "collect_count": data.get("collect_count", 0)
                },
                images=data.get("photos", []),
                cover_image=data.get("cover", {}).get("url_list", [""])[0]
            )
            
            return poi
            
        except Exception as e:
            logger.error(f"Error parsing detail POI: {str(e)}")
            return None
    
    async def _parse_video_as_review(self, data: Dict[str, Any], poi_id: str) -> Optional[Review]:
        """将视频解析为评论"""
        try:
            # 抖音视频作为POI的"评论"
            author = data.get("author", {})
            statistics = data.get("statistics", {})
            
            # 创建时间
            create_time = data.get("create_time", 0)
            created_at = datetime.fromtimestamp(create_time) if create_time else datetime.utcnow()
            
            # 视频封面作为图片
            images = []
            if data.get("video", {}).get("cover"):
                cover_url = data["video"]["cover"].get("url_list", [""])[0]
                if cover_url:
                    images.append(cover_url)
            
            review = Review(
                review_id=f"douyin_video_{data['aweme_id']}",
                poi_id=poi_id,
                platform=self.platform,
                platform_review_id=data["aweme_id"],
                content=data.get("desc", ""),
                author_id=author.get("uid"),
                author_name=author.get("nickname"),
                useful_count=statistics.get("digg_count", 0),
                reply_count=statistics.get("comment_count", 0),
                images=images,
                created_at=created_at,
                # 额外信息
                metadata={
                    "video_url": data.get("video", {}).get("play_addr", {}).get("url_list", [""])[0],
                    "share_count": statistics.get("share_count", 0),
                    "play_count": statistics.get("play_count", 0)
                }
            )
            
            return review
            
        except Exception as e:
            logger.error(f"Error parsing video as review: {str(e)}")
            return None
```

### Task 6.4: 高级平台验证脚本

#### 6.4.1 高级平台测试脚本
```python
# scripts/test/test_advanced_adapters.py
"""高级平台适配器测试脚本"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.adapters.factory import adapter_factory
from src.adapters.dianping.dianping_adapter import DianpingAdapter
from src.adapters.ctrip.ctrip_adapter import CtripAdapter
from src.adapters.douyin.douyin_adapter import DouyinAdapter
from src.adapters.base.adapter_interface import SearchQuery
from src.utils.logger.logger import get_logger

logger = get_logger("test.advanced_adapters")

async def test_dianping_adapter():
    """测试大众点评适配器"""
    logger.info("Testing Dianping adapter...")
    
    # 注册适配器
    adapter = DianpingAdapter()
    adapter_factory.register("dianping", adapter)
    
    # 测试搜索
    query = SearchQuery(
        keyword="北京烤鸭",
        city="北京",
        page=1,
        page_size=5
    )
    
    try:
        pois = await adapter.search_pois(query)
        logger.info(f"Found {len(pois)} POIs on Dianping")
        
        if pois:
            # 测试详情获取
            poi = pois[0]
            logger.info(f"Testing detail for: {poi.name}")
            
            detail = await adapter.get_poi_detail(
                poi.platform_poi_id
            )
            
            if detail:
                logger.info(f"Got detail: {detail.name}")
                logger.info(f"  Address: {detail.address}")
                logger.info(f"  Rating: {detail.rating}")
                logger.info(f"  Phone: {detail.phone}")
                
                # 测试评论获取
                reviews = await adapter.get_poi_reviews(
                    poi.platform_poi_id,
                    limit=3
                )
                logger.info(f"Got {len(reviews)} reviews")
                
                for review in reviews:
                    logger.info(f"  Review by {review.author_name}: {review.content[:50]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Dianping test failed: {str(e)}")
        return False

async def test_ctrip_adapter():
    """测试携程适配器"""
    logger.info("\nTesting Ctrip adapter...")
    
    # 注册适配器
    adapter = CtripAdapter()
    adapter_factory.register("ctrip", adapter)
    
    # 测试搜索
    query = SearchQuery(
        keyword="外滩",
        city="上海",
        page=1,
        page_size=5
    )
    
    try:
        pois = await adapter.search_pois(query)
        logger.info(f"Found {len(pois)} POIs on Ctrip")
        
        if pois:
            # 测试详情获取
            poi = pois[0]
            logger.info(f"Testing detail for: {poi.name}")
            
            detail = await adapter.get_poi_detail(
                poi.poi_id
            )
            
            if detail:
                logger.info(f"Got detail: {detail.name}")
                logger.info(f"  Category: {detail.category}")
                logger.info(f"  Rating: {detail.rating}")
                logger.info(f"  Price: {detail.price} {detail.price_unit}")
                
                # 测试评论获取
                reviews = await adapter.get_poi_reviews(
                    poi.poi_id,
                    limit=3
                )
                logger.info(f"Got {len(reviews)} reviews")
        
        return True
        
    except Exception as e:
        logger.error(f"Ctrip test failed: {str(e)}")
        return False

async def test_douyin_adapter():
    """测试抖音适配器"""
    logger.info("\nTesting Douyin adapter...")
    
    # 注册适配器
    adapter = DouyinAdapter()
    adapter_factory.register("douyin", adapter)
    
    # 测试搜索
    query = SearchQuery(
        keyword="成都大熊猫基地",
        city="成都",
        page=1,
        page_size=5
    )
    
    try:
        pois = await adapter.search_pois(query)
        logger.info(f"Found {len(pois)} POIs on Douyin")
        
        if pois:
            # 测试详情获取
            poi = pois[0]
            logger.info(f"Testing detail for: {poi.name}")
            
            detail = await adapter.get_poi_detail(
                poi.poi_id
            )
            
            if detail:
                logger.info(f"Got detail: {detail.name}")
                logger.info(f"  Video count: {detail.features.get('video_count', 0)}")
                logger.info(f"  Visitor count: {detail.features.get('visitor_count', 0)}")
                
                # 测试视频获取（作为评论）
                videos = await adapter.get_poi_reviews(
                    poi.poi_id,
                    limit=3
                )
                logger.info(f"Got {len(videos)} videos")
                
                for video in videos:
                    logger.info(f"  Video by {video.author_name}: {video.content[:50]}...")
                    logger.info(f"    Likes: {video.useful_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Douyin test failed: {str(e)}")
        return False

async def test_all_advanced_adapters():
    """测试所有高级适配器"""
    results = {
        "dianping": False,
        "ctrip": False,
        "douyin": False
    }
    
    # 测试大众点评
    try:
        results["dianping"] = await test_dianping_adapter()
    except Exception as e:
        logger.error(f"Dianping test error: {str(e)}")
    
    # 测试携程
    try:
        results["ctrip"] = await test_ctrip_adapter()
    except Exception as e:
        logger.error(f"Ctrip test error: {str(e)}")
    
    # 测试抖音
    try:
        results["douyin"] = await test_douyin_adapter()
    except Exception as e:
        logger.error(f"Douyin test error: {str(e)}")
    
    # 显示结果
    logger.info("\n" + "="*50)
    logger.info("Advanced Adapter Test Results:")
    logger.info("="*50)
    
    for platform, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{platform.capitalize()}: {status}")
    
    # 整体结果
    all_passed = all(results.values())
    if all_passed:
        logger.info("\n✅ All advanced adapter tests passed!")
    else:
        logger.info("\n❌ Some advanced adapter tests failed!")
    
    return all_passed

async def main():
    """主测试函数"""
    try:
        # 确保基础服务运行
        logger.info("Starting advanced adapter tests...")
        logger.info("Note: Make sure Redis and other services are running")
        
        # 运行测试
        success = await test_all_advanced_adapters()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 6.4.2 适配器注册脚本
```python
# scripts/setup/register_all_adapters.py
"""注册所有平台适配器"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.adapters.factory import adapter_factory
from src.adapters.amap.amap_adapter import AmapAdapter
from src.adapters.mafengwo.mafengwo_adapter import MafengwoAdapter
from src.adapters.xiaohongshu.xiaohongshu_adapter import XiaohongshuAdapter
from src.adapters.dianping.dianping_adapter import DianpingAdapter
from src.adapters.ctrip.ctrip_adapter import CtripAdapter
from src.adapters.douyin.douyin_adapter import DouyinAdapter
from src.adapters.weibo.weibo_adapter import WeiboAdapter
from src.adapters.bilibili.bilibili_adapter import BilibiliAdapter
from src.utils.logger.logger import get_logger

logger = get_logger("setup.adapters")

def register_all_adapters():
    """注册所有平台适配器"""
    logger.info("Registering all platform adapters...")
    
    adapters = [
        ("amap", AmapAdapter),
        ("mafengwo", MafengwoAdapter),
        ("xiaohongshu", XiaohongshuAdapter),
        ("dianping", DianpingAdapter),
        ("ctrip", CtripAdapter),
        ("douyin", DouyinAdapter),
        ("weibo", WeiboAdapter),
        ("bilibili", BilibiliAdapter)
    ]
    
    registered = []
    failed = []
    
    for platform_id, adapter_class in adapters:
        try:
            adapter = adapter_class()
            adapter_factory.register(platform_id, adapter)
            registered.append(platform_id)
            logger.info(f"✅ Registered {platform_id} adapter")
        except Exception as e:
            failed.append((platform_id, str(e)))
            logger.error(f"❌ Failed to register {platform_id}: {str(e)}")
    
    # 显示结果
    logger.info("\n" + "="*50)
    logger.info("Adapter Registration Summary:")
    logger.info("="*50)
    logger.info(f"Successfully registered: {len(registered)}")
    logger.info(f"Failed: {len(failed)}")
    
    if registered:
        logger.info("\nRegistered adapters:")
        for platform in registered:
            logger.info(f"  - {platform}")
    
    if failed:
        logger.info("\nFailed adapters:")
        for platform, error in failed:
            logger.info(f"  - {platform}: {error}")
    
    # 显示支持的平台
    logger.info("\nSupported platforms:")
    for platform in adapter_factory.get_supported_platforms():
        adapter = adapter_factory.get_adapter(platform)
        logger.info(f"  - {platform}: {adapter.platform_name}")
        logger.info(f"    Supported types: {', '.join(adapter.supported_types)}")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = register_all_adapters()
    if not success:
        sys.exit(1)
```

---

## 执行验证

### Claude Code执行步骤：

1. **注册所有适配器**：
```bash
cd /Users/xiao/Documents/BaiduNetSyncDownload/CodeDev/CrawlPOIData/travel-crawler-system
python scripts/setup/register_all_adapters.py
```

预期输出：
- 显示所有8个平台适配器注册成功
- 列出每个平台支持的数据类型

2. **测试高级适配器**：
```bash
python scripts/test/test_advanced_adapters.py
```

预期输出：
- 大众点评适配器测试通过
- 携程适配器测试通过
- 抖音适配器测试通过
- 显示获取的POI和评论样例

## 注意事项

1. **反爬处理**：
   - 大众点评：需要处理CSS加密、SVG字体加密
   - 携程：需要处理API签名验证
   - 抖音：需要处理_signature参数生成

2. **Cookie管理**：
   - 各平台都需要维护有效的Cookie池
   - 定期更新Cookie避免失效

3. **请求频率**：
   - 严格控制请求频率
   - 使用代理池轮换
   - 模拟人类行为

4. **数据解析**：
   - 各平台数据结构差异大
   - 需要针对性的解析逻辑
   - 处理动态加载和加密数据

## 下一步

完成高级平台适配器后，还需要实现：
- 微博适配器（社交媒体数据）
- B站适配器（视频数据）
- 监控与日志系统
- 生产环境部署配置