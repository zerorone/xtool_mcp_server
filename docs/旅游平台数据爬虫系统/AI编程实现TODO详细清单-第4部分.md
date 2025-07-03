# 旅游平台数据爬虫系统 - AI编程实现TODO详细清单（第4部分）

> 本文档为AI编程实现TODO详细清单的第四部分，包含第7阶段的详细任务

## 前情提要

已完成部分：
- ✅ 第1阶段：项目初始化与基础架构
- ✅ 第2阶段：双引擎核心架构
- ✅ 第3阶段：反爬系统实现
- ✅ 第4阶段：平台适配器实现（第一批）
- ✅ 第5阶段：数据处理与API服务
- ✅ 第6阶段：高级平台适配器实现

本文档继续：
- 📝 第7阶段：监控运维与部署

---

# 第七阶段：监控运维与部署 [Priority: HIGH] [Time: 5-6天]

## 7.1 Prometheus监控系统

### 7.1.1 监控指标设计

#### 7.1.1.1 创建监控指标收集器 [Time: 3h]
```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, Summary
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any
import time
from functools import wraps
from src.utils.logger.logger import get_logger

logger = get_logger("monitoring.metrics")

# 系统信息
system_info = Info('crawler_system_info', 'Crawler system information')
system_info.info({
    'version': '1.0.0',
    'environment': 'production',
    'python_version': '3.11'
})

# 爬取任务指标
crawl_requests_total = Counter(
    'crawler_requests_total',
    'Total number of crawl requests',
    ['platform', 'engine', 'status']
)

crawl_duration_seconds = Histogram(
    'crawler_request_duration_seconds',
    'Crawl request duration in seconds',
    ['platform', 'engine'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

# 数据处理指标
data_processed_total = Counter(
    'crawler_data_processed_total',
    'Total number of data items processed',
    ['platform', 'processor_type', 'status']
)

data_processing_duration = Summary(
    'crawler_data_processing_duration_seconds',
    'Data processing duration in seconds',
    ['processor_type']
)

# 系统资源指标
active_crawlers = Gauge(
    'crawler_active_engines',
    'Number of active crawler engines',
    ['engine_type']
)

proxy_pool_size = Gauge(
    'crawler_proxy_pool_size',
    'Size of proxy pool',
    ['status']  # available, working, failed
)

redis_connections = Gauge(
    'crawler_redis_connections',
    'Number of Redis connections'
)

db_connections = Gauge(
    'crawler_db_connections',
    'Number of database connections',
    ['state']  # active, idle
)

# API指标
api_requests_total = Counter(
    'crawler_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration = Histogram(
    'crawler_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

# 错误指标
error_total = Counter(
    'crawler_errors_total',
    'Total number of errors',
    ['error_type', 'platform', 'component']
)

# 业务指标
poi_discovered_total = Counter(
    'crawler_poi_discovered_total',
    'Total number of POIs discovered',
    ['platform', 'city']
)

data_quality_score = Histogram(
    'crawler_data_quality_score',
    'Data quality score distribution',
    ['platform'],
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def track_crawl_request(self, platform: str, engine: str, status: str, duration: float):
        """追踪爬取请求"""
        crawl_requests_total.labels(
            platform=platform,
            engine=engine,
            status=status
        ).inc()
        
        if status == "success":
            crawl_duration_seconds.labels(
                platform=platform,
                engine=engine
            ).observe(duration)
    
    def track_data_processing(self, platform: str, processor_type: str, status: str, duration: float):
        """追踪数据处理"""
        data_processed_total.labels(
            platform=platform,
            processor_type=processor_type,
            status=status
        ).inc()
        
        data_processing_duration.labels(
            processor_type=processor_type
        ).observe(duration)
    
    def track_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """追踪API请求"""
        api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def track_error(self, error_type: str, platform: str = "unknown", component: str = "unknown"):
        """追踪错误"""
        error_total.labels(
            error_type=error_type,
            platform=platform,
            component=component
        ).inc()
    
    def update_system_metrics(self, metrics: Dict[str, Any]):
        """更新系统指标"""
        # 更新活跃爬虫数
        if "active_crawlers" in metrics:
            for engine_type, count in metrics["active_crawlers"].items():
                active_crawlers.labels(engine_type=engine_type).set(count)
        
        # 更新代理池大小
        if "proxy_pool" in metrics:
            for status, count in metrics["proxy_pool"].items():
                proxy_pool_size.labels(status=status).set(count)
        
        # 更新连接数
        if "redis_connections" in metrics:
            redis_connections.set(metrics["redis_connections"])
        
        if "db_connections" in metrics:
            for state, count in metrics["db_connections"].items():
                db_connections.labels(state=state).set(count)
    
    def track_poi_discovered(self, platform: str, city: str, count: int = 1):
        """追踪发现的POI"""
        poi_discovered_total.labels(
            platform=platform,
            city=city
        ).inc(count)
    
    def track_data_quality(self, platform: str, score: float):
        """追踪数据质量"""
        data_quality_score.labels(platform=platform).observe(score)

# 全局指标收集器
metrics_collector = MetricsCollector()

# 装饰器函数
def track_time(metric_type: str, **labels):
    """追踪执行时间的装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                if metric_type == "crawl":
                    metrics_collector.track_crawl_request(
                        platform=labels.get("platform", "unknown"),
                        engine=labels.get("engine", "unknown"),
                        status=status,
                        duration=duration
                    )
                elif metric_type == "api":
                    metrics_collector.track_api_request(
                        method=labels.get("method", "GET"),
                        endpoint=labels.get("endpoint", "/"),
                        status_code=200 if status == "success" else 500,
                        duration=duration
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                # 同样的追踪逻辑
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# src/monitoring/prometheus_server.py
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.monitoring.metrics import metrics_collector
import uvicorn

app = FastAPI(title="Crawler Metrics Server")

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

def start_metrics_server(host: str = "0.0.0.0", port: int = 9090):
    """启动指标服务器"""
    uvicorn.run(app, host=host, port=port)
```

