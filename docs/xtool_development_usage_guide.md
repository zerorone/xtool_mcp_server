# 🎯 Zen 自举开发使用指南

本指南说明如何使用 xtool MCP Server 的工具来执行"用 Zen 开发 Zen"的开发计划。

## 🚀 快速开始

### 1. 初始化开发环境

```bash
# 激活 zen 环境
source xtool_venv/bin/activate

# 查看当前可用的 Xtool 工具
# 在 Claude 中使用 listmodels 工具查看可用模型
```

### 2. 开始第一天的开发

#### 早晨：规划和准备
```
# 在 Claude 中调用 planner 工具
planner:
  topic: "Day 1 - 增强记忆系统架构设计"
  complexity: "expert"
  constraints: "参考 TODO_zen_development.md 中的 Day 1 任务"
```

#### 深度思考架构设计
```
# 使用 thinkdeep 进行架构分析
thinkdeep:
  topic: "三层记忆架构设计（全局/项目/会话）"
  depth: "first-principles"
  thinking_mode: "comprehensive"
  constraints: |
    - 分析不同层级记忆的生命周期
    - 设计高效的索引和检索机制
    - 考虑记忆衰减和优化策略
    - 确保系统可扩展性
```

#### 记录重要决策
```
# 使用 memory 工具记录架构决策
memory:
  action: "save"
  topic: "三层记忆架构设计决策"
  content: "[thinkdeep 的输出结果]"
  context: "XTOOL_development"
  importance: "critical"
```

### 3. 编码实现阶段

#### 创建核心类
```python
# 开始编写 utils/enhanced_memory.py
# 使用 Claude 的代码能力实现设计
```

#### 代码审查
```
# 完成编码后，使用 codereview 工具
codereview:
  thinking_mode: "comprehensive"
  constraints: |
    - 检查代码质量和设计模式
    - 验证错误处理机制
    - 评估性能影响
    - 确保代码可维护性
```

### 4. 调试和问题解决

#### 遇到问题时
```
# 使用 debug 工具
debug:
  problem: "记忆持久化时出现序列化错误"
  context: "enhanced_memory.py 第 125 行"
  thinking_mode: "systematic"
```

### 5. 每日总结

#### 晚上回顾
```
# 使用 challenge 工具挑战当日工作
challenge:
  topic: "今日完成的记忆系统架构设计"
  perspective: "devil's advocate"
  constraints: |
    - 是否有更好的设计方案？
    - 当前设计的潜在问题？
    - 性能瓶颈在哪里？
```

#### 记录进展
```
# 使用 memory 记录当日总结
memory:
  action: "save"
  topic: "Day 1 开发总结"
  content: |
    完成的任务：[列表]
    遇到的挑战：[描述]
    明日计划：[任务]
  context: "XTOOL_development_daily"
```

## 🔄 工作流模式

### 1. 架构设计模式
```
thinkdeep（深度分析）→ memory（记录决策）→ 实现 → codereview（审查）→ debug（解决问题）
```

### 2. 功能实现模式
```
planner（规划任务）→ 编码 → codereview（审查）→ debug（调试）→ memory（记录经验）
```

### 3. 问题解决模式
```
debug（定位问题）→ thinkdeep（分析原因）→ 修复 → challenge（验证方案）
```

### 4. 优化改进模式
```
challenge（挑战现状）→ thinkdeep（深度分析）→ 实施 → codereview（验证改进）
```

## 📝 具体示例

### 示例1：设计记忆检索算法

```
# Step 1: 深度思考
thinkdeep:
  topic: "设计高效的多维度记忆检索算法"
  thinking_mode: "algorithmic"
  depth: "comprehensive"
  constraints: |
    - 支持关键词、标签、时间、相似度等多维度
    - 响应时间 < 100ms
    - 支持模糊匹配和精确匹配
    - 考虑记忆权重和衰减

# Step 2: 实现算法
[编写代码]

# Step 3: 审查代码
codereview:
  focus_areas: ["performance", "correctness", "maintainability"]
  
# Step 4: 记录设计
memory:
  action: "save"
  topic: "多维度记忆检索算法设计"
  content: "[算法设计和实现细节]"
```

### 示例2：集成思维模式

```
# Step 1: 规划集成顺序
planner:
  topic: "25种思维模式集成计划"
  total_steps: 5
  
# Step 2: 分析每种模式
thinkdeep:
  topic: "第一性原理思维模式的特点和应用场景"
  thinking_mode: "analytical"
  
# Step 3: 实现集成
[编写集成代码]

# Step 4: 测试效果
challenge:
  topic: "第一性原理思维模式的实现效果"
  constraints: "测试各种边界情况"
```

## 🛠️ 工具组合使用

### 1. 复杂问题解决组合
```
debug → thinkdeep → challenge → codereview → memory
```

### 2. 架构设计组合
```
thinkdeep → planner → memory → codereview
```

### 3. 持续改进组合
```
challenge → thinkdeep → debug → codereview → memory
```

## 📊 进度跟踪

### 使用 TODO 文件
1. 每天早晨查看 `TODO_zen_development.md`
2. 完成任务后标记为完成
3. 使用 memory 记录完成情况
4. 晚上更新进度

### 使用 planner 跟踪
```
# 每天开始时
planner:
  topic: "今日开发任务"
  step_number: 1
  total_steps: [当日任务数]
  
# 完成任务时
planner:
  step: "完成 [具体任务]"
  step_number: [当前步骤]
  next_step_required: true/false
```

## 🎯 最佳实践

1. **始终先思考**：使用 thinkdeep 进行深度分析
2. **记录一切**：使用 memory 保存重要信息
3. **持续挑战**：使用 challenge 验证设计
4. **质量第一**：使用 codereview 确保代码质量
5. **快速解决**：使用 debug 定位和解决问题

## 🚨 注意事项

1. **工具调用格式**：确保按照每个工具的正确格式调用
2. **上下文保持**：使用 continuation_id 保持工具间的上下文
3. **记忆管理**：定期使用 memory 的 recall 功能查看历史记录
4. **进度控制**：严格按照 TODO 文件的任务顺序执行

通过遵循这个指南，你将能够充分利用 Zen 的强大功能来开发 Zen 自己，真正实现"吃自己的狗粮"的开发理念！