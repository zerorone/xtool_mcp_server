"""
Xtool Advisor - 智能工具推荐系统

根据用户问题自动分析并推荐最合适的 Xtool 工具，
提供 30 秒等待时间让用户确认或修改选择。
"""

import logging
import re
from typing import Any, Optional

from pydantic import Field

from config import TEMPERATURE_ANALYTICAL
from tools.models import ToolModelCategory
from tools.shared.base_models import ToolRequest
from tools.simple.base import SimpleTool

logger = logging.getLogger(__name__)


class XtoolAdvisorRequest(ToolRequest):
    """XTOOL Advisor 请求模型"""

    query: str = Field(..., description="用户的问题或需求描述")
    context: Optional[str] = Field(None, description="额外的上下文信息")
    preferred_thinking: Optional[str] = Field(None, description="用户偏好的思维模式")
    auto_proceed: Optional[bool] = Field(True, description="是否在等待时间后自动执行")
    wait_time: Optional[int] = Field(30, description="等待用户确认的时间（秒）")


class XtoolAdvisorTool(SimpleTool):
    """
    智能工具推荐系统，根据用户问题自动分析并推荐合适的 Xtool 工具。
    """

    # 工具推荐规则
    TOOL_PATTERNS = {
        "mcp__zen__debug": {
            "keywords": ["bug", "错误", "error", "异常", "调试", "debug", "问题", "issue", "故障", "crash", "失败"],
            "patterns": [r"为什么.*不工作", r".*报错", r".*失败", r".*崩溃"],
            "description": "系统化调试，根因分析",
            "thinking_modes": ["systematic_investigation", "root_cause_analysis", "evidence_based"],
        },
        "mcp__zen__codereview": {
            "keywords": ["代码审查", "review", "代码质量", "code quality", "重构建议", "最佳实践"],
            "patterns": [r"审查.*代码", r"检查.*代码", r"代码.*怎么样"],
            "description": "全面代码审查，多维度评估",
            "thinking_modes": ["critical_evaluation", "best_practices", "quality_focus"],
        },
        "mcp__zen__planner": {
            "keywords": ["计划", "规划", "plan", "设计", "架构", "方案", "步骤", "流程"],
            "patterns": [r"如何.*实现", r"怎么.*设计", r".*的步骤"],
            "description": "分步骤规划，支持修订",
            "thinking_modes": ["strategic_planning", "systematic_decomposition", "iterative_refinement"],
        },
        "mcp__zen__analyze": {
            "keywords": ["分析", "评估", "analyze", "性能", "架构分析", "技术债务"],
            "patterns": [r"分析.*系统", r"评估.*性能", r".*的优缺点"],
            "description": "深度分析，专家验证",
            "thinking_modes": ["comprehensive_analysis", "multi_perspective", "expert_validation"],
        },
        "mcp__zen__thinkdeep": {
            "keywords": ["深入思考", "复杂问题", "深度分析", "探索", "研究"],
            "patterns": [r"深入.*理解", r"详细.*分析", r".*的本质"],
            "description": "多阶段深度思考",
            "thinking_modes": ["deep_thinking", "hypothesis_testing", "comprehensive_investigation"],
        },
        "mcp__zen__consensus": {
            "keywords": ["决策", "选择", "比较", "权衡", "方案对比", "技术选型"],
            "patterns": [r".*还是.*好", r"如何选择", r"比较.*方案"],
            "description": "多角度共识分析",
            "thinking_modes": ["multi_model_consensus", "balanced_evaluation", "decision_matrix"],
        },
        "mcp__zen__secaudit": {
            "keywords": ["安全", "漏洞", "security", "审计", "渗透", "加密", "认证"],
            "patterns": [r".*安全.*问题", r".*漏洞", r"安全.*审计"],
            "description": "安全审计，合规检查",
            "thinking_modes": ["security_mindset", "threat_modeling", "compliance_focus"],
        },
        "mcp__zen__refactor": {
            "keywords": ["重构", "优化代码", "代码异味", "refactor", "改进", "简化"],
            "patterns": [r"重构.*代码", r"优化.*结构", r"改进.*设计"],
            "description": "重构分析，改进建议",
            "thinking_modes": ["clean_code", "design_patterns", "incremental_improvement"],
        },
        "mcp__zen__chat": {
            "keywords": ["讨论", "聊天", "想法", "概念", "理解", "解释", "是什么"],
            "patterns": [r".*是什么", r"解释.*概念", r"讨论.*想法"],
            "description": "协作思考，概念探讨",
            "thinking_modes": ["collaborative", "exploratory", "conceptual"],
        },
        "mcp__zen__challenge": {
            "keywords": ["挑战", "质疑", "批判", "假设", "验证", "压力测试"],
            "patterns": [r"质疑.*假设", r"挑战.*观点", r"批判.*分析"],
            "description": "批判性审查，挑战假设",
            "thinking_modes": ["critical_challenge", "assumption_testing", "devil_advocate"],
        },
        "mcp__zen__thinkboost": {
            "keywords": ["思维模式", "认知框架", "思考方法", "增强思维"],
            "patterns": [r".*思维.*模式", r"如何.*思考", r"增强.*认知"],
            "description": "思维模式增强",
            "thinking_modes": ["meta_cognition", "pattern_application", "cognitive_frameworks"],
        },
        "mcp__zen__tracer": {
            "keywords": ["追踪", "调用链", "执行流程", "依赖关系", "代码流"],
            "patterns": [r"追踪.*执行", r".*调用.*关系", r"代码.*流程"],
            "description": "代码追踪，依赖分析",
            "thinking_modes": ["flow_analysis", "dependency_mapping", "systematic_tracing"],
        },
    }

    # 初始化标志
    _initialized = False

    def __init__(self):
        super().__init__()
        self._initialize_thinking_modes()

    @classmethod
    def _initialize_thinking_modes(cls):
        """初始化思维模式管理器（只执行一次）"""
        if cls._initialized:
            return

        # 导入统一的思维模式管理器
        try:
            from utils.thinking_mode_manager import (
                DevelopmentStage,
                ProblemType,
                ThinkingModeType,
                get_thinking_mode_manager,
            )

            # 获取管理器实例
            thinking_manager = get_thinking_mode_manager()

            # 将导入的内容存储为类属性
            cls.DevelopmentStage = DevelopmentStage
            cls.ProblemType = ProblemType
            cls.ThinkingModeType = ThinkingModeType
            cls.thinking_manager = thinking_manager
            cls.MANAGER_AVAILABLE = True
        except ImportError:
            cls.MANAGER_AVAILABLE = False
            # 如果管理器不可用，尝试导入增强的思维模式
            try:
                from .thinking_modes_enhanced import (
                    CORE_THINKING_METHODS,
                    PROBLEM_THINKING_MAP,
                    PROFESSIONAL_THINKING_METHODS,
                    STAGE_THINKING_MAP,
                    THINKING_COMBINATIONS,
                )

                # 合并核心和专业思维方法
                EXTENDED_THINKING_MODES = {**CORE_THINKING_METHODS, **PROFESSIONAL_THINKING_METHODS}

                # 存储为类属性
                cls.EXTENDED_THINKING_MODES = EXTENDED_THINKING_MODES
                cls.STAGE_THINKING_MAP = STAGE_THINKING_MAP
                cls.PROBLEM_THINKING_MAP = PROBLEM_THINKING_MAP
                cls.THINKING_COMBINATIONS = THINKING_COMBINATIONS
            except ImportError:
                # 降级到基础思维模式
                cls.EXTENDED_THINKING_MODES = {
                    "socratic_questioning": {
                        "name": "苏格拉底式反问",
                        "description": "通过系统性提问来深化理解和发现盲点",
                        "questions": [
                            "这个假设的依据是什么？",
                            "有什么证据支持这个观点？",
                            "从另一个角度看会怎样？",
                            "这个结论的反例是什么？",
                            "最坏的情况会是什么？",
                        ],
                        "suitable_for": ["测试设计", "需求分析", "架构评审"],
                    },
                    "craftsman_spirit": {
                        "name": "工匠精神",
                        "description": "追求卓越，注重细节，持续改进",
                        "principles": [
                            "精益求精，不断打磨",
                            "注重细节，追求完美",
                            "深入理解，掌握本质",
                            "持续学习，不断进步",
                        ],
                        "suitable_for": ["代码优化", "性能调优", "用户体验"],
                    },
                    "research_mindset": {
                        "name": "钻研精神",
                        "description": "深入探究，不满足于表面理解",
                        "approach": [
                            "深挖根源，理解原理",
                            "多角度验证，交叉检验",
                            "系统化实验，数据驱动",
                            "持续迭代，逐步深入",
                        ],
                        "suitable_for": ["性能问题", "复杂bug", "新技术学习"],
                    },
                    "first_principles": {
                        "name": "第一性原理",
                        "description": "回归本质，从基础原理推导",
                        "steps": ["识别并质疑现有假设", "分解到基本要素", "从头开始重新构建", "验证新的解决方案"],
                        "suitable_for": ["架构设计", "创新方案", "困难问题"],
                    },
                    "systems_thinking": {
                        "name": "系统思维",
                        "description": "整体视角，理解相互关系",
                        "elements": ["识别系统边界", "理解组件关系", "分析反馈循环", "预测涌现行为"],
                        "suitable_for": ["架构分析", "性能优化", "集成问题"],
                    },
                }
                cls.STAGE_THINKING_MAP = {}
                cls.PROBLEM_THINKING_MAP = {}
                cls.THINKING_COMBINATIONS = {}

        cls._initialized = True

    def _detect_code_development(self, query_lower: str) -> bool:
        """
        检测查询是否涉及代码开发，需要使用 context7 规范

        Args:
            query_lower: 小写查询文本

        Returns:
            bool: 是否需要 context7 规范
        """
        # 代码开发关键词
        code_dev_keywords = [
            "代码", "编程", "开发", "实现", "编写代码", "写代码",
            "code", "develop", "programming", "implement", "coding",
            "函数", "方法", "类", "模块", "API", "接口",
            "function", "method", "class", "module", "api", "interface",
            "算法", "数据结构", "逻辑", "业务逻辑",
            "algorithm", "data structure", "logic", "business logic",
            "脚本", "程序", "应用", "系统实现",
            "script", "program", "application", "system implementation"
        ]

        # 编程语言关键词
        language_keywords = [
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
            "php", "ruby", "swift", "kotlin", "scala", "dart", "r", "matlab",
            "html", "css", "sql", "bash", "shell", "powershell"
        ]

        # 开发框架关键词
        framework_keywords = [
            "django", "flask", "fastapi", "spring", "springboot",
            "react", "vue", "angular", "nodejs", "express",
            "laravel", "rails", "asp.net", "gin", "echo",
            "pandas", "numpy", "tensorflow", "pytorch"
        ]

        # 开发活动关键词
        dev_activity_keywords = [
            "写", "编写", "开发", "实现", "构建", "创建",
            "write", "develop", "implement", "build", "create",
            "新增功能", "添加功能", "功能实现", "业务实现",
            "add feature", "implement feature", "feature development",
            "重构代码", "优化代码", "修改代码", "改进代码",
            "refactor", "optimize code", "modify code", "improve code"
        ]

        # 检查是否包含代码开发相关关键词
        all_keywords = code_dev_keywords + language_keywords + framework_keywords + dev_activity_keywords

        for keyword in all_keywords:
            if keyword in query_lower:
                return True

        # 检查组合模式（更精确的检测）
        dev_patterns = [
            ("写", "代码"), ("编写", "程序"), ("开发", "功能"),
            ("实现", "逻辑"), ("创建", "类"), ("定义", "函数"),
            ("构建", "API"), ("设计", "接口"), ("编程", "实现")
        ]

        for pattern in dev_patterns:
            if all(word in query_lower for word in pattern):
                return True

        return False

    def get_name(self) -> str:
        return "xtool_advisor"

    def get_description(self) -> str:
        return (
            "XTOOL ADVISOR - 智能工具推荐系统。"
            "根据您的问题自动分析并推荐最合适的 Xtool 工具，"
            "提供个性化的思维模式建议，支持30秒确认机制。"
        )

    def get_system_prompt(self) -> str:
        return """你是 Xtool 工具集的智能顾问，负责：

1. 分析用户问题，理解其真实需求
2. 推荐最合适的 Xtool 工具组合
3. 提供个性化的思维模式建议
4. 解释推荐理由和使用方法

你的分析应该：
- 准确理解问题本质
- 考虑问题的复杂度和类型
- 匹配最佳工具和思维模式
- 提供清晰的使用指导"""

    def get_default_temperature(self) -> float:
        return TEMPERATURE_ANALYTICAL

    def get_model_category(self) -> ToolModelCategory:
        return ToolModelCategory.BALANCED

    def get_request_model(self):
        return XtoolAdvisorRequest

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        return {
            "query": {"type": "string", "description": "用户的问题或需求描述"},
            "context": {"type": "string", "description": "额外的上下文信息"},
            "preferred_thinking": {"type": "string", "description": "用户偏好的思维模式"},
            "auto_proceed": {"type": "boolean", "default": True, "description": "是否在等待时间后自动执行"},
            "wait_time": {
                "type": "integer",
                "default": 30,
                "minimum": 0,
                "maximum": 300,
                "description": "等待用户确认的时间（秒）",
            },
        }

    def get_required_fields(self) -> list[str]:
        return ["query"]

    def analyze_query(self, query: str, context: Optional[str] = None) -> tuple[list[str], list[str], bool]:
        """
        分析用户查询，返回推荐的工具、思维模式和是否需要context7规范。

        Returns:
            (recommended_tools, recommended_thinking_modes, needs_context7)
        """
        query_lower = query.lower()
        if context:
            query_lower += " " + context.lower()

        # 检查是否需要 context7 规范（代码开发相关）
        needs_context7 = self._detect_code_development(query_lower)

        # 工具匹配得分
        tool_scores = {}

        for tool, config in self.TOOL_PATTERNS.items():
            score = 0

            # 关键词匹配
            for keyword in config["keywords"]:
                if keyword in query_lower:
                    score += 2

            # 模式匹配
            for pattern in config["patterns"]:
                if re.search(pattern, query_lower):
                    score += 3

            if score > 0:
                tool_scores[tool] = score

        # 获取得分最高的工具（最多3个）
        recommended_tools = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        recommended_tools = [tool for tool, _ in recommended_tools]

        # 如果没有匹配到工具，根据问题类型推荐
        if not recommended_tools:
            if "怎么" in query or "如何" in query:
                recommended_tools = ["mcp__zen__planner", "mcp__zen__chat"]
            elif "为什么" in query:
                recommended_tools = ["mcp__zen__thinkdeep", "mcp__zen__debug"]
            else:
                recommended_tools = ["mcp__zen__chat", "mcp__zen__thinkdeep"]

        # 推荐思维模式
        recommended_thinking = []

        # 如果思维模式管理器可用，使用它来获取推荐
        if self.MANAGER_AVAILABLE:
            # 构建上下文信息
            context_info = {"query": query_lower, "tools": recommended_tools}

            # 尝试识别开发阶段
            if "需求" in query_lower and "分析" in query_lower:
                context_info["stage"] = self.DevelopmentStage.REQUIREMENT_ANALYSIS
            elif "需求" in query_lower and ("分解" in query_lower or "拆分" in query_lower):
                context_info["stage"] = self.DevelopmentStage.REQUIREMENT_DECOMPOSITION
            elif "测试" in query_lower or "验证" in query_lower:
                context_info["stage"] = self.DevelopmentStage.TEST_VERIFICATION
            elif "调试" in query_lower or "debug" in query_lower or "排错" in query_lower:
                context_info["stage"] = self.DevelopmentStage.DEBUG_TROUBLESHOOT
            elif "架构" in query_lower and "设计" in query_lower:
                context_info["stage"] = self.DevelopmentStage.ARCHITECTURE_DESIGN
            elif "功能" in query_lower and "设计" in query_lower:
                context_info["stage"] = self.DevelopmentStage.FUNCTION_DESIGN
            elif "功能" in query_lower and ("分解" in query_lower or "拆分" in query_lower):
                context_info["stage"] = self.DevelopmentStage.FUNCTION_DECOMPOSITION
            elif "代码" in query_lower or "开发" in query_lower or "实现" in query_lower:
                context_info["stage"] = self.DevelopmentStage.CODE_DEVELOPMENT
            elif "项目" in query_lower and "管理" in query_lower:
                context_info["stage"] = self.DevelopmentStage.PROJECT_MANAGEMENT
            elif "运维" in query_lower or "监控" in query_lower:
                context_info["stage"] = self.DevelopmentStage.OPERATION_MONITORING

            # 尝试识别问题类型
            if "bug" in query_lower or "错误" in query_lower or "修复" in query_lower:
                context_info["problem_type"] = self.ProblemType.BUG_FIX
            elif "性能" in query_lower and ("优化" in query_lower or "提升" in query_lower):
                context_info["problem_type"] = self.ProblemType.PERFORMANCE_OPTIMIZATION
            elif "新功能" in query_lower or "新增" in query_lower:
                context_info["problem_type"] = self.ProblemType.NEW_FEATURE
            elif "重构" in query_lower:
                context_info["problem_type"] = self.ProblemType.CODE_REFACTOR
            elif "技术选型" in query_lower or "选择" in query_lower:
                context_info["problem_type"] = self.ProblemType.TECH_SELECTION
            elif "安全" in query_lower or "漏洞" in query_lower:
                context_info["problem_type"] = self.ProblemType.SECURITY_AUDIT
            elif "文档" in query_lower:
                context_info["problem_type"] = self.ProblemType.DOCUMENTATION

            # 使用管理器自动选择思维模式
            recommended_modes = self.thinking_manager.auto_select_modes(context_info)
            recommended_thinking = [mode.type.value for mode in recommended_modes]

            # 确保测试和调试场景包含工匠精神和钻研精神
            if "测试" in query_lower or "全面" in query_lower:
                if self.ThinkingModeType.CRAFTSMAN_SPIRIT.value not in recommended_thinking:
                    recommended_thinking.append(self.ThinkingModeType.CRAFTSMAN_SPIRIT.value)
                if self.ThinkingModeType.RESEARCH_MINDSET.value not in recommended_thinking:
                    recommended_thinking.append(self.ThinkingModeType.RESEARCH_MINDSET.value)

            if "调试" in query_lower or "debug" in query_lower or "bug" in query_lower:
                if self.ThinkingModeType.RESEARCH_MINDSET.value not in recommended_thinking:
                    recommended_thinking.insert(0, self.ThinkingModeType.RESEARCH_MINDSET.value)
                if self.ThinkingModeType.CRAFTSMAN_SPIRIT.value not in recommended_thinking:
                    recommended_thinking.insert(1, self.ThinkingModeType.CRAFTSMAN_SPIRIT.value)

        else:
            # 使用原有的逻辑
            # 基于工具推荐思维模式
            for tool in recommended_tools:
                if tool in self.TOOL_PATTERNS:
                    recommended_thinking.extend(self.TOOL_PATTERNS[tool]["thinking_modes"])

            # 基于问题特征推荐扩展思维模式
            if "测试" in query_lower or "全面" in query_lower:
                recommended_thinking.append("socratic_questioning")
                recommended_thinking.append("craftsman_spirit")  # 测试需要精益求精
                recommended_thinking.append("research_mindset")  # 测试需要深入探究
                recommended_thinking.append("mece_principle")  # 测试需要完整覆盖

            if "调试" in query_lower or "debug" in query_lower or "bug" in query_lower or "错误" in query_lower:
                recommended_thinking.append("research_mindset")  # 调试需要深挖根源
                recommended_thinking.append("craftsman_spirit")  # 调试需要注重细节
                recommended_thinking.append("first_principles")  # 调试需要回归本质

            if "优化" in query_lower or "改进" in query_lower or "完善" in query_lower:
                recommended_thinking.append("craftsman_spirit")
                recommended_thinking.append("data_driven")  # 优化需要数据支撑
                recommended_thinking.append("trade_off_thinking")  # 优化需要权衡

            if "深入" in query_lower or "原理" in query_lower or "本质" in query_lower:
                recommended_thinking.append("research_mindset")
                recommended_thinking.append("first_principles")

            if "创新" in query_lower or "新方案" in query_lower:
                recommended_thinking.append("first_principles")
                recommended_thinking.append("evolutionary_thinking")

            if "系统" in query_lower or "整体" in query_lower or "架构" in query_lower:
                recommended_thinking.append("systems_thinking")
                recommended_thinking.append("trade_off_thinking")

            if "需求" in query_lower or "分析" in query_lower:
                recommended_thinking.append("socratic_questioning")
                recommended_thinking.append("scenario_thinking")

            if "设计" in query_lower:
                recommended_thinking.append("user_journey")
                recommended_thinking.append("atomic_thinking")

            if "安全" in query_lower or "漏洞" in query_lower:
                recommended_thinking.append("defensive_programming")
                recommended_thinking.append("risk_driven")

            # 基于问题类型推荐思维模式（如果有映射的话）
            if hasattr(self, "PROBLEM_THINKING_MAP") and self.PROBLEM_THINKING_MAP:
                for problem_type, thinking_modes in self.PROBLEM_THINKING_MAP.items():
                    if problem_type in query_lower:
                        recommended_thinking.extend(thinking_modes[:3])  # 取前3个

        # 去重
        recommended_thinking = list(dict.fromkeys(recommended_thinking))

        return recommended_tools, recommended_thinking, needs_context7

    async def prepare_prompt(self, request: XtoolAdvisorRequest) -> str:
        """准备分析提示"""
        # 分析查询
        tools, thinking_modes, needs_context7 = self.analyze_query(request.query, request.context)

        # 如果用户有偏好的思维模式，优先使用
        if request.preferred_thinking:
            thinking_modes.insert(0, request.preferred_thinking)

        context7_note = ""
        if needs_context7:
            context7_note = "\n🔧 **代码开发规范提示**：此查询涉及代码开发，建议使用 'use context7' 获取最新的语言文档和开发规范。"

        prompt = f"""请分析以下用户问题并提供 Xtool 工具推荐：

用户问题：{request.query}
{f"上下文：{request.context}" if request.context else ""}
{context7_note}

初步分析结果：
- 推荐工具：{", ".join(tools)}
- 推荐思维模式：{", ".join(thinking_modes[:3])}
{"- Context7 规范：需要" if needs_context7 else "- Context7 规范：不需要"}

请提供：
1. 问题分析（理解用户真实需求）
2. 工具推荐及理由
3. 思维模式建议
4. 使用指导
{"5. Context7 规范使用指导（如何使用 'use context7' 获取相关文档）" if needs_context7 else ""}

用户设置：
- 自动执行：{"是" if request.auto_proceed else "否"}
- 等待时间：{request.wait_time}秒"""

        return prompt

    def format_response(self, response: str, request: XtoolAdvisorRequest, model_info: dict = None) -> str:
        """格式化响应，添加等待确认提示"""
        tools, thinking_modes, needs_context7 = self.analyze_query(request.query, request.context)

        context7_section = ""
        if needs_context7:
            context7_section = f"""
🔧 **Context7 规范提示**
{"=" * 60}
检测到代码开发场景，强烈建议使用 Context7 规范：

**使用方法：**
1. 在开始代码开发前，输入：`use context7`
2. 这将获取最新的编程语言文档和开发规范
3. 确保代码质量和最佳实践

**适用场景：**
- 编写新代码或功能
- 学习新的编程语言或框架
- 需要最新API文档
- 代码规范和最佳实践指导
"""

        formatted = f"""{response}
{context7_section}
{"=" * 60}
📋 **快速执行选项**
{"=" * 60}

基于分析，我推荐使用：

**主要工具：** {self.TOOL_PATTERNS.get(tools[0], {}).get("description", tools[0]) if tools else "需要更多信息"}
**命令：** `{tools[0]}`

**备选工具：**
"""

        for i, tool in enumerate(tools[1:3], 2):
            tool_info = self.TOOL_PATTERNS.get(tool, {})
            formatted += f"{i}. `{tool}` - {tool_info.get('description', tool)}\n"

        formatted += """
**推荐思维模式：**
"""

        for mode in thinking_modes[:3]:
            # 如果管理器可用，使用它来获取详细信息
            if self.MANAGER_AVAILABLE:
                try:
                    mode_type = self.ThinkingModeType(mode)
                    mode_obj = self.thinking_manager.get_mode(mode_type)
                    if mode_obj:
                        formatted += f"- {mode_obj.name}：{mode_obj.description}\n"
                        continue
                except (AttributeError, KeyError):
                    # 如果思维模式对象不存在或格式不正确，跳过
                    pass

            # 降级到原有逻辑
            if hasattr(self, "EXTENDED_THINKING_MODES") and mode in self.EXTENDED_THINKING_MODES:
                mode_info = self.EXTENDED_THINKING_MODES[mode]
                formatted += f"- {mode_info['name']}：{mode_info['description']}\n"
            else:
                formatted += f"- {mode}\n"

        if request.auto_proceed and request.wait_time > 0:
            formatted += f"""
{"=" * 60}
⏱️ **自动执行提示**
{"=" * 60}

将在 {request.wait_time} 秒后自动执行推荐的工具。

**中止方法：**
- 输入任意内容来修改选择
- 输入 "stop" 或 "取消" 来中止自动执行
- 直接输入其他工具名来切换

**立即执行：** 输入 "go" 或 "继续"
"""

        return formatted