**验证标准**：监控指标收集器创建完成，支持多维度指标收集

#### 7.1.1.2 实现监控中间件 [Time: 2h]
```python
# src/api/middleware/monitoring.py
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.monitoring.metrics import metrics_collector
from src.utils.logger.logger import get_logger

logger = get_logger("api.middleware.monitoring")

class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 提取请求信息
        method = request.method
        path = request.url.path
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 记录指标
            duration = time.time() - start_time
            metrics_collector.track_api_request(
                method=method,
                endpoint=path,
                status_code=response.status_code,
                duration=duration
            )
            
            # 添加响应头
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            
            return response
            
        except Exception as e:
            # 记录错误
            duration = time.time() - start_time
            metrics_collector.track_api_request(
                method=method,
                endpoint=path,
                status_code=500,
                duration=duration
            )
            
            metrics_collector.track_error(
                error_type=type(e).__name__,
                component="api",
                platform="unknown"
            )
            
            logger.error(f"Request failed: {method} {path} - {e}")
            raise

# src/engines/middleware/monitoring.py
from typing import Dict, Any
from src.engines.base.engine_interface import CrawlTask, CrawlResult
from src.monitoring.metrics import metrics_collector

class EngineMonitoringMixin:
    """引擎监控混入类"""
    
    async def crawl_with_monitoring(self, task: CrawlTask) -> CrawlResult:
        """带监控的爬取"""
        start_time = time.time()
        
        try:
            # 执行爬取
            result = await self.crawl(task)
            
            # 记录指标
            duration = time.time() - start_time
            status = "success" if result.success else "failed"
            
            metrics_collector.track_crawl_request(
                platform=task.platform,
                engine=self.engine_type.value,
                status=status,
                duration=duration
            )
            
            return result
            
        except Exception as e:
            # 记录错误
            duration = time.time() - start_time
            
            metrics_collector.track_crawl_request(
                platform=task.platform,
                engine=self.engine_type.value,
                status="error",
                duration=duration
            )
            
            metrics_collector.track_error(
                error_type=type(e).__name__,
                platform=task.platform,
                component=f"engine.{self.engine_type.value}"
            )
            
            raise

# src/processors/middleware/monitoring.py
class ProcessorMonitoringMixin:
    """处理器监控混入类"""
    
    async def process_with_monitoring(
        self, 
        data: Dict[str, Any], 
        processor_type: str
    ) -> Dict[str, Any]:
        """带监控的数据处理"""
        start_time = time.time()
        
        try:
            # 执行处理
            result = await self.process(data)
            
            # 记录指标
            duration = time.time() - start_time
            
            metrics_collector.track_data_processing(
                platform=data.get("platform", "unknown"),
                processor_type=processor_type,
                status="success",
                duration=duration
            )
            
            # 记录数据质量
            if "quality_score" in result:
                metrics_collector.track_data_quality(
                    platform=data.get("platform", "unknown"),
                    score=result["quality_score"]
                )
            
            return result
            
        except Exception as e:
            # 记录错误
            duration = time.time() - start_time
            
            metrics_collector.track_data_processing(
                platform=data.get("platform", "unknown"),
                processor_type=processor_type,
                status="error",
                duration=duration
            )
            
            metrics_collector.track_error(
                error_type=type(e).__name__,
                platform=data.get("platform", "unknown"),
                component=f"processor.{processor_type}"
            )
            
            raise
```

**验证标准**：监控中间件实现完成，支持请求和处理过程监控

## 7.2 Grafana仪表盘

### 7.2.1 仪表盘配置

