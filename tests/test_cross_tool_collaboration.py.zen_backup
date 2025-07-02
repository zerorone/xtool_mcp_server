"""
Cross-Tool Collaboration Test Suite

This test suite validates that different tools in the Zen MCP Server can work
together effectively to solve complex tasks through collaboration.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from server import handle_call_tool
from utils.path_intelligence import PathIntelligence
from utils.project_detector import ProjectDetector
from utils.todo_parser import TaskManager, TodoParser


class TestMemoryAndAnalysisCollaboration:
    """Test collaboration between memory and analysis tools"""

    @pytest.mark.asyncio
    async def test_memory_assisted_analysis(self):
        """Test using memory to enhance analysis context"""
        # Step 1: Save project context to memory
        project_context = {
            "project_name": "TestProject",
            "architecture": {"backend": "Python/FastAPI", "frontend": "React/TypeScript", "database": "PostgreSQL"},
            "current_issues": ["Performance degradation in API endpoints", "Memory leaks in React components"],
            "recent_changes": ["Added new caching layer", "Refactored authentication system"],
        }

        save_result = await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(project_context),
                "metadata": {"type": "project_context", "project": "TestProject", "timestamp": "2024-01-01"},
            },
        )
        assert save_result.status == "success"

        # Step 2: Use ThinkBoost to analyze a problem with context
        analysis_result = await handle_call_tool(
            "thinkboost",
            {
                "problem": "API endpoints are slow after recent caching layer addition",
                "context": "Project uses FastAPI with PostgreSQL. Recent changes include new caching layer.",
            },
        )
        assert analysis_result.status == "success"
        assert "THINKING PATTERNS" in analysis_result.output

        # Step 3: Save analysis results back to memory
        save_analysis_result = await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": "Analysis suggests investigating cache invalidation and connection pooling",
                "metadata": {"type": "analysis_result", "problem": "API performance", "tool": "thinkboost"},
            },
        )
        assert save_analysis_result.status == "success"

        # Step 4: Recall all related information
        recall_result = await handle_call_tool(
            "memory", {"operation": "recall", "query": "API performance TestProject"}
        )
        assert recall_result.status == "success"
        assert "TestProject" in recall_result.output

    @pytest.mark.asyncio
    async def test_iterative_problem_solving(self):
        """Test iterative problem solving using multiple tools"""
        # Problem: Debug a complex issue through iterations

        # Iteration 1: Initial analysis
        initial_analysis = await handle_call_tool(
            "thinkboost",
            {
                "problem": "Users report data inconsistency between UI and database",
                "context": "E-commerce platform with real-time inventory updates",
            },
        )
        assert initial_analysis.status == "success"

        # Save initial findings
        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(
                    {
                        "iteration": 1,
                        "findings": "Potential race condition or caching issue",
                        "next_steps": ["Check cache TTL", "Verify transaction isolation"],
                    }
                ),
                "metadata": {"type": "debug_iteration", "iteration": 1},
            },
        )

        # Iteration 2: Deeper investigation
        deeper_analysis = await handle_call_tool(
            "thinkboost",
            {
                "problem": "Investigate race condition in inventory update system",
                "context": "Multiple services updating inventory: API, background jobs, webhooks",
            },
        )
        assert deeper_analysis.status == "success"

        # Save deeper findings
        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(
                    {
                        "iteration": 2,
                        "findings": "Missing distributed locks on inventory updates",
                        "solution": "Implement Redis-based distributed locking",
                    }
                ),
                "metadata": {"type": "debug_iteration", "iteration": 2},
            },
        )

        # Recall all iterations
        iterations_result = await handle_call_tool(
            "memory", {"operation": "recall", "query": "debug_iteration", "filters": {"type": "debug_iteration"}}
        )
        assert iterations_result.status == "success"


class TestPlanningAndExecutionCollaboration:
    """Test collaboration in planning and execution workflows"""

    @pytest.mark.asyncio
    async def test_todo_driven_development_flow(self):
        """Test complete TODO-driven development workflow"""
        # Step 1: Create TODO list
        todo_content = """
# Feature: User Authentication Refactor

