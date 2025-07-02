# 旅游平台数据爬虫系统 - 项目开发TODO详细指南
## 第3部分：反爬对抗系统实现

> 本部分实现代理池管理、浏览器指纹库和行为模拟系统，为爬虫提供强大的反爬对抗能力

---

## Phase 3: 反爬对抗系统（Day 5-7）

### Task 3.1: 实现代理池管理系统

#### 3.1.1 代理模型定义
```python
# src/anti_detection/proxy/models.py
"""代理相关数据模型"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import base64

class ProxyType(str, Enum):
    """代理类型"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class ProxyStatus(str, Enum):
    """代理状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    FAILED = "failed"
    BLACKLISTED = "blacklisted"

class ProxyLocation(BaseModel):
    """代理地理位置"""
    country: str = Field(..., description="国家代码")
    country_name: str = Field(..., description="国家名称")
    city: Optional[str] = Field(None, description="城市")
    region: Optional[str] = Field(None, description="地区")
    isp: Optional[str] = Field(None, description="ISP提供商")

class Proxy(BaseModel):
    """代理模型"""
    # 基础信息
    proxy_id: str = Field(..., description="代理唯一ID")
    proxy_url: str = Field(..., description="代理URL")
    proxy_type: ProxyType = Field(..., description="代理类型")
    
    # 认证信息
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    
    # 地理信息
    location: Optional[ProxyLocation] = Field(None, description="地理位置")
    
    # 性能指标
    score: int = Field(default=100, ge=0, le=100, description="代理评分")
    response_time: float = Field(default=0.0, description="响应时间(秒)")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="成功率")
    
    # 使用统计
    success_count: int = Field(default=0, description="成功次数")
    fail_count: int = Field(default=0, description="失败次数")
    total_bandwidth: int = Field(default=0, description="总带宽(字节)")
    
    # 状态信息
    status: ProxyStatus = Field(default=ProxyStatus.TESTING, description="代理状态")
    last_check_at: Optional[datetime] = Field(None, description="最后检查时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    # 限制信息
    max_concurrent: int = Field(default=10, description="最大并发数")
    current_concurrent: int = Field(default=0, description="当前并发数")
    
    # 平台限制
    allowed_platforms: List[str] = Field(default_factory=list, description="允许的平台")
    blocked_platforms: List[str] = Field(default_factory=list, description="禁止的平台")
    
    # 元数据
    provider: Optional[str] = Field(None, description="代理提供商")
    expire_at: Optional[datetime] = Field(None, description="过期时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('proxy_url')
    def validate_proxy_url(cls, v, values):
        """验证代理URL格式"""
        proxy_type = values.get('proxy_type')
        if proxy_type and not v.startswith(f"{proxy_type}://"):
            raise ValueError(f"Proxy URL must start with {proxy_type}://")
        return v
    
    def get_auth_string(self) -> Optional[str]:
        """获取认证字符串"""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}"
            return base64.b64encode(auth.encode()).decode()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于请求库）"""
        proxy_dict = {
            self.proxy_type: self.proxy_url
        }
        
        # 添加认证
        if self.username and self.password:
            # 格式: protocol://username:password@host:port
            parts = self.proxy_url.split("://")
            if len(parts) == 2:
                proxy_dict[self.proxy_type] = f"{parts[0]}://{self.username}:{self.password}@{parts[1]}"
        
        return proxy_dict
    
    def update_stats(self, success: bool, response_time: float = 0.0):
        """更新统计信息"""
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
        
        # 更新成功率
        total = self.success_count + self.fail_count
        self.success_rate = self.success_count / total if total > 0 else 0.0
        
        # 更新响应时间（移动平均）
        if success and response_time > 0:
            alpha = 0.3  # 平滑因子
            self.response_time = alpha * response_time + (1 - alpha) * self.response_time
        
        # 更新评分
        self._update_score()
        
        self.updated_at = datetime.utcnow()
    
    def _update_score(self):
        """更新代理评分"""
        # 基础分数
        base_score = 50
        
        # 成功率影响（最多40分）
        success_score = self.success_rate * 40
        
        # 响应时间影响（最多10分）
        if self.response_time > 0:
            # 响应时间越短分数越高
            if self.response_time < 1:
                time_score = 10
            elif self.response_time < 3:
                time_score = 8
            elif self.response_time < 5:
                time_score = 5
            else:
                time_score = 2
        else:
            time_score = 5
        
        self.score = int(base_score + success_score + time_score)

class ProxyPool(BaseModel):
    """代理池统计"""
    total_count: int = Field(default=0, description="总代理数")
    active_count: int = Field(default=0, description="活跃代理数")
    testing_count: int = Field(default=0, description="测试中代理数")
    failed_count: int = Field(default=0, description="失败代理数")
    
    by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")
    by_location: Dict[str, int] = Field(default_factory=dict, description="按地区统计")
    by_provider: Dict[str, int] = Field(default_factory=dict, description="按提供商统计")
    
    average_score: float = Field(default=0.0, description="平均评分")
    average_response_time: float = Field(default=0.0, description="平均响应时间")
```

