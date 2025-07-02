"""
增强的思维模式定义 - 基于软件开发全生命周期思维方法

本模块定义了基于软件开发全生命周期的专业思维模式，
涵盖了从需求分析到运维监控的所有阶段。
"""

# 核心思维方法定义
CORE_THINKING_METHODS = {
    # 基础思维方法
    "socratic_questioning": {
        "name": "苏格拉底提问法",
        "description": "通过连续追问深入本质",
        "core_principle": "问'为什么'而非'是什么'",
        "application_stages": ["需求分析", "测试验证", "问题诊断"],
        "questions": [
            "这个假设的依据是什么？",
            "有什么证据支持这个观点？",
            "从另一个角度看会怎样？",
            "这个结论的反例是什么？",
            "最坏的情况会是什么？",
        ],
        "six_layers": [
            "表面需求 - 你需要什么？",
            "功能需求 - 这个功能要解决什么问题？",
            "业务需求 - 为什么要解决这个问题？",
            "根本需求 - 不解决这个问题会怎样？",
            "价值需求 - 解决后能带来什么价值？",
            "本质需求 - 这个需求的本质是什么？",
        ],
    },
    "occam_razor": {
        "name": "奥卡姆剃刀原则",
        "description": "最简单的解释往往是正确的",
        "core_principle": "避免过度复杂化",
        "application_stages": ["方案选择", "代码设计", "架构决策"],
        "guidelines": [
            "在功能相同的情况下选择最简单的方案",
            "避免过度设计和过早优化",
            "保持代码的简洁和可读性",
            "减少不必要的抽象层次",
        ],
    },
    "mece_principle": {
        "name": "MECE原则（麦肯锡思维）",
        "description": "相互独立，完全穷尽",
        "core_principle": "确保完整性和独立性",
        "application_stages": ["需求分解", "功能分解", "测试设计", "问题分析"],
        "check_dimensions": [
            "完整性验证：子需求组合是否等于父需求",
            "独立性验证：子需求之间是否有重叠",
            "可行性验证：每个子需求是否可以独立实现",
            "一致性验证：分解逻辑是否统一",
        ],
    },
    "first_principles": {
        "name": "第一性原理",
        "description": "从基本原理出发推导",
        "core_principle": "回归问题本质",
        "application_stages": ["架构设计", "技术选型", "创新方案", "需求分析"],
        "steps": ["识别并质疑现有假设", "分解到基本要素", "从头开始重新构建", "验证新的解决方案"],
    },
    "descartes_method": {
        "name": "笛卡尔方法论",
        "description": "分解复杂问题为简单问题",
        "core_principle": "大问题拆解为小问题",
        "application_stages": ["系统分析", "功能拆解", "需求分解"],
        "steps": [
            "怀疑一切可以怀疑的东西",
            "将复杂问题分解为简单部分",
            "从简单到复杂按顺序解决",
            "全面复查确保没有遗漏",
        ],
    },
    "systems_thinking": {
        "name": "系统思维",
        "description": "整体大于部分之和",
        "core_principle": "考虑组件间相互作用",
        "application_stages": ["架构设计", "项目管理", "集成测试", "性能优化"],
        "elements": ["识别系统边界", "理解组件关系", "分析反馈循环", "预测涌现行为"],
    },
}