## Tasks
- [ ] 🔍 Analyze current authentication system [!!!] (2h) #analysis
- [ ] 📝 Design new JWT-based auth flow [!!] (3h) #design
- [ ] 🏗️ Implement auth service [!!] (5h) #implementation
- [ ] ✅ Write unit tests (3h) #testing
- [ ] 📚 Update API documentation (2h) #documentation

## Dependencies
- Task "Design new JWT-based auth flow" requires "Analyze current authentication system"
- Task "Implement auth service" requires "Design new JWT-based auth flow"
- Task "Write unit tests" requires "Implement auth service"
"""

        # Parse TODO
        parser = TodoParser()
        tasks = parser.parse_content(todo_content)

        # Create task manager
        manager = TaskManager()
        for task in tasks:
            manager.add_task(task)

        # Step 2: Get optimal next task
        optimal_tasks = manager.get_optimal_next_tasks(1)
        assert len(optimal_tasks) > 0

        first_task = optimal_tasks[0]
        assert "Analyze" in first_task.title  # Should start with analysis

        # Step 3: Use ThinkBoost to approach the task
        task_approach = await handle_call_tool(
            "thinkboost",
            {
                "problem": f"How to approach: {first_task.title}",
                "context": "Refactoring authentication system to use JWT",
            },
        )
        assert task_approach.status == "success"

        # Step 4: Save task progress
        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(
                    {
                        "task_id": first_task.id,
                        "task_title": first_task.title,
                        "status": "in_progress",
                        "approach": "Following systematic analysis pattern",
                        "findings": [],
                    }
                ),
                "metadata": {"type": "task_progress", "task_id": first_task.id},
            },
        )

        # Step 5: Complete task and update
        manager.update_task_status(first_task.id, "completed")

        # Get next optimal task
        next_tasks = manager.get_optimal_next_tasks(1)
        assert len(next_tasks) > 0
        assert "Design" in next_tasks[0].title  # Should move to design

    @pytest.mark.asyncio
    async def test_project_aware_planning(self):
        """Test planning that adapts to project type"""
        # Detect project type
        detector = ProjectDetector()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python project structure
            project_dir = Path(tmpdir)
            (project_dir / "requirements.txt").write_text("fastapi\npytest\n")
            (project_dir / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
            (project_dir / "tests").mkdir()

            # Detect project
            env = detector.detect_project(str(project_dir))
            assert env.project_type.value == "python"

            # Plan based on project type
            planning_context = {
                "project_type": env.project_type.value,
                "frameworks": env.frameworks,
                "task": "Add user authentication",
            }

            plan_result = await handle_call_tool(
                "thinkboost",
                {
                    "problem": "Plan authentication implementation for FastAPI project",
                    "context": json.dumps(planning_context),
                },
            )
            assert plan_result.status == "success"

            # Save plan to memory
            await handle_call_tool(
                "memory",
                {
                    "operation": "save",
                    "content": json.dumps(
                        {
                            "project": str(project_dir),
                            "plan": "FastAPI authentication implementation plan",
                            "project_type": env.project_type.value,
                        }
                    ),
                    "metadata": {"type": "project_plan"},
                },
            )


class TestIntelligentWorkflowCollaboration:
    """Test intelligent workflows using multiple tools"""

    @pytest.mark.asyncio
    async def test_code_review_workflow(self):
        """Test complete code review workflow"""
        # Sample code to review
        code_sample = """
def process_user_data(users):
    results = []
    for user in users:
        if user.get('active') == True:
            result = {
                'id': user['id'],
                'name': user['name'].upper(),
                'email': user['email']
            }
            results.append(result)
    return results
"""

        # Step 1: Initial code analysis
        analysis = await handle_call_tool(
            "thinkboost", {"problem": "Review this Python code for improvements", "context": code_sample}
        )
        assert analysis.status == "success"

        # Step 2: Save code and initial review
        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(
                    {
                        "code": code_sample,
                        "initial_review": "Code needs optimization and better practices",
                        "issues": [
                            "Use of == True is redundant",
                            "Could use list comprehension",
                            "No error handling",
                            "No type hints",
                        ],
                    }
                ),
                "metadata": {"type": "code_review", "language": "python"},
            },
        )

        # Step 3: Generate improvement suggestions
        improvements = await handle_call_tool(
            "thinkboost",
            {
                "problem": "Generate specific improvements for the code",
                "context": "Issues: redundant boolean check, needs list comprehension, missing type hints",
            },
        )
        assert improvements.status == "success"

        # Step 4: Create refactoring TODO
        refactor_todo = """