#### 3.1.2 代理池管理器实现
```python
# src/anti_detection/proxy/manager.py
"""代理池管理器"""
import asyncio
import random
import time
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
import aiohttp
import json

from src.anti_detection.proxy.models import (
    Proxy, ProxyType, ProxyStatus, ProxyLocation, ProxyPool
)
from src.core.redis import get_redis, RedisKeys
from src.core.database import db_transaction
from src.utils.logger.logger import get_logger
from sqlalchemy import select, update, and_, or_
from sqlalchemy.dialects.postgresql import insert

logger = get_logger("proxy.manager")

class ProxyManager:
    """代理池管理器"""
    
    def __init__(self):
        self.redis = get_redis()
        self._check_interval = 300  # 5分钟检查一次
        self._min_pool_size = 100
        self._score_threshold = 70
        self._check_task: Optional[asyncio.Task] = None
        self._platform_proxy_cache: Dict[str, List[Proxy]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化代理池"""
        logger.info("Initializing proxy manager...")
        
        # 从数据库加载代理
        await self._load_proxies_from_db()
        
        # 启动定期检查任务
        self._check_task = asyncio.create_task(self._periodic_check())
        
        logger.info("Proxy manager initialized")
    
    async def shutdown(self):
        """关闭代理管理器"""
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Proxy manager shut down")
    
    async def add_proxy(self, proxy: Proxy) -> bool:
        """添加代理"""
        try:
            # 验证代理
            is_valid = await self._validate_proxy(proxy)
            if not is_valid:
                logger.warning(f"Proxy validation failed: {proxy.proxy_url}")
                return False
            
            # 保存到数据库
            async with db_transaction() as session:
                stmt = insert(proxies_table).values(
                    proxy_id=proxy.proxy_id,
                    proxy_url=proxy.proxy_url,
                    proxy_type=proxy.proxy_type,
                    username=proxy.username,
                    password=proxy.password,
                    location=proxy.location.dict() if proxy.location else None,
                    score=proxy.score,
                    status=proxy.status,
                    provider=proxy.provider,
                    metadata=proxy.metadata
                ).on_conflict_do_update(
                    index_elements=['proxy_id'],
                    set_=dict(
                        score=proxy.score,
                        status=proxy.status,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.execute(stmt)
            
            # 添加到Redis
            await self._add_to_redis(proxy)
            
            logger.info(f"Added proxy: {proxy.proxy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add proxy: {e}")
            return False
    
    async def add_proxies_batch(self, proxies: List[Proxy]) -> int:
        """批量添加代理"""
        success_count = 0
        
        # 并发验证
        validation_tasks = [self._validate_proxy(proxy) for proxy in proxies]
        validation_results = await asyncio.gather(*validation_tasks)
        
        valid_proxies = [
            proxy for proxy, is_valid in zip(proxies, validation_results) if is_valid
        ]
        
        if valid_proxies:
            # 批量保存到数据库
            async with db_transaction() as session:
                for proxy in valid_proxies:
                    stmt = insert(proxies_table).values(
                        proxy_id=proxy.proxy_id,
                        proxy_url=proxy.proxy_url,
                        proxy_type=proxy.proxy_type,
                        username=proxy.username,
                        password=proxy.password,
                        location=proxy.location.dict() if proxy.location else None,
                        score=proxy.score,
                        status=proxy.status,
                        provider=proxy.provider,
                        metadata=proxy.metadata
                    ).on_conflict_do_nothing()
                    await session.execute(stmt)
                    success_count += 1
            
            # 批量添加到Redis
            for proxy in valid_proxies:
                await self._add_to_redis(proxy)
        
        logger.info(f"Added {success_count}/{len(proxies)} proxies to pool")
        return success_count
    
    async def get_proxy(self, platform: str, retry_times: int = 3) -> Optional[Proxy]:
        """获取适合平台的代理"""
        for attempt in range(retry_times):
            try:
                # 优先从缓存获取
                cached_proxies = self._platform_proxy_cache.get(platform, [])
                if cached_proxies:
                    # 移除已使用的代理
                    proxy = cached_proxies.pop(0)
                    if await self._is_proxy_available(proxy):
                        return proxy
                
                # 从Redis获取
                proxy = await self._get_from_redis(platform)
                if proxy:
                    return proxy
                
                # 从数据库获取
                proxy = await self._get_from_db(platform)
                if proxy:
                    await self._add_to_redis(proxy)
                    return proxy
                
                # 如果没有合适的代理，等待后重试
                if attempt < retry_times - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error getting proxy: {e}")
                if attempt < retry_times - 1:
                    await asyncio.sleep(1)
        
        logger.warning(f"No available proxy for platform: {platform}")
        return None
    
    async def release_proxy(self, proxy: Proxy, success: bool, response_time: float = 0.0):
        """释放代理"""
        try:
            # 更新统计
            proxy.update_stats(success, response_time)
            proxy.last_used_at = datetime.utcnow()
            
            # 更新并发数
            proxy.current_concurrent = max(0, proxy.current_concurrent - 1)
            
            # 更新数据库
            async with db_transaction() as session:
                stmt = update(proxies_table).where(
                    proxies_table.c.proxy_id == proxy.proxy_id
                ).values(
                    score=proxy.score,
                    success_count=proxy.success_count,
                    fail_count=proxy.fail_count,
                    success_rate=proxy.success_rate,
                    response_time=proxy.response_time,
                    last_used_at=proxy.last_used_at,
                    current_concurrent=proxy.current_concurrent,
                    updated_at=datetime.utcnow()
                )
                await session.execute(stmt)
            
            # 更新Redis
            if proxy.score >= self._score_threshold:
                await self._add_to_redis(proxy)
            else:
                await self._remove_from_redis(proxy)
            
            # 如果代理表现不好，加入黑名单
            if proxy.score < 30:
                await self.blacklist_proxy(proxy, "Low score")
                
        except Exception as e:
            logger.error(f"Error releasing proxy: {e}")
    
    async def blacklist_proxy(self, proxy: Proxy, reason: str):
        """将代理加入黑名单"""
        try:
            proxy.status = ProxyStatus.BLACKLISTED
            
            # 更新数据库
            async with db_transaction() as session:
                stmt = update(proxies_table).where(
                    proxies_table.c.proxy_id == proxy.proxy_id
                ).values(
                    status=ProxyStatus.BLACKLISTED,
                    metadata=proxy.metadata.update({"blacklist_reason": reason}),
                    updated_at=datetime.utcnow()
                )
                await session.execute(stmt)
            
            # 从Redis移除
            await self._remove_from_redis(proxy)
            
            # 添加到黑名单
            blacklist_key = RedisKeys.PROXY_BLACKLIST
            await self.redis.sadd(blacklist_key, proxy.proxy_id)
            await self.redis.expire(blacklist_key, 24 * 3600)  # 24小时后自动移除
            
            logger.info(f"Blacklisted proxy {proxy.proxy_id}: {reason}")
            
        except Exception as e:
            logger.error(f"Error blacklisting proxy: {e}")
    
    async def get_pool_stats(self) -> ProxyPool:
        """获取代理池统计"""
        try:
            stats = ProxyPool()
            
            # 从数据库获取统计
            async with db_transaction() as session:
                # 总数统计
                result = await session.execute(
                    "SELECT status, COUNT(*) FROM proxies GROUP BY status"
                )
                status_counts = dict(result.fetchall())
                
                stats.total_count = sum(status_counts.values())
                stats.active_count = status_counts.get(ProxyStatus.ACTIVE, 0)
                stats.testing_count = status_counts.get(ProxyStatus.TESTING, 0)
                stats.failed_count = status_counts.get(ProxyStatus.FAILED, 0)
                
                # 类型统计
                result = await session.execute(
                    "SELECT proxy_type, COUNT(*) FROM proxies WHERE status = 'active' GROUP BY proxy_type"
                )
                stats.by_type = dict(result.fetchall())
                
                # 提供商统计
                result = await session.execute(
                    "SELECT provider, COUNT(*) FROM proxies WHERE status = 'active' GROUP BY provider"
                )
                stats.by_provider = dict(result.fetchall())
                
                # 平均指标
                result = await session.execute(
                    "SELECT AVG(score), AVG(response_time) FROM proxies WHERE status = 'active'"
                )
                avg_score, avg_time = result.fetchone()
                stats.average_score = avg_score or 0.0
                stats.average_response_time = avg_time or 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return ProxyPool()
    
    async def _validate_proxy(self, proxy: Proxy) -> bool:
        """验证代理可用性"""
        try:
            # 测试URL
            test_url = "http://httpbin.org/ip"
            
            # 创建会话
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            ) as session:
                start_time = time.time()
                
                # 发送请求
                async with session.get(
                    test_url,
                    proxy=proxy.proxy_url,
                    proxy_auth=aiohttp.BasicAuth(proxy.username, proxy.password) if proxy.username else None
                ) as response:
                    if response.status == 200:
                        elapsed = time.time() - start_time
                        
                        # 获取返回的IP
                        data = await response.json()
                        proxy_ip = data.get("origin", "")
                        
                        # 更新代理信息
                        proxy.response_time = elapsed
                        proxy.status = ProxyStatus.ACTIVE
                        proxy.metadata["last_check_ip"] = proxy_ip
                        proxy.last_check_at = datetime.utcnow()
                        
                        return True
                    else:
                        proxy.status = ProxyStatus.FAILED
                        return False
                        
        except asyncio.TimeoutError:
            logger.debug(f"Proxy timeout: {proxy.proxy_url}")
            proxy.status = ProxyStatus.FAILED
            return False
        except Exception as e:
            logger.debug(f"Proxy validation error: {e}")
            proxy.status = ProxyStatus.FAILED
            return False
    
    async def _load_proxies_from_db(self):
        """从数据库加载代理"""
        try:
            async with db_transaction() as session:
                stmt = select(proxies_table).where(
                    and_(
                        proxies_table.c.status == ProxyStatus.ACTIVE,
                        proxies_table.c.score >= self._score_threshold
                    )
                ).limit(1000)
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                # 转换为Proxy对象并添加到Redis
                for row in rows:
                    proxy = Proxy(**dict(row))
                    await self._add_to_redis(proxy)
                
                logger.info(f"Loaded {len(rows)} proxies from database")
                
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
    
    async def _add_to_redis(self, proxy: Proxy):
        """添加代理到Redis"""
        try:
            # 添加到总池
            pool_key = RedisKeys.PROXY_POOL
            await self.redis.zadd(pool_key, {proxy.proxy_id: proxy.score})
            
            # 添加代理详情
            detail_key = f"{pool_key}:{proxy.proxy_id}"
            await self.redis.setex(
                detail_key,
                3600,  # 1小时过期
                proxy.json()
            )
            
            # 更新平台索引
            if proxy.allowed_platforms:
                for platform in proxy.allowed_platforms:
                    platform_key = f"{pool_key}:platform:{platform}"
                    await self.redis.zadd(platform_key, {proxy.proxy_id: proxy.score})
                    
        except Exception as e:
            logger.error(f"Error adding proxy to Redis: {e}")
    
    async def _remove_from_redis(self, proxy: Proxy):
        """从Redis移除代理"""
        try:
            # 从总池移除
            pool_key = RedisKeys.PROXY_POOL
            await self.redis.zrem(pool_key, proxy.proxy_id)
            
            # 删除详情
            detail_key = f"{pool_key}:{proxy.proxy_id}"
            await self.redis.delete(detail_key)
            
            # 从平台索引移除
            if proxy.allowed_platforms:
                for platform in proxy.allowed_platforms:
                    platform_key = f"{pool_key}:platform:{platform}"
                    await self.redis.zrem(platform_key, proxy.proxy_id)
                    
        except Exception as e:
            logger.error(f"Error removing proxy from Redis: {e}")
    
    async def _get_from_redis(self, platform: str) -> Optional[Proxy]:
        """从Redis获取代理"""
        try:
            # 优先从平台专用池获取
            platform_key = f"{RedisKeys.PROXY_POOL}:platform:{platform}"
            proxy_ids = await self.redis.zrevrange(platform_key, 0, 10)
            
            # 如果没有平台专用代理，从总池获取
            if not proxy_ids:
                pool_key = RedisKeys.PROXY_POOL
                proxy_ids = await self.redis.zrevrange(pool_key, 0, 10)
            
            # 尝试获取可用代理
            for proxy_id in proxy_ids:
                # 获取代理详情
                detail_key = f"{RedisKeys.PROXY_POOL}:{proxy_id}"
                proxy_data = await self.redis.get(detail_key)
                
                if proxy_data:
                    proxy = Proxy.parse_raw(proxy_data)
                    
                    # 检查是否可用
                    if await self._is_proxy_available(proxy):
                        # 增加并发数
                        proxy.current_concurrent += 1
                        return proxy
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting proxy from Redis: {e}")
            return None
    
    async def _get_from_db(self, platform: str) -> Optional[Proxy]:
        """从数据库获取代理"""
        try:
            async with db_transaction() as session:
                # 构建查询条件
                conditions = [
                    proxies_table.c.status == ProxyStatus.ACTIVE,
                    proxies_table.c.score >= self._score_threshold,
                    proxies_table.c.current_concurrent < proxies_table.c.max_concurrent
                ]
                
                # 平台过滤
                platform_condition = or_(
                    proxies_table.c.allowed_platforms.contains([platform]),
                    proxies_table.c.allowed_platforms == []
                )
                conditions.append(platform_condition)
                
                # 查询
                stmt = select(proxies_table).where(
                    and_(*conditions)
                ).order_by(
                    proxies_table.c.score.desc()
                ).limit(1)
                
                result = await session.execute(stmt)
                row = result.fetchone()
                
                if row:
                    proxy = Proxy(**dict(row))
                    proxy.current_concurrent += 1
                    
                    # 更新并发数
                    update_stmt = update(proxies_table).where(
                        proxies_table.c.proxy_id == proxy.proxy_id
                    ).values(
                        current_concurrent=proxy.current_concurrent
                    )
                    await session.execute(update_stmt)
                    
                    return proxy
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting proxy from database: {e}")
            return None
    
    async def _is_proxy_available(self, proxy: Proxy) -> bool:
        """检查代理是否可用"""
        # 检查状态
        if proxy.status != ProxyStatus.ACTIVE:
            return False
        
        # 检查评分
        if proxy.score < self._score_threshold:
            return False
        
        # 检查并发限制
        if proxy.current_concurrent >= proxy.max_concurrent:
            return False
        
        # 检查是否在黑名单
        blacklist_key = RedisKeys.PROXY_BLACKLIST
        is_blacklisted = await self.redis.sismember(blacklist_key, proxy.proxy_id)
        if is_blacklisted:
            return False
        
        return True
    
    async def _periodic_check(self):
        """定期检查代理池"""
        while True:
            try:
                await asyncio.sleep(self._check_interval)
                
                # 获取池统计
                stats = await self.get_pool_stats()
                logger.info(f"Proxy pool stats: {stats.dict()}")
                
                # 检查池大小
                if stats.active_count < self._min_pool_size:
                    logger.warning(
                        f"Proxy pool size ({stats.active_count}) below minimum ({self._min_pool_size})"
                    )
                    # TODO: 触发代理补充逻辑
                
                # 清理失效代理
                await self._cleanup_failed_proxies()
                
                # 检查需要重新验证的代理
                await self._revalidate_proxies()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic check: {e}")
    
    async def _cleanup_failed_proxies(self):
        """清理失效代理"""
        try:
            async with db_transaction() as session:
                # 删除长期失败的代理
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                stmt = update(proxies_table).where(
                    and_(
                        proxies_table.c.status == ProxyStatus.FAILED,
                        proxies_table.c.updated_at < cutoff_time
                    )
                ).values(
                    status=ProxyStatus.BLACKLISTED
                )
                
                result = await session.execute(stmt)
                if result.rowcount > 0:
                    logger.info(f"Cleaned up {result.rowcount} failed proxies")
                    
        except Exception as e:
            logger.error(f"Error cleaning up proxies: {e}")
    
    async def _revalidate_proxies(self):
        """重新验证代理"""
        try:
            # 获取需要重新验证的代理
            check_interval = timedelta(hours=1)
            cutoff_time = datetime.utcnow() - check_interval
            
            async with db_transaction() as session:
                stmt = select(proxies_table).where(
                    and_(
                        proxies_table.c.status == ProxyStatus.ACTIVE,
                        or_(
                            proxies_table.c.last_check_at < cutoff_time,
                            proxies_table.c.last_check_at.is_(None)
                        )
                    )
                ).limit(50)
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                if rows:
                    # 并发验证
                    proxies = [Proxy(**dict(row)) for row in rows]
                    validation_tasks = [self._validate_proxy(proxy) for proxy in proxies]
                    validation_results = await asyncio.gather(*validation_tasks)
                    
                    # 更新结果
                    for proxy, is_valid in zip(proxies, validation_results):
                        if is_valid:
                            await self._add_to_redis(proxy)
                        else:
                            await self._remove_from_redis(proxy)
                        
                        # 更新数据库
                        update_stmt = update(proxies_table).where(
                            proxies_table.c.proxy_id == proxy.proxy_id
                        ).values(
                            status=proxy.status,
                            score=proxy.score,
                            response_time=proxy.response_time,
                            last_check_at=proxy.last_check_at,
                            updated_at=datetime.utcnow()
                        )
                        await session.execute(update_stmt)
                    
                    logger.info(f"Revalidated {len(rows)} proxies")
                    
        except Exception as e:
            logger.error(f"Error revalidating proxies: {e}")

# 创建全局代理管理器实例
proxy_manager = ProxyManager()
```