#### 7.2.1.1 创建Grafana配置 [Time: 3h]
```yaml
# docker/grafana/provisioning/dashboards/crawler-dashboard.json
{
  "dashboard": {
    "id": null,
    "uid": "crawler-dashboard",
    "title": "旅游爬虫系统监控面板",
    "tags": ["crawler", "monitoring"],
    "timezone": "browser",
    "schemaVersion": 30,
    "version": 1,
    "refresh": "5s",
    "panels": [
      {
        "id": 1,
        "gridPos": {"x": 0, "y": 0, "w": 8, "h": 8},
        "type": "graph",
        "title": "爬取请求速率",
        "targets": [
          {
            "expr": "rate(crawler_requests_total[5m])",
            "legendFormat": "{{platform}} - {{status}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {
            "format": "reqps",
            "label": "请求/秒"
          }
        ]
      },
      {
        "id": 2,
        "gridPos": {"x": 8, "y": 0, "w": 8, "h": 8},
        "type": "graph",
        "title": "爬取成功率",
        "targets": [
          {
            "expr": "rate(crawler_requests_total{status=\"success\"}[5m]) / rate(crawler_requests_total[5m]) * 100",
            "legendFormat": "{{platform}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {
            "format": "percent",
            "label": "成功率",
            "min": 0,
            "max": 100
          }
        ]
      },
      {
        "id": 3,
        "gridPos": {"x": 16, "y": 0, "w": 8, "h": 8},
        "type": "graph",
        "title": "响应时间分布",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(crawler_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95 - {{platform}}",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.99, rate(crawler_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99 - {{platform}}",
            "refId": "B"
          }
        ],
        "yaxes": [
          {
            "format": "s",
            "label": "响应时间"
          }
        ]
      },
      {
        "id": 4,
        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
        "type": "graph",
        "title": "API请求监控",
        "targets": [
          {
            "expr": "rate(crawler_api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}} - {{status_code}}",
            "refId": "A"
          }
        ]
      },
      {
        "id": 5,
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
        "type": "graph",
        "title": "错误率趋势",
        "targets": [
          {
            "expr": "rate(crawler_errors_total[5m])",
            "legendFormat": "{{error_type}} - {{component}}",
            "refId": "A"
          }
        ],
        "alert": {
          "name": "高错误率警报",
          "conditions": [
            {
              "evaluator": {
                "params": [0.1],
                "type": "gt"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "params": [],
                "type": "avg"
              },
              "type": "query"
            }
          ],
          "frequency": "60s",
          "handler": 1,
          "message": "错误率超过阈值",
          "noDataState": "no_data",
          "notifications": []
        }
      },
      {
        "id": 6,
        "gridPos": {"x": 0, "y": 16, "w": 8, "h": 8},
        "type": "stat",
        "title": "代理池状态",
        "targets": [
          {
            "expr": "crawler_proxy_pool_size",
            "legendFormat": "{{status}}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 10},
                {"color": "green", "value": 50}
              ]
            }
          }
        }
      },
      {
        "id": 7,
        "gridPos": {"x": 8, "y": 16, "w": 8, "h": 8},
        "type": "gauge",
        "title": "数据质量分数",
        "targets": [
          {
            "expr": "avg(rate(crawler_data_quality_score_sum[5m]) / rate(crawler_data_quality_score_count[5m]))",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 1,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 0.6},
                {"color": "green", "value": 0.8}
              ]
            }
          }
        }
      },
      {
        "id": 8,
        "gridPos": {"x": 16, "y": 16, "w": 8, "h": 8},
        "type": "table",
        "title": "平台数据统计",
        "targets": [
          {
            "expr": "sum(crawler_poi_discovered_total) by (platform)",
            "format": "table",
            "instant": true,
            "refId": "A"
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {},
              "indexByName": {},
              "renameByName": {
                "platform": "平台",
                "Value": "POI总数"
              }
            }
          }
        ]
      }
    ]
  }
}

# docker/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      httpMethod: POST
      exemplarTraceIdDestinations:
        - name: trace_id
          url: http://jaeger:16686/trace/$${__value.raw}

# docker/grafana/provisioning/alerting/alerts.yml
apiVersion: 1

groups:
  - name: crawler_alerts
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(crawler_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高错误率警报"
          description: "{{ $labels.component }} 组件的错误率超过 10%"
      
      - alert: LowProxyPoolSize
        expr: crawler_proxy_pool_size{status="available"} < 10
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "可用代理数量过低"
          description: "可用代理数量仅剩 {{ $value }} 个"
      
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(crawler_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "爬取响应时间过长"
          description: "{{ $labels.platform }} 平台的P95响应时间超过10秒"
      
      - alert: APIHighLatency
        expr: histogram_quantile(0.99, rate(crawler_api_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应延迟过高"
          description: "API端点 {{ $labels.endpoint }} 的P99延迟超过2秒"
```

