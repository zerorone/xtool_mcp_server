# 旅游平台数据爬虫系统 - AI编程实现TODO详细清单（第3部分）

> 本文档为AI编程实现TODO详细清单的第三部分，包含第6-7阶段的详细任务

## 前情提要

已完成部分：
- ✅ 第1阶段：项目初始化与基础架构
- ✅ 第2阶段：双引擎核心架构
- ✅ 第3阶段：反爬系统实现
- ✅ 第4阶段：平台适配器实现（第一批）
- ✅ 第5阶段：数据处理与API服务

本文档继续：
- 📝 第6阶段：高级平台适配器实现
- 📝 第7阶段：监控运维与部署

---

# 第六阶段：高级平台适配器实现 [Priority: HIGH] [Time: 7-8天]

## 6.1 小红书适配器

### 6.1.1 小红书数据爬取

#### 6.1.1.1 实现小红书适配器基础 [Time: 5h]
```python
# src/adapters/xiaohongshu/adapter.py
import asyncio
import json
import hashlib
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from src.adapters.base.adapter_interface import PlatformAdapter
from src.engines.base.engine_interface import CrawlTask, EngineType
from src.core.anti_detection.fingerprint_manager import FingerprintManager
from src.core.anti_detection.behavior_simulator import BehaviorSimulator
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.xiaohongshu")

class XiaohongshuAdapter(PlatformAdapter):
    """小红书适配器"""
    
    def __init__(self):
        super().__init__()
        self.platform_name = "xiaohongshu"
        self.base_url = "https://www.xiaohongshu.com"
        self.api_base = "https://edith.xiaohongshu.com/api/sns/web/v1"
        
        # 反爬配置
        self.fingerprint_manager = FingerprintManager()
        self.behavior_simulator = BehaviorSimulator()
        
        # 请求头配置
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.xiaohongshu.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://www.xiaohongshu.com"
        }
    
    async def search_notes(
        self, 
        keyword: str, 
        page: int = 1, 
        sort_type: str = "general"
    ) -> List[Dict[str, Any]]:
        """搜索笔记"""
        try:
            # 生成签名
            params = {
                "keyword": keyword,
                "page": page,
                "page_size": 20,
                "search_id": self._generate_search_id(),
                "sort": sort_type,
                "note_type": 0
            }
            
            # 添加签名参数
            params.update(self._generate_signature(params))
            
            # 构建URL
            search_url = f"{self.api_base}/homefeed"
            
            # 创建爬取任务 - 使用MediaCrawl引擎
            task = CrawlTask(
                task_id=f"xhs_search_{keyword}_{page}",
                platform="xiaohongshu",
                url=search_url,
                headers=self.headers,
                params=params,
                engine_type=EngineType.MEDIACRAWL,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_search_results(result.json_data)
            else:
                logger.error(f"Xiaohongshu search failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Xiaohongshu search error: {e}")
            return []
    
    async def get_note_detail(self, note_id: str) -> Optional[Dict[str, Any]]:
        """获取笔记详情"""
        try:
            # 构建详情URL
            detail_url = f"{self.base_url}/discovery/item/{note_id}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"xhs_detail_{note_id}",
                platform="xiaohongshu",
                url=detail_url,
                headers=self.headers,
                engine_type=EngineType.MEDIACRAWL,
                extraction_rules={
                    "text_selectors": {
                        "title": "h1.title",
                        "content": "div.content",
                        "tags": "span.tag"
                    },
                    "attr_selectors": {
                        "images": {
                            "selector": "div.swiper-slide img",
                            "attribute": "src"
                        }
                    },
                    "js_extractors": {
                        "interaction_data": """
                        (() => {
                            const likeElement = document.querySelector('.like-wrapper');
                            const collectElement = document.querySelector('.collect-wrapper');
                            const commentElement = document.querySelector('.comment-wrapper');
                            
                            return {
                                likes: likeElement ? likeElement.innerText : '0',
                                collects: collectElement ? collectElement.innerText : '0',
                                comments: commentElement ? commentElement.innerText : '0'
                            };
                        })()
                        """
                    }
                },
                timeout=30
            )
            
            # 模拟人类行为
            await self.behavior_simulator.simulate_human_behavior(
                task.metadata.get("page"), 
                "scroll"
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success:
                return await self._parse_note_detail(result)
            else:
                logger.error(f"Xiaohongshu detail failed: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Xiaohongshu detail error: {e}")
            return None
    
    def _generate_search_id(self) -> str:
        """生成搜索ID"""
        timestamp = str(int(time.time() * 1000))
        random_str = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"{timestamp}_{random_str}"
    
    def _generate_signature(self, params: Dict[str, Any]) -> Dict[str, str]:
        """生成签名参数"""
        # 小红书的签名算法比较复杂，这里简化处理
        # 实际需要逆向工程获取完整算法
        
        # X-S签名
        x_s = self._calculate_x_s(params)
        
        # X-T时间戳
        x_t = str(int(time.time() * 1000))
        
        return {
            "X-S": x_s,
            "X-T": x_t,
            "X-S-Common": self._calculate_x_s_common()
        }
    
    def _calculate_x_s(self, params: Dict[str, Any]) -> str:
        """计算X-S签名"""
        # 简化的签名算法示例
        sorted_params = sorted(params.items())
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # 添加盐值
        salt = "xiaohongshu_salt_2024"
        sign_str = f"{param_str}{salt}"
        
        # 计算MD5
        return hashlib.md5(sign_str.encode()).hexdigest()
    
    def _calculate_x_s_common(self) -> str:
        """计算X-S-Common参数"""
        # 包含设备信息等
        common_data = {
            "s0": "0",  # 平台类型
            "s1": "",   # 会话ID
            "x0": "1",  # 版本号
            "x1": "3.6.8",  # 应用版本
            "x2": "Windows",
            "x3": "xhs-pc-web",
            "x4": "1.4.4",
            "x5": self._generate_device_id(),
            "x6": "main_1.4.4",
            "x7": "0",
            "x8": "0",
            "x9": "10.15.7",
            "x10": "undefined"
        }
        
        return ";".join([f"{k}={v}" for k, v in common_data.items()])
    
    def _generate_device_id(self) -> str:
        """生成设备ID"""
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
    
    async def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        notes = []
        
        try:
            if "data" in data and "items" in data["data"]:
                for item in data["data"]["items"]:
                    note_card = item.get("note_card", {})
                    note = await self._extract_note_info(note_card)
                    if note:
                        notes.append(note)
            
            return notes
            
        except Exception as e:
            logger.error(f"Parse search results error: {e}")
            return notes
    
    async def _extract_note_info(self, note_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取笔记信息"""
        try:
            note = {
                "platform": "xiaohongshu",
                "note_id": note_data.get("note_id", ""),
                "title": note_data.get("title", ""),
                "desc": note_data.get("desc", ""),
                "type": note_data.get("type", "normal"),
                "user": {
                    "user_id": note_data.get("user", {}).get("user_id", ""),
                    "nickname": note_data.get("user", {}).get("nickname", ""),
                    "avatar": note_data.get("user", {}).get("avatar", "")
                },
                "interact_info": {
                    "liked_count": note_data.get("interact_info", {}).get("liked_count", 0),
                    "collected_count": note_data.get("interact_info", {}).get("collected_count", 0),
                    "comment_count": note_data.get("interact_info", {}).get("comment_count", 0)
                },
                "image_list": [img.get("url", "") for img in note_data.get("image_list", [])],
                "tag_list": [tag.get("name", "") for tag in note_data.get("tag_list", [])],
                "at_user_list": note_data.get("at_user_list", []),
                "time": note_data.get("time", 0),
                "last_update_time": note_data.get("last_update_time", 0)
            }
            
            # 如果是视频笔记，添加视频信息
            if note["type"] == "video":
                note["video_info"] = {
                    "url": note_data.get("video", {}).get("url", ""),
                    "cover": note_data.get("video", {}).get("cover", {}).get("url", ""),
                    "duration": note_data.get("video", {}).get("duration", 0)
                }
            
            return note
            
        except Exception as e:
            logger.error(f"Extract note info error: {e}")
            return None
    
    async def _parse_note_detail(self, crawl_result) -> Dict[str, Any]:
        """解析笔记详情"""
        try:
            detail = {
                "platform": "xiaohongshu",
                "extracted_data": crawl_result.extracted_data,
                "html_content": crawl_result.html,
                "url": crawl_result.url
            }
            
            # 从提取的数据中获取详细信息
            if crawl_result.extracted_data:
                detail.update({
                    "title": crawl_result.extracted_data.get("title", [""])[0],
                    "content": "\n".join(crawl_result.extracted_data.get("content", [])),
                    "tags": crawl_result.extracted_data.get("tags", []),
                    "images": crawl_result.extracted_data.get("images", []),
                    "interaction": crawl_result.extracted_data.get("interaction_data", {})
                })
            
            return detail
            
        except Exception as e:
            logger.error(f"Parse note detail error: {e}")
            return {}
```