### Task 3.2: 实现浏览器指纹管理系统

#### 3.2.1 指纹模型定义
```python
# src/anti_detection/fingerprint/models.py
"""浏览器指纹数据模型"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import hashlib
import json

class BrowserFingerprint(BaseModel):
    """浏览器指纹模型"""
    # 基础信息
    fingerprint_id: str = Field(..., description="指纹唯一ID")
    
    # User Agent
    user_agent: str = Field(..., description="User Agent字符串")
    platform: str = Field(..., description="操作系统平台")
    browser_name: str = Field(..., description="浏览器名称")
    browser_version: str = Field(..., description="浏览器版本")
    
    # 屏幕信息
    screen_width: int = Field(..., description="屏幕宽度")
    screen_height: int = Field(..., description="屏幕高度")
    screen_depth: int = Field(default=24, description="颜色深度")
    device_scale_factor: float = Field(default=1.0, description="设备像素比")
    
    # 时区和语言
    timezone: str = Field(..., description="时区")
    timezone_offset: int = Field(..., description="时区偏移(分钟)")
    language: str = Field(..., description="主要语言")
    languages: List[str] = Field(default_factory=list, description="语言列表")
    
    # WebGL信息
    webgl_vendor: str = Field(..., description="WebGL供应商")
    webgl_renderer: str = Field(..., description="WebGL渲染器")
    
    # Canvas指纹
    canvas_fingerprint: str = Field(..., description="Canvas指纹")
    
    # 音频指纹
    audio_fingerprint: Optional[str] = Field(None, description="音频指纹")
    
    # 字体列表
    fonts: List[str] = Field(default_factory=list, description="已安装字体")
    
    # 插件信息
    plugins: List[Dict[str, str]] = Field(default_factory=list, description="浏览器插件")
    
    # 硬件信息
    hardware_concurrency: int = Field(default=4, description="CPU核心数")
    device_memory: Optional[int] = Field(None, description="设备内存(GB)")
    max_touch_points: int = Field(default=0, description="最大触摸点数")
    
    # 特性检测
    webrtc_enabled: bool = Field(default=True, description="WebRTC是否启用")
    cookies_enabled: bool = Field(default=True, description="Cookies是否启用")
    do_not_track: Optional[str] = Field(None, description="DNT设置")
    
    # 移动设备相关
    is_mobile: bool = Field(default=False, description="是否移动设备")
    has_touch: bool = Field(default=False, description="是否支持触摸")
    device_type: str = Field(default="desktop", description="设备类型")
    
    # 使用统计
    use_count: int = Field(default=0, description="使用次数")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    # 平台限制
    allowed_platforms: List[str] = Field(default_factory=list, description="允许的平台")
    blocked_platforms: List[str] = Field(default_factory=list, description="禁止的平台")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def generate_id(cls, fingerprint_data: Dict[str, Any]) -> str:
        """生成指纹ID"""
        # 使用关键字段生成唯一ID
        key_fields = [
            fingerprint_data.get("user_agent", ""),
            str(fingerprint_data.get("screen_width", "")),
            str(fingerprint_data.get("screen_height", "")),
            fingerprint_data.get("timezone", ""),
            fingerprint_data.get("webgl_vendor", ""),
            fingerprint_data.get("webgl_renderer", "")
        ]
        
        fingerprint_string = "|".join(key_fields)
        return hashlib.md5(fingerprint_string.encode()).hexdigest()
    
    def to_playwright_context(self) -> Dict[str, Any]:
        """转换为Playwright上下文选项"""
        return {
            "user_agent": self.user_agent,
            "viewport": {
                "width": self.screen_width,
                "height": self.screen_height
            },
            "device_scale_factor": self.device_scale_factor,
            "is_mobile": self.is_mobile,
            "has_touch": self.has_touch,
            "locale": self.language,
            "timezone_id": self.timezone,
            "geolocation": None,  # 可以添加地理位置
            "permissions": [],  # 可以添加权限
            "extra_http_headers": {},  # 可以添加额外headers
            "offline": False,
            "http_credentials": None,
            "color_scheme": "light",  # 或 "dark"
            "reduced_motion": "no-preference",
            "forced_colors": "none"
        }
    
    def to_puppeteer_options(self) -> Dict[str, Any]:
        """转换为Puppeteer选项"""
        return {
            "userAgent": self.user_agent,
            "viewport": {
                "width": self.screen_width,
                "height": self.screen_height,
                "deviceScaleFactor": self.device_scale_factor,
                "isMobile": self.is_mobile,
                "hasTouch": self.has_touch
            },
            "timezoneId": self.timezone,
            "locale": self.language
        }
    
    def get_init_script(self) -> str:
        """获取初始化脚本"""
        return f"""
        // 覆盖浏览器指纹
        (function() {{
            // Navigator properties
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{self.platform}'
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: () => {json.dumps(self.languages)}
            }});
            
            Object.defineProperty(navigator, 'language', {{
                get: () => '{self.language}'
            }});
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {self.hardware_concurrency}
            }});
            
            // Screen properties
            Object.defineProperty(screen, 'width', {{
                get: () => {self.screen_width}
            }});
            
            Object.defineProperty(screen, 'height', {{
                get: () => {self.screen_height}
            }});
            
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {self.screen_depth}
            }});
            
            // WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return '{self.webgl_vendor}';
                }}
                if (parameter === 37446) {{
                    return '{self.webgl_renderer}';
                }}
                return getParameter.apply(this, arguments);
            }};
            
            // Plugins
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = {json.dumps(self.plugins)};
                    return Object.assign([], plugins);
                }}
            }});
            
            // Battery API
            navigator.getBattery = undefined;
            
            // WebRTC
            if (!{str(self.webrtc_enabled).lower()}) {{
                navigator.mediaDevices = undefined;
                window.RTCPeerConnection = undefined;
                window.RTCSessionDescription = undefined;
                window.RTCIceCandidate = undefined;
            }}
        }})();
        """

class FingerprintPool(BaseModel):
    """指纹池统计"""
    total_count: int = Field(default=0, description="总指纹数")
    desktop_count: int = Field(default=0, description="桌面指纹数")
    mobile_count: int = Field(default=0, description="移动指纹数")
    
    by_browser: Dict[str, int] = Field(default_factory=dict, description="按浏览器统计")
    by_platform: Dict[str, int] = Field(default_factory=dict, description="按平台统计")
    by_screen_resolution: Dict[str, int] = Field(default_factory=dict, description="按分辨率统计")
    
    average_use_count: float = Field(default=0.0, description="平均使用次数")
    recently_used_count: int = Field(default=0, description="最近使用的指纹数")
```