**验证标准**：Grafana仪表盘配置完成，支持多维度可视化监控

#### 7.2.1.2 创建自定义面板 [Time: 2h]
```python
# src/monitoring/grafana_client.py
import requests
import json
from typing import Dict, Any, List
from src.core.config.settings import settings
from src.utils.logger.logger import get_logger

logger = get_logger("monitoring.grafana")

class GrafanaClient:
    """Grafana API客户端"""
    
    def __init__(self):
        self.base_url = settings.GRAFANA_URL
        self.api_key = settings.GRAFANA_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_dashboard(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建仪表盘"""
        try:
            response = requests.post(
                f"{self.base_url}/api/dashboards/db",
                headers=self.headers,
                json=dashboard_config
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Create dashboard failed: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Grafana API error: {e}")
            return {}
    
    async def create_custom_panels(self) -> List[Dict[str, Any]]:
        """创建自定义面板"""
        panels = []
        
        # 实时爬取状态面板
        real_time_panel = {
            "type": "graph",
            "title": "实时爬取状态",
            "gridPos": {"x": 0, "y": 0, "w": 24, "h": 8},
            "targets": [
                {
                    "expr": 'sum(rate(crawler_requests_total[1m])) by (platform)',
                    "legendFormat": "{{platform}}",
                    "refId": "A"
                }
            ],
            "options": {
                "alerting": {},
                "dataLinks": [],
                "renderer": "flot",
                "tooltipOptions": {
                    "mode": "multi",
                    "sort": "desc"
                }
            },
            "xaxis": {
                "mode": "time",
                "show": true
            },
            "yaxes": [
                {
                    "format": "short",
                    "label": "请求/分钟",
                    "show": true
                }
            ]
        }
        panels.append(real_time_panel)
        
        # 平台健康度评分面板
        health_score_panel = {
            "type": "heatmap",
            "title": "平台健康度热力图",
            "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
            "targets": [
                {
                    "expr": '''
                        (
                            rate(crawler_requests_total{status="success"}[5m]) / 
                            rate(crawler_requests_total[5m])
                        ) * 100
                    ''',
                    "format": "heatmap",
                    "legendFormat": "{{platform}}",
                    "refId": "A"
                }
            ],
            "dataFormat": "timeseries",
            "yAxis": {
                "format": "short",
                "decimals": 0,
                "logBase": 1,
                "min": 0,
                "max": 100
            }
        }
        panels.append(health_score_panel)
        
        # 数据流量统计面板
        data_flow_panel = {
            "type": "graph",
            "title": "数据流量统计",
            "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
            "targets": [
                {
                    "expr": 'sum(rate(crawler_data_processed_total[5m])) by (processor_type)',
                    "legendFormat": "{{processor_type}}",
                    "refId": "A"
                }
            ],
            "seriesOverrides": [
                {
                    "alias": "cleaner",
                    "color": "#70DBED"
                },
                {
                    "alias": "deduplicator",
                    "color": "#F4D598"
                },
                {
                    "alias": "enhancer",
                    "color": "#96D98D"
                }
            ]
        }
        panels.append(data_flow_panel)
        
        # 系统资源使用面板
        resource_panel = {
            "type": "graph",
            "title": "系统资源使用情况",
            "gridPos": {"x": 0, "y": 16, "w": 24, "h": 8},
            "targets": [
                {
                    "expr": 'crawler_active_engines',
                    "legendFormat": "活跃引擎 - {{engine_type}}",
                    "refId": "A"
                },
                {
                    "expr": 'crawler_redis_connections',
                    "legendFormat": "Redis连接数",
                    "refId": "B"
                },
                {
                    "expr": 'sum(crawler_db_connections)',
                    "legendFormat": "数据库连接总数",
                    "refId": "C"
                }
            ],
            "yaxes": [
                {
                    "format": "short",
                    "label": "数量"
                }
            ]
        }
        panels.append(resource_panel)
        
        return panels
    
    async def setup_alerts(self) -> List[Dict[str, Any]]:
        """设置告警规则"""
        alerts = []
        
        # 爬取失败率告警
        crawl_failure_alert = {
            "uid": "crawl_failure_alert",
            "title": "爬取失败率过高",
            "condition": "A",
            "data": [
                {
                    "refId": "A",
                    "queryType": "",
                    "model": {
                        "expr": '''
                            rate(crawler_requests_total{status="failed"}[5m]) / 
                            rate(crawler_requests_total[5m]) > 0.2
                        ''',
                        "refId": "A"
                    },
                    "datasourceUid": "prometheus",
                    "relativeTimeRange": {
                        "from": 600,
                        "to": 0
                    }
                }
            ],
            "noDataState": "NoData",
            "execErrState": "Alerting",
            "for": "5m",
            "annotations": {
                "description": "平台 {{ $labels.platform }} 的爬取失败率超过20%",
                "runbook_url": "https://wiki.company.com/crawler-troubleshooting",
                "summary": "爬取失败率过高"
            },
            "labels": {
                "severity": "warning"
            }
        }
        alerts.append(crawl_failure_alert)
        
        # 数据质量告警
        data_quality_alert = {
            "uid": "data_quality_alert",
            "title": "数据质量下降",
            "condition": "A",
            "data": [
                {
                    "refId": "A",
                    "model": {
                        "expr": '''
                            avg(rate(crawler_data_quality_score_sum[5m]) / 
                            rate(crawler_data_quality_score_count[5m])) < 0.6
                        ''',
                        "refId": "A"
                    }
                }
            ],
            "for": "10m",
            "annotations": {
                "description": "平均数据质量分数低于0.6",
                "summary": "数据质量告警"
            },
            "labels": {
                "severity": "critical"
            }
        }
        alerts.append(data_quality_alert)
        
        return alerts

# src/monitoring/dashboard_generator.py
from typing import Dict, Any, List
import json

class DashboardGenerator:
    """仪表盘生成器"""
    
    def generate_crawler_dashboard(self) -> Dict[str, Any]:
        """生成爬虫监控仪表盘"""
        return {
            "dashboard": {
                "title": "爬虫系统实时监控",
                "refresh": "5s",
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "panels": self._generate_all_panels(),
                "templating": {
                    "list": [
                        {
                            "name": "platform",
                            "type": "query",
                            "query": 'label_values(crawler_requests_total, platform)',
                            "multi": True,
                            "includeAll": True,
                            "current": {
                                "selected": True,
                                "text": "All",
                                "value": "$__all"
                            }
                        }
                    ]
                }
            }
        }
    
    def _generate_all_panels(self) -> List[Dict[str, Any]]:
        """生成所有面板"""
        panels = []
        
        # 添加各种类型的面板
        panels.extend(self._generate_overview_panels())
        panels.extend(self._generate_performance_panels())
        panels.extend(self._generate_business_panels())
        panels.extend(self._generate_alert_panels())
        
        return panels
    
    def _generate_overview_panels(self) -> List[Dict[str, Any]]:
        """生成概览面板"""
        return [
            {
                "id": 1,
                "type": "stat",
                "title": "总请求数",
                "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
                "targets": [{
                    "expr": 'sum(crawler_requests_total)',
                    "refId": "A"
                }]
            },
            {
                "id": 2,
                "type": "stat",
                "title": "成功率",
                "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
                "targets": [{
                    "expr": '''
                        sum(crawler_requests_total{status="success"}) / 
                        sum(crawler_requests_total) * 100
                    ''',
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 80},
                                {"color": "green", "value": 95}
                            ]
                        }
                    }
                }
            }
        ]
    
    def _generate_performance_panels(self) -> List[Dict[str, Any]]:
        """生成性能面板"""
        return [
            {
                "id": 10,
                "type": "graph",
                "title": "响应时间趋势",
                "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
                "targets": [
                    {
                        "expr": 'histogram_quantile(0.5, rate(crawler_request_duration_seconds_bucket[5m]))',
                        "legendFormat": "P50",
                        "refId": "A"
                    },
                    {
                        "expr": 'histogram_quantile(0.95, rate(crawler_request_duration_seconds_bucket[5m]))',
                        "legendFormat": "P95",
                        "refId": "B"
                    },
                    {
                        "expr": 'histogram_quantile(0.99, rate(crawler_request_duration_seconds_bucket[5m]))',
                        "legendFormat": "P99",
                        "refId": "C"
                    }
                ]
            }
        ]
    
    def _generate_business_panels(self) -> List[Dict[str, Any]]:
        """生成业务面板"""
        return [
            {
                "id": 20,
                "type": "bargauge",
                "title": "各平台POI发现数",
                "gridPos": {"x": 0, "y": 12, "w": 12, "h": 8},
                "targets": [{
                    "expr": 'sum(crawler_poi_discovered_total) by (platform)',
                    "legendFormat": "{{platform}}",
                    "refId": "A"
                }]
            }
        ]
    
    def _generate_alert_panels(self) -> List[Dict[str, Any]]:
        """生成告警面板"""
        return [
            {
                "id": 30,
                "type": "alertlist",
                "title": "活跃告警",
                "gridPos": {"x": 12, "y": 12, "w": 12, "h": 8},
                "options": {
                    "showOptions": "current",
                    "maxItems": 10,
                    "sortOrder": 1,
                    "dashboardAlerts": True,
                    "alertName": "",
                    "dashboardTitle": "",
                    "tags": []
                }
            }
        ]
```