**验证标准**：小红书适配器基础功能实现完成，支持笔记搜索和详情获取

#### 6.1.1.2 实现小红书数据处理 [Time: 3h]
```python
# src/adapters/xiaohongshu/processor.py
import re
from typing import Dict, Any, List
from datetime import datetime
from src.processors.cleaner.base_cleaner import DataCleaner
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.xiaohongshu.processor")

class XiaohongshuDataProcessor:
    """小红书数据处理器"""
    
    def __init__(self):
        self.emoji_pattern = re.compile("[\U00010000-\U0010ffff]", flags=re.UNICODE)
        self.mention_pattern = re.compile(r'@[\w\u4e00-\u9fa5]+')
        self.topic_pattern = re.compile(r'#[^#]+#')
    
    async def process_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理笔记数据"""
        try:
            # 基础清洗
            processed = await self._clean_basic_info(note_data)
            
            # 提取结构化信息
            processed = await self._extract_structured_info(processed)
            
            # 计算质量分数
            processed["quality_score"] = await self._calculate_quality_score(processed)
            
            # 分类标记
            processed["categories"] = await self._categorize_note(processed)
            
            return processed
            
        except Exception as e:
            logger.error(f"Process note error: {e}")
            return note_data
    
    async def _clean_basic_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗基础信息"""
        # 清理标题
        if "title" in data:
            data["title"] = self._clean_text(data["title"])
        
        # 清理描述
        if "desc" in data:
            data["desc"] = self._clean_text(data["desc"])
        
        # 清理内容
        if "content" in data:
            data["content"] = self._clean_text(data["content"])
        
        # 标准化时间
        if "time" in data and isinstance(data["time"], (int, float)):
            data["created_at"] = datetime.fromtimestamp(data["time"] / 1000).isoformat()
        
        return data
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 保留emoji（小红书特色）
        # text = self.emoji_pattern.sub("", text)
        
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 清理特殊字符
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        return text.strip()
    
    async def _extract_structured_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取结构化信息"""
        content = data.get("content", "") + " " + data.get("desc", "")
        
        # 提取@用户
        mentions = self.mention_pattern.findall(content)
        data["mentioned_users"] = list(set(mentions))
        
        # 提取话题标签
        topics = self.topic_pattern.findall(content)
        data["topics"] = list(set(topics))
        
        # 提取POI信息
        poi_info = await self._extract_poi_info(content, data.get("tags", []))
        if poi_info:
            data["poi_info"] = poi_info
        
        # 提取价格信息
        prices = await self._extract_prices(content)
        if prices:
            data["mentioned_prices"] = prices
        
        return data
    
    async def _extract_poi_info(self, content: str, tags: List[str]) -> Optional[Dict[str, Any]]:
        """提取POI信息"""
        poi_info = {}
        
        # 从标签中提取位置
        location_keywords = ["位于", "地址", "坐标", "地点"]
        for tag in tags:
            for keyword in location_keywords:
                if keyword in tag:
                    poi_info["location_tag"] = tag
                    break
        
        # 从内容中提取地址
        address_pattern = r'(?:地址|位于|在)[：:]?\s*([^，。,\n]+)'
        match = re.search(address_pattern, content)
        if match:
            poi_info["address"] = match.group(1).strip()
        
        # 提取店名
        shop_pattern = r'(?:店名|餐厅|酒店|民宿)[：:]?\s*([^，。,\n]+)'
        match = re.search(shop_pattern, content)
        if match:
            poi_info["name"] = match.group(1).strip()
        
        return poi_info if poi_info else None
    
    async def _extract_prices(self, content: str) -> List[Dict[str, Any]]:
        """提取价格信息"""
        prices = []
        
        # 价格模式
        price_patterns = [
            r'(?:￥|¥|人民币|RMB|rmb)\s*(\d+(?:\.\d{1,2})?)',
            r'(\d+(?:\.\d{1,2})?)\s*(?:元|块)',
            r'(?:价格|价位|人均)[：:]?\s*(\d+(?:\.\d{1,2})?)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    price = float(match)
                    prices.append({
                        "amount": price,
                        "currency": "CNY",
                        "context": self._get_price_context(content, match)
                    })
                except ValueError:
                    continue
        
        return prices
    
    def _get_price_context(self, content: str, price_str: str) -> str:
        """获取价格上下文"""
        try:
            index = content.find(price_str)
            start = max(0, index - 20)
            end = min(len(content), index + len(price_str) + 20)
            return content[start:end].strip()
        except:
            return ""
    
    async def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """计算内容质量分数"""
        score = 0.0
        
        # 内容长度（20%）
        content_length = len(data.get("content", "")) + len(data.get("desc", ""))
        if content_length > 500:
            score += 0.2
        elif content_length > 200:
            score += 0.15
        elif content_length > 100:
            score += 0.1
        
        # 图片数量（20%）
        image_count = len(data.get("image_list", []))
        if image_count >= 9:
            score += 0.2
        elif image_count >= 6:
            score += 0.15
        elif image_count >= 3:
            score += 0.1
        
        # 互动数据（30%）
        interact = data.get("interact_info", {})
        total_interact = (
            interact.get("liked_count", 0) + 
            interact.get("collected_count", 0) * 2 + 
            interact.get("comment_count", 0) * 3
        )
        
        if total_interact > 10000:
            score += 0.3
        elif total_interact > 5000:
            score += 0.25
        elif total_interact > 1000:
            score += 0.2
        elif total_interact > 100:
            score += 0.1
        
        # 标签和话题（15%）
        tag_count = len(data.get("tag_list", [])) + len(data.get("topics", []))
        if tag_count >= 5:
            score += 0.15
        elif tag_count >= 3:
            score += 0.1
        elif tag_count >= 1:
            score += 0.05
        
        # POI信息（15%）
        if data.get("poi_info"):
            score += 0.15
        
        return round(score, 2)
    
    async def _categorize_note(self, data: Dict[str, Any]) -> List[str]:
        """分类笔记"""
        categories = []
        
        content = (data.get("content", "") + " " + 
                  data.get("title", "") + " " + 
                  " ".join(data.get("tag_list", [])))
        
        # 旅游相关
        travel_keywords = ["旅游", "旅行", "攻略", "景点", "打卡", "出游", "行程"]
        if any(keyword in content for keyword in travel_keywords):
            categories.append("travel")
        
        # 美食相关
        food_keywords = ["美食", "餐厅", "好吃", "推荐", "人均", "口味", "必吃"]
        if any(keyword in content for keyword in food_keywords):
            categories.append("food")
        
        # 住宿相关
        hotel_keywords = ["酒店", "民宿", "住宿", "客房", "入住", "预订"]
        if any(keyword in content for keyword in hotel_keywords):
            categories.append("accommodation")
        
        # 购物相关
        shopping_keywords = ["购物", "买", "店", "商场", "特产", "伴手礼"]
        if any(keyword in content for keyword in shopping_keywords):
            categories.append("shopping")
        
        # 默认分类
        if not categories:
            categories.append("other")
        
        return categories
```