- [ ] Remove redundant boolean comparison
- [ ] Convert to list comprehension
- [ ] Add type hints
- [ ] Add error handling for missing keys
- [ ] Add docstring
"""

        parser = TodoParser()
        refactor_tasks = parser.parse_content(refactor_todo)
        assert len(refactor_tasks) == 5

    @pytest.mark.asyncio
    async def test_debugging_collaboration_workflow(self):
        """Test collaborative debugging workflow"""
        # Error scenario
        error_context = {
            "error": "AttributeError: 'NoneType' object has no attribute 'split'",
            "file": "data_processor.py",
            "line": 42,
            "code_snippet": "tokens = text.split(' ')",
            "stack_trace": [
                "File 'main.py', line 10, in <module>",
                "File 'data_processor.py', line 42, in process_text",
            ],
        }

        # Step 1: Analyze the error
        error_analysis = await handle_call_tool(
            "thinkboost",
            {"problem": f"Debug this error: {error_context['error']}", "context": json.dumps(error_context)},
        )
        assert error_analysis.status == "success"

        # Step 2: Save debugging session
        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(
                    {
                        "error": error_context,
                        "analysis": "Variable 'text' is None, need null check",
                        "fix_suggestions": [
                            "Add null check before split",
                            "Use default value",
                            "Validate input at function entry",
                        ],
                    }
                ),
                "metadata": {"type": "debug_session", "error_type": "AttributeError"},
            },
        )

        # Step 3: Create fix plan
        fix_plan = await handle_call_tool(
            "thinkboost",
            {
                "problem": "Create a fix plan for NoneType error in text processing",
                "context": "Need to handle None values gracefully in text.split() operation",
            },
        )
        assert fix_plan.status == "success"

        # Step 4: Check for similar issues in history
        similar_issues = await handle_call_tool(
            "memory", {"operation": "recall", "query": "AttributeError NoneType", "filters": {"type": "debug_session"}}
        )
        assert similar_issues.status == "success"


class TestPathIntelligenceCollaboration:
    """Test path intelligence integration with other tools"""

    @pytest.mark.asyncio
    async def test_intelligent_file_navigation(self):
        """Test intelligent file navigation workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project structure
            project_dir = Path(tmpdir)
            (project_dir / "src").mkdir()
            (project_dir / "src" / "auth").mkdir()
            (project_dir / "src" / "auth" / "jwt_handler.py").write_text("# JWT handler")
            (project_dir / "src" / "auth" / "validators.py").write_text("# Validators")
            (project_dir / "tests").mkdir()
            (project_dir / "tests" / "test_jwt_handler.py").write_text("# Tests")

            os.chdir(str(project_dir))

            # Initialize path intelligence
            path_intel = PathIntelligence()

            # Learn from usage
            path_intel.learn_path_usage("src/auth/jwt_handler.py", "source", "authentication")
            path_intel.learn_path_usage("tests/test_jwt_handler.py", "test", "authentication")

            # Step 1: Get file recommendations
            auth_files = path_intel.recommend_paths("auth")
            assert len(auth_files) > 0

            # Step 2: Analyze file relationships
            analysis = await handle_call_tool(
                "thinkboost",
                {
                    "problem": "Analyze the relationship between auth files",
                    "context": f"Files: {[r.path for r in auth_files[:3]]}",
                },
            )
            assert analysis.status == "success"

            # Step 3: Save navigation pattern
            await handle_call_tool(
                "memory",
                {
                    "operation": "save",
                    "content": json.dumps(
                        {
                            "pattern": "auth_navigation",
                            "files": [r.path for r in auth_files[:3]],
                            "context": "authentication",
                        }
                    ),
                    "metadata": {"type": "navigation_pattern"},
                },
            )

            # Step 4: Suggest next file based on current
            next_files = path_intel.suggest_next_file("src/auth/jwt_handler.py", "test")
            assert any("test" in f.path for f in next_files)