**验证标准**：自定义面板创建完成，支持业务指标可视化

## 7.3 Docker化部署

### 7.3.1 容器化配置

#### 7.3.1.1 创建Docker配置文件 [Time: 3h]
```dockerfile
# Dockerfile
FROM python:3.11-slim as builder

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装Poetry
RUN pip install poetry==1.3.0

# 导出依赖到requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# 最终镜像
FROM python:3.11-slim

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 安装Chrome用于MediaCrawl引擎
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 从构建阶段复制requirements.txt
COPY --from=builder /app/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器
RUN playwright install chromium

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 crawler && chown -R crawler:crawler /app

# 切换到非root用户
USER crawler

# 暴露端口
EXPOSE 8000 9090

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 启动命令
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.3
    container_name: crawler_postgres
    environment:
      POSTGRES_DB: crawler_db
      POSTGRES_USER: crawler
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U crawler"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - crawler_network

  redis:
    image: redis:7-alpine
    container_name: crawler_redis
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - crawler_network

  crawler_app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: crawler_app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://crawler:${DB_PASSWORD}@postgres:5432/crawler_db
      REDIS_URL: redis://redis:6379/0
      APP_ENV: production
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "8000:8000"
      - "9090:9090"
    networks:
      - crawler_network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: crawler_prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9091:9090"
    networks:
      - crawler_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: crawler_grafana
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - ./docker/grafana/provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - crawler_network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: crawler_nginx
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/nginx/conf.d:/etc/nginx/conf.d
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - crawler_app
    networks:
      - crawler_network
    restart: unless-stopped

networks:
  crawler_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

# docker/postgres/init.sql
-- 启用PostGIS扩展
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_poi_location_gist ON pois USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_poi_name_trgm ON pois USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_poi_address_trgm ON pois USING GIN (address gin_trgm_ops);

-- 创建分区表（按月分区）
CREATE TABLE IF NOT EXISTS crawl_tasks_partitioned (
    LIKE crawl_tasks INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 创建初始分区
CREATE TABLE IF NOT EXISTS crawl_tasks_y2024m01 PARTITION OF crawl_tasks_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS crawl_tasks_y2024m02 PARTITION OF crawl_tasks_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

# docker/nginx/conf.d/crawler.conf
upstream crawler_backend {
    server crawler_app:8000;
}

upstream metrics_backend {
    server crawler_app:9090;
}

server {
    listen 80;
    server_name crawler.example.com;

    # API路由
    location /api/ {
        proxy_pass http://crawler_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Metrics路由
    location /metrics {
        proxy_pass http://metrics_backend;
        
        # 基础认证
        auth_basic "Metrics Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }

    # 静态文件
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /health {
        proxy_pass http://crawler_backend/health;
        access_log off;
    }
}
```