**验证标准**：小红书数据处理器实现完成，支持内容清洗和结构化提取

## 6.2 抖音适配器

### 6.2.1 抖音视频数据爬取

#### 6.2.1.1 实现抖音适配器基础 [Time: 5h]
```python
# src/adapters/douyin/adapter.py
import asyncio
import json
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from src.adapters.base.adapter_interface import PlatformAdapter
from src.engines.base.engine_interface import CrawlTask, EngineType
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.douyin")

class DouyinAdapter(PlatformAdapter):
    """抖音适配器"""
    
    def __init__(self):
        super().__init__()
        self.platform_name = "douyin"
        self.base_url = "https://www.douyin.com"
        self.api_base = "https://www.douyin.com/aweme/v1/web"
        
        # 请求头配置
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
            "Cookie": ""  # 需要有效的cookie
        }
    
    async def search_videos(
        self, 
        keyword: str, 
        offset: int = 0, 
        count: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索视频"""
        try:
            # 构建搜索参数
            params = {
                "device_platform": "webapp",
                "aid": "6383",
                "channel": "channel_pc_web",
                "search_channel": "aweme_video_web",
                "keyword": keyword,
                "search_source": "normal_search",
                "query_correct_type": "1",
                "is_filter_search": "0",
                "from_group_id": "",
                "offset": offset,
                "count": count,
                "version_code": "190600",
                "version_name": "19.6.0"
            }
            
            # 添加签名
            params.update(await self._generate_signature(params))
            
            # 构建URL
            search_url = f"{self.api_base}/search/item/?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"douyin_search_{keyword}_{offset}",
                platform="douyin",
                url=search_url,
                headers=self.headers,
                engine_type=EngineType.MEDIACRAWL,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_search_results(result.json_data)
            else:
                logger.error(f"Douyin search failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Douyin search error: {e}")
            return []
    
    async def get_video_detail(self, aweme_id: str) -> Optional[Dict[str, Any]]:
        """获取视频详情"""
        try:
            # 构建详情URL
            detail_url = f"{self.base_url}/video/{aweme_id}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"douyin_detail_{aweme_id}",
                platform="douyin",
                url=detail_url,
                headers=self.headers,
                engine_type=EngineType.MEDIACRAWL,
                extraction_rules={
                    "js_extractors": {
                        "video_data": """
                        (() => {
                            // 从页面中提取视频数据
                            const scripts = document.querySelectorAll('script');
                            for (let script of scripts) {
                                if (script.innerHTML.includes('RENDER_DATA')) {
                                    const match = script.innerHTML.match(/window\.__RENDER_DATA__\s*=\s*(.+?);\s*<\/script>/);
                                    if (match) {
                                        try {
                                            return JSON.parse(decodeURIComponent(match[1]));
                                        } catch (e) {
                                            console.error('Parse error:', e);
                                        }
                                    }
                                }
                            }
                            return null;
                        })()
                        """
                    }
                },
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success:
                return await self._parse_video_detail(result)
            else:
                logger.error(f"Douyin detail failed: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Douyin detail error: {e}")
            return None
    
    async def get_user_videos(
        self, 
        user_id: str, 
        max_cursor: int = 0, 
        count: int = 20
    ) -> List[Dict[str, Any]]:
        """获取用户视频列表"""
        try:
            params = {
                "device_platform": "webapp",
                "aid": "6383",
                "sec_user_id": user_id,
                "max_cursor": max_cursor,
                "count": count,
                "version_code": "190600",
                "version_name": "19.6.0"
            }
            
            # 添加签名
            params.update(await self._generate_signature(params))
            
            # 构建URL
            user_url = f"{self.api_base}/post/?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"douyin_user_{user_id}_{max_cursor}",
                platform="douyin",
                url=user_url,
                headers=self.headers,
                engine_type=EngineType.MEDIACRAWL,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_user_videos(result.json_data)
            else:
                logger.error(f"Get user videos failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Get user videos error: {e}")
            return []
    
    async def _generate_signature(self, params: Dict[str, Any]) -> Dict[str, str]:
        """生成签名参数"""
        # 抖音的签名算法比较复杂，需要逆向工程
        # 这里简化处理
        
        # X-Bogus参数
        x_bogus = await self._calculate_x_bogus(params)
        
        # msToken
        ms_token = self._generate_ms_token()
        
        return {
            "X-Bogus": x_bogus,
            "msToken": ms_token,
            "_signature": await self._calculate_signature(params)
        }
    
    async def _calculate_x_bogus(self, params: Dict[str, Any]) -> str:
        """计算X-Bogus参数"""
        # 简化的算法示例
        import base64
        
        param_str = urlencode(sorted(params.items()))
        timestamp = str(int(time.time()))
        
        # 混合参数和时间戳
        mixed = f"{param_str}{timestamp}"
        
        # Base64编码
        encoded = base64.b64encode(mixed.encode()).decode()
        
        # 添加特殊字符
        return f"DFSzswVOQXs7ANkSNTkTNGATOBU0{encoded[:20]}"
    
    def _generate_ms_token(self) -> str:
        """生成msToken"""
        import random
        import string
        
        # 生成128位随机字符串
        return ''.join(random.choices(string.ascii_letters + string.digits, k=128))
    
    async def _calculate_signature(self, params: Dict[str, Any]) -> str:
        """计算签名"""
        # 简化的签名算法
        import hashlib
        
        # 按照特定顺序排列参数
        sign_params = []
        for key in sorted(params.keys()):
            sign_params.append(f"{key}={params[key]}")
        
        sign_str = "&".join(sign_params)
        
        # 添加密钥
        secret = "douyin_secret_2024"
        sign_str = f"{sign_str}{secret}"
        
        # 计算SHA256
        return hashlib.sha256(sign_str.encode()).hexdigest()
    
    async def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        videos = []
        
        try:
            if "data" in data:
                for item in data["data"]:
                    if item.get("type") == 1:  # 视频类型
                        video = await self._extract_video_info(item.get("aweme_info", {}))
                        if video:
                            videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Parse search results error: {e}")
            return videos
    
    async def _extract_video_info(self, video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取视频信息"""
        try:
            video = {
                "platform": "douyin",
                "aweme_id": video_data.get("aweme_id", ""),
                "desc": video_data.get("desc", ""),
                "create_time": video_data.get("create_time", 0),
                "author": {
                    "uid": video_data.get("author", {}).get("uid", ""),
                    "nickname": video_data.get("author", {}).get("nickname", ""),
                    "signature": video_data.get("author", {}).get("signature", ""),
                    "avatar": video_data.get("author", {}).get("avatar_thumb", {}).get("url_list", [""])[0]
                },
                "music": {
                    "id": video_data.get("music", {}).get("id", ""),
                    "title": video_data.get("music", {}).get("title", ""),
                    "author": video_data.get("music", {}).get("author", "")
                },
                "statistics": {
                    "comment_count": video_data.get("statistics", {}).get("comment_count", 0),
                    "digg_count": video_data.get("statistics", {}).get("digg_count", 0),
                    "share_count": video_data.get("statistics", {}).get("share_count", 0),
                    "play_count": video_data.get("statistics", {}).get("play_count", 0)
                },
                "video": {
                    "play_addr": video_data.get("video", {}).get("play_addr", {}).get("url_list", [""])[0],
                    "cover": video_data.get("video", {}).get("cover", {}).get("url_list", [""])[0],
                    "duration": video_data.get("video", {}).get("duration", 0),
                    "width": video_data.get("video", {}).get("width", 0),
                    "height": video_data.get("video", {}).get("height", 0)
                },
                "text_extra": video_data.get("text_extra", []),
                "video_labels": video_data.get("video_labels", [])
            }
            
            # 提取话题标签
            video["hashtags"] = []
            for extra in video["text_extra"]:
                if extra.get("type") == 1:  # 话题类型
                    video["hashtags"].append(extra.get("hashtag_name", ""))
            
            return video
            
        except Exception as e:
            logger.error(f"Extract video info error: {e}")
            return None
    
    async def _parse_video_detail(self, crawl_result) -> Dict[str, Any]:
        """解析视频详情"""
        try:
            detail = {
                "platform": "douyin",
                "url": crawl_result.url
            }
            
            # 从提取的数据中获取详细信息
            if crawl_result.extracted_data and crawl_result.extracted_data.get("video_data"):
                render_data = crawl_result.extracted_data["video_data"]
                
                # 解析渲染数据
                if render_data and isinstance(render_data, dict):
                    # 提取视频信息
                    video_detail = render_data.get("aweme", {}).get("detail", {})
                    if video_detail:
                        detail["video_info"] = await self._extract_video_info(video_detail)
                    
                    # 提取评论
                    comments = render_data.get("comment", {}).get("comments", [])
                    detail["top_comments"] = await self._extract_comments(comments[:10])
            
            return detail
            
        except Exception as e:
            logger.error(f"Parse video detail error: {e}")
            return {}
    
    async def _extract_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取评论信息"""
        extracted_comments = []
        
        for comment in comments:
            try:
                extracted = {
                    "cid": comment.get("cid", ""),
                    "text": comment.get("text", ""),
                    "create_time": comment.get("create_time", 0),
                    "digg_count": comment.get("digg_count", 0),
                    "user": {
                        "uid": comment.get("user", {}).get("uid", ""),
                        "nickname": comment.get("user", {}).get("nickname", ""),
                        "avatar": comment.get("user", {}).get("avatar_thumb", {}).get("url_list", [""])[0]
                    },
                    "reply_count": comment.get("reply_comment_count", 0)
                }
                extracted_comments.append(extracted)
            except Exception as e:
                logger.debug(f"Extract comment error: {e}")
                continue
        
        return extracted_comments
    
    async def _parse_user_videos(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析用户视频列表"""
        videos = []
        
        try:
            if "aweme_list" in data:
                for video_data in data["aweme_list"]:
                    video = await self._extract_video_info(video_data)
                    if video:
                        videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Parse user videos error: {e}")
            return videos
```

