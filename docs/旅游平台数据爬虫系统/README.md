# 旅游平台数据爬虫系统 - 项目文档总览

## 项目简介

旅游平台数据爬虫系统是一个基于双引擎架构的大规模数据采集系统，支持8大主流旅游和社交平台的数据抓取，具备完善的反爬对抗能力和数据处理管道。

### 核心特性
- 🚀 **双引擎架构**：Crawl4AI + MediaCrawl，兼顾效率与功能
- 🛡️ **反爬对抗**：代理池、浏览器指纹、行为模拟三重防护
- 🌐 **多平台支持**：覆盖高德、马蜂窝、大众点评、携程、小红书、抖音、微博、B站
- 📊 **数据处理**：智能清洗、去重、增强处理管道
- 🔧 **API服务**：完整的RESTful API接口
- 📈 **监控运维**：Prometheus + Grafana全方位监控

---

## 文档结构

### 📋 规划文档
| 文档名称 | 描述 | 状态 |
|---------|------|------|
| [项目开发计划总览](项目开发计划总览.md) | 整体开发策略和阶段规划 | ✅ 完成 |
| [项目执行时间表](项目执行时间表.md) | 详细的时间安排和里程碑 | ✅ 完成 |
| [项目风险管理计划](项目风险管理计划.md) | 风险识别、评估与应对策略 | ✅ 完成 |

### 🛠️ 技术文档
| 文档名称 | 描述 | 状态 |
|---------|------|------|
| [技术实现指南](技术实现指南.md) | 核心技术要点和最佳实践 | ✅ 完成 |

### 📝 详细实施指南
| 文档名称 | 描述 | 状态 |
|---------|------|------|
| [第1部分-项目初始化与基础架构](项目开发TODO-第1部分-项目初始化与基础架构.md) | 环境搭建、配置管理、Docker部署 | ✅ 完成 |
| [第2部分-双引擎核心实现](项目开发TODO-第2部分-双引擎核心实现.md) | Crawl4AI和MediaCrawl引擎开发 | ✅ 完成 |
| [第3部分-反爬系统实现](项目开发TODO-第3部分-反爬系统实现.md) | 代理池、指纹、行为模拟系统 | ✅ 完成 |
| [第4部分-平台适配器实现](项目开发TODO-第4部分-平台适配器实现.md) | 高德、马蜂窝、大众点评、携程适配器 | ✅ 完成 |
| [第5部分-数据处理与API服务](项目开发TODO-第5部分-数据处理与API服务.md) | 数据清洗、去重、API开发 | ✅ 完成 |
| [第6部分-高级平台适配器实现](项目开发TODO-第6部分-高级平台适配器实现.md) | 小红书、抖音、微博、B站适配器 | ✅ 完成 |
| [第7部分-监控运维与部署](项目开发TODO-第7部分-监控运维与部署.md) | Prometheus监控、Grafana仪表盘、K8s部署 | ✅ 完成 |

---

## 快速开始

### 环境要求
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (with PostGIS)
- Redis 7+

### 安装部署
```bash
# 1. 克隆项目
git clone <repository-url>
cd travel-crawler-system

# 2. 创建虚拟环境
poetry install

# 3. 启动基础服务
docker-compose up -d postgres redis

# 4. 初始化数据库
poetry run python scripts/init_database.py

# 5. 启动应用
poetry run python src/main.py
```

### 验证安装
```bash
# 健康检查
curl http://localhost:8000/health

# API文档
open http://localhost:8000/api/v1/docs
```

---

## 系统架构

### 整体架构图
```
┌─────────────────────────────────────────────────────────────┐
│                      Web API Layer                         │
│                    (FastAPI + Uvicorn)                     │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Task       │  │   Data      │  │   Platform  │        │
│  │ Scheduler   │  │ Processor   │  │  Adapters   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                     Engine Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Crawl4AI   │  │ MediaCrawl  │  │    Anti     │        │
│  │   Engine    │  │   Engine    │  │ Detection   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │    Redis    │  │   Docker    │        │
│  │ + PostGIS   │  │   Cache     │  │  Container  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈
- **后端框架**：FastAPI + SQLAlchemy + Alembic
- **爬虫引擎**：Crawl4AI + Playwright
- **数据库**：PostgreSQL 15 + PostGIS
- **缓存**：Redis 7
- **容器化**：Docker + Docker Compose
- **监控**：Prometheus + Grafana
- **测试**：Pytest + Coverage

---

## 开发指南

### 代码规范
- 遵循PEP 8编码规范
- 使用Black代码格式化
- 使用isort导入排序
- 使用MyPy类型检查
- 代码覆盖率 ≥ 80%

### 提交规范
```bash
# 提交格式
<type>: <description>