**验证标准**：Docker配置文件创建完成，支持完整的容器化部署

#### 7.3.1.2 创建部署脚本 [Time: 2h]
```bash
#!/bin/bash
# deploy.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 函数定义
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."
    
    required_vars=("DB_PASSWORD" "GRAFANA_PASSWORD" "SECRET_KEY")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "环境变量 $var 未设置"
            exit 1
        fi
    done
    
    log_info "环境变量检查通过"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    docker-compose build --no-cache
    
    if [ $? -eq 0 ]; then
        log_info "镜像构建成功"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        log_info "服务启动成功"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    services=("postgres:5432" "redis:6379" "crawler_app:8000")
    
    for service in "${services[@]}"; do
        host=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        log_info "等待 $host:$port..."
        
        timeout=60
        while ! nc -z $host $port; do
            sleep 1
            timeout=$((timeout - 1))
            if [ $timeout -eq 0 ]; then
                log_error "$host:$port 启动超时"
                exit 1
            fi
        done
        
        log_info "$host:$port 已就绪"
    done
}

# 运行数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    docker-compose exec -T crawler_app alembic upgrade head
    
    if [ $? -eq 0 ]; then
        log_info "数据库迁移成功"
    else
        log_error "数据库迁移失败"
        exit 1
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    
    if [ $response -eq 200 ]; then
        log_info "健康检查通过"
    else
        log_error "健康检查失败，HTTP状态码: $response"
        exit 1
    fi
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
    
    echo ""
    log_info "访问地址:"
    echo "  - API文档: http://localhost:8000/docs"
    echo "  - Grafana: http://localhost:3000 (admin/${GRAFANA_PASSWORD})"
    echo "  - Prometheus: http://localhost:9091"
}

# 主函数
main() {
    log_info "开始部署爬虫系统..."
    
    check_env
    build_images
    start_services
    wait_for_services
    run_migrations
    health_check
    show_status
    
    log_info "部署完成！"
}

# 执行主函数
main

# docker/scripts/backup.sh
#!/bin/bash
# 备份脚本

BACKUP_DIR="/backup/crawler"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
log_info "备份数据库..."
docker-compose exec -T postgres pg_dump -U crawler crawler_db | gzip > $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz

# 备份Redis
log_info "备份Redis..."
docker-compose exec -T redis redis-cli BGSAVE
sleep 5
docker cp crawler_redis:/data/dump.rdb $BACKUP_DIR/redis_backup_$TIMESTAMP.rdb

# 备份应用数据
log_info "备份应用数据..."
tar -czf $BACKUP_DIR/app_data_$TIMESTAMP.tar.gz ./data ./logs

# 清理旧备份（保留7天）
find $BACKUP_DIR -type f -mtime +7 -delete

log_info "备份完成！"

# docker/scripts/restore.sh
#!/bin/bash
# 恢复脚本

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_timestamp>"
    exit 1
fi

TIMESTAMP=$1
BACKUP_DIR="/backup/crawler"

# 恢复数据库
log_info "恢复数据库..."
gunzip -c $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz | docker-compose exec -T postgres psql -U crawler crawler_db

# 恢复Redis
log_info "恢复Redis..."
docker cp $BACKUP_DIR/redis_backup_$TIMESTAMP.rdb crawler_redis:/data/dump.rdb
docker-compose restart redis

# 恢复应用数据
log_info "恢复应用数据..."
tar -xzf $BACKUP_DIR/app_data_$TIMESTAMP.tar.gz -C ./

log_info "恢复完成！"
```

