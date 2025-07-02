"""
统一的思维模式管理器
Unified Thinking Mode Manager

提供思维模式的统一管理、映射和调配功能。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ThinkingModeType(Enum):
    """思维模式类型枚举"""

    # 基础思维方法
    SOCRATIC_QUESTIONING = "socratic_questioning"
    OCCAM_RAZOR = "occam_razor"
    MECE_PRINCIPLE = "mece_principle"
    FIRST_PRINCIPLES = "first_principles"
    DESCARTES_METHOD = "descartes_method"
    SYSTEMS_THINKING = "systems_thinking"

    # 专业思维方法
    CRAFTSMAN_SPIRIT = "craftsman_spirit"
    RESEARCH_MINDSET = "research_mindset"
    CONTRACTUAL_DESIGN = "contractual_design"
    DEFENSIVE_PROGRAMMING = "defensive_programming"
    USER_JOURNEY = "user_journey"
    ATOMIC_THINKING = "atomic_thinking"
    RISK_DRIVEN = "risk_driven"
    DATA_DRIVEN = "data_driven"
    LIFECYCLE_THINKING = "lifecycle_thinking"
    TRADE_OFF_THINKING = "trade_off_thinking"
    EVOLUTIONARY_THINKING = "evolutionary_thinking"
    SCENARIO_THINKING = "scenario_thinking"

    # 特殊模式
    AUTO = "auto"  # 自动选择
    DEFAULT = "default"  # 默认组合


class DevelopmentStage(Enum):
    """开发阶段枚举"""

    REQUIREMENT_ANALYSIS = "需求分析"
    REQUIREMENT_DECOMPOSITION = "需求分解"
    DATA_DESIGN = "数据设计"
    ARCHITECTURE_DESIGN = "架构设计"
    FUNCTION_DESIGN = "功能设计"
    FUNCTION_DECOMPOSITION = "功能分解"
    CODE_DEVELOPMENT = "代码开发"
    TEST_VERIFICATION = "测试验证"
    DEBUG_TROUBLESHOOT = "调试排错"
    PROJECT_MANAGEMENT = "项目管理"
    OPERATION_MONITORING = "运维监控"


class ProblemType(Enum):
    """问题类型枚举"""

    BUG_FIX = "bug修复"
    PERFORMANCE_OPTIMIZATION = "性能优化"
    NEW_FEATURE = "新功能开发"
    ARCHITECTURE_DESIGN = "架构设计"
    CODE_REFACTOR = "代码重构"
    TECH_SELECTION = "技术选型"
    REQUIREMENT_ANALYSIS = "需求分析"
    TEST_DESIGN = "测试设计"
    SECURITY_AUDIT = "安全审计"
    DOCUMENTATION = "文档编写"


@dataclass
class ThinkingMode:
    """思维模式定义"""

    type: ThinkingModeType
    name: str
    description: str
    core_principle: str
    suitable_for: list[str]
    keywords: list[str]
    effectiveness_score: dict[str, float]  # 问题类型 -> 效果评分

    # 可选的详细信息
    questions: Optional[list[str]] = None
    steps: Optional[list[str]] = None
    principles: Optional[list[str]] = None
    approach: Optional[list[str]] = None
    elements: Optional[list[str]] = None
    guidelines: Optional[list[str]] = None


class ThinkingModeManager:
    """思维模式统一管理器"""

    def __init__(self):
        self._modes: dict[ThinkingModeType, ThinkingMode] = {}
        self._stage_mapping: dict[DevelopmentStage, dict[str, list[ThinkingModeType]]] = {}
        self._problem_mapping: dict[ProblemType, list[ThinkingModeType]] = {}
        self._combinations: dict[str, dict[str, any]] = {}

        self._initialize_thinking_modes()
        self._initialize_mappings()
        self._initialize_combinations()

    def _initialize_thinking_modes(self):
        """初始化所有思维模式"""
        # 苏格拉底提问法
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.SOCRATIC_QUESTIONING,
                name="苏格拉底提问法",
                description="通过连续追问深入本质",
                core_principle="问'为什么'而非'是什么'",
                suitable_for=["需求分析", "测试验证", "问题诊断"],
                keywords=["为什么", "假设", "证据", "本质", "深入"],
                effectiveness_score={"需求分析": 0.9, "测试验证": 0.85, "问题诊断": 0.8},
                questions=[
                    "这个假设的依据是什么？",
                    "有什么证据支持这个观点？",
                    "从另一个角度看会怎样？",
                    "这个结论的反例是什么？",
                    "最坏的情况会是什么？",
                ],
            )
        )

        # MECE原则
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.MECE_PRINCIPLE,
                name="MECE原则",
                description="相互独立，完全穷尽",
                core_principle="确保完整性和独立性",
                suitable_for=["需求分解", "功能分解", "测试设计", "问题分析"],
                keywords=["完整", "独立", "分解", "穷尽", "覆盖"],
                effectiveness_score={"需求分解": 0.95, "功能分解": 0.95, "测试设计": 0.9, "问题分析": 0.85},
                principles=[
                    "完整性验证：子需求组合是否等于父需求",
                    "独立性验证：子需求之间是否有重叠",
                    "可行性验证：每个子需求是否可以独立实现",
                    "一致性验证：分解逻辑是否统一",
                ],
            )
        )

        # 第一性原理
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.FIRST_PRINCIPLES,
                name="第一性原理",
                description="从基本原理出发推导",
                core_principle="回归问题本质",
                suitable_for=["架构设计", "技术选型", "创新方案", "需求分析"],
                keywords=["本质", "基础", "原理", "创新", "突破"],
                effectiveness_score={"架构设计": 0.9, "技术选型": 0.85, "创新方案": 0.95, "需求分析": 0.8},
                steps=["识别并质疑现有假设", "分解到基本要素", "从头开始重新构建", "验证新的解决方案"],
            )
        )

        # 系统思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.SYSTEMS_THINKING,
                name="系统思维",
                description="整体大于部分之和",
                core_principle="考虑组件间相互作用",
                suitable_for=["架构设计", "项目管理", "集成测试", "性能优化"],
                keywords=["系统", "整体", "关系", "架构", "集成"],
                effectiveness_score={"架构设计": 0.95, "项目管理": 0.9, "集成测试": 0.85, "性能优化": 0.8},
                elements=["识别系统边界", "理解组件关系", "分析反馈循环", "预测涌现行为"],
            )
        )

        # 工匠精神
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.CRAFTSMAN_SPIRIT,
                name="工匠精神",
                description="追求卓越，注重细节，持续改进",
                core_principle="精益求精",
                suitable_for=["代码优化", "性能调优", "用户体验", "测试验证", "调试排错"],
                keywords=["优化", "改进", "完善", "精益", "细节", "测试", "调试"],
                effectiveness_score={"代码优化": 0.9, "测试验证": 0.9, "调试排错": 0.85, "用户体验": 0.8},
                principles=["精益求精，不断打磨", "注重细节，追求完美", "深入理解，掌握本质", "持续学习，不断进步"],
            )
        )

        # 钻研精神
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.RESEARCH_MINDSET,
                name="钻研精神",
                description="深入探究，不满足于表面理解",
                core_principle="深挖根源",
                suitable_for=["性能问题", "复杂bug", "新技术学习", "测试验证", "调试排错"],
                keywords=["深入", "原理", "探究", "根源", "测试", "调试", "bug"],
                effectiveness_score={"复杂bug": 0.95, "性能问题": 0.9, "测试验证": 0.85, "调试排错": 0.9},
                approach=["深挖根源，理解原理", "多角度验证，交叉检验", "系统化实验，数据驱动", "持续迭代，逐步深入"],
            )
        )

        # 奥卡姆剃刀原则
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.OCCAM_RAZOR,
                name="奥卡姆剃刀原则",
                description="最简单的解释往往是正确的",
                core_principle="避免过度复杂化",
                suitable_for=["方案选择", "代码设计", "架构决策"],
                keywords=["简单", "简化", "最简", "精简", "简洁"],
                effectiveness_score={"方案选择": 0.9, "代码设计": 0.85, "架构决策": 0.8, "重构": 0.9},
                guidelines=[
                    "在功能相同的情况下选择最简单的方案",
                    "避免过度设计和过早优化",
                    "保持代码的简洁和可读性",
                    "减少不必要的抽象层次",
                ],
            )
        )

        # 笛卡尔方法论
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.DESCARTES_METHOD,
                name="笛卡尔方法论",
                description="分解复杂问题为简单问题",
                core_principle="大问题拆解为小问题",
                suitable_for=["系统分析", "功能拆解", "需求分解"],
                keywords=["分解", "拆解", "拆分", "分步", "步骤"],
                effectiveness_score={"系统分析": 0.9, "功能拆解": 0.95, "需求分解": 0.9, "问题分析": 0.85},
                steps=[
                    "怀疑一切可以怀疑的东西",
                    "将复杂问题分解为简单部分",
                    "从简单到复杂按顺序解决",
                    "全面复查确保没有遗漏",
                ],
            )
        )

        # 契约式设计思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.CONTRACTUAL_DESIGN,
                name="契约式设计思维",
                description="明确定义接口契约和职责",
                core_principle="前置条件、后置条件、不变量",
                suitable_for=["接口设计", "代码开发", "API设计", "模块集成"],
                keywords=["契约", "接口", "约定", "规范", "API"],
                effectiveness_score={"接口设计": 0.95, "API设计": 0.95, "代码开发": 0.85, "模块集成": 0.9},
                elements=[
                    "前置条件：函数入参的严格验证",
                    "后置条件：函数出参的明确定义",
                    "不变量：函数执行过程中保持的约束",
                    "异常契约：明确的异常处理约定",
                ],
            )
        )

        # 防御式编程思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.DEFENSIVE_PROGRAMMING,
                name="防御式编程思维",
                description="假设一切都可能出错",
                core_principle="防患于未然",
                suitable_for=["代码开发", "安全编程", "异常处理", "系统集成"],
                keywords=["防御", "异常", "错误", "安全", "验证"],
                effectiveness_score={"安全编程": 0.95, "异常处理": 0.95, "代码开发": 0.85, "系统集成": 0.9},
                approach=[
                    "对所有输入进行验证",
                    "处理所有可能的异常情况",
                    "使用断言验证关键假设",
                    "编写健壮的错误处理代码",
                ],
            )
        )

        # 用户旅程思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.USER_JOURNEY,
                name="用户旅程思维",
                description="从用户视角设计完整体验",
                core_principle="用户体验优先",
                suitable_for=["功能设计", "UI/UX设计", "需求分析", "测试设计"],
                keywords=["用户", "体验", "流程", "旅程", "场景"],
                effectiveness_score={"功能设计": 0.9, "UI/UX设计": 0.95, "需求分析": 0.85, "测试设计": 0.8},
                steps=["识别用户角色和目标", "映射完整的用户流程", "识别关键接触点", "优化每个环节的体验"],
            )
        )

        # 原子化思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.ATOMIC_THINKING,
                name="原子化思维",
                description="将功能分解到不可再分的最小单元",
                core_principle="单一职责原则",
                suitable_for=["功能分解", "微服务设计", "单元测试", "模块化设计"],
                keywords=["原子", "单元", "模块", "组件", "微服务"],
                effectiveness_score={"功能分解": 0.95, "微服务设计": 0.9, "单元测试": 0.9, "模块化设计": 0.95},
                principles=["单一职责原则", "高内聚低耦合", "可测试性优先", "可组合性设计"],
            )
        )

        # 风险驱动思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.RISK_DRIVEN,
                name="风险驱动思维",
                description="优先处理高风险项",
                core_principle="风险优先级",
                suitable_for=["项目管理", "测试策略", "架构决策", "安全设计"],
                keywords=["风险", "风险评估", "优先级", "威胁", "安全"],
                effectiveness_score={"项目管理": 0.9, "测试策略": 0.95, "架构决策": 0.85, "安全设计": 0.95},
                approach=["识别所有潜在风险", "评估风险概率和影响", "制定风险缓解策略", "持续监控和调整"],
            )
        )

        # 数据驱动思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.DATA_DRIVEN,
                name="数据驱动思维",
                description="基于数据做决策",
                core_principle="用数据说话",
                suitable_for=["性能优化", "用户体验", "项目管理", "质量改进"],
                keywords=["数据", "指标", "度量", "分析", "统计"],
                effectiveness_score={"性能优化": 0.95, "用户体验": 0.85, "项目管理": 0.9, "质量改进": 0.9},
                approach=["定义关键指标", "收集和分析数据", "基于数据洞察决策", "持续度量和优化"],
            )
        )

        # 生命周期思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.LIFECYCLE_THINKING,
                name="生命周期思维",
                description="考虑事物的完整生命周期",
                core_principle="全生命周期管理",
                suitable_for=["文档管理", "数据管理", "系统设计", "项目规划"],
                keywords=["生命周期", "周期", "阶段", "演进", "全程"],
                effectiveness_score={"文档管理": 0.9, "数据管理": 0.9, "系统设计": 0.85, "项目规划": 0.85},
                elements=["创建和初始化", "使用和维护", "演进和升级", "退役和清理"],
            )
        )

        # 权衡思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.TRADE_OFF_THINKING,
                name="权衡思维",
                description="在多个目标间寻找平衡",
                core_principle="平衡取舍",
                suitable_for=["架构设计", "技术选型", "方案评估", "资源分配"],
                keywords=["权衡", "平衡", "取舍", "折中", "选择"],
                effectiveness_score={"架构设计": 0.9, "技术选型": 0.95, "方案评估": 0.9, "资源分配": 0.85},
                elements=["性能 vs 可维护性", "灵活性 vs 简单性", "安全性 vs 易用性", "成本 vs 质量"],
            )
        )

        # 演进思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.EVOLUTIONARY_THINKING,
                name="演进思维",
                description="系统是逐步演进的",
                core_principle="持续演进",
                suitable_for=["架构设计", "产品规划", "技术债务", "重构策略"],
                keywords=["演进", "迭代", "渐进", "升级", "重构"],
                effectiveness_score={"架构设计": 0.85, "产品规划": 0.9, "技术债务": 0.9, "重构策略": 0.95},
                principles=["从简单开始", "迭代式改进", "保持可扩展性", "平滑升级路径"],
            )
        )

        # 场景化思维
        self._register_mode(
            ThinkingMode(
                type=ThinkingModeType.SCENARIO_THINKING,
                name="场景化思维",
                description="通过具体场景验证理解",
                core_principle="场景验证",
                suitable_for=["需求分析", "测试设计", "功能验证", "用户体验"],
                keywords=["场景", "用例", "案例", "示例", "情景"],
                effectiveness_score={"需求分析": 0.9, "测试设计": 0.95, "功能验证": 0.9, "用户体验": 0.85},
                approach=["收集真实使用场景", "构建典型用例", "边界场景分析", "异常场景处理"],
            )
        )

    def _register_mode(self, mode: ThinkingMode):
        """注册思维模式"""
        self._modes[mode.type] = mode

    def _initialize_mappings(self):
        """初始化映射关系"""
        # 开发阶段映射
        self._stage_mapping = {
            DevelopmentStage.REQUIREMENT_ANALYSIS: {
                "primary": [
                    ThinkingModeType.SOCRATIC_QUESTIONING,
                    ThinkingModeType.FIRST_PRINCIPLES,
                    ThinkingModeType.SCENARIO_THINKING,
                ],
                "secondary": [ThinkingModeType.USER_JOURNEY, ThinkingModeType.SYSTEMS_THINKING],
            },
            DevelopmentStage.REQUIREMENT_DECOMPOSITION: {
                "primary": [ThinkingModeType.MECE_PRINCIPLE, ThinkingModeType.DESCARTES_METHOD],
                "secondary": [ThinkingModeType.SYSTEMS_THINKING, ThinkingModeType.ATOMIC_THINKING],
            },
            DevelopmentStage.TEST_VERIFICATION: {
                "primary": [
                    ThinkingModeType.MECE_PRINCIPLE,
                    ThinkingModeType.RISK_DRIVEN,
                    ThinkingModeType.CRAFTSMAN_SPIRIT,
                    ThinkingModeType.RESEARCH_MINDSET,
                ],
                "secondary": [ThinkingModeType.SCENARIO_THINKING, ThinkingModeType.DATA_DRIVEN],
            },
            DevelopmentStage.DEBUG_TROUBLESHOOT: {
                "primary": [
                    ThinkingModeType.RESEARCH_MINDSET,
                    ThinkingModeType.CRAFTSMAN_SPIRIT,
                    ThinkingModeType.FIRST_PRINCIPLES,
                ],
                "secondary": [ThinkingModeType.SYSTEMS_THINKING, ThinkingModeType.DATA_DRIVEN],
            },
            DevelopmentStage.DATA_DESIGN: {
                "primary": [
                    ThinkingModeType.FIRST_PRINCIPLES,
                    ThinkingModeType.SYSTEMS_THINKING,
                    ThinkingModeType.MECE_PRINCIPLE,
                ],
                "secondary": [ThinkingModeType.LIFECYCLE_THINKING, ThinkingModeType.TRADE_OFF_THINKING],
            },
            DevelopmentStage.ARCHITECTURE_DESIGN: {
                "primary": [
                    ThinkingModeType.SYSTEMS_THINKING,
                    ThinkingModeType.FIRST_PRINCIPLES,
                    ThinkingModeType.TRADE_OFF_THINKING,
                ],
                "secondary": [ThinkingModeType.EVOLUTIONARY_THINKING, ThinkingModeType.RISK_DRIVEN],
            },
            DevelopmentStage.FUNCTION_DESIGN: {
                "primary": [
                    ThinkingModeType.SYSTEMS_THINKING,
                    ThinkingModeType.MECE_PRINCIPLE,
                    ThinkingModeType.USER_JOURNEY,
                ],
                "secondary": [ThinkingModeType.SCENARIO_THINKING, ThinkingModeType.ATOMIC_THINKING],
            },
            DevelopmentStage.FUNCTION_DECOMPOSITION: {
                "primary": [
                    ThinkingModeType.MECE_PRINCIPLE,
                    ThinkingModeType.ATOMIC_THINKING,
                    ThinkingModeType.DESCARTES_METHOD,
                ],
                "secondary": [ThinkingModeType.SYSTEMS_THINKING],
            },
            DevelopmentStage.CODE_DEVELOPMENT: {
                "primary": [
                    ThinkingModeType.CONTRACTUAL_DESIGN,
                    ThinkingModeType.DEFENSIVE_PROGRAMMING,
                    ThinkingModeType.CRAFTSMAN_SPIRIT,
                ],
                "secondary": [ThinkingModeType.MECE_PRINCIPLE, ThinkingModeType.OCCAM_RAZOR],
            },
            DevelopmentStage.PROJECT_MANAGEMENT: {
                "primary": [
                    ThinkingModeType.SYSTEMS_THINKING,
                    ThinkingModeType.DATA_DRIVEN,
                    ThinkingModeType.RISK_DRIVEN,
                ],
                "secondary": [ThinkingModeType.LIFECYCLE_THINKING, ThinkingModeType.TRADE_OFF_THINKING],
            },
            DevelopmentStage.OPERATION_MONITORING: {
                "primary": [
                    ThinkingModeType.DATA_DRIVEN,
                    ThinkingModeType.SYSTEMS_THINKING,
                    ThinkingModeType.RISK_DRIVEN,
                ],
                "secondary": [ThinkingModeType.LIFECYCLE_THINKING, ThinkingModeType.SCENARIO_THINKING],
            },
        }

        # 问题类型映射
        self._problem_mapping = {
            ProblemType.BUG_FIX: [
                ThinkingModeType.RESEARCH_MINDSET,
                ThinkingModeType.FIRST_PRINCIPLES,
                ThinkingModeType.SYSTEMS_THINKING,
                ThinkingModeType.CRAFTSMAN_SPIRIT,
            ],
            ProblemType.TEST_DESIGN: [
                ThinkingModeType.MECE_PRINCIPLE,
                ThinkingModeType.SCENARIO_THINKING,
                ThinkingModeType.RISK_DRIVEN,
                ThinkingModeType.CRAFTSMAN_SPIRIT,
                ThinkingModeType.RESEARCH_MINDSET,
            ],
            ProblemType.ARCHITECTURE_DESIGN: [
                ThinkingModeType.SYSTEMS_THINKING,
                ThinkingModeType.FIRST_PRINCIPLES,
                ThinkingModeType.TRADE_OFF_THINKING,
                ThinkingModeType.EVOLUTIONARY_THINKING,
            ],
            ProblemType.PERFORMANCE_OPTIMIZATION: [
                ThinkingModeType.DATA_DRIVEN,
                ThinkingModeType.SYSTEMS_THINKING,
                ThinkingModeType.TRADE_OFF_THINKING,
                ThinkingModeType.CRAFTSMAN_SPIRIT,
            ],
            ProblemType.NEW_FEATURE: [
                ThinkingModeType.USER_JOURNEY,
                ThinkingModeType.MECE_PRINCIPLE,
                ThinkingModeType.SCENARIO_THINKING,
                ThinkingModeType.ATOMIC_THINKING,
            ],
            ProblemType.CODE_REFACTOR: [
                ThinkingModeType.CRAFTSMAN_SPIRIT,
                ThinkingModeType.ATOMIC_THINKING,
                ThinkingModeType.MECE_PRINCIPLE,
                ThinkingModeType.OCCAM_RAZOR,
            ],
            ProblemType.TECH_SELECTION: [
                ThinkingModeType.FIRST_PRINCIPLES,
                ThinkingModeType.TRADE_OFF_THINKING,
                ThinkingModeType.RISK_DRIVEN,
                ThinkingModeType.DATA_DRIVEN,
            ],
            ProblemType.REQUIREMENT_ANALYSIS: [
                ThinkingModeType.SOCRATIC_QUESTIONING,
                ThinkingModeType.SCENARIO_THINKING,
                ThinkingModeType.USER_JOURNEY,
                ThinkingModeType.FIRST_PRINCIPLES,
            ],
            ProblemType.SECURITY_AUDIT: [
                ThinkingModeType.DEFENSIVE_PROGRAMMING,
                ThinkingModeType.RISK_DRIVEN,
                ThinkingModeType.MECE_PRINCIPLE,
                ThinkingModeType.SYSTEMS_THINKING,
            ],
            ProblemType.DOCUMENTATION: [
                ThinkingModeType.LIFECYCLE_THINKING,
                ThinkingModeType.MECE_PRINCIPLE,
                ThinkingModeType.USER_JOURNEY,
                ThinkingModeType.SYSTEMS_THINKING,
            ],
        }

    def _initialize_combinations(self):
        """初始化思维模式组合"""
        self._combinations = {
            "深度分析套装": {
                "modes": [
                    ThinkingModeType.FIRST_PRINCIPLES,
                    ThinkingModeType.SYSTEMS_THINKING,
                    ThinkingModeType.MECE_PRINCIPLE,
                ],
                "description": "用于复杂问题的深度分析",
                "use_cases": ["架构设计", "性能瓶颈", "系统集成"],
            },
            "质量保证套装": {
                "modes": [
                    ThinkingModeType.CRAFTSMAN_SPIRIT,
                    ThinkingModeType.MECE_PRINCIPLE,
                    ThinkingModeType.RISK_DRIVEN,
                ],
                "description": "确保高质量交付",
                "use_cases": ["代码审查", "测试设计", "质量改进"],
            },
            "问题诊断套装": {
                "modes": [
                    ThinkingModeType.RESEARCH_MINDSET,
                    ThinkingModeType.SYSTEMS_THINKING,
                    ThinkingModeType.DATA_DRIVEN,
                ],
                "description": "系统化问题诊断和解决",
                "use_cases": ["bug修复", "性能问题", "故障排查"],
            },
        }

    def get_mode(self, mode_type: ThinkingModeType) -> Optional[ThinkingMode]:
        """获取思维模式"""
        return self._modes.get(mode_type)

    def get_modes_for_stage(self, stage: DevelopmentStage, priority: str = "all") -> list[ThinkingMode]:
        """获取开发阶段的推荐思维模式"""
        stage_map = self._stage_mapping.get(stage, {})

        if priority == "primary":
            mode_types = stage_map.get("primary", [])
        elif priority == "secondary":
            mode_types = stage_map.get("secondary", [])
        else:  # all
            mode_types = stage_map.get("primary", []) + stage_map.get("secondary", [])

        return [self._modes[mt] for mt in mode_types if mt in self._modes]

    def get_modes_for_problem(self, problem_type: ProblemType) -> list[ThinkingMode]:
        """获取问题类型的推荐思维模式"""
        mode_types = self._problem_mapping.get(problem_type, [])
        return [self._modes[mt] for mt in mode_types if mt in self._modes]

    def get_modes_by_keywords(self, text: str) -> list[ThinkingMode]:
        """根据关键词匹配思维模式"""
        text_lower = text.lower()
        scores = {}

        for mode_type, mode in self._modes.items():
            score = 0
            for keyword in mode.keywords:
                if keyword in text_lower:
                    score += 1

            if score > 0:
                scores[mode_type] = score

        # 按得分排序
        sorted_modes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [self._modes[mt] for mt, _ in sorted_modes]

    def get_combination(self, name: str) -> Optional[dict]:
        """获取思维模式组合"""
        combo = self._combinations.get(name)
        if combo:
            return {
                "name": name,
                "modes": [self._modes[mt] for mt in combo["modes"] if mt in self._modes],
                "description": combo["description"],
                "use_cases": combo["use_cases"],
            }
        return None

    def recommend_modes(self, context: dict[str, any]) -> dict[str, list[ThinkingMode]]:
        """智能推荐思维模式"""
        recommendations = {"primary": [], "secondary": [], "combinations": []}

        # 基于关键词推荐
        if "query" in context:
            keyword_modes = self.get_modes_by_keywords(context["query"])
            recommendations["primary"].extend(keyword_modes[:3])

        # 基于开发阶段推荐
        if "stage" in context and isinstance(context["stage"], DevelopmentStage):
            stage_modes = self.get_modes_for_stage(context["stage"], "primary")
            recommendations["primary"].extend(stage_modes)

            secondary_modes = self.get_modes_for_stage(context["stage"], "secondary")
            recommendations["secondary"].extend(secondary_modes)

        # 基于问题类型推荐
        if "problem_type" in context and isinstance(context["problem_type"], ProblemType):
            problem_modes = self.get_modes_for_problem(context["problem_type"])
            recommendations["primary"].extend(problem_modes[:3])

        # 去重 - 使用集合来跟踪已添加的模式类型
        seen_primary = set()
        unique_primary = []
        for mode in recommendations["primary"]:
            if mode.type not in seen_primary:
                seen_primary.add(mode.type)
                unique_primary.append(mode)
        recommendations["primary"] = unique_primary

        seen_secondary = set()
        unique_secondary = []
        for mode in recommendations["secondary"]:
            if mode.type not in seen_secondary:
                seen_secondary.add(mode.type)
                unique_secondary.append(mode)
        recommendations["secondary"] = unique_secondary

        # 推荐组合
        for combo_name, combo_info in self._combinations.items():
            # 检查是否有匹配的思维模式
            primary_types = [m.type for m in recommendations["primary"]]
            if any(mt in primary_types for mt in combo_info["modes"]):
                recommendations["combinations"].append(self.get_combination(combo_name))

        return recommendations

    def get_default_modes(self) -> list[ThinkingMode]:
        """获取默认思维模式"""
        default_types = [
            ThinkingModeType.FIRST_PRINCIPLES,
            ThinkingModeType.SYSTEMS_THINKING,
            ThinkingModeType.MECE_PRINCIPLE,
        ]
        return [self._modes[mt] for mt in default_types if mt in self._modes]

    def auto_select_modes(self, context: dict[str, any]) -> list[ThinkingMode]:
        """自动选择最合适的思维模式"""
        recommendations = self.recommend_modes(context)

        # 优先返回主要推荐
        if recommendations["primary"]:
            return recommendations["primary"][:5]

        # 如果没有主要推荐，返回次要推荐
        if recommendations["secondary"]:
            return recommendations["secondary"][:5]

        # 最后返回默认模式
        return self.get_default_modes()


# 全局实例
_thinking_mode_manager = None


def get_thinking_mode_manager() -> ThinkingModeManager:
    """获取思维模式管理器的全局实例"""
    global _thinking_mode_manager
    if _thinking_mode_manager is None:
        _thinking_mode_manager = ThinkingModeManager()
    return _thinking_mode_manager