**验证标准**：抖音适配器基础功能实现完成，支持视频搜索、详情和用户视频获取

## 6.3 微博适配器

### 6.3.1 微博数据爬取

#### 6.3.1.1 实现微博适配器基础 [Time: 4h]
```python
# src/adapters/weibo/adapter.py
import asyncio
import json
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from src.adapters.base.adapter_interface import PlatformAdapter
from src.engines.base.engine_interface import CrawlTask, EngineType
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.weibo")

class WeiboAdapter(PlatformAdapter):
    """微博适配器"""
    
    def __init__(self):
        super().__init__()
        self.platform_name = "weibo"
        self.base_url = "https://weibo.com"
        self.api_base = "https://weibo.com/ajax"
        
        # 请求头配置
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest"
        }
    
    async def search_weibo(
        self, 
        keyword: str, 
        page: int = 1,
        search_type: str = "realtime"  # realtime/hot
    ) -> List[Dict[str, Any]]:
        """搜索微博"""
        try:
            # 构建搜索参数
            params = {
                "q": keyword,
                "page": page,
                "typeall": "1",
                "suball": "1",
                "timescope": "custom:2024-01-01:2024-12-31",
                "Refer": "g",
                "type": "wb" if search_type == "realtime" else "hot"
            }
            
            # 构建URL
            search_url = f"{self.api_base}/side/search?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"weibo_search_{keyword}_{page}",
                platform="weibo",
                url=search_url,
                headers=self.headers,
                engine_type=EngineType.MEDIACRAWL,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_search_results(result.json_data)
            else:
                logger.error(f"Weibo search failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Weibo search error: {e}")
            return []
    
    async def get_weibo_detail(self, weibo_id: str) -> Optional[Dict[str, Any]]:
        """获取微博详情"""
        try:
            # 构建详情URL
            detail_url = f"{self.api_base}/statuses/show?id={weibo_id}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"weibo_detail_{weibo_id}",
                platform="weibo",
                url=detail_url,
                headers=self.headers,
                engine_type=EngineType.CRAWL4AI,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_weibo_detail(result.json_data)
            else:
                logger.error(f"Weibo detail failed: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Weibo detail error: {e}")
            return None
    
    async def get_user_weibo(
        self, 
        uid: str, 
        page: int = 1,
        feature: int = 0  # 0:全部 1:原创 2:图片 3:视频
    ) -> List[Dict[str, Any]]:
        """获取用户微博"""
        try:
            params = {
                "uid": uid,
                "page": page,
                "feature": feature,
                "since_id": ""
            }
            
            # 构建URL
            user_url = f"{self.api_base}/statuses/mymblog?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"weibo_user_{uid}_{page}",
                platform="weibo",
                url=user_url,
                headers=self.headers,
                engine_type=EngineType.CRAWL4AI,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_user_weibo(result.json_data)
            else:
                logger.error(f"Get user weibo failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Get user weibo error: {e}")
            return []
    
    async def get_comments(
        self, 
        weibo_id: str, 
        max_id: int = 0
    ) -> List[Dict[str, Any]]:
        """获取微博评论"""
        try:
            params = {
                "id": weibo_id,
                "mid": weibo_id,
                "max_id": max_id,
                "count": 20,
                "flow": "0"
            }
            
            # 构建URL
            comment_url = f"{self.api_base}/statuses/buildComments?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"weibo_comments_{weibo_id}_{max_id}",
                platform="weibo",
                url=comment_url,
                headers=self.headers,
                engine_type=EngineType.CRAWL4AI,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_comments(result.json_data)
            else:
                logger.error(f"Get comments failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Get comments error: {e}")
            return []
    
    async def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        weibos = []
        
        try:
            if "data" in data and "cards" in data["data"]:
                for card in data["data"]["cards"]:
                    if card.get("card_type") == 9:  # 微博卡片
                        mblog = card.get("mblog", {})
                        weibo = await self._extract_weibo_info(mblog)
                        if weibo:
                            weibos.append(weibo)
            
            return weibos
            
        except Exception as e:
            logger.error(f"Parse search results error: {e}")
            return weibos
    
    async def _extract_weibo_info(self, mblog: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取微博信息"""
        try:
            # 解析微博文本
            text, text_length = await self._parse_weibo_text(mblog.get("text", ""))
            
            weibo = {
                "platform": "weibo",
                "id": mblog.get("id", ""),
                "mid": mblog.get("mid", ""),
                "text": text,
                "text_length": text_length,
                "source": mblog.get("source", ""),
                "created_at": mblog.get("created_at", ""),
                "user": {
                    "id": mblog.get("user", {}).get("id", ""),
                    "screen_name": mblog.get("user", {}).get("screen_name", ""),
                    "profile_image_url": mblog.get("user", {}).get("profile_image_url", ""),
                    "verified": mblog.get("user", {}).get("verified", False),
                    "verified_type": mblog.get("user", {}).get("verified_type", -1),
                    "followers_count": mblog.get("user", {}).get("followers_count", 0),
                    "description": mblog.get("user", {}).get("description", "")
                },
                "reposts_count": mblog.get("reposts_count", 0),
                "comments_count": mblog.get("comments_count", 0),
                "attitudes_count": mblog.get("attitudes_count", 0),
                "pic_ids": mblog.get("pic_ids", []),
                "is_long_text": mblog.get("isLongText", False),
                "topics": await self._extract_topics(mblog.get("text", "")),
                "at_users": await self._extract_mentions(mblog.get("text", ""))
            }
            
            # 处理图片
            if mblog.get("pics"):
                weibo["pics"] = [
                    {
                        "pid": pic.get("pid", ""),
                        "url": pic.get("large", {}).get("url", ""),
                        "thumbnail": pic.get("thumbnail", {}).get("url", "")
                    }
                    for pic in mblog.get("pics", [])
                ]
            
            # 处理视频
            if mblog.get("page_info") and mblog["page_info"].get("type") == "video":
                weibo["video"] = {
                    "url": mblog["page_info"].get("media_info", {}).get("stream_url", ""),
                    "cover": mblog["page_info"].get("page_pic", {}).get("url", ""),
                    "duration": mblog["page_info"].get("media_info", {}).get("duration", 0)
                }
            
            # 处理转发微博
            if mblog.get("retweeted_status"):
                weibo["retweeted_status"] = await self._extract_weibo_info(mblog["retweeted_status"])
            
            return weibo
            
        except Exception as e:
            logger.error(f"Extract weibo info error: {e}")
            return None
    
    async def _parse_weibo_text(self, html_text: str) -> tuple:
        """解析微博文本"""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', html_text)
        
        # 解码HTML实体
        import html
        text = html.unescape(text)
        
        # 计算文本长度（中文算2个字符）
        length = 0
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                length += 2
            else:
                length += 1
        
        return text, length
    
    async def _extract_topics(self, text: str) -> List[str]:
        """提取话题"""
        # 匹配#话题#格式
        pattern = r'#([^#]+)#'
        topics = re.findall(pattern, text)
        return list(set(topics))
    
    async def _extract_mentions(self, text: str) -> List[str]:
        """提取@用户"""
        # 匹配@用户格式
        pattern = r'@([\w\u4e00-\u9fa5-]+)'
        mentions = re.findall(pattern, text)
        return list(set(mentions))
    
    async def _parse_weibo_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析微博详情"""
        try:
            if not data.get("ok"):
                return {}
            
            mblog = data.get("data", {})
            detail = await self._extract_weibo_info(mblog)
            
            # 添加额外的详情信息
            if detail:
                detail["long_text"] = mblog.get("longText", {}).get("longTextContent", "")
                detail["edit_count"] = mblog.get("edit_count", 0)
                detail["region_name"] = mblog.get("region_name", "")
                detail["reward_scheme"] = mblog.get("reward_scheme", "")
            
            return detail
            
        except Exception as e:
            logger.error(f"Parse weibo detail error: {e}")
            return {}
    
    async def _parse_user_weibo(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析用户微博"""
        weibos = []
        
        try:
            if "data" in data and "list" in data["data"]:
                for mblog in data["data"]["list"]:
                    weibo = await self._extract_weibo_info(mblog)
                    if weibo:
                        weibos.append(weibo)
            
            return weibos
            
        except Exception as e:
            logger.error(f"Parse user weibo error: {e}")
            return weibos
    
    async def _parse_comments(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析评论"""
        comments = []
        
        try:
            if "data" in data:
                for comment in data["data"]:
                    parsed = {
                        "id": comment.get("id", ""),
                        "mid": comment.get("mid", ""),
                        "text": await self._parse_weibo_text(comment.get("text", ""))[0],
                        "created_at": comment.get("created_at", ""),
                        "source": comment.get("source", ""),
                        "user": {
                            "id": comment.get("user", {}).get("id", ""),
                            "screen_name": comment.get("user", {}).get("screen_name", ""),
                            "profile_image_url": comment.get("user", {}).get("profile_image_url", "")
                        },
                        "like_count": comment.get("like_count", 0),
                        "total_number": comment.get("total_number", 0)
                    }
                    comments.append(parsed)
            
            return comments
            
        except Exception as e:
            logger.error(f"Parse comments error: {e}")
            return comments
```