#### 3.2.2 指纹管理器实现
```python
# src/anti_detection/fingerprint/manager.py
"""浏览器指纹管理器"""
import asyncio
import random
import json
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from pathlib import Path

from src.anti_detection.fingerprint.models import BrowserFingerprint, FingerprintPool
from src.anti_detection.fingerprint.generator import FingerprintGenerator
from src.core.redis import get_redis, RedisKeys
from src.core.database import db_transaction
from src.utils.logger.logger import get_logger
from src.core.config.settings import settings
from sqlalchemy import select, update, and_, or_

logger = get_logger("fingerprint.manager")

class FingerprintManager:
    """浏览器指纹管理器"""
    
    def __init__(self):
        self.redis = get_redis()
        self._pool_size = settings.FINGERPRINT_POOL_SIZE
        self._rotation_interval = settings.FINGERPRINT_ROTATION_INTERVAL
        self._generator = FingerprintGenerator()
        self._fingerprint_cache: Dict[str, BrowserFingerprint] = {}
        self._platform_fingerprints: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
        
        # 加载预定义指纹
        self._predefined_fingerprints_path = (
            settings.DATA_DIR / "fingerprints" / "predefined.json"
        )
    
    async def initialize(self):
        """初始化指纹池"""
        logger.info("Initializing fingerprint manager...")
        
        # 加载预定义指纹
        await self._load_predefined_fingerprints()
        
        # 从数据库加载指纹
        await self._load_fingerprints_from_db()
        
        # 生成不足的指纹
        await self._ensure_pool_size()
        
        logger.info(f"Fingerprint manager initialized with {len(self._fingerprint_cache)} fingerprints")
    
    async def get_fingerprint(self, platform: Optional[str] = None) -> BrowserFingerprint:
        """获取一个指纹"""
        async with self._lock:
            # 获取可用指纹列表
            available_fingerprints = await self._get_available_fingerprints(platform)
            
            if not available_fingerprints:
                # 生成新指纹
                fingerprint = await self._generator.generate()
                await self.add_fingerprint(fingerprint)
                return fingerprint
            
            # 选择使用次数最少的指纹
            fingerprint_id = min(
                available_fingerprints,
                key=lambda fid: self._fingerprint_cache.get(fid, BrowserFingerprint(
                    fingerprint_id=fid,
                    user_agent="",
                    webgl_vendor="",
                    webgl_renderer="",
                    canvas_fingerprint="",
                    timezone=""
                )).use_count
            )
            
            fingerprint = self._fingerprint_cache[fingerprint_id]
            
            # 更新使用统计
            fingerprint.use_count += 1
            fingerprint.last_used_at = datetime.utcnow()
            
            # 异步更新数据库
            asyncio.create_task(self._update_fingerprint_usage(fingerprint))
            
            return fingerprint
    
    async def add_fingerprint(self, fingerprint: BrowserFingerprint) -> bool:
        """添加指纹"""
        try:
            # 生成ID
            if not fingerprint.fingerprint_id:
                fingerprint.fingerprint_id = BrowserFingerprint.generate_id(
                    fingerprint.dict()
                )
            
            # 保存到数据库
            async with db_transaction() as session:
                # 使用upsert避免重复
                stmt = """
                INSERT INTO browser_fingerprints 
                (fingerprint_id, user_agent, platform, browser_name, browser_version,
                 screen_width, screen_height, timezone, webgl_vendor, webgl_renderer,
                 canvas_fingerprint, languages, fonts, plugins, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (fingerprint_id) DO UPDATE
                SET updated_at = CURRENT_TIMESTAMP
                """
                
                await session.execute(stmt, (
                    fingerprint.fingerprint_id,
                    fingerprint.user_agent,
                    fingerprint.platform,
                    fingerprint.browser_name,
                    fingerprint.browser_version,
                    fingerprint.screen_width,
                    fingerprint.screen_height,
                    fingerprint.timezone,
                    fingerprint.webgl_vendor,
                    fingerprint.webgl_renderer,
                    fingerprint.canvas_fingerprint,
                    fingerprint.languages,
                    fingerprint.fonts,
                    json.dumps(fingerprint.plugins),
                    json.dumps(fingerprint.metadata)
                ))
            
            # 添加到缓存
            async with self._lock:
                self._fingerprint_cache[fingerprint.fingerprint_id] = fingerprint
            
            # 添加到Redis
            await self._add_to_redis(fingerprint)
            
            logger.debug(f"Added fingerprint: {fingerprint.fingerprint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add fingerprint: {e}")
            return False
    
    async def add_fingerprints_batch(self, fingerprints: List[BrowserFingerprint]) -> int:
        """批量添加指纹"""
        success_count = 0
        
        for fingerprint in fingerprints:
            if await self.add_fingerprint(fingerprint):
                success_count += 1
        
        logger.info(f"Added {success_count}/{len(fingerprints)} fingerprints")
        return success_count
    
    async def rotate_fingerprints(self):
        """轮换指纹"""
        try:
            # 获取需要轮换的指纹（使用次数过多或时间过长）
            rotate_threshold_count = 100
            rotate_threshold_time = datetime.utcnow() - timedelta(
                seconds=self._rotation_interval
            )
            
            fingerprints_to_rotate = []
            
            async with self._lock:
                for fid, fingerprint in self._fingerprint_cache.items():
                    if (fingerprint.use_count > rotate_threshold_count or 
                        (fingerprint.last_used_at and 
                         fingerprint.last_used_at < rotate_threshold_time)):
                        fingerprints_to_rotate.append(fingerprint)
            
            # 生成新指纹替换
            for old_fingerprint in fingerprints_to_rotate:
                new_fingerprint = await self._generator.generate()
                
                # 继承平台限制
                new_fingerprint.allowed_platforms = old_fingerprint.allowed_platforms
                new_fingerprint.blocked_platforms = old_fingerprint.blocked_platforms
                
                # 添加新指纹
                await self.add_fingerprint(new_fingerprint)
                
                # 移除旧指纹
                await self._remove_fingerprint(old_fingerprint)
            
            logger.info(f"Rotated {len(fingerprints_to_rotate)} fingerprints")
            
        except Exception as e:
            logger.error(f"Error rotating fingerprints: {e}")
    
    async def get_pool_stats(self) -> FingerprintPool:
        """获取指纹池统计"""
        try:
            stats = FingerprintPool()
            
            async with self._lock:
                fingerprints = list(self._fingerprint_cache.values())
            
            stats.total_count = len(fingerprints)
            
            # 设备类型统计
            stats.desktop_count = sum(1 for f in fingerprints if not f.is_mobile)
            stats.mobile_count = sum(1 for f in fingerprints if f.is_mobile)
            
            # 浏览器统计
            for f in fingerprints:
                browser = f.browser_name
                stats.by_browser[browser] = stats.by_browser.get(browser, 0) + 1
            
            # 平台统计
            for f in fingerprints:
                platform = f.platform
                stats.by_platform[platform] = stats.by_platform.get(platform, 0) + 1
            
            # 分辨率统计
            for f in fingerprints:
                resolution = f"{f.screen_width}x{f.screen_height}"
                stats.by_screen_resolution[resolution] = \
                    stats.by_screen_resolution.get(resolution, 0) + 1
            
            # 使用统计
            if fingerprints:
                stats.average_use_count = sum(f.use_count for f in fingerprints) / len(fingerprints)
                
                recent_threshold = datetime.utcnow() - timedelta(hours=1)
                stats.recently_used_count = sum(
                    1 for f in fingerprints 
                    if f.last_used_at and f.last_used_at > recent_threshold
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return FingerprintPool()
    
    async def _load_predefined_fingerprints(self):
        """加载预定义指纹"""
        try:
            if self._predefined_fingerprints_path.exists():
                with open(self._predefined_fingerprints_path, 'r') as f:
                    data = json.load(f)
                
                fingerprints = [
                    BrowserFingerprint(**fp_data) for fp_data in data
                ]
                
                # 批量添加
                await self.add_fingerprints_batch(fingerprints)
                
                logger.info(f"Loaded {len(fingerprints)} predefined fingerprints")
            else:
                logger.warning("No predefined fingerprints found")
                
        except Exception as e:
            logger.error(f"Error loading predefined fingerprints: {e}")
    
    async def _load_fingerprints_from_db(self):
        """从数据库加载指纹"""
        try:
            async with db_transaction() as session:
                stmt = select(browser_fingerprints_table).limit(self._pool_size)
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                async with self._lock:
                    for row in rows:
                        fingerprint = BrowserFingerprint(**dict(row))
                        self._fingerprint_cache[fingerprint.fingerprint_id] = fingerprint
                
                logger.info(f"Loaded {len(rows)} fingerprints from database")
                
        except Exception as e:
            logger.error(f"Error loading fingerprints from database: {e}")
    
    async def _ensure_pool_size(self):
        """确保池大小满足要求"""
        try:
            current_size = len(self._fingerprint_cache)
            
            if current_size < self._pool_size:
                # 生成不足的指纹
                needed = self._pool_size - current_size
                logger.info(f"Generating {needed} fingerprints to meet pool size")
                
                new_fingerprints = []
                for _ in range(needed):
                    fingerprint = await self._generator.generate()
                    new_fingerprints.append(fingerprint)
                
                # 批量添加
                await self.add_fingerprints_batch(new_fingerprints)
                
        except Exception as e:
            logger.error(f"Error ensuring pool size: {e}")
    
    async def _get_available_fingerprints(self, platform: Optional[str] = None) -> List[str]:
        """获取可用的指纹ID列表"""
        available = []
        
        for fid, fingerprint in self._fingerprint_cache.items():
            # 平台过滤
            if platform:
                if fingerprint.blocked_platforms and platform in fingerprint.blocked_platforms:
                    continue
                if fingerprint.allowed_platforms and platform not in fingerprint.allowed_platforms:
                    continue
            
            available.append(fid)
        
        return available
    
    async def _update_fingerprint_usage(self, fingerprint: BrowserFingerprint):
        """更新指纹使用信息"""
        try:
            async with db_transaction() as session:
                stmt = update(browser_fingerprints_table).where(
                    browser_fingerprints_table.c.fingerprint_id == fingerprint.fingerprint_id
                ).values(
                    use_count=fingerprint.use_count,
                    last_used_at=fingerprint.last_used_at,
                    updated_at=datetime.utcnow()
                )
                await session.execute(stmt)
                
        except Exception as e:
            logger.error(f"Error updating fingerprint usage: {e}")
    
    async def _add_to_redis(self, fingerprint: BrowserFingerprint):
        """添加指纹到Redis"""
        try:
            # 添加到总池
            pool_key = RedisKeys.FINGERPRINT_POOL
            await self.redis.sadd(pool_key, fingerprint.fingerprint_id)
            
            # 添加指纹详情
            detail_key = f"{pool_key}:{fingerprint.fingerprint_id}"
            await self.redis.setex(
                detail_key,
                3600,  # 1小时过期
                fingerprint.json()
            )
            
            # 更新已使用集合
            if fingerprint.last_used_at:
                used_key = RedisKeys.FINGERPRINT_USED
                await self.redis.zadd(
                    used_key,
                    {fingerprint.fingerprint_id: fingerprint.last_used_at.timestamp()}
                )
                
        except Exception as e:
            logger.error(f"Error adding fingerprint to Redis: {e}")
    
    async def _remove_fingerprint(self, fingerprint: BrowserFingerprint):
        """移除指纹"""
        try:
            # 从缓存移除
            async with self._lock:
                self._fingerprint_cache.pop(fingerprint.fingerprint_id, None)
            
            # 从Redis移除
            pool_key = RedisKeys.FINGERPRINT_POOL
            await self.redis.srem(pool_key, fingerprint.fingerprint_id)
            
            detail_key = f"{pool_key}:{fingerprint.fingerprint_id}"
            await self.redis.delete(detail_key)
            
            # 从数据库标记为删除
            async with db_transaction() as session:
                stmt = update(browser_fingerprints_table).where(
                    browser_fingerprints_table.c.fingerprint_id == fingerprint.fingerprint_id
                ).values(
                    metadata=fingerprint.metadata.update({"deleted": True}),
                    updated_at=datetime.utcnow()
                )
                await session.execute(stmt)
                
        except Exception as e:
            logger.error(f"Error removing fingerprint: {e}")

# 创建全局指纹管理器实例
fingerprint_manager = FingerprintManager()
```

