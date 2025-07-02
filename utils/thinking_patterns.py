"""
Thinking Patterns Registry - 27 Expert Thinking Modes for Zen

This module implements a comprehensive thinking pattern registry system that enables
intelligent mode selection and application based on problem context. Each pattern
represents a specific cognitive approach optimized for different types of challenges.

Key Features:
- 27 distinct thinking patterns covering all major cognitive approaches
- Pattern metadata for intelligent selection
- Trigger keywords and context matching
- Effectiveness scoring for different problem types
- Integration with memory system for learning
- 包含苏格拉底式反问和工匠精神等专业思维模式
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ThinkingCategory(Enum):
    """Categories of thinking patterns"""

    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    STRATEGIC = "strategic"
    SYSTEMS = "systems"
    CRITICAL = "critical"
    PRACTICAL = "practical"


@dataclass
class ThinkingPattern:
    """
    Represents a single thinking pattern with its characteristics
    """

    name: str
    category: ThinkingCategory
    description: str
    trigger_keywords: list[str]
    strengths: list[str]
    use_cases: list[str]
    prompt_template: str
    effectiveness_scores: dict[str, float]  # Problem type -> effectiveness (0-1)

    def matches_context(self, context: str) -> float:
        """
        Calculate how well this pattern matches the given context
        Returns a score between 0 and 1
        """
        context_lower = context.lower()
        match_score = 0.0

        # Check keyword matches
        for keyword in self.trigger_keywords:
            if keyword.lower() in context_lower:
                match_score += 0.2

        # Check use case relevance
        for use_case in self.use_cases:
            if any(word in context_lower for word in use_case.lower().split()):
                match_score += 0.1

        return min(match_score, 1.0)


class ThinkingPatternRegistry:
    """
    Central registry for all thinking patterns
    """

    def __init__(self):
        self.patterns: dict[str, ThinkingPattern] = {}
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize all 27 thinking patterns"""

        # 1. First Principles Thinking
        self.register_pattern(
            ThinkingPattern(
                name="first_principles",
                category=ThinkingCategory.ANALYTICAL,
                description="Break down complex problems to fundamental truths and rebuild from ground up",
                trigger_keywords=["fundamental", "basic", "core", "foundation", "root cause", "why"],
                strengths=["Eliminates assumptions", "Creates innovative solutions", "Deep understanding"],
                use_cases=["Complex problem solving", "Innovation", "Challenging assumptions"],
                prompt_template="""Apply First Principles Thinking:
1. Identify and question all assumptions
2. Break down to fundamental truths
3. Reason up from first principles
4. Build new solutions without constraints""",
                effectiveness_scores={
                    "innovation": 0.95,
                    "problem_solving": 0.9,
                    "debugging": 0.85,
                    "architecture": 0.9,
                },
            )
        )

        # 2. Systems Thinking
        self.register_pattern(
            ThinkingPattern(
                name="systems_thinking",
                category=ThinkingCategory.SYSTEMS,
                description="Understand interconnections, feedback loops, and emergent behaviors in complex systems",
                trigger_keywords=["system", "interconnect", "feedback", "holistic", "ecosystem", "dependencies"],
                strengths=["Sees big picture", "Identifies leverage points", "Predicts side effects"],
                use_cases=["Architecture design", "Dependency analysis", "Performance optimization"],
                prompt_template="""Apply Systems Thinking:
1. Map all components and relationships
2. Identify feedback loops and delays
3. Find leverage points for maximum impact
4. Consider emergent behaviors""",
                effectiveness_scores={"architecture": 0.95, "integration": 0.9, "scalability": 0.85, "complexity": 0.9},
            )
        )

        # 3. Critical Thinking
        self.register_pattern(
            ThinkingPattern(
                name="critical_thinking",
                category=ThinkingCategory.CRITICAL,
                description="Evaluate information objectively, identify biases, and make reasoned judgments",
                trigger_keywords=["evaluate", "assess", "judge", "critique", "analyze", "evidence"],
                strengths=["Unbiased analysis", "Logical reasoning", "Evidence-based decisions"],
                use_cases=["Code review", "Decision making", "Risk assessment"],
                prompt_template="""Apply Critical Thinking:
1. Examine evidence objectively
2. Identify assumptions and biases
3. Evaluate logic and reasoning
4. Form evidence-based conclusions""",
                effectiveness_scores={
                    "review": 0.95,
                    "validation": 0.9,
                    "decision_making": 0.85,
                    "risk_assessment": 0.9,
                },
            )
        )

        # 4. Creative Thinking
        self.register_pattern(
            ThinkingPattern(
                name="creative_thinking",
                category=ThinkingCategory.CREATIVE,
                description="Generate novel ideas and innovative solutions through divergent thinking",
                trigger_keywords=["creative", "innovative", "novel", "brainstorm", "ideate", "imagine"],
                strengths=["Original solutions", "Breaks conventions", "Multiple perspectives"],
                use_cases=["Feature design", "Problem workarounds", "UI/UX innovation"],
                prompt_template="""Apply Creative Thinking:
1. Generate multiple diverse ideas
2. Combine unrelated concepts
3. Challenge conventions
4. Explore 'what if' scenarios""",
                effectiveness_scores={
                    "innovation": 0.95,
                    "design": 0.9,
                    "problem_solving": 0.8,
                    "feature_development": 0.85,
                },
            )
        )

        # 5. Strategic Thinking
        self.register_pattern(
            ThinkingPattern(
                name="strategic_thinking",
                category=ThinkingCategory.STRATEGIC,
                description="Plan long-term approaches considering goals, resources, and competitive landscape",
                trigger_keywords=["strategy", "plan", "long-term", "competitive", "advantage", "roadmap"],
                strengths=["Long-term vision", "Resource optimization", "Competitive positioning"],
                use_cases=["Project planning", "Technology choices", "Product roadmap"],
                prompt_template="""Apply Strategic Thinking:
1. Define clear objectives
2. Analyze competitive landscape
3. Identify strategic advantages
4. Plan resource allocation""",
                effectiveness_scores={
                    "planning": 0.95,
                    "architecture": 0.85,
                    "product_development": 0.9,
                    "technology_selection": 0.85,
                },
            )
        )

        # 6. Analytical Thinking
        self.register_pattern(
            ThinkingPattern(
                name="analytical_thinking",
                category=ThinkingCategory.ANALYTICAL,
                description="Break down complex information into components for detailed examination",
                trigger_keywords=["analyze", "examine", "investigate", "dissect", "study", "detail"],
                strengths=["Detailed insights", "Pattern recognition", "Data-driven conclusions"],
                use_cases=["Performance analysis", "Bug investigation", "Data analysis"],
                prompt_template="""Apply Analytical Thinking:
1. Decompose into components
2. Examine each part systematically
3. Identify patterns and relationships
4. Synthesize findings""",
                effectiveness_scores={
                    "debugging": 0.95,
                    "performance": 0.9,
                    "data_analysis": 0.95,
                    "optimization": 0.85,
                },
            )
        )

        # 7. Design Thinking
        self.register_pattern(
            ThinkingPattern(
                name="design_thinking",
                category=ThinkingCategory.CREATIVE,
                description="Human-centered approach to innovation that integrates needs, possibilities, and requirements",
                trigger_keywords=["design", "user", "experience", "empathy", "prototype", "iterate"],
                strengths=["User-focused", "Iterative improvement", "Practical solutions"],
                use_cases=["API design", "User interfaces", "Developer experience"],
                prompt_template="""Apply Design Thinking:
1. Empathize with users
2. Define the problem clearly
3. Ideate multiple solutions
4. Prototype and test
5. Iterate based on feedback""",
                effectiveness_scores={
                    "api_design": 0.95,
                    "user_experience": 0.95,
                    "interface_design": 0.9,
                    "product_development": 0.85,
                },
            )
        )

        # 8. Computational Thinking
        self.register_pattern(
            ThinkingPattern(
                name="computational_thinking",
                category=ThinkingCategory.ANALYTICAL,
                description="Solve problems using concepts fundamental to computing: decomposition, patterns, abstraction, algorithms",
                trigger_keywords=["algorithm", "compute", "automate", "abstract", "decompose", "pattern"],
                strengths=["Systematic approach", "Scalable solutions", "Automation focus"],
                use_cases=["Algorithm design", "Automation", "Optimization problems"],
                prompt_template="""Apply Computational Thinking:
1. Decompose the problem
2. Recognize patterns
3. Abstract general principles
4. Design algorithms""",
                effectiveness_scores={
                    "algorithm_design": 0.95,
                    "automation": 0.9,
                    "optimization": 0.9,
                    "data_structures": 0.85,
                },
            )
        )

        # 9. Engineering Thinking
        self.register_pattern(
            ThinkingPattern(
                name="engineering_thinking",
                category=ThinkingCategory.PRACTICAL,
                description="Apply engineering principles: constraints, trade-offs, iterative refinement, and reliability",
                trigger_keywords=["engineer", "build", "construct", "reliable", "robust", "trade-off"],
                strengths=["Practical solutions", "Reliability focus", "Trade-off analysis"],
                use_cases=["System design", "Infrastructure", "Production readiness"],
                prompt_template="""Apply Engineering Thinking:
1. Define requirements and constraints
2. Analyze trade-offs
3. Design for reliability
4. Plan for failure modes
5. Iterate and refine""",
                effectiveness_scores={
                    "system_design": 0.95,
                    "infrastructure": 0.9,
                    "reliability": 0.95,
                    "production": 0.9,
                },
            )
        )

        # 10. Product Thinking
        self.register_pattern(
            ThinkingPattern(
                name="product_thinking",
                category=ThinkingCategory.STRATEGIC,
                description="Focus on user value, market fit, and business viability",
                trigger_keywords=["product", "feature", "user value", "market", "viability", "mvp"],
                strengths=["User value focus", "Market awareness", "Business alignment"],
                use_cases=["Feature prioritization", "MVP definition", "Product strategy"],
                prompt_template="""Apply Product Thinking:
1. Identify user needs
2. Validate market demand
3. Define value proposition
4. Plan MVP approach
5. Measure success metrics""",
                effectiveness_scores={
                    "product_development": 0.95,
                    "feature_design": 0.9,
                    "prioritization": 0.85,
                    "strategy": 0.85,
                },
            )
        )

        # 11. Business Thinking
        self.register_pattern(
            ThinkingPattern(
                name="business_thinking",
                category=ThinkingCategory.STRATEGIC,
                description="Consider cost-benefit, ROI, market dynamics, and business sustainability",
                trigger_keywords=["business", "cost", "roi", "revenue", "profit", "market"],
                strengths=["ROI focus", "Cost awareness", "Business viability"],
                use_cases=["Technology decisions", "Resource allocation", "Build vs buy"],
                prompt_template="""Apply Business Thinking:
1. Analyze costs and benefits
2. Calculate ROI
3. Consider market dynamics
4. Evaluate sustainability
5. Align with business goals""",
                effectiveness_scores={
                    "decision_making": 0.9,
                    "resource_planning": 0.95,
                    "technology_selection": 0.85,
                    "strategy": 0.9,
                },
            )
        )

        # 12. Data Thinking
        self.register_pattern(
            ThinkingPattern(
                name="data_thinking",
                category=ThinkingCategory.ANALYTICAL,
                description="Make decisions based on data analysis, metrics, and evidence",
                trigger_keywords=["data", "metrics", "measure", "analytics", "evidence", "statistics"],
                strengths=["Evidence-based", "Objective insights", "Measurable outcomes"],
                use_cases=["Performance optimization", "A/B testing", "Analytics implementation"],
                prompt_template="""Apply Data Thinking:
1. Identify key metrics
2. Collect relevant data
3. Analyze patterns and trends
4. Draw data-driven conclusions
5. Plan measurement strategy""",
                effectiveness_scores={
                    "analytics": 0.95,
                    "optimization": 0.9,
                    "performance": 0.85,
                    "decision_making": 0.85,
                },
            )
        )

        # 13. User Thinking
        self.register_pattern(
            ThinkingPattern(
                name="user_thinking",
                category=ThinkingCategory.PRACTICAL,
                description="Prioritize user needs, experience, and journey throughout solutions",
                trigger_keywords=["user", "customer", "experience", "journey", "usability", "needs"],
                strengths=["User empathy", "Experience focus", "Practical solutions"],
                use_cases=["API usability", "Error messages", "Documentation", "Developer tools"],
                prompt_template="""Apply User Thinking:
1. Understand user goals
2. Map user journey
3. Identify pain points
4. Design intuitive solutions
5. Validate with users""",
                effectiveness_scores={
                    "user_experience": 0.95,
                    "api_design": 0.9,
                    "documentation": 0.85,
                    "interface_design": 0.9,
                },
            )
        )

        # 14. Agile Thinking
        self.register_pattern(
            ThinkingPattern(
                name="agile_thinking",
                category=ThinkingCategory.PRACTICAL,
                description="Embrace iterative development, feedback loops, and adaptive planning",
                trigger_keywords=["agile", "iterate", "feedback", "adaptive", "sprint", "incremental"],
                strengths=["Flexibility", "Fast feedback", "Continuous improvement"],
                use_cases=["Development process", "Project management", "Feature rollout"],
                prompt_template="""Apply Agile Thinking:
1. Break into small iterations
2. Deliver incremental value
3. Gather feedback early
4. Adapt based on learning
5. Maintain flexibility""",
                effectiveness_scores={
                    "project_management": 0.95,
                    "development_process": 0.9,
                    "feature_development": 0.85,
                    "team_collaboration": 0.85,
                },
            )
        )

        # 15. Lean Thinking
        self.register_pattern(
            ThinkingPattern(
                name="lean_thinking",
                category=ThinkingCategory.PRACTICAL,
                description="Eliminate waste, maximize value, and optimize flow",
                trigger_keywords=["lean", "waste", "efficiency", "value", "optimize", "minimal"],
                strengths=["Efficiency focus", "Waste elimination", "Value maximization"],
                use_cases=["Process optimization", "Code refactoring", "Resource usage"],
                prompt_template="""Apply Lean Thinking:
1. Identify value streams
2. Eliminate waste
3. Optimize flow
4. Reduce complexity
5. Continuous improvement""",
                effectiveness_scores={
                    "optimization": 0.95,
                    "refactoring": 0.9,
                    "process_improvement": 0.9,
                    "efficiency": 0.95,
                },
            )
        )

        # 16. Holistic Thinking
        self.register_pattern(
            ThinkingPattern(
                name="holistic_thinking",
                category=ThinkingCategory.SYSTEMS,
                description="Consider the whole system and all interdependencies",
                trigger_keywords=["holistic", "whole", "comprehensive", "integrated", "complete", "overall"],
                strengths=["Complete view", "Integration focus", "Balance considerations"],
                use_cases=["System architecture", "Integration planning", "Impact analysis"],
                prompt_template="""Apply Holistic Thinking:
1. View the complete system
2. Consider all stakeholders
3. Analyze interdependencies
4. Balance competing needs
5. Optimize the whole""",
                effectiveness_scores={
                    "architecture": 0.95,
                    "integration": 0.95,
                    "system_design": 0.9,
                    "planning": 0.85,
                },
            )
        )

        # 17. Modular Thinking
        self.register_pattern(
            ThinkingPattern(
                name="modular_thinking",
                category=ThinkingCategory.PRACTICAL,
                description="Design in independent, reusable, and composable modules",
                trigger_keywords=["modular", "component", "reusable", "composable", "decouple", "module"],
                strengths=["Reusability", "Maintainability", "Scalability"],
                use_cases=["Component design", "Microservices", "Library architecture"],
                prompt_template="""Apply Modular Thinking:
1. Identify natural boundaries
2. Define clear interfaces
3. Minimize dependencies
4. Maximize reusability
5. Enable composition""",
                effectiveness_scores={
                    "architecture": 0.9,
                    "component_design": 0.95,
                    "maintainability": 0.9,
                    "scalability": 0.85,
                },
            )
        )

        # 18. Abstract Thinking
        self.register_pattern(
            ThinkingPattern(
                name="abstract_thinking",
                category=ThinkingCategory.ANALYTICAL,
                description="Extract general principles and patterns from specific instances",
                trigger_keywords=["abstract", "general", "pattern", "principle", "concept", "theory"],
                strengths=["Pattern recognition", "Generalization", "Reusable solutions"],
                use_cases=["Framework design", "Pattern extraction", "Architecture principles"],
                prompt_template="""Apply Abstract Thinking:
1. Identify common patterns
2. Extract general principles
3. Remove specific details
4. Define abstractions
5. Apply broadly""",
                effectiveness_scores={
                    "framework_design": 0.95,
                    "pattern_recognition": 0.95,
                    "architecture": 0.85,
                    "generalization": 0.9,
                },
            )
        )

        # 19. Concrete Thinking
        self.register_pattern(
            ThinkingPattern(
                name="concrete_thinking",
                category=ThinkingCategory.PRACTICAL,
                description="Focus on specific, practical, and tangible implementations",
                trigger_keywords=["concrete", "specific", "practical", "implement", "tangible", "actual"],
                strengths=["Practical solutions", "Clear implementation", "Immediate results"],
                use_cases=["Implementation details", "Bug fixes", "Specific optimizations"],
                prompt_template="""Apply Concrete Thinking:
1. Focus on specifics
2. Define exact steps
3. Consider practical constraints
4. Implement tangible solutions
5. Measure real results""",
                effectiveness_scores={
                    "implementation": 0.95,
                    "debugging": 0.9,
                    "optimization": 0.85,
                    "practical_solutions": 0.95,
                },
            )
        )

        # 20. Lateral Thinking
        self.register_pattern(
            ThinkingPattern(
                name="lateral_thinking",
                category=ThinkingCategory.CREATIVE,
                description="Approach problems from unexpected angles and find indirect solutions",
                trigger_keywords=["lateral", "indirect", "alternative", "unconventional", "creative", "outside"],
                strengths=["Innovative solutions", "Breakthrough ideas", "Constraint bypass"],
                use_cases=["Workarounds", "Creative solutions", "Constraint challenges"],
                prompt_template="""Apply Lateral Thinking:
1. Challenge assumptions
2. Approach from new angles
3. Find indirect paths
4. Use random stimulation
5. Explore alternatives""",
                effectiveness_scores={
                    "innovation": 0.9,
                    "problem_solving": 0.85,
                    "creative_solutions": 0.95,
                    "workarounds": 0.9,
                },
            )
        )

        # 21. Vertical Thinking
        self.register_pattern(
            ThinkingPattern(
                name="vertical_thinking",
                category=ThinkingCategory.ANALYTICAL,
                description="Deep, focused analysis following logical sequences step by step",
                trigger_keywords=["vertical", "deep", "focused", "sequential", "logical", "drill"],
                strengths=["Thorough analysis", "Logical progression", "Deep understanding"],
                use_cases=["Root cause analysis", "Deep debugging", "Performance profiling"],
                prompt_template="""Apply Vertical Thinking:
1. Start from the top
2. Drill down systematically
3. Follow logical sequences
4. Explore each level fully
5. Reach root causes""",
                effectiveness_scores={
                    "debugging": 0.95,
                    "root_cause_analysis": 0.95,
                    "deep_analysis": 0.9,
                    "investigation": 0.9,
                },
            )
        )

        # 22. Reverse Thinking
        self.register_pattern(
            ThinkingPattern(
                name="reverse_thinking",
                category=ThinkingCategory.CREATIVE,
                description="Work backwards from desired outcome or invert the problem",
                trigger_keywords=["reverse", "backward", "invert", "opposite", "end-to-start", "goal"],
                strengths=["Clear goal focus", "Constraint identification", "Alternative paths"],
                use_cases=["Goal planning", "Reverse engineering", "Debugging from symptoms"],
                prompt_template="""Apply Reverse Thinking:
1. Start with desired outcome
2. Work backwards step by step
3. Identify prerequisites
4. Find critical path
5. Plan forward execution""",
                effectiveness_scores={
                    "planning": 0.9,
                    "reverse_engineering": 0.95,
                    "goal_achievement": 0.85,
                    "problem_solving": 0.85,
                },
            )
        )

        # 23. Analogical Thinking
        self.register_pattern(
            ThinkingPattern(
                name="analogical_thinking",
                category=ThinkingCategory.CREATIVE,
                description="Draw parallels from other domains to solve current problems",
                trigger_keywords=["analogy", "similar", "parallel", "like", "compare", "metaphor"],
                strengths=["Cross-domain insights", "Pattern transfer", "Creative solutions"],
                use_cases=["Pattern recognition", "Solution adaptation", "Concept explanation"],
                prompt_template="""Apply Analogical Thinking:
1. Identify the core problem
2. Find similar problems in other domains
3. Extract successful patterns
4. Adapt to current context
5. Apply transferred insights""",
                effectiveness_scores={
                    "pattern_recognition": 0.85,
                    "creative_solutions": 0.9,
                    "knowledge_transfer": 0.95,
                    "innovation": 0.85,
                },
            )
        )

        # 24. Inductive Thinking
        self.register_pattern(
            ThinkingPattern(
                name="inductive_thinking",
                category=ThinkingCategory.ANALYTICAL,
                description="Build general conclusions from specific observations and patterns",
                trigger_keywords=["inductive", "observe", "pattern", "generalize", "evidence", "conclude"],
                strengths=["Pattern discovery", "Theory building", "Evidence-based"],
                use_cases=["Pattern extraction", "Trend analysis", "Hypothesis formation"],
                prompt_template="""Apply Inductive Thinking:
1. Gather specific observations
2. Identify patterns
3. Form hypotheses
4. Test with more data
5. Build general conclusions""",
                effectiveness_scores={"pattern_recognition": 0.9, "analysis": 0.85, "research": 0.9, "discovery": 0.85},
            )
        )

        # 25. Deductive Thinking
        self.register_pattern(
            ThinkingPattern(
                name="deductive_thinking",
                category=ThinkingCategory.ANALYTICAL,
                description="Apply general principles to reach specific conclusions",
                trigger_keywords=["deductive", "principle", "rule", "apply", "conclude", "therefore"],
                strengths=["Logical certainty", "Clear reasoning", "Predictable outcomes"],
                use_cases=["Rule application", "Constraint validation", "Logical proofs"],
                prompt_template="""Apply Deductive Thinking:
1. Start with general principles
2. Apply to specific case
3. Follow logical rules
4. Derive conclusions
5. Validate reasoning""",
                effectiveness_scores={
                    "validation": 0.95,
                    "logic_verification": 0.95,
                    "rule_application": 0.9,
                    "proof": 0.9,
                },
            )
        )

        # 26. Socratic Thinking (苏格拉底式反问)
        self.register_pattern(
            ThinkingPattern(
                name="socratic_thinking",
                category=ThinkingCategory.CRITICAL,
                description="通过系统性提问来揭示假设、挑战思维、深化理解",
                trigger_keywords=["验证", "测试", "检验", "全面", "深度", "为什么", "假设", "前提", "证据"],
                strengths=["深度探究", "假设挑战", "批判性验证", "思维清晰"],
                use_cases=["需求验证", "测试设计", "方案评审", "假设检验", "深度分析"],
                prompt_template="""应用苏格拉底式思考：
1. 澄清概念：这个真正意味着什么？能否举例说明？
2. 挑战假设：我们基于什么假设？这些假设是否成立？
3. 探究证据：支持这个观点的证据是什么？如何验证？
4. 质疑视角：从其他角度看会如何？谁会持不同意见？
5. 审视影响：如果这是真的，会导致什么？有何连锁反应？
6. 元认知反思：为什么我们这样思考？还有其他思考方式吗？""",
                effectiveness_scores={
                    "validation": 0.95,
                    "testing": 0.95,
                    "review": 0.9,
                    "critical_analysis": 0.95,
                    "requirement_analysis": 0.9,
                },
            )
        )

        # 27. Craftsman Thinking (工匠精神)
        self.register_pattern(
            ThinkingPattern(
                name="craftsman_thinking",
                category=ThinkingCategory.PRACTICAL,
                description="追求卓越、精益求精、关注细节、持续改进的工匠精神",
                trigger_keywords=["精益", "完美", "细节", "优化", "打磨", "精进", "品质", "工艺"],
                strengths=["极致品质", "细节把控", "持续优化", "专业精神"],
                use_cases=["代码优化", "性能调优", "架构完善", "产品打磨", "质量提升"],
                prompt_template="""应用工匠精神思考：
1. 品质追求：当前方案离完美还有多远？哪些细节可以改进？
2. 精益求精：即使已经很好，还能更好吗？如何做到极致？
3. 技艺磨练：这个实现展现了什么水平？如何体现专业性？
4. 细节雕琢：每个细节都经过深思熟虑了吗？边界情况如何？
5. 持续改进：下一次迭代可以优化什么？长期如何演进？
6. 匠心传承：这个方案是否值得成为最佳实践？如何分享经验？""",
                effectiveness_scores={
                    "optimization": 0.95,
                    "quality": 0.95,
                    "refactoring": 0.9,
                    "performance": 0.9,
                    "best_practices": 0.95,
                },
            )
        )

    def register_pattern(self, pattern: ThinkingPattern):
        """Register a thinking pattern"""
        self.patterns[pattern.name] = pattern

    def get_pattern(self, name: str) -> Optional[ThinkingPattern]:
        """Get a specific pattern by name"""
        return self.patterns.get(name)

    def select_patterns(self, context: str, problem_type: str, max_patterns: int = 3) -> list[ThinkingPattern]:
        """
        Select the most appropriate thinking patterns for the given context

        Args:
            context: The problem context or description
            problem_type: Type of problem (e.g., "debugging", "architecture", "optimization")
            max_patterns: Maximum number of patterns to return

        Returns:
            List of selected thinking patterns, ordered by relevance
        """
        pattern_scores = []

        for pattern in self.patterns.values():
            # Calculate context match score
            context_score = pattern.matches_context(context)

            # Get effectiveness score for problem type
            effectiveness = pattern.effectiveness_scores.get(problem_type, 0.5)

            # Combined score
            total_score = (context_score * 0.6) + (effectiveness * 0.4)

            pattern_scores.append((pattern, total_score))

        # Sort by score and return top patterns
        pattern_scores.sort(key=lambda x: x[1], reverse=True)
        return [pattern for pattern, _ in pattern_scores[:max_patterns]]

    def get_patterns_by_category(self, category: ThinkingCategory) -> list[ThinkingPattern]:
        """Get all patterns in a specific category"""
        return [p for p in self.patterns.values() if p.category == category]

    def get_all_patterns(self) -> list[ThinkingPattern]:
        """Get all registered patterns"""
        return list(self.patterns.values())


# Global registry instance
thinking_registry = ThinkingPatternRegistry()