# 专业思维方法定义
PROFESSIONAL_THINKING_METHODS = {
    "craftsman_spirit": {
        "name": "工匠精神",
        "description": "追求卓越，注重细节，持续改进",
        "principles": ["精益求精，不断打磨", "注重细节，追求完美", "深入理解，掌握本质", "持续学习，不断进步"],
        "suitable_for": ["代码优化", "性能调优", "用户体验", "测试验证", "调试排错"],
    },
    "research_mindset": {
        "name": "钻研精神",
        "description": "深入探究，不满足于表面理解",
        "approach": ["深挖根源，理解原理", "多角度验证，交叉检验", "系统化实验，数据驱动", "持续迭代，逐步深入"],
        "suitable_for": ["性能问题", "复杂bug", "新技术学习", "测试验证", "调试排错"],
    },
    "contractual_design": {
        "name": "契约式设计思维",
        "description": "明确定义接口契约和职责",
        "elements": [
            "前置条件：函数入参的严格验证",
            "后置条件：函数出参的明确定义",
            "不变量：函数执行过程中保持的约束",
            "异常契约：明确的异常处理约定",
        ],
        "suitable_for": ["接口设计", "代码开发", "API设计", "模块集成"],
    },
    "defensive_programming": {
        "name": "防御式编程思维",
        "description": "假设一切都可能出错",
        "practices": ["对所有输入进行验证", "处理所有可能的异常情况", "使用断言验证关键假设", "编写健壮的错误处理代码"],
        "suitable_for": ["代码开发", "安全编程", "异常处理", "系统集成"],
    },
    "user_journey": {
        "name": "用户旅程思维",
        "description": "从用户视角设计完整体验",
        "steps": ["识别用户角色和目标", "映射完整的用户流程", "识别关键接触点", "优化每个环节的体验"],
        "suitable_for": ["功能设计", "UI/UX设计", "需求分析", "测试设计"],
    },
    "atomic_thinking": {
        "name": "原子化思维",
        "description": "将功能分解到不可再分的最小单元",
        "principles": ["单一职责原则", "高内聚低耦合", "可测试性优先", "可组合性设计"],
        "suitable_for": ["功能分解", "微服务设计", "单元测试", "模块化设计"],
    },
    "risk_driven": {
        "name": "风险驱动思维",
        "description": "优先处理高风险项",
        "approach": ["识别所有潜在风险", "评估风险概率和影响", "制定风险缓解策略", "持续监控和调整"],
        "suitable_for": ["项目管理", "测试策略", "架构决策", "安全设计"],
    },
    "data_driven": {
        "name": "数据驱动思维",
        "description": "基于数据做决策",
        "practices": ["定义关键指标", "收集和分析数据", "基于数据洞察决策", "持续度量和优化"],
        "suitable_for": ["性能优化", "用户体验", "项目管理", "质量改进"],
    },
    "lifecycle_thinking": {
        "name": "生命周期思维",
        "description": "考虑事物的完整生命周期",
        "phases": ["创建和初始化", "使用和维护", "演进和升级", "退役和清理"],
        "suitable_for": ["文档管理", "数据管理", "系统设计", "项目规划"],
    },
    "trade_off_thinking": {
        "name": "权衡思维",
        "description": "在多个目标间寻找平衡",
        "dimensions": ["性能 vs 可维护性", "灵活性 vs 简单性", "安全性 vs 易用性", "成本 vs 质量"],
        "suitable_for": ["架构设计", "技术选型", "方案评估", "资源分配"],
    },
    "evolutionary_thinking": {
        "name": "演进思维",
        "description": "系统是逐步演进的",
        "principles": ["从简单开始", "迭代式改进", "保持可扩展性", "平滑升级路径"],
        "suitable_for": ["架构设计", "产品规划", "技术债务", "重构策略"],
    },
    "scenario_thinking": {
        "name": "场景化思维",
        "description": "通过具体场景验证理解",
        "approach": ["收集真实使用场景", "构建典型用例", "边界场景分析", "异常场景处理"],
        "suitable_for": ["需求分析", "测试设计", "功能验证", "用户体验"],
    },
}