class TestComplexScenarioCollaboration:
    """Test complex real-world scenario collaborations"""

    @pytest.mark.asyncio
    async def test_feature_development_lifecycle(self):
        """Test complete feature development lifecycle"""
        feature_name = "User Notification System"

        # Phase 1: Planning
        planning_result = await handle_call_tool(
            "thinkboost",
            {
                "problem": f"Plan the implementation of {feature_name}",
                "context": "Web application with email and push notification requirements",
            },
        )
        assert planning_result.status == "success"

        # Save plan
        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(
                    {
                        "feature": feature_name,
                        "phase": "planning",
                        "components": [
                            "Notification service interface",
                            "Email provider integration",
                            "Push notification handler",
                            "User preference management",
                            "Notification templates",
                        ],
                    }
                ),
                "metadata": {"type": "feature_plan", "feature": feature_name},
            },
        )

        # Phase 2: Create development tasks
        todo_content = f"""
# {feature_name} Implementation

- [ ] Design notification service interface [!!!] (3h) #architecture
- [ ] Implement email provider adapter [!!] (4h) #backend
- [ ] Create push notification handler [!!] (4h) #backend
- [ ] Build user preference API [!!] (3h) #backend
- [ ] Design notification templates (2h) #frontend
- [ ] Add notification UI components (4h) #frontend
- [ ] Write integration tests (3h) #testing
- [ ] Update API documentation (2h) #docs
"""

        parser = TodoParser()
        tasks = parser.parse_content(todo_content)

        manager = TaskManager()
        for task in tasks:
            manager.add_task(task)

        # Phase 3: Execute tasks with context
        current_task = manager.get_optimal_next_tasks(1)[0]

        # Approach current task
        task_approach = await handle_call_tool(
            "thinkboost",
            {"problem": f"How to implement: {current_task.title}", "context": f"Part of {feature_name} feature"},
        )
        assert task_approach.status == "success"

        # Phase 4: Track progress
        progress = manager.get_progress_report()

        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(
                    {"feature": feature_name, "progress": progress, "current_task": current_task.title}
                ),
                "metadata": {"type": "feature_progress", "feature": feature_name},
            },
        )

        # Phase 5: Review implementation approach
        review_result = await handle_call_tool(
            "thinkboost",
            {
                "problem": "Review the notification system architecture",
                "context": "Components: service interface, email adapter, push handler, preferences API",
            },
        )
        assert review_result.status == "success"

    @pytest.mark.asyncio
    async def test_multi_tool_investigation(self):
        """Test investigation using multiple tools in sequence"""
        # Scenario: Investigate performance issue

        # Step 1: Initial report
        issue_report = {
            "type": "performance",
            "description": "API response times increased by 300% after deployment",
            "affected_endpoints": ["/api/users", "/api/products", "/api/orders"],
            "deployment_changes": ["Updated ORM version", "Added new middleware", "Changed DB connection pool"],
        }

        # Save issue report
        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(issue_report),
                "metadata": {"type": "issue_report", "severity": "high"},
            },
        )

        # Step 2: Analyze potential causes
        analysis = await handle_call_tool(
            "thinkboost",
            {
                "problem": "Identify likely causes of 300% API performance degradation",
                "context": json.dumps(issue_report),
            },
        )
        assert analysis.status == "success"

        # Step 3: Create investigation plan
        investigation_todo = """
- [ ] Check database query performance [!!!]
- [ ] Profile middleware execution time [!!!]
- [ ] Verify connection pool settings [!!]
- [ ] Review ORM query generation [!!]
- [ ] Analyze server resource usage [!]
"""

        parser = TodoParser()
        parser.parse_content(investigation_todo)

        # Step 4: Document findings iteratively
        findings = {
            "database_queries": "N+1 query problem detected in user endpoint",
            "middleware": "New auth middleware adds 50ms per request",
            "connection_pool": "Pool size too small for current load",
            "solution": "Optimize queries, increase pool size, cache auth results",
        }

        await handle_call_tool(
            "memory",
            {
                "operation": "save",
                "content": json.dumps(findings),
                "metadata": {"type": "investigation_findings", "issue": "performance_degradation"},
            },
        )

        # Step 5: Generate fix recommendations
        fix_recommendations = await handle_call_tool(
            "thinkboost", {"problem": "Create action plan to fix performance issues", "context": json.dumps(findings)}
        )
        assert fix_recommendations.status == "success"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