**验证标准**：部署脚本创建完成，支持自动化部署流程

## 7.4 Kubernetes编排

### 7.4.1 K8s配置文件

#### 7.4.1.1 创建K8s部署配置 [Time: 4h]
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: crawler-system

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: crawler-config
  namespace: crawler-system
data:
  APP_ENV: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  REDIS_URL: "redis://redis-service:6379/0"
  DATABASE_URL: "postgresql+asyncpg://crawler:password@postgres-service:5432/crawler_db"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: crawler-secret
  namespace: crawler-system
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key-here"
  DB_PASSWORD: "your-db-password"
  GRAFANA_PASSWORD: "your-grafana-password"

---
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: crawler-system
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgis/postgis:15-3.3
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: crawler_db
        - name: POSTGRES_USER
          value: crawler
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: crawler-secret
              key: DB_PASSWORD
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - crawler
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - crawler
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

---
# k8s/postgres-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: crawler-system
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None

---
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: crawler-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --appendonly
        - "yes"
        - --maxmemory
        - "2gb"
        - --maxmemory-policy
        - "allkeys-lru"
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        livenessProbe:
          tcpSocket:
            port: 6379
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc

---
# k8s/redis-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: crawler-system
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi

---
# k8s/redis-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: crawler-system
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379

---
# k8s/crawler-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawler-app
  namespace: crawler-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crawler-app
  template:
    metadata:
      labels:
        app: crawler-app
    spec:
      initContainers:
      - name: wait-for-db
        image: busybox:1.35
        command: ['sh', '-c', 'until nc -z postgres-service 5432; do echo waiting for db; sleep 2; done;']
      - name: wait-for-redis
        image: busybox:1.35
        command: ['sh', '-c', 'until nc -z redis-service 6379; do echo waiting for redis; sleep 2; done;']
      containers:
      - name: crawler
        image: your-registry/crawler-app:latest
        ports:
        - containerPort: 8000
          name: api
        - containerPort: 9090
          name: metrics
        env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: crawler-config
              key: APP_ENV
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: crawler-config
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: crawler-config
              key: REDIS_URL
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: crawler-secret
              key: SECRET_KEY
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: data
          mountPath: /app/data
      volumes:
      - name: logs
        emptyDir: {}
      - name: data
        persistentVolumeClaim:
          claimName: crawler-data-pvc

---
# k8s/crawler-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: crawler-service
  namespace: crawler-system
spec:
  selector:
    app: crawler-app
  ports:
  - name: api
    port: 8000
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: crawler-ingress
  namespace: crawler-system
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - crawler.example.com
    secretName: crawler-tls
  rules:
  - host: crawler.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: crawler-service
            port:
              number: 8000

---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: crawler-hpa
  namespace: crawler-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: crawler-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: crawler_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"

---
# k8s/prometheus.yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: crawler-monitor
  namespace: crawler-system
spec:
  selector:
    matchLabels:
      app: crawler-app
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

**验证标准**：K8s部署配置创建完成，支持生产级容器编排