**验证标准**：微博适配器基础功能实现完成，支持微博搜索、详情、用户微博和评论获取

## 6.4 B站适配器

### 6.4.1 B站视频数据爬取

#### 6.4.1.1 实现B站适配器基础 [Time: 4h]
```python
# src/adapters/bilibili/adapter.py
import asyncio
import json
import re
import time
import hashlib
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from src.adapters.base.adapter_interface import PlatformAdapter
from src.engines.base.engine_interface import CrawlTask, EngineType
from src.utils.logger.logger import get_logger

logger = get_logger("adapter.bilibili")

class BilibiliAdapter(PlatformAdapter):
    """B站适配器"""
    
    def __init__(self):
        super().__init__()
        self.platform_name = "bilibili"
        self.base_url = "https://www.bilibili.com"
        self.api_base = "https://api.bilibili.com"
        
        # 请求头配置
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.bilibili.com"
        }
        
        # WBI签名密钥（需要定期更新）
        self.img_key = "7cd084941338484aae1ad9425b84077c"
        self.sub_key = "4932caff0ff746eab6f01bf08b70ac45"
    
    async def search_videos(
        self, 
        keyword: str, 
        page: int = 1,
        order: str = "totalrank",  # 综合排序
        duration: int = 0  # 时长筛选
    ) -> List[Dict[str, Any]]:
        """搜索视频"""
        try:
            # 构建搜索参数
            params = {
                "keyword": keyword,
                "page": page,
                "page_size": 20,
                "order": order,
                "duration": duration,
                "search_type": "video",
                "platform": "pc"
            }
            
            # 添加WBI签名
            params = await self._add_wbi_sign(params)
            
            # 构建URL
            search_url = f"{self.api_base}/x/web-interface/search/type?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"bilibili_search_{keyword}_{page}",
                platform="bilibili",
                url=search_url,
                headers=self.headers,
                engine_type=EngineType.CRAWL4AI,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_search_results(result.json_data)
            else:
                logger.error(f"Bilibili search failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Bilibili search error: {e}")
            return []
    
    async def get_video_detail(self, bvid: str) -> Optional[Dict[str, Any]]:
        """获取视频详情"""
        try:
            # 获取视频基本信息
            params = {"bvid": bvid}
            params = await self._add_wbi_sign(params)
            
            detail_url = f"{self.api_base}/x/web-interface/view?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"bilibili_detail_{bvid}",
                platform="bilibili",
                url=detail_url,
                headers=self.headers,
                engine_type=EngineType.CRAWL4AI,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                detail = await self._parse_video_detail(result.json_data)
                
                # 获取评论
                if detail:
                    detail["comments"] = await self.get_comments(detail["aid"])
                
                return detail
            else:
                logger.error(f"Bilibili detail failed: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Bilibili detail error: {e}")
            return None
    
    async def get_user_videos(
        self, 
        mid: str, 
        pn: int = 1,
        ps: int = 20
    ) -> List[Dict[str, Any]]:
        """获取用户投稿视频"""
        try:
            params = {
                "mid": mid,
                "pn": pn,
                "ps": ps,
                "order": "pubdate",
                "tid": 0
            }
            
            params = await self._add_wbi_sign(params)
            
            user_url = f"{self.api_base}/x/space/arc/search?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"bilibili_user_{mid}_{pn}",
                platform="bilibili",
                url=user_url,
                headers=self.headers,
                engine_type=EngineType.CRAWL4AI,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_user_videos(result.json_data)
            else:
                logger.error(f"Get user videos failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Get user videos error: {e}")
            return []
    
    async def get_comments(
        self, 
        aid: int, 
        pn: int = 1,
        sort: int = 0  # 0:按时间 2:按热度
    ) -> List[Dict[str, Any]]:
        """获取视频评论"""
        try:
            params = {
                "type": 1,
                "oid": aid,
                "pn": pn,
                "ps": 20,
                "sort": sort,
                "nohot": 0
            }
            
            comment_url = f"{self.api_base}/x/v2/reply/main?{urlencode(params)}"
            
            # 创建爬取任务
            task = CrawlTask(
                task_id=f"bilibili_comments_{aid}_{pn}",
                platform="bilibili",
                url=comment_url,
                headers=self.headers,
                engine_type=EngineType.CRAWL4AI,
                timeout=30
            )
            
            # 执行爬取
            result = await self.crawl_engine.crawl(task)
            
            if result.success and result.json_data:
                return await self._parse_comments(result.json_data)
            else:
                logger.error(f"Get comments failed: {result.error_message}")
                return []
                
        except Exception as e:
            logger.error(f"Get comments error: {e}")
            return []
    
    async def _add_wbi_sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """添加WBI签名"""
        # 添加时间戳
        wts = str(int(time.time()))
        params["wts"] = wts
        
        # 按照特定规则排序参数
        sorted_params = sorted(params.items())
        
        # 构建待签名字符串
        query = urlencode(sorted_params)
        
        # 计算签名
        w_rid = self._calculate_wrid(query)
        
        # 添加签名
        params["w_rid"] = w_rid
        
        return params
    
    def _calculate_wrid(self, query: str) -> str:
        """计算w_rid签名"""
        # 混淆密钥
        mixin_key = self._get_mixin_key()
        
        # 构建签名字符串
        sign_str = f"{query}{mixin_key}"
        
        # 计算MD5
        return hashlib.md5(sign_str.encode()).hexdigest()
    
    def _get_mixin_key(self) -> str:
        """获取混淆密钥"""
        # WBI签名的密钥混淆算法
        # 这里简化处理，实际需要根据B站的算法动态生成
        orig = self.img_key + self.sub_key
        
        # 字符映射表
        char_map = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
            27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
            37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
            22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52
        ]
        
        # 根据映射表重排字符
        mixin = ""
        for i in char_map[:32]:
            if i < len(orig):
                mixin += orig[i]
        
        return mixin
    
    async def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        videos = []
        
        try:
            if data.get("code") == 0 and "result" in data["data"]:
                for item in data["data"]["result"]:
                    video = await self._extract_video_info(item)
                    if video:
                        videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Parse search results error: {e}")
            return videos
    
    async def _extract_video_info(self, video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取视频信息"""
        try:
            # 处理时长格式
            duration_str = video_data.get("duration", "00:00")
            duration_seconds = await self._parse_duration(duration_str)
            
            video = {
                "platform": "bilibili",
                "bvid": video_data.get("bvid", ""),
                "aid": video_data.get("aid", 0),
                "title": re.sub(r'<[^>]+>', '', video_data.get("title", "")),
                "description": video_data.get("description", ""),
                "pic": f"https:{video_data.get('pic', '')}" if not video_data.get('pic', '').startswith('http') else video_data.get('pic', ''),
                "author": video_data.get("author", ""),
                "mid": video_data.get("mid", 0),
                "play": video_data.get("play", 0),
                "danmaku": video_data.get("danmaku", 0),
                "reply": video_data.get("reply", 0),
                "favorite": video_data.get("favorite", 0),
                "coin": video_data.get("coin", 0),
                "share": video_data.get("share", 0),
                "like": video_data.get("like", 0),
                "duration": duration_seconds,
                "pubdate": video_data.get("pubdate", 0),
                "tag": video_data.get("tag", "").split(",") if video_data.get("tag") else [],
                "tname": video_data.get("tname", ""),
                "tid": video_data.get("tid", 0)
            }
            
            return video
            
        except Exception as e:
            logger.error(f"Extract video info error: {e}")
            return None
    
    async def _parse_duration(self, duration_str: str) -> int:
        """解析时长字符串为秒数"""
        try:
            parts = duration_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                return 0
        except:
            return 0
    
    async def _parse_video_detail(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析视频详情"""
        try:
            if data.get("code") != 0:
                return None
            
            video_data = data["data"]
            
            detail = {
                "platform": "bilibili",
                "bvid": video_data.get("bvid", ""),
                "aid": video_data.get("aid", 0),
                "videos": video_data.get("videos", 1),
                "tid": video_data.get("tid", 0),
                "tname": video_data.get("tname", ""),
                "pic": video_data.get("pic", ""),
                "title": video_data.get("title", ""),
                "pubdate": video_data.get("pubdate", 0),
                "ctime": video_data.get("ctime", 0),
                "desc": video_data.get("desc", ""),
                "duration": video_data.get("duration", 0),
                "owner": {
                    "mid": video_data.get("owner", {}).get("mid", 0),
                    "name": video_data.get("owner", {}).get("name", ""),
                    "face": video_data.get("owner", {}).get("face", "")
                },
                "stat": {
                    "aid": video_data.get("stat", {}).get("aid", 0),
                    "view": video_data.get("stat", {}).get("view", 0),
                    "danmaku": video_data.get("stat", {}).get("danmaku", 0),
                    "reply": video_data.get("stat", {}).get("reply", 0),
                    "favorite": video_data.get("stat", {}).get("favorite", 0),
                    "coin": video_data.get("stat", {}).get("coin", 0),
                    "share": video_data.get("stat", {}).get("share", 0),
                    "like": video_data.get("stat", {}).get("like", 0),
                    "dislike": video_data.get("stat", {}).get("dislike", 0)
                },
                "pages": [
                    {
                        "cid": page.get("cid", 0),
                        "page": page.get("page", 1),
                        "part": page.get("part", ""),
                        "duration": page.get("duration", 0)
                    }
                    for page in video_data.get("pages", [])
                ],
                "tags": [
                    {
                        "tag_id": tag.get("tag_id", 0),
                        "tag_name": tag.get("tag_name", "")
                    }
                    for tag in video_data.get("tag", [])
                ] if isinstance(video_data.get("tag"), list) else []
            }
            
            return detail
            
        except Exception as e:
            logger.error(f"Parse video detail error: {e}")
            return None
    
    async def _parse_user_videos(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析用户视频"""
        videos = []
        
        try:
            if data.get("code") == 0 and "vlist" in data["data"]["list"]:
                for video_data in data["data"]["list"]["vlist"]:
                    video = {
                        "platform": "bilibili",
                        "bvid": video_data.get("bvid", ""),
                        "aid": video_data.get("aid", 0),
                        "title": video_data.get("title", ""),
                        "description": video_data.get("description", ""),
                        "pic": f"https:{video_data.get('pic', '')}" if not video_data.get('pic', '').startswith('http') else video_data.get('pic', ''),
                        "author": video_data.get("author", ""),
                        "mid": video_data.get("mid", 0),
                        "play": video_data.get("play", 0),
                        "video_review": video_data.get("video_review", 0),
                        "favorites": video_data.get("favorites", 0),
                        "length": video_data.get("length", ""),
                        "created": video_data.get("created", 0),
                        "comment": video_data.get("comment", 0)
                    }
                    videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Parse user videos error: {e}")
            return videos
    
    async def _parse_comments(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析评论"""
        comments = []
        
        try:
            if data.get("code") == 0 and "replies" in data["data"]:
                for reply in data["data"]["replies"]:
                    comment = {
                        "rpid": reply.get("rpid", 0),
                        "oid": reply.get("oid", 0),
                        "type": reply.get("type", 1),
                        "mid": reply.get("mid", 0),
                        "uname": reply.get("member", {}).get("uname", ""),
                        "avatar": reply.get("member", {}).get("avatar", ""),
                        "content": reply.get("content", {}).get("message", ""),
                        "ctime": reply.get("ctime", 0),
                        "like": reply.get("like", 0),
                        "count": reply.get("count", 0),
                        "rcount": reply.get("rcount", 0)
                    }
                    comments.append(comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Parse comments error: {e}")
            return comments
```

**验证标准**：B站适配器基础功能实现完成，支持视频搜索、详情、用户视频和评论获取

---

## 验证和测试要求

### 阶段六验证清单
- [ ] 小红书适配器测试通过
- [ ] 抖音适配器测试通过
- [ ] 微博适配器测试通过
- [ ] B站适配器测试通过
- [ ] 反爬策略有效性验证

### 代码质量要求
- 代码覆盖率 > 80%
- 适配器接口统一
- 错误处理完善
- 数据格式标准化

### 性能要求
- 单平台爬取速度 > 100条/分钟
- 并发支持 > 10个任务
- 反爬成功率 > 90%

---

**注意**：本文档为第三部分，包含第6阶段的详细实现。第7阶段（监控运维与部署）将在第4部分中详细说明。

每个任务都包含具体的实现代码、验证标准和预估工时，可以直接用于指导AI编程助手进行开发工作。