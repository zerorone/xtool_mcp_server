"""
思维模式配置文件 - 定义各种工具的思维模式组合

这个配置文件定义了不同工具类型应该使用的思维模式组合，
以及思维方法工具箱中所有可用的思维模式类型。
"""

from enum import Enum
from typing import Optional


class ToolThinkingMode(Enum):
    """工具思维模式枚举"""

    # 基础工具模式
    DEBUG = "debug"  # 调试模式
    ANALYZE = "analyze"  # 分析模式
    CODEREVIEW = "codereview"  # 代码审查模式
    REFACTOR = "refactor"  # 重构模式
    PLANNER = "planner"  # 规划模式
    SECAUDIT = "secaudit"  # 安全审计模式
    TESTGEN = "testgen"  # 测试生成模式
    DOCGEN = "docgen"  # 文档生成模式
    PRECOMMIT = "precommit"  # 提交前检查模式

    # 高级模式
    THINKDEEP = "thinkdeep"  # 深度思考模式
    CONSENSUS = "consensus"  # 共识构建模式
    TRACER = "tracer"  # 追踪分析模式
    CHAT = "chat"  # 对话交流模式

    # 特殊模式
    AUTO = "auto"  # 自动选择模式
    CUSTOM = "custom"  # 自定义模式
    HYBRID = "hybrid"  # 混合模式


