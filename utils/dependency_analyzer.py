"""
Task Dependency Analysis System

This module provides advanced dependency analysis for the TODO-driven development system.
It can detect both explicit and implicit dependencies, perform topological sorting,
and find critical paths through tasks.
"""

import re
from collections import defaultdict, deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .todo_parser import Task


class DependencyAnalyzer:
    """Analyzes and resolves task dependencies"""

    def __init__(self):
        self.dependency_graph = defaultdict(set)  # task_id -> set of dependent task_ids
        self.reverse_graph = defaultdict(set)  # task_id -> set of prerequisite task_ids
        self.tasks = {}

    def add_tasks(self, tasks: list["Task"]):
        """Add tasks and build dependency graphs"""
        # Import at runtime to avoid circular import

        self.tasks = {task.id: task for task in tasks}

        # Build initial graphs from explicit dependencies
        for task in tasks:
            for dep in task.dependencies:
                if dep.dependency_type == "requires":
                    # Task requires dep.task_id to be completed first
                    self.reverse_graph[task.id].add(dep.task_id)
                    self.dependency_graph[dep.task_id].add(task.id)
                elif dep.dependency_type == "blocks":
                    # Task blocks dep.task_id
                    self.reverse_graph[dep.task_id].add(task.id)
                    self.dependency_graph[task.id].add(dep.task_id)

    def detect_implicit_dependencies(self):
        """Detect implicit dependencies from task content and context"""
        for task_id, task in self.tasks.items():
            # Check task title and description for references to other tasks
            content = f"{task.title} {task.description or ''}"

            # Look for patterns like "after <task>", "requires <task>", "depends on <task>"
            dependency_patterns = [
                r"after\s+[\"']?(.+?)[\"']?\s*(?:is|are|has|have)?(?:\s+(?:completed|done|finished))?",
                r"requires?\s+[\"']?(.+?)[\"']?\s*(?:to\s+be)?(?:\s+(?:completed|done|finished))?",
                r"depends?\s+on\s+[\"']?(.+?)[\"']?",
                r"needs?\s+[\"']?(.+?)[\"']?\s*(?:to\s+be)?(?:\s+(?:completed|done|finished))?",
                r"blocks?\s+[\"']?(.+?)[\"']?",
                r"(?:based|builds?)\s+on\s+[\"']?(.+?)[\"']?",
            ]

            for pattern in dependency_patterns:
                matches = re.findall(pattern, content.lower())
                for match in matches:
                    # Try to find matching task
                    match_lower = match.strip().lower()
                    for other_id, other_task in self.tasks.items():
                        if other_id != task_id:
                            other_title_lower = other_task.title.lower()
                            # Check for partial matches
                            if (
                                match_lower in other_title_lower
                                or other_title_lower in match_lower
                                or self._fuzzy_match(match_lower, other_title_lower)
                            ):
                                # Add implicit dependency
                                if other_id not in self.reverse_graph[task_id]:
                                    self.reverse_graph[task_id].add(other_id)
                                    self.dependency_graph[other_id].add(task_id)
                                    # Add to task's dependencies
                                    from .todo_parser import TaskDependency

                                    task.dependencies.append(
                                        TaskDependency(
                                            task_id=other_id,
                                            dependency_type="requires",
                                            notes="Implicit dependency detected",
                                        )
                                    )

    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy matching for task names"""
        # Check if significant words match
        words1 = {word for word in str1.split() if len(word) > 3}
        words2 = {word for word in str2.split() if len(word) > 3}

        if not words1 or not words2:
            return False

        common = words1.intersection(words2)
        ratio = len(common) / min(len(words1), len(words2))

        return ratio >= threshold

    def get_execution_order(self) -> list[str]:
        """Get optimal task execution order using topological sort"""
        # Count incoming edges for each task
        in_degree = defaultdict(int)
        for task_id in self.tasks:
            in_degree[task_id] = len(self.reverse_graph[task_id])

        # Find all tasks with no dependencies
        queue = deque([task_id for task_id in self.tasks if in_degree[task_id] == 0])
        result = []

        while queue:
            # Sort queue by priority for optimal ordering
            sorted_queue = sorted(
                queue, key=lambda tid: (-self._get_priority_value(self.tasks[tid].priority), self.tasks[tid].created_at)
            )

            current = sorted_queue[0]
            queue.remove(current)
            result.append(current)

            # Reduce in-degree for dependent tasks
            for dependent in self.dependency_graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for circular dependencies
        if len(result) != len(self.tasks):
            cycles = self.detect_circular_dependencies()
            raise ValueError(f"Circular dependencies detected: {cycles}")

        return result

    def detect_circular_dependencies(self) -> list[list[str]]:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(task_id, path):
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)

            for dependent in self.dependency_graph[task_id]:
                if dependent not in visited:
                    if dfs(dependent, path):
                        return True
                elif dependent in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dependent)
                    cycle = path[cycle_start:] + [dependent]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(task_id)
            return False

        for task_id in self.tasks:
            if task_id not in visited:
                dfs(task_id, [])

        return cycles

    def find_critical_path(self) -> tuple[list[str], float]:
        """Find the critical path through tasks (longest path by time)"""
        # Ensure we have execution order
        try:
            execution_order = self.get_execution_order()
        except ValueError:
            return [], 0.0

        # Dynamic programming to find longest path
        longest_time = defaultdict(float)
        predecessor = {}

        for task_id in execution_order:
            task = self.tasks[task_id]
            task_time = task.estimated_hours or 1.0  # Default 1 hour if not specified

            # Find maximum time from all prerequisites
            max_prerequisite_time = 0.0
            max_predecessor = None

            for prereq_id in self.reverse_graph[task_id]:
                if prereq_id in longest_time:
                    if longest_time[prereq_id] > max_prerequisite_time:
                        max_prerequisite_time = longest_time[prereq_id]
                        max_predecessor = prereq_id

            longest_time[task_id] = max_prerequisite_time + task_time
            if max_predecessor:
                predecessor[task_id] = max_predecessor

        # Find task with maximum total time
        if not longest_time:
            return [], 0.0

        end_task = max(longest_time.keys(), key=lambda k: longest_time[k])
        total_time = longest_time[end_task]

        # Reconstruct path
        path = []
        current = end_task
        while current:
            path.append(current)
            current = predecessor.get(current)

        path.reverse()

        return path, total_time

    def get_parallel_execution_plan(self) -> list[list[str]]:
        """Get tasks that can be executed in parallel"""
        execution_order = self.get_execution_order()
        completed = set()
        stages = []

        remaining = set(execution_order)

        while remaining:
            # Find all tasks that can be executed now
            stage = []
            for task_id in remaining:
                # Check if all prerequisites are completed
                if all(prereq in completed for prereq in self.reverse_graph[task_id]):
                    stage.append(task_id)

            if not stage:
                # This shouldn't happen if dependency graph is valid
                break

            stages.append(stage)
            completed.update(stage)
            remaining.difference_update(stage)

        return stages

    def _get_priority_value(self, priority) -> int:
        """Convert priority enum to numeric value"""
        priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        return priority_map.get(priority.value, 2)

    def analyze_task_impact(self, task_id: str) -> dict:
        """Analyze the impact of a task on the overall project"""
        if task_id not in self.tasks:
            return {}

        # Direct dependents
        direct_dependents = list(self.dependency_graph[task_id])

        # All downstream tasks (transitive closure)
        all_dependents = set()
        queue = deque(direct_dependents)

        while queue:
            current = queue.popleft()
            if current not in all_dependents:
                all_dependents.add(current)
                queue.extend(self.dependency_graph[current])

        # Calculate time impact
        task = self.tasks[task_id]
        direct_time_impact = task.estimated_hours or 1.0

        total_time_impact = direct_time_impact
        for dep_id in all_dependents:
            dep_task = self.tasks[dep_id]
            total_time_impact += dep_task.estimated_hours or 1.0

        # Check if task is on critical path
        critical_path, _ = self.find_critical_path()
        is_critical = task_id in critical_path

        return {
            "task_id": task_id,
            "direct_dependents": direct_dependents,
            "total_dependents": len(all_dependents),
            "all_dependent_tasks": list(all_dependents),
            "direct_time_impact": direct_time_impact,
            "total_time_impact": total_time_impact,
            "is_on_critical_path": is_critical,
            "blocking_score": len(all_dependents) * (3 if is_critical else 1),
        }