#### 3.2.3 指纹生成器实现
```python
# src/anti_detection/fingerprint/generator.py
"""浏览器指纹生成器"""
import random
import hashlib
from typing import List, Dict, Any
from datetime import datetime

from src.anti_detection.fingerprint.models import BrowserFingerprint
from src.utils.logger.logger import get_logger

logger = get_logger("fingerprint.generator")

class FingerprintGenerator:
    """浏览器指纹生成器"""
    
    def __init__(self):
        # User Agent组件
        self.browsers = {
            "Chrome": {
                "versions": ["120.0.6099.130", "121.0.6167.85", "122.0.6261.58"],
                "engine": "AppleWebKit/537.36 (KHTML, like Gecko)"
            },
            "Firefox": {
                "versions": ["121.0", "122.0", "123.0"],
                "engine": "Gecko/20100101"
            },
            "Safari": {
                "versions": ["17.2.1", "17.3", "17.3.1"],
                "engine": "AppleWebKit/605.1.15 (KHTML, like Gecko)"
            }
        }
        
        self.platforms = {
            "Windows": ["Windows NT 10.0; Win64; x64", "Windows NT 11.0; Win64; x64"],
            "macOS": ["Macintosh; Intel Mac OS X 14_2_1", "Macintosh; Intel Mac OS X 14_3"],
            "Linux": ["X11; Linux x86_64", "X11; Ubuntu; Linux x86_64"]
        }
        
        self.mobile_devices = {
            "iPhone": {
                "platform": "iPhone; CPU iPhone OS 17_2_1 like Mac OS X",
                "extra": "Mobile/15E148"
            },
            "Android": {
                "platform": "Linux; Android 13",
                "models": ["SM-S918B", "Pixel 7", "ONEPLUS A6013"]
            }
        }
        
        # 屏幕分辨率
        self.desktop_resolutions = [
            (1920, 1080), (2560, 1440), (1366, 768), (1440, 900),
            (1536, 864), (1280, 720), (1600, 900), (3840, 2160)
        ]
        
        self.mobile_resolutions = [
            (390, 844), (393, 852), (412, 915), (360, 780), (375, 812)
        ]
        
        # 时区
        self.timezones = [
            ("Asia/Shanghai", -480),
            ("Asia/Tokyo", -540),
            ("Europe/London", 0),
            ("America/New_York", 300),
            ("America/Los_Angeles", 480),
            ("Europe/Berlin", -60),
            ("Australia/Sydney", -660)
        ]
        
        # WebGL供应商和渲染器
        self.webgl_vendors = ["Intel Inc.", "NVIDIA Corporation", "AMD", "Apple Inc."]
        
        self.webgl_renderers = {
            "Intel Inc.": [
                "Intel(R) UHD Graphics 630",
                "Intel(R) Iris(R) Xe Graphics",
                "Intel(R) HD Graphics 620"
            ],
            "NVIDIA Corporation": [
                "NVIDIA GeForce GTX 1060 6GB/PCIe/SSE2",
                "NVIDIA GeForce RTX 3060/PCIe/SSE2",
                "NVIDIA GeForce GTX 1660 Ti/PCIe/SSE2"
            ],
            "AMD": [
                "AMD Radeon RX 580 Series",
                "AMD Radeon RX 6600 XT",
                "AMD Radeon Pro 5500M"
            ],
            "Apple Inc.": [
                "Apple M1",
                "Apple M1 Pro",
                "Apple M2"
            ]
        }
        
        # 语言
        self.languages = [
            ["zh-CN", "zh", "en"],
            ["en-US", "en"],
            ["ja-JP", "ja", "en"],
            ["ko-KR", "ko", "en"],
            ["fr-FR", "fr", "en"],
            ["de-DE", "de", "en"]
        ]
        
        # 字体列表
        self.fonts = [
            ["Arial", "Verdana", "Times New Roman", "Georgia", "Courier New"],
            ["Arial", "Helvetica", "Times", "Courier", "Verdana"],
            ["微软雅黑", "宋体", "黑体", "Arial", "Times New Roman"]
        ]
        
        # 插件
        self.plugins = [
            {"name": "PDF Viewer", "filename": "internal-pdf-viewer"},
            {"name": "Chrome PDF Plugin", "filename": "internal-pdf-viewer"},
            {"name": "Native Client", "filename": "internal-nacl-plugin"}
        ]
    
    async def generate(self) -> BrowserFingerprint:
        """生成一个新的浏览器指纹"""
        # 决定设备类型
        is_mobile = random.random() < 0.3  # 30%概率是移动设备
        
        if is_mobile:
            return await self._generate_mobile_fingerprint()
        else:
            return await self._generate_desktop_fingerprint()
    
    async def _generate_desktop_fingerprint(self) -> BrowserFingerprint:
        """生成桌面浏览器指纹"""
        # 选择浏览器
        browser_name = random.choice(list(self.browsers.keys()))
        browser_info = self.browsers[browser_name]
        browser_version = random.choice(browser_info["versions"])
        
        # 选择平台
        platform_name = random.choice(list(self.platforms.keys()))
        platform_string = random.choice(self.platforms[platform_name])
        
        # 构建User Agent
        if browser_name == "Chrome":
            user_agent = f"Mozilla/5.0 ({platform_string}) {browser_info['engine']} Chrome/{browser_version} Safari/537.36"
        elif browser_name == "Firefox":
            user_agent = f"Mozilla/5.0 ({platform_string}) {browser_info['engine']} Firefox/{browser_version}"
        else:  # Safari
            user_agent = f"Mozilla/5.0 ({platform_string}) {browser_info['engine']} Version/{browser_version} Safari/605.1.15"
        
        # 选择屏幕分辨率
        screen_width, screen_height = random.choice(self.desktop_resolutions)
        
        # 选择WebGL信息
        webgl_vendor = random.choice(self.webgl_vendors)
        webgl_renderer = random.choice(self.webgl_renderers[webgl_vendor])
        
        # 选择时区
        timezone, timezone_offset = random.choice(self.timezones)
        
        # 选择语言
        languages = random.choice(self.languages)
        
        # 生成Canvas指纹
        canvas_fingerprint = self._generate_canvas_fingerprint()
        
        # 生成音频指纹
        audio_fingerprint = self._generate_audio_fingerprint()
        
        # 创建指纹对象
        fingerprint_data = {
            "user_agent": user_agent,
            "platform": platform_name,
            "browser_name": browser_name,
            "browser_version": browser_version,
            "screen_width": screen_width,
            "screen_height": screen_height,
            "screen_depth": 24,
            "device_scale_factor": random.choice([1.0, 1.25, 1.5, 2.0]),
            "timezone": timezone,
            "timezone_offset": timezone_offset,
            "language": languages[0],
            "languages": languages,
            "webgl_vendor": webgl_vendor,
            "webgl_renderer": webgl_renderer,
            "canvas_fingerprint": canvas_fingerprint,
            "audio_fingerprint": audio_fingerprint,
            "fonts": random.choice(self.fonts),
            "plugins": random.sample(self.plugins, k=random.randint(1, len(self.plugins))),
            "hardware_concurrency": random.choice([4, 6, 8, 12, 16]),
            "device_memory": random.choice([4, 8, 16, 32]),
            "max_touch_points": 0,
            "webrtc_enabled": random.choice([True, False]),
            "cookies_enabled": True,
            "do_not_track": random.choice(["1", None]),
            "is_mobile": False,
            "has_touch": False,
            "device_type": "desktop"
        }
        
        # 生成ID
        fingerprint_id = BrowserFingerprint.generate_id(fingerprint_data)
        fingerprint_data["fingerprint_id"] = fingerprint_id
        
        return BrowserFingerprint(**fingerprint_data)
    
    async def _generate_mobile_fingerprint(self) -> BrowserFingerprint:
        """生成移动浏览器指纹"""
        # 选择设备类型
        device_type = random.choice(["iPhone", "Android"])
        
        if device_type == "iPhone":
            # iOS设备
            device_info = self.mobile_devices["iPhone"]
            platform = "iPhone"
            browser_name = "Safari"
            browser_version = "17.2"
            
            user_agent = f"Mozilla/5.0 ({device_info['platform']}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{browser_version} {device_info['extra']} Safari/604.1"
            
            webgl_vendor = "Apple Inc."
            webgl_renderer = "Apple GPU"
            
        else:
            # Android设备
            device_info = self.mobile_devices["Android"]
            platform = "Android"
            browser_name = "Chrome"
            browser_version = random.choice(self.browsers["Chrome"]["versions"])
            model = random.choice(device_info["models"])
            
            user_agent = f"Mozilla/5.0 ({device_info['platform']}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Mobile Safari/537.36"
            
            webgl_vendor = random.choice(["Qualcomm", "ARM"])
            webgl_renderer = "Adreno (TM) 640" if webgl_vendor == "Qualcomm" else "Mali-G78"
        
        # 选择屏幕分辨率
        screen_width, screen_height = random.choice(self.mobile_resolutions)
        
        # 选择时区
        timezone, timezone_offset = random.choice(self.timezones)
        
        # 选择语言
        languages = random.choice(self.languages)
        
        # 生成Canvas指纹
        canvas_fingerprint = self._generate_canvas_fingerprint()
        
        # 创建指纹对象
        fingerprint_data = {
            "user_agent": user_agent,
            "platform": platform,
            "browser_name": browser_name,
            "browser_version": browser_version,
            "screen_width": screen_width,
            "screen_height": screen_height,
            "screen_depth": 24,
            "device_scale_factor": random.choice([2.0, 3.0]),
            "timezone": timezone,
            "timezone_offset": timezone_offset,
            "language": languages[0],
            "languages": languages,
            "webgl_vendor": webgl_vendor,
            "webgl_renderer": webgl_renderer,
            "canvas_fingerprint": canvas_fingerprint,
            "audio_fingerprint": None,  # 移动设备通常不暴露音频指纹
            "fonts": [],  # 移动设备字体列表通常为空
            "plugins": [],  # 移动设备没有插件
            "hardware_concurrency": random.choice([4, 6, 8]),
            "device_memory": random.choice([2, 3, 4, 6, 8]),
            "max_touch_points": random.choice([5, 10]),
            "webrtc_enabled": True,
            "cookies_enabled": True,
            "do_not_track": None,
            "is_mobile": True,
            "has_touch": True,
            "device_type": "mobile"
        }
        
        # 生成ID
        fingerprint_id = BrowserFingerprint.generate_id(fingerprint_data)
        fingerprint_data["fingerprint_id"] = fingerprint_id
        
        return BrowserFingerprint(**fingerprint_data)
    
    def _generate_canvas_fingerprint(self) -> str:
        """生成Canvas指纹"""
        # 模拟Canvas指纹生成
        # 实际的Canvas指纹是通过在Canvas上绘制特定内容然后转换为图像数据得到的
        # 这里生成一个模拟的指纹
        random_data = f"canvas_{random.randint(1000000, 9999999)}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(random_data.encode()).hexdigest()
    
    def _generate_audio_fingerprint(self) -> str:
        """生成音频指纹"""
        # 模拟音频指纹生成
        # 实际的音频指纹是通过Web Audio API生成的
        random_data = f"audio_{random.randint(1000000, 9999999)}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(random_data.encode()).hexdigest()
```