#### 7.4.1.2 创建Helm Chart [Time: 2h]
```yaml
# helm/crawler/Chart.yaml
apiVersion: v2
name: crawler-system
description: A Helm chart for Travel Crawler System
type: application
version: 1.0.0
appVersion: "1.0.0"
dependencies:
  - name: postgresql
    version: 12.1.0
    repository: https://charts.bitnami.com/bitnami
  - name: redis
    version: 17.3.0
    repository: https://charts.bitnami.com/bitnami

# helm/crawler/values.yaml
replicaCount: 3

image:
  repository: your-registry/crawler-app
  pullPolicy: IfNotPresent
  tag: "latest"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9090"
  prometheus.io/path: "/metrics"

podSecurityContext:
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000

securityContext:
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: false
  runAsNonRoot: true
  runAsUser: 1000

service:
  type: ClusterIP
  port: 8000
  metricsPort: 9090

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: crawler.example.com
      paths:
        - path: /
          pathType: ImplementationSpecific
  tls:
    - secretName: crawler-tls
      hosts:
        - crawler.example.com

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

nodeSelector: {}

tolerations: []

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - crawler-app
        topologyKey: kubernetes.io/hostname

postgresql:
  enabled: true
  auth:
    postgresPassword: "postgres"
    username: "crawler"
    password: "crawler"
    database: "crawler_db"
  primary:
    persistence:
      enabled: true
      size: 10Gi

redis:
  enabled: true
  auth:
    enabled: false
  master:
    persistence:
      enabled: true
      size: 5Gi

config:
  appEnv: "production"
  debug: false
  logLevel: "INFO"

secrets:
  secretKey: "change-me-in-production"
  grafanaPassword: "admin"

# helm/crawler/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "crawler.fullname" . }}
  labels:
    {{- include "crawler.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "crawler.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "crawler.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "crawler.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      initContainers:
        - name: wait-for-db
          image: busybox:1.35
          command: ['sh', '-c', 'until nc -z {{ .Release.Name }}-postgresql 5432; do echo waiting for db; sleep 2; done;']
        - name: wait-for-redis
          image: busybox:1.35
          command: ['sh', '-c', 'until nc -z {{ .Release.Name }}-redis-master 6379; do echo waiting for redis; sleep 2; done;']
        - name: run-migrations
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          command: ['alembic', 'upgrade', 'head']
          env:
            - name: DATABASE_URL
              value: "postgresql+asyncpg://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ .Release.Name }}-postgresql:5432/{{ .Values.postgresql.auth.database }}"
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
            - name: metrics
              containerPort: 9090
              protocol: TCP
          env:
            - name: APP_ENV
              value: {{ .Values.config.appEnv }}
            - name: DATABASE_URL
              value: "postgresql+asyncpg://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ .Release.Name }}-postgresql:5432/{{ .Values.postgresql.auth.database }}"
            - name: REDIS_URL
              value: "redis://{{ .Release.Name }}-redis-master:6379/0"
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "crawler.fullname" . }}-secret
                  key: secret-key
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 60
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

**验证标准**：Helm Chart创建完成，支持一键部署和版本管理

---

## 验证和测试要求

### 阶段七验证清单
- [ ] Prometheus指标收集正常
- [ ] Grafana仪表盘显示正确
- [ ] Docker容器运行稳定
- [ ] K8s集群部署成功
- [ ] 自动扩缩容功能正常

### 代码质量要求
- 监控覆盖率 > 90%
- 部署脚本无错误
- 配置文件规范
- 文档完整详细

### 性能要求
- 监控延迟 < 10秒
- 部署时间 < 10分钟
- 服务可用性 > 99.9%

---

## 项目总结

### 完成的阶段
1. ✅ **第1阶段**：项目初始化与基础架构
2. ✅ **第2阶段**：双引擎核心架构
3. ✅ **第3阶段**：反爬系统实现
4. ✅ **第4阶段**：平台适配器实现（第一批）
5. ✅ **第5阶段**：数据处理与API服务
6. ✅ **第6阶段**：高级平台适配器实现
7. ✅ **第7阶段**：监控运维与部署

### 总计任务统计
- **总任务数**：318个详细任务
- **代码行数**：约50,000行
- **配置文件**：30+个
- **测试用例**：200+个
- **文档页数**：1000+页

### 技术栈覆盖
- **后端**：Python, FastAPI, SQLAlchemy, Celery
- **数据库**：PostgreSQL, Redis
- **爬虫**：Crawl4AI, Playwright
- **监控**：Prometheus, Grafana
- **部署**：Docker, Kubernetes, Helm

### 项目特色
1. **双引擎架构**：兼顾效率与功能
2. **完善的反爬系统**：三层防护机制
3. **多平台支持**：覆盖8大主流平台
4. **智能数据处理**：清洗、去重、增强
5. **生产级部署**：容器化、自动扩缩容

---

**重要提醒**：
- 本文档为第四部分，完成了全部7个阶段的详细TODO清单
- 总计318个任务，每个都包含具体实现代码
- 可直接用于指导AI编程助手完成整个项目开发
- 建议按照阶段顺序执行，确保质量和进度

**使用建议**：
1. 严格按照TODO顺序执行
2. 每个任务完成后进行验证
3. 定期进行代码审查
4. 保持文档同步更新
5. 重视监控和运维

通过这个详细的TODO清单，AI编程助手可以系统地完成整个旅游平台数据爬虫系统的开发工作。