# 思维方法工具箱 - 所有可用的思维模式
THINKING_PATTERNS_TOOLBOX = {
    # 分析类思维模式
    "第一性原理": {
        "name": "第一性原理",
        "description": "从基本原理出发，逐步构建理解",
        "category": "analytical",
        "strengths": ["深度理解", "本质洞察", "去除假设"],
        "use_cases": ["复杂问题分解", "创新解决方案", "系统设计"],
    },
    "系统思维": {
        "name": "系统思维",
        "description": "将问题作为相互关联的系统来理解",
        "category": "analytical",
        "strengths": ["整体视角", "关系理解", "动态分析"],
        "use_cases": ["架构设计", "性能优化", "依赖分析"],
    },
    "批判性思维": {
        "name": "批判性思维",
        "description": "质疑假设，评估证据，逻辑推理",
        "category": "analytical",
        "strengths": ["逻辑严谨", "偏见识别", "论证评估"],
        "use_cases": ["代码审查", "安全分析", "决策评估"],
    },
    "分析思维": {
        "name": "分析思维",
        "description": "将复杂问题分解为可管理的部分",
        "category": "analytical",
        "strengths": ["问题分解", "结构化分析", "细节关注"],
        "use_cases": ["调试", "性能分析", "代码理解"],
    },
    "计算思维": {
        "name": "计算思维",
        "description": "用算法和数据结构的方式思考问题",
        "category": "analytical",
        "strengths": ["算法设计", "效率优化", "自动化"],
        "use_cases": ["算法优化", "数据处理", "自动化设计"],
    },
    # 创造类思维模式
    "创造性思维": {
        "name": "创造性思维",
        "description": "产生新颖独特的想法和解决方案",
        "category": "creative",
        "strengths": ["创新", "想象力", "突破常规"],
        "use_cases": ["功能设计", "用户体验", "问题解决"],
    },
    "设计思维": {
        "name": "设计思维",
        "description": "以用户为中心的问题解决方法",
        "category": "creative",
        "strengths": ["用户导向", "迭代改进", "原型设计"],
        "use_cases": ["界面设计", "API设计", "用户体验"],
    },
    "横向思维": {
        "name": "横向思维",
        "description": "从不同角度和维度思考问题",
        "category": "creative",
        "strengths": ["视角转换", "创新方案", "打破定式"],
        "use_cases": ["创新解决方案", "替代方案", "突破瓶颈"],
    },
    "逆向思维": {
        "name": "逆向思维",
        "description": "从结果倒推原因，从目标倒推路径",
        "category": "creative",
        "strengths": ["目标导向", "路径规划", "问题预防"],
        "use_cases": ["测试设计", "故障排查", "安全分析"],
    },
    "类比思维": {
        "name": "类比思维",
        "description": "通过相似性理解和解决问题",
        "category": "creative",
        "strengths": ["知识迁移", "模式识别", "快速理解"],
        "use_cases": ["学习新技术", "问题解决", "概念理解"],
    },
    # 战略类思维模式
    "战略思维": {
        "name": "战略思维",
        "description": "长远规划和全局优化",
        "category": "strategic",
        "strengths": ["长期规划", "资源优化", "风险管理"],
        "use_cases": ["项目规划", "架构决策", "技术选型"],
    },
    "商业思维": {
        "name": "商业思维",
        "description": "从商业价值和ROI角度思考",
        "category": "strategic",
        "strengths": ["价值评估", "成本效益", "市场理解"],
        "use_cases": ["功能优先级", "技术决策", "资源分配"],
    },
    "产品思维": {
        "name": "产品思维",
        "description": "从产品和用户价值角度思考",
        "category": "strategic",
        "strengths": ["用户价值", "产品迭代", "功能规划"],
        "use_cases": ["功能设计", "用户故事", "产品改进"],
    },
    # 实践类思维模式
    "工程思维": {
        "name": "工程思维",
        "description": "注重实践、可行性和工程化",
        "category": "practical",
        "strengths": ["实用性", "可维护性", "工程化"],
        "use_cases": ["系统设计", "代码实现", "部署方案"],
    },
    "敏捷思维": {
        "name": "敏捷思维",
        "description": "迭代、反馈、持续改进",
        "category": "practical",
        "strengths": ["快速迭代", "响应变化", "持续改进"],
        "use_cases": ["项目管理", "开发流程", "团队协作"],
    },
    "精益思维": {
        "name": "精益思维",
        "description": "消除浪费，最大化价值",
        "category": "practical",
        "strengths": ["效率优化", "去除冗余", "价值流"],
        "use_cases": ["流程优化", "代码重构", "性能优化"],
    },
    # 系统类思维模式
    "整体思维": {
        "name": "整体思维",
        "description": "从整体和部分的关系理解问题",
        "category": "systems",
        "strengths": ["全局视野", "综合分析", "平衡考虑"],
        "use_cases": ["架构设计", "系统集成", "影响分析"],
    },
    "数据思维": {
        "name": "数据思维",
        "description": "基于数据和证据做决策",
        "category": "systems",
        "strengths": ["客观分析", "量化评估", "趋势识别"],
        "use_cases": ["性能分析", "监控设计", "决策支持"],
    },
    # 逻辑类思维模式
    "归纳思维": {
        "name": "归纳思维",
        "description": "从具体实例推导一般规律",
        "category": "logical",
        "strengths": ["模式发现", "规律总结", "经验提炼"],
        "use_cases": ["最佳实践", "模式识别", "规范制定"],
    },
    "演绎思维": {
        "name": "演绎思维",
        "description": "从一般原理推导具体结论",
        "category": "logical",
        "strengths": ["逻辑推理", "预测结果", "验证假设"],
        "use_cases": ["问题诊断", "影响预测", "方案验证"],
    },
    # 其他思维模式
    "元认知": {
        "name": "元认知",
        "description": "思考思考本身，反思认知过程",
        "category": "meta",
        "strengths": ["自我反思", "学习优化", "认知改进"],
        "use_cases": ["学习总结", "方法改进", "思维优化"],
    },
    "直觉思维": {
        "name": "直觉思维",
        "description": "基于经验和模式的快速判断",
        "category": "intuitive",
        "strengths": ["快速决策", "经验运用", "模式识别"],
        "use_cases": ["快速诊断", "初步判断", "经验应用"],
    },
    "结构化思维": {
        "name": "结构化思维",
        "description": "用框架和模型组织思考",
        "category": "structured",
        "strengths": ["清晰逻辑", "完整覆盖", "系统方法"],
        "use_cases": ["问题分析", "方案设计", "文档组织"],
    },
    "假设驱动": {
        "name": "假设驱动",
        "description": "形成假设并系统验证",
        "category": "scientific",
        "strengths": ["科学方法", "系统验证", "迭代改进"],
        "use_cases": ["调试", "性能优化", "问题解决"],
    },
    "根因分析": {
        "name": "根因分析",
        "description": "深入挖掘问题的根本原因",
        "category": "diagnostic",
        "strengths": ["深度诊断", "问题定位", "永久解决"],
        "use_cases": ["故障排查", "性能问题", "质量改进"],
    },
    # 精神类思维模式
    "工匠精神": {
        "name": "工匠精神",
        "description": "追求卓越，精益求精，注重细节和品质",
        "category": "mindset",
        "strengths": ["极致品质", "精细打磨", "持续改进", "专注细节"],
        "use_cases": ["代码优化", "性能调优", "用户体验", "产品打磨", "质量提升"],
    },
    "钻研精神": {
        "name": "钻研精神",
        "description": "深入探究，不断学习，追求技术本质",
        "category": "mindset",
        "strengths": ["深度学习", "技术突破", "知识积累", "本质理解"],
        "use_cases": ["技术研究", "问题攻关", "知识探索", "创新突破", "疑难解决"],
    },
    # 哲学类思维模式
    "苏格拉底式反问": {
        "name": "苏格拉底式反问",
        "description": "通过连续提问引导深入思考，挑战假设，揭示真相",
        "category": "philosophical",
        "strengths": ["深度探索", "假设挑战", "逻辑验证", "本质追问"],
        "use_cases": ["需求分析", "方案评审", "问题诊断", "知识传授", "决策验证"],
    },
    # 分解类思维模式
    "原子性思维": {
        "name": "原子性思维",
        "description": "将复杂系统分解为不可再分的最小单元，确保每个单元的独立性和完整性",
        "category": "decomposition",
        "strengths": ["最小化分解", "独立验证", "清晰边界", "易于测试"],
        "use_cases": ["功能拆分", "模块设计", "单元测试", "微服务设计", "组件化开发"],
    },
    "MECE原则": {
        "name": "MECE原则",
        "description": "完全穷尽、相互独立 - 确保分类既无遗漏又无重叠",
        "category": "decomposition",
        "strengths": ["完整覆盖", "清晰分类", "无重复", "系统化"],
        "use_cases": ["问题分解", "方案设计", "测试用例", "架构设计", "需求分析"],
    },
    "层次化分解": {
        "name": "层次化分解",
        "description": "按照业务、逻辑、实现等层次进行系统化分解",
        "category": "decomposition",
        "strengths": ["层次清晰", "逐级细化", "关注分离", "易于管理"],
        "use_cases": ["系统设计", "架构分层", "功能规划", "复杂度管理", "模块化设计"],
    },
    # 关系类思维模式
    "依赖关系分析": {
        "name": "依赖关系分析",
        "description": "分析和管理系统中的时序、数据、状态等各类依赖关系",
        "category": "relational",
        "strengths": ["依赖识别", "解耦设计", "风险预测", "优化路径"],
        "use_cases": ["系统集成", "性能优化", "故障分析", "重构规划", "部署设计"],
    },
    "组合复用思维": {
        "name": "组合复用思维",
        "description": "通过组合小而专的组件来构建复杂功能，实现高内聚低耦合",
        "category": "relational",
        "strengths": ["复用性高", "灵活组合", "维护简单", "扩展性强"],
        "use_cases": ["组件设计", "代码复用", "框架开发", "插件系统", "模块组合"],
    },
    # 工程实践类思维模式
    "契约式设计": {
        "name": "契约式设计",
        "description": "通过明确的前置条件、后置条件和不变量来设计接口，确保代码的正确性和可靠性",
        "category": "engineering",
        "strengths": ["接口明确", "责任清晰", "错误预防", "文档化"],
        "use_cases": ["API设计", "接口定义", "函数契约", "模块边界", "错误处理"],
    },
    "防御式编程": {
        "name": "防御式编程",
        "description": "预防性地处理潜在错误，通过输入验证、异常处理和状态检查确保程序稳定性",
        "category": "engineering",
        "strengths": ["稳定性高", "错误预防", "容错能力", "安全性强"],
        "use_cases": ["输入验证", "异常处理", "资源管理", "安全编程", "边界检查"],
    },
    "单一职责原则": {
        "name": "单一职责原则",
        "description": "每个模块、类或函数应该只有一个变化的理由，只负责一项职责",
        "category": "engineering",
        "strengths": ["职责明确", "易于维护", "低耦合", "高内聚"],
        "use_cases": ["类设计", "函数拆分", "模块划分", "架构设计", "代码重构"],
    },
    "测试驱动思维": {
        "name": "测试驱动思维",
        "description": "先写测试再写代码，通过测试驱动设计和开发，确保代码质量和完整性",
        "category": "engineering",
        "strengths": ["质量保证", "设计驱动", "回归预防", "文档作用"],
        "use_cases": ["功能开发", "接口设计", "重构保护", "需求验证", "质量保证"],
    },
    "SOLID原则": {
        "name": "SOLID原则",
        "description": "面向对象设计的五大原则：单一职责、开闭原则、里氏替换、接口隔离、依赖倒置",
        "category": "engineering",
        "strengths": ["设计合理", "扩展性好", "维护性高", "耦合度低"],
        "use_cases": ["面向对象设计", "架构设计", "代码重构", "设计模式", "框架开发"],
    },
}