# 开发阶段与思维方法映射
STAGE_THINKING_MAP = {
    "需求分析": {
        "primary": ["socratic_questioning", "first_principles", "scenario_thinking"],
        "secondary": ["user_journey", "systems_thinking"],
        "focus": "深入挖掘真实需求，区分手段和目的",
    },
    "需求分解": {
        "primary": ["mece_principle", "descartes_method"],
        "secondary": ["systems_thinking", "atomic_thinking"],
        "focus": "确保完整性和独立性，建立清晰层次",
    },
    "数据设计": {
        "primary": ["first_principles", "systems_thinking", "mece_principle"],
        "secondary": ["lifecycle_thinking", "trade_off_thinking"],
        "focus": "从业务本质出发，确保数据完整性",
    },
    "架构设计": {
        "primary": ["systems_thinking", "first_principles", "trade_off_thinking"],
        "secondary": ["evolutionary_thinking", "risk_driven"],
        "focus": "整体视角，平衡各种质量属性",
    },
    "功能设计": {
        "primary": ["systems_thinking", "mece_principle", "user_journey"],
        "secondary": ["scenario_thinking", "atomic_thinking"],
        "focus": "用户体验优先，功能职责明确",
    },
    "功能分解": {
        "primary": ["mece_principle", "atomic_thinking", "descartes_method"],
        "secondary": ["systems_thinking"],
        "focus": "细粒度分解，保持可组合性",
    },
    "代码开发": {
        "primary": ["contractual_design", "defensive_programming", "craftsman_spirit"],
        "secondary": ["mece_principle", "occam_razor"],
        "focus": "高质量代码，防御性编程",
    },
    "测试验证": {
        "primary": ["mece_principle", "risk_driven", "craftsman_spirit", "research_mindset"],
        "secondary": ["scenario_thinking", "data_driven"],
        "focus": "完整覆盖，风险驱动",
    },
    "调试排错": {
        "primary": ["research_mindset", "craftsman_spirit", "first_principles"],
        "secondary": ["systems_thinking", "data_driven"],
        "focus": "深挖根源，系统分析",
    },
    "项目管理": {
        "primary": ["systems_thinking", "data_driven", "risk_driven"],
        "secondary": ["lifecycle_thinking", "trade_off_thinking"],
        "focus": "全局视角，数据驱动决策",
    },
    "运维监控": {
        "primary": ["data_driven", "systems_thinking", "risk_driven"],
        "secondary": ["lifecycle_thinking", "scenario_thinking"],
        "focus": "实时监控，预防性维护",
    },
}

# 问题类型与思维方法映射
PROBLEM_THINKING_MAP = {
    "bug修复": ["research_mindset", "first_principles", "systems_thinking", "craftsman_spirit"],
    "性能优化": ["data_driven", "systems_thinking", "trade_off_thinking", "craftsman_spirit"],
    "新功能开发": ["user_journey", "mece_principle", "scenario_thinking", "atomic_thinking"],
    "架构设计": ["systems_thinking", "first_principles", "trade_off_thinking", "evolutionary_thinking"],
    "代码重构": ["craftsman_spirit", "atomic_thinking", "mece_principle", "occam_razor"],
    "技术选型": ["first_principles", "trade_off_thinking", "risk_driven", "data_driven"],
    "需求分析": ["socratic_questioning", "scenario_thinking", "user_journey", "first_principles"],
    "测试设计": ["mece_principle", "scenario_thinking", "risk_driven", "craftsman_spirit"],
    "安全审计": ["defensive_programming", "risk_driven", "mece_principle", "systems_thinking"],
    "文档编写": ["lifecycle_thinking", "mece_principle", "user_journey", "systems_thinking"],
}

# 思维方法组合模式
THINKING_COMBINATIONS = {
    "深度分析套装": {
        "methods": ["first_principles", "systems_thinking", "mece_principle"],
        "description": "用于复杂问题的深度分析",
        "use_cases": ["架构设计", "性能瓶颈", "系统集成"],
    },
    "质量保证套装": {
        "methods": ["craftsman_spirit", "mece_principle", "risk_driven"],
        "description": "确保高质量交付",
        "use_cases": ["代码审查", "测试设计", "质量改进"],
    },
    "创新突破套装": {
        "methods": ["first_principles", "trade_off_thinking", "evolutionary_thinking"],
        "description": "突破现有限制，创新解决方案",
        "use_cases": ["技术创新", "架构演进", "产品创新"],
    },
    "问题诊断套装": {
        "methods": ["research_mindset", "systems_thinking", "data_driven"],
        "description": "系统化问题诊断和解决",
        "use_cases": ["bug修复", "性能问题", "故障排查"],
    },
    "用户体验套装": {
        "methods": ["user_journey", "scenario_thinking", "craftsman_spirit"],
        "description": "优化用户体验",
        "use_cases": ["UI设计", "功能优化", "用户研究"],
    },
}
