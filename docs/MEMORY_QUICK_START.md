# 增强记忆系统快速入门

## 1分钟上手

### 启用增强记忆
```bash
export ENABLE_ENHANCED_MEMORY=true
```

### 基础使用
```python
from utils.intelligent_memory_retrieval import enhanced_save_memory, intelligent_recall_memory

# 保存
key = enhanced_save_memory(
    content="重要发现：系统存在SQL注入漏洞",
    tags=["security", "critical"],
    mem_type="security",
    importance="high",
    layer="project"
)

# 召回
memories = intelligent_recall_memory(
    tags=["security"],
    limit=10
)
```

## 5分钟掌握核心

### 智能搜索
```python
from utils.memory_recall_algorithms import advanced_memory_recall

# 语义搜索（不需要精确匹配）
results = advanced_memory_recall(
    query="authentication problems"  # 可以找到 "auth issues", "login bugs" 等
)

# 带上下文的搜索
context = {"tags": ["critical"], "type": "bug"}
results = advanced_memory_recall(
    query="memory leak",
    context=context,
    context_weight=0.5  # 50% 权重给上下文匹配
)

# 思维模式搜索
results = advanced_memory_recall(
    thinking_patterns=["debugging", "critical_analysis"]
)
```

### 生命周期管理
```python
from utils.memory_lifecycle import evaluate_memory_health

# 检查系统健康
health = evaluate_memory_health()
print(f"健康分数: {health['health_score']:.2f}")
print(f"待清理: {health['memories_to_delete']}")
```

## 常用场景

### 场景1：Bug追踪
```python
# 保存bug信息
enhanced_save_memory(
    content="内存泄漏：数据库连接池未正确释放",
    tags=["bug", "memory-leak", "database"],
    mem_type="bug",
    importance="high",
    layer="project"
)

# 搜索相关bug
bugs = advanced_memory_recall(
    query="database connection",
    mem_type="bug"
)
```

### 场景2：架构决策记录
```python
# 记录架构决策
enhanced_save_memory(
    content="""
    决策：采用微服务架构
    原因：
    1. 团队可以独立开发和部署
    2. 技术栈灵活性
    3. 易于水平扩展
    风险：
    - 增加系统复杂度
    - 需要服务发现和负载均衡
    """,
    tags=["architecture", "microservices", "decision"],
    mem_type="architecture",
    importance="high",
    layer="project"
)

# 查找架构相关决策
decisions = intelligent_recall_memory(
    tags=["architecture"],
    mem_type="architecture"
)
```

### 场景3：知识库构建
```python
# 保存最佳实践
enhanced_save_memory(
    content="Python最佳实践：使用类型提示提高代码可读性",
    tags=["python", "best-practice", "type-hints"],
    mem_type="documentation",
    layer="global"  # 全局知识
)

# 搜索特定语言的最佳实践
practices = advanced_memory_recall(
    query="python type",
    tags=["best-practice"]
)
```

## 配置选项

### 基础配置
```bash
# 记忆系统开关
export ENABLE_ENHANCED_MEMORY=true

# 质量阈值（低于此值的记忆会被标记）
export MEMORY_QUALITY_THRESHOLD=0.3

# 衰减天数（多少天后开始衰减）
export MEMORY_DECAY_DAYS=30
```

### 高级配置
```bash
# 衰减曲线类型
export MEMORY_DECAY_CURVE=exponential  # linear|exponential|logarithmic|step

# 记忆复活提升值
export MEMORY_RESURRECTION_BOOST=0.3

# 存储限制
export MEMORY_PROJECT_MAX_ITEMS=5000
```

## 最佳实践

### DO ✅
- 使用描述性标签
- 设置合适的重要性级别
- 定期检查系统健康状况
- 利用语义搜索而非精确匹配
- 为重要内容添加结构化信息

### DON'T ❌
- 避免过于宽泛的标签（如"misc"）
- 不要忽略元数据字段
- 避免存储过于临时的信息
- 不要依赖单一搜索维度

## 故障排除

### 搜索无结果？
```python
# 检查是否启用
import os
print(os.getenv("ENABLE_ENHANCED_MEMORY"))  # 应该是 "true"

# 降低质量阈值
results = intelligent_recall_memory(
    query="...",
    min_quality=0.1  # 默认是 0.3
)
```

### 记忆质量低？
```python
# 查看详细评分
from utils.memory_lifecycle import get_lifecycle_manager
manager = get_lifecycle_manager()

# 评估特定记忆
value = manager.evaluate_memory_value(memory)
print(f"质量因素:")
print(f"  内容质量: {value['quality']:.2f}")
print(f"  衰减影响: {value['decay']:.2f}")
print(f"  历史价值: {value['historical']:.2f}")
```

## 进阶技巧

### 批量导入
```python
# 从现有文档批量创建记忆
documents = [...]  # 你的文档列表
for doc in documents:
    enhanced_save_memory(
        content=doc['content'],
        tags=extract_tags(doc),  # 自定义标签提取
        mem_type=classify_document(doc),  # 自定义分类
        layer="project"
    )
```

### 定期维护
```python
# 设置定期任务清理低价值记忆
from utils.memory_lifecycle import get_lifecycle_manager
manager = get_lifecycle_manager()

# 执行优化（dry_run=False 真正删除）
stats = manager.optimize_memory_storage(dry_run=False)
print(f"清理了 {stats['deleted']} 个低价值记忆")
```

## 下一步

- 查看 [详细功能文档](ENHANCED_MEMORY_FEATURES.md)
- 探索 [API 参考](../utils/)
- 了解 [架构设计](MEMORY_SYSTEM_DEVELOPMENT_SUMMARY.md)