# 工具思维模式配置 - 定义每种工具模式应该使用的思维模式组合
TOOL_THINKING_PATTERNS = {
    ToolThinkingMode.DEBUG: {
        "primary": ["根因分析", "假设驱动", "系统思维"],
        "secondary": ["逆向思维", "分析思维", "批判性思维"],
        "optional": ["数据思维", "整体思维", "钻研精神", "苏格拉底式反问", "依赖关系分析", "防御式编程"],
    },
    ToolThinkingMode.ANALYZE: {
        "primary": ["系统思维", "分析思维", "第一性原理"],
        "secondary": ["数据思维", "结构化思维", "批判性思维"],
        "optional": ["战略思维", "整体思维", "MECE原则", "层次化分解"],
    },
    ToolThinkingMode.CODEREVIEW: {
        "primary": ["批判性思维", "工程思维", "结构化思维"],
        "secondary": ["系统思维", "精益思维", "设计思维"],
        "optional": [
            "安全思维",
            "性能思维",
            "工匠精神",
            "原子性思维",
            "苏格拉底式反问",
            "契约式设计",
            "防御式编程",
            "SOLID原则",
        ],
    },
    ToolThinkingMode.REFACTOR: {
        "primary": ["设计思维", "精益思维", "工程思维"],
        "secondary": ["系统思维", "创造性思维", "结构化思维"],
        "optional": ["战略思维", "产品思维", "原子性思维", "组合复用思维", "MECE原则", "单一职责原则", "SOLID原则"],
    },
    ToolThinkingMode.PLANNER: {
        "primary": ["战略思维", "系统思维", "结构化思维"],
        "secondary": ["敏捷思维", "产品思维", "分析思维"],
        "optional": ["商业思维", "风险思维", "MECE原则", "层次化分解"],
    },
    ToolThinkingMode.SECAUDIT: {
        "primary": ["批判性思维", "逆向思维", "系统思维"],
        "secondary": ["根因分析", "假设驱动", "整体思维"],
        "optional": ["攻击者思维", "风险思维"],
    },
    ToolThinkingMode.TESTGEN: {
        "primary": ["逆向思维", "批判性思维", "系统思维"],
        "secondary": ["边界思维", "假设驱动", "结构化思维"],
        "optional": ["创造性思维", "数据思维", "原子性思维", "MECE原则", "测试驱动思维", "契约式设计"],
    },
    ToolThinkingMode.DOCGEN: {
        "primary": ["结构化思维", "系统思维", "用户思维"],
        "secondary": ["分析思维", "设计思维", "教学思维"],
        "optional": ["视觉思维", "叙事思维", "层次化分解"],
    },
    ToolThinkingMode.PRECOMMIT: {
        "primary": ["批判性思维", "系统思维", "整体思维"],
        "secondary": ["工程思维", "质量思维", "影响分析"],
        "optional": ["风险思维", "协作思维", "依赖关系分析"],
    },
    ToolThinkingMode.THINKDEEP: {
        "primary": ["第一性原理", "系统思维", "元认知"],
        "secondary": ["批判性思维", "创造性思维", "横向思维"],
        "optional": ["哲学思维", "跨学科思维", "苏格拉底式反问"],
    },
    ToolThinkingMode.CONSENSUS: {
        "primary": ["系统思维", "批判性思维", "综合思维"],
        "secondary": ["多视角思维", "平衡思维", "整合思维"],
        "optional": ["谈判思维", "共识构建", "苏格拉底式反问"],
    },
    ToolThinkingMode.TRACER: {
        "primary": ["系统思维", "流程思维", "追踪思维"],
        "secondary": ["分析思维", "数据思维", "可视化思维"],
        "optional": ["调试思维", "性能思维", "依赖关系分析", "层次化分解"],
    },
    ToolThinkingMode.CHAT: {
        "primary": ["对话思维", "共情思维", "适应性思维"],
        "secondary": ["创造性思维", "类比思维", "教学思维"],
        "optional": ["幽默思维", "叙事思维", "苏格拉底式反问"],
    },
}