### Task 3.3: 创建反爬系统测试脚本

#### 3.3.1 测试反爬系统
```python
# scripts/test_antidetection.py
"""测试反爬系统功能"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.anti_detection.proxy.manager import proxy_manager
from src.anti_detection.proxy.models import Proxy, ProxyType, ProxyLocation
from src.anti_detection.fingerprint.manager import fingerprint_manager
from src.anti_detection.behavior.simulator import BehaviorSimulator
from src.utils.logger.logger import get_logger

logger = get_logger("test.antidetection")

async def test_proxy_system():
    """测试代理系统"""
    logger.info("Testing proxy system...")
    
    # 初始化代理管理器
    await proxy_manager.initialize()
    
    # 添加测试代理
    test_proxies = [
        Proxy(
            proxy_id=f"test_proxy_{i}",
            proxy_url=f"http://proxy{i}.example.com:8080",
            proxy_type=ProxyType.HTTP,
            location=ProxyLocation(
                country="US",
                country_name="United States",
                city="New York"
            ),
            provider="TestProvider",
            score=80 + i
        )
        for i in range(5)
    ]
    
    # 批量添加
    added_count = await proxy_manager.add_proxies_batch(test_proxies)
    logger.info(f"Added {added_count} test proxies")
    
    # 获取代理
    proxy = await proxy_manager.get_proxy("test")
    assert proxy is not None, "Failed to get proxy"
    logger.info(f"✓ Got proxy: {proxy.proxy_id}")
    
    # 释放代理
    await proxy_manager.release_proxy(proxy, success=True, response_time=1.5)
    logger.info("✓ Released proxy successfully")
    
    # 获取统计
    stats = await proxy_manager.get_pool_stats()
    logger.info(f"✓ Proxy pool stats: {stats.dict()}")
    
    # 清理
    await proxy_manager.shutdown()
    
    return True

async def test_fingerprint_system():
    """测试指纹系统"""
    logger.info("Testing fingerprint system...")
    
    # 初始化指纹管理器
    await fingerprint_manager.initialize()
    
    # 获取指纹
    fingerprint = await fingerprint_manager.get_fingerprint()
    assert fingerprint is not None, "Failed to get fingerprint"
    logger.info(f"✓ Got fingerprint: {fingerprint.fingerprint_id}")
    logger.info(f"  User Agent: {fingerprint.user_agent}")
    logger.info(f"  Screen: {fingerprint.screen_width}x{fingerprint.screen_height}")
    logger.info(f"  WebGL: {fingerprint.webgl_vendor} - {fingerprint.webgl_renderer}")
    
    # 获取平台特定指纹
    platform_fingerprint = await fingerprint_manager.get_fingerprint("xiaohongshu")
    assert platform_fingerprint is not None, "Failed to get platform fingerprint"
    logger.info(f"✓ Got platform-specific fingerprint: {platform_fingerprint.fingerprint_id}")
    
    # 获取统计
    stats = await fingerprint_manager.get_pool_stats()
    logger.info(f"✓ Fingerprint pool stats:")
    logger.info(f"  Total: {stats.total_count}")
    logger.info(f"  Desktop: {stats.desktop_count}")
    logger.info(f"  Mobile: {stats.mobile_count}")
    logger.info(f"  Average use count: {stats.average_use_count:.2f}")
    
    return True

async def test_behavior_simulator():
    """测试行为模拟器"""
    logger.info("Testing behavior simulator...")
    
    # 由于行为模拟需要真实的浏览器页面，这里只测试基础功能
    simulator = BehaviorSimulator()
    
    # 测试配置
    logger.info(f"✓ Mouse speed range: {simulator.min_mouse_speed}-{simulator.max_mouse_speed} px/s")
    logger.info(f"✓ Scroll delay range: {simulator.min_scroll_delay}-{simulator.max_scroll_delay}s")
    logger.info(f"✓ Type delay range: {simulator.min_type_delay}-{simulator.max_type_delay}s")
    
    return True

async def test_integration():
    """测试反爬系统集成"""
    logger.info("Testing anti-detection integration...")
    
    # 模拟一个完整的反爬配置流程
    # 1. 获取代理
    await proxy_manager.initialize()
    proxy = await proxy_manager.get_proxy("test")
    
    # 2. 获取指纹
    await fingerprint_manager.initialize()
    fingerprint = await fingerprint_manager.get_fingerprint("test")
    
    # 3. 创建爬取配置
    crawl_config = {
        "proxy": proxy.to_dict() if proxy else None,
        "fingerprint": fingerprint.to_playwright_context() if fingerprint else None,
        "behavior_simulation": True
    }
    
    logger.info("✓ Created crawl configuration:")
    logger.info(f"  Proxy: {proxy.proxy_id if proxy else 'None'}")
    logger.info(f"  Fingerprint: {fingerprint.fingerprint_id if fingerprint else 'None'}")
    logger.info(f"  Behavior simulation: {crawl_config['behavior_simulation']}")
    
    # 清理
    if proxy:
        await proxy_manager.release_proxy(proxy, success=True)
    
    await proxy_manager.shutdown()
    
    return True

async def main():
    """主测试流程"""
    logger.info("Starting anti-detection system tests...")
    
    tests = [
        ("Proxy System", test_proxy_system),
        ("Fingerprint System", test_fingerprint_system),
        ("Behavior Simulator", test_behavior_simulator),
        ("Integration", test_integration)
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
        logger.info("\n✅ All anti-detection tests passed!")
    else:
        logger.error("\n❌ Some anti-detection tests failed!")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
```