# 示例
feat: 添加高德地图POI搜索功能
fix: 修复代理池连接超时问题
docs: 更新API接口文档
```

### 分支策略
- `main`: 主分支，生产环境代码
- `develop`: 开发分支，集成测试
- `feature/*`: 功能分支
- `hotfix/*`: 热修复分支

---

## API文档

### 认证方式
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/pois/search
```

### 主要接口
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/pois/search` - POI搜索
- `GET /api/v1/pois/{id}` - POI详情
- `POST /api/v1/tasks` - 创建爬取任务
- `GET /api/v1/tasks/{id}` - 任务状态查询

### 完整API文档
访问 `http://localhost:8000/api/v1/docs` 查看完整的交互式API文档。

---

## 监控运维

### 性能指标
- **爬取成功率** ≥ 95%
- **API响应时间** ≤ 3秒
- **数据处理延迟** ≤ 1分钟
- **系统可用性** ≥ 99.9%

### 监控面板
- **Grafana地址**：http://localhost:3000
- **Prometheus地址**：http://localhost:9090
- **默认账号**：admin/admin

### 日志查看
```bash
# 应用日志
tail -f logs/app.log

# 爬虫日志
tail -f logs/crawler.log

# 错误日志
tail -f logs/error.log
```

---

## 部署指南

### 开发环境
```bash
# 启动开发环境
docker-compose -f docker-compose.yml up -d

# 查看服务状态
docker-compose ps
```

### 生产环境
```bash
# 构建生产镜像
docker build -t travel-crawler:latest -f docker/production/Dockerfile .

# 部署到Kubernetes
kubectl apply -f k8s/
```

### 环境配置
参考 `.env.example` 文件配置相应的环境变量。

---

## 测试指南

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_crawler.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 性能测试
```bash
# API性能测试
locust -f tests/performance/locustfile.py

# 爬虫性能测试
python tests/performance/crawler_benchmark.py
```

---

## 故障排查

### 常见问题

#### 1. 爬虫失败率高
**症状**：爬取成功率下降，出现大量403/429错误

**排查步骤**：
1. 检查代理池状态：`curl http://localhost:8000/api/v1/proxy/status`
2. 查看反爬日志：`grep "anti-crawl" logs/crawler.log`
3. 验证指纹轮换：检查User-Agent和浏览器指纹是否正常轮换

**解决方案**：
- 更新代理池
- 调整请求频率
- 升级反爬策略

#### 2. 数据库连接超时
**症状**：API响应慢，数据库连接错误

**排查步骤**：
1. 检查数据库状态：`docker-compose ps postgres`
2. 查看连接池：`SELECT count(*) FROM pg_stat_activity;`
3. 检查慢查询：查看PostgreSQL慢查询日志

**解决方案**：
- 优化SQL查询
- 调整连接池配置
- 增加数据库索引

#### 3. Redis缓存问题
**症状**：缓存命中率低，响应时间长

**排查步骤**：
1. 检查Redis状态：`redis-cli ping`
2. 查看内存使用：`redis-cli info memory`
3. 分析缓存命中率：`redis-cli info stats`

**解决方案**：
- 调整缓存过期时间
- 优化缓存键设计
- 增加Redis内存

### 日志级别调整
```python
# 临时调整日志级别
import logging
logging.getLogger('crawler').setLevel(logging.DEBUG)
```

---

## 贡献指南

### 代码贡献流程
1. Fork项目到个人仓库
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交变更：`git commit -m "Add new feature"`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

### 问题反馈
- **Bug报告**：使用GitHub Issues
- **功能请求**：使用GitHub Discussions
- **安全问题**：发送邮件到 security@example.com

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 联系方式

- **项目负责人**：[Name] <email@example.com>
- **技术支持**：[Support Team] <support@example.com>
- **项目地址**：https://github.com/your-org/travel-crawler-system

---

## 更新日志

### v1.0.0 (2024-02-28)
- ✨ 初始版本发布
- 🚀 支持8大平台数据爬取
- 🛡️ 完整的反爬对抗系统
- 📊 数据处理和API服务
- 📈 监控和部署方案

---

## 相关资源

- [Python官方文档](https://docs.python.org/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Crawl4AI文档](https://github.com/unclecode/crawl4ai)
- [Playwright文档](https://playwright.dev/python/)
- [PostgreSQL文档](https://www.postgresql.org/docs/)
- [Redis文档](https://redis.io/documentation)

---

*本文档持续更新中，如有疑问请及时反馈。*