# 思维模式权重配置
THINKING_PATTERN_WEIGHTS = {
    "primary": 0.5,  # 主要模式权重
    "secondary": 0.3,  # 次要模式权重
    "optional": 0.2,  # 可选模式权重
}


# 自动模式选择规则
# 修复后的关键词映射 - 解决冲突问题
AUTO_SELECTION_RULES = {
    "keywords": {
        "bug|error|exception|crash|fail": ToolThinkingMode.DEBUG,
        "analyze|analysis|understand|examine|investigate": ToolThinkingMode.ANALYZE,
        "review|inspect|quality|compliance|standard": ToolThinkingMode.CODEREVIEW,
        "refactor|optimize|improve|enhance|restructure": ToolThinkingMode.REFACTOR,
        "plan|strategy|roadmap|design|architect": ToolThinkingMode.PLANNER,
        "security|vulnerability|threat|risk|audit": ToolThinkingMode.SECAUDIT,
        "test|testing|coverage|scenario|edge_case": ToolThinkingMode.TESTGEN,
        "document|docs|explain|describe|comment": ToolThinkingMode.DOCGEN,
        "commit|validate|verify|check|lint": ToolThinkingMode.PRECOMMIT,
        "think|reason|consider|reflect|contemplate": ToolThinkingMode.THINKDEEP,
    },
    "context_patterns": {
        "performance": ["性能思维", "数据思维", "系统思维"],
        "architecture": ["架构思维", "系统思维", "设计思维", "层次化分解"],
        "user_experience": ["用户思维", "设计思维", "产品思维"],
        "data_processing": ["数据思维", "算法思维", "系统思维"],
        "integration": ["系统思维", "接口思维", "整合思维", "依赖关系分析"],
        "decomposition": ["原子性思维", "MECE原则", "层次化分解", "组合复用思维"],
        "questioning": ["苏格拉底式反问", "批判性思维", "第一性原理"],
        "code_quality": ["契约式设计", "防御式编程", "单一职责原则", "测试驱动思维"],
        "design_principles": ["SOLID原则", "设计思维", "工程思维", "原子性思维"],
    },
}


def get_thinking_patterns_for_mode(mode: ToolThinkingMode, max_patterns: int = 5) -> list[str]:
    """
    获取指定模式的思维模式列表

    Args:
        mode: 工具思维模式
        max_patterns: 最大返回模式数量

    Returns:
        思维模式名称列表
    """
    if mode not in TOOL_THINKING_PATTERNS:
        return []

    config = TOOL_THINKING_PATTERNS[mode]
    patterns = []

    # 按权重添加模式
    patterns.extend(config.get("primary", []))
    patterns.extend(config.get("secondary", []))
    patterns.extend(config.get("optional", []))

    return patterns[:max_patterns]


def get_pattern_details(pattern_name: str) -> Optional[dict]:
    """
    获取思维模式的详细信息

    Args:
        pattern_name: 思维模式名称

    Returns:
        思维模式详细信息字典
    """
    return THINKING_PATTERNS_TOOLBOX.get(pattern_name)


def suggest_patterns_for_context(context: str, problem_type: Optional[str] = None) -> list[str]:
    """
    根据上下文推荐思维模式

    Args:
        context: 问题上下文
        problem_type: 问题类型（可选）

    Returns:
        推荐的思维模式列表
    """
    suggested_patterns = []
    context_lower = context.lower()

    # 基于关键词匹配
    import re

    for keyword_pattern, mode in AUTO_SELECTION_RULES["keywords"].items():
        if re.search(keyword_pattern, context_lower):
            patterns = get_thinking_patterns_for_mode(mode)
            suggested_patterns.extend(patterns[:3])
            break

    # 基于上下文模式 - 修复匹配逻辑
    for ctx_type, patterns in AUTO_SELECTION_RULES["context_patterns"].items():
        # 将下划线替换为空格进行匹配
        ctx_keywords = ctx_type.replace("_", " ").split()
        if any(keyword in context_lower for keyword in ctx_keywords):
            suggested_patterns.extend(patterns)

    # 如果仍然没有推荐，使用通用模式
    if not suggested_patterns:
        # 检查中文关键词
        if any(word in context for word in ["性能", "优化", "瓶颈"]):
            suggested_patterns.extend(["性能思维", "数据思维", "系统思维"])
        elif any(word in context for word in ["错误", "问题", "调试", "bug"]):
            suggested_patterns.extend(["根因分析", "系统思维", "假设驱动", "防御式编程"])
        elif any(word in context for word in ["设计", "架构", "重构"]):
            suggested_patterns.extend(["设计思维", "系统思维", "工程思维", "SOLID原则"])
        elif any(word in context for word in ["分解", "拆分", "模块", "组件"]):
            suggested_patterns.extend(["原子性思维", "MECE原则", "层次化分解", "单一职责原则"])
        elif any(word in context for word in ["测试", "验证", "用例"]):
            suggested_patterns.extend(["测试驱动思维", "契约式设计", "MECE原则"])
        elif any(word in context for word in ["为什么", "如何", "原因", "本质"]):
            suggested_patterns.extend(["苏格拉底式反问", "第一性原理", "根因分析"])
        elif any(word in context for word in ["接口", "契约", "协议", "边界"]):
            suggested_patterns.extend(["契约式设计", "防御式编程", "单一职责原则"])
        elif any(word in context for word in ["依赖", "耦合", "关系", "集成"]):
            suggested_patterns.extend(["依赖关系分析", "组合复用思维", "SOLID原则"])
        else:
            # 默认推荐
            suggested_patterns.extend(["系统思维", "分析思维", "批判性思维", "钻研精神", "苏格拉底式反问"])

    # 去重并返回
    seen = set()
    unique_patterns = []
    for pattern in suggested_patterns:
        if pattern not in seen and pattern in THINKING_PATTERNS_TOOLBOX:
            seen.add(pattern)
            unique_patterns.append(pattern)

    return unique_patterns[:5]


# 平衡的思维模式效率评分 (修复后)
PATTERN_EFFICIENCY_SCORES = {
    "第一性原理": 0.85,
    "系统思维": 0.80,
    "批判性思维": 0.75,
    "分析思维": 0.80,
    "计算思维": 0.85,
    "创造性思维": 0.70,
    "设计思维": 0.70,
    "横向思维": 0.65,
    "逆向思维": 0.75,
    "类比思维": 0.70,
    "战略思维": 0.75,
    "商业思维": 0.70,
    "产品思维": 0.70,
    "工程思维": 0.85,
    "敏捷思维": 0.75,
    "精益思维": 0.80,
    "整体思维": 0.75,
    "数据思维": 0.80,
    "归纳思维": 0.75,
    "演绎思维": 0.80,
    "概率思维": 0.70,
    "模型思维": 0.75,
    "直觉思维": 0.60,
    "结构化思维": 0.85,
    "步骤化思维": 0.80,
    "假设驱动": 0.78,
    "根因分析": 0.82,
    "MECE原则": 0.90,
    "奥卡姆剃刀": 0.88,
    "MVP思维": 0.80,
    "DRY原则": 0.85,
    "SOLID原则": 0.80,
    "YAGNI原则": 0.85,
    "钻研精神": 0.70,
    "苏格拉底式反问": 0.75,
    "用户思维": 0.70,
    "服务思维": 0.70,
    "预测思维": 0.65,
    "场景思维": 0.75,
}

# 简化的问题类型映射 (修复后) - 从62种减少到25种核心类型
SIMPLIFIED_PROBLEM_TYPE_PATTERNS = {
    # 核心开发问题 (12种)
    "bug": ["根因分析", "假设驱动"],
    "feature": ["设计思维", "系统思维"],
    "refactor": ["结构化思维", "SOLID原则"],
    "architecture": ["系统思维", "设计思维"],
    "performance": ["性能思维", "系统思维"],
    "security": ["批判性思维", "风险评估"],
    "testing": ["测试驱动思维", "边界分析"],
    "debugging": ["根因分析", "假设驱动"],
    "optimization": ["分析思维", "约束思维"],
    "integration": ["系统思维", "依赖关系分析"],
    "deployment": ["系统思维", "风险评估"],
    "maintenance": ["系统化维护", "质量评估"],
    # 分析和规划问题 (8种)
    "analysis": ["分析思维", "模式识别"],
    "design": ["设计思维", "创造性思维"],
    "planning": ["战略思维", "依赖关系分析"],
    "research": ["探索性思维", "分析思维"],
    "investigation": ["根因分析", "系统化调查"],
    "review": ["批判性思维", "质量评估"],
    "documentation": ["结构化思维", "用户思维"],
    "requirements": ["设计思维", "利益相关者分析"],
    # 通用问题类型 (5种)
    "implementation": ["结构化思维", "步骤化思维"],
    "validation": ["系统化验证", "批判性思维"],
    "exploration": ["探索性思维", "创造性思维"],
    "decision_making": ["分析思维", "风险评估"],
    "general": ["结构化思维", "分析思维"],
}


def get_pattern_efficiency_score(pattern_name: str) -> float:
    """获取思维模式的效率分数 (修复后的版本)"""
    return PATTERN_EFFICIENCY_SCORES.get(pattern_name, 0.65)


def get_simplified_problem_patterns(problem_type: str) -> list[str]:
    """获取简化的问题类型对应的思维模式 (修复后的版本)"""
    return SIMPLIFIED_PROBLEM_TYPE_PATTERNS.get(problem_type, ["结构化思维", "分析思维"])