### 验证步骤汇总

执行以下命令验证Phase 3的实现：

```bash
# 1. 创建必要的目录
mkdir -p data/fingerprints
mkdir -p data/proxies

# 2. 创建预定义指纹文件（可选）
cat > data/fingerprints/predefined.json << 'EOF'
[
  {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "platform": "Windows",
    "browser_name": "Chrome",
    "browser_version": "121.0.0.0",
    "screen_width": 1920,
    "screen_height": 1080,
    "timezone": "Asia/Shanghai",
    "timezone_offset": -480,
    "language": "zh-CN",
    "languages": ["zh-CN", "zh", "en"],
    "webgl_vendor": "Intel Inc.",
    "webgl_renderer": "Intel(R) UHD Graphics 630",
    "canvas_fingerprint": "predefined_canvas_001",
    "is_mobile": false,
    "device_type": "desktop"
  }
]
EOF

# 3. 运行反爬系统测试
poetry run python scripts/test_antidetection.py

# 4. 检查日志
tail -f logs/crawler.log | grep -E "(proxy|fingerprint|behavior)"
```

如果所有测试都通过，说明反爬对抗系统已经成功实现！

---

## 下一步

完成Phase 3后，我们将进入Phase 4：实现平台适配器。请确保：
1. 代理池管理正常工作
2. 指纹库能够正常轮换
3. 行为模拟器配置正确
4. 反爬组件能够正确集成

准备好后，继续执行第4部分的任务。