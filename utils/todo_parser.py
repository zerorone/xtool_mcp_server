"""
TODO File Parser and Task Management System

This module provides intelligent TODO file parsing and task management capabilities
for the Zen MCP Server. It enables task-driven development with dependency analysis,
branch management, and progress tracking.

Key Features:
- Parse Markdown TODO files with checkbox syntax
- Extract task hierarchies and dependencies
- Track task status and progress
- Support task branching and context switching
- Integration with thinking patterns for task approach
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from utils.context_manager import TaskContextManager
from utils.conversation_memory import recall_memory, save_memory
from utils.dependency_analyzer import DependencyAnalyzer
from utils.thinking_patterns import thinking_registry


class TaskStatus(Enum):
    """Task completion status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TaskDependency:
    """Represents a dependency between tasks"""

    task_id: str
    dependency_type: str = "requires"  # requires, blocks, related
    notes: Optional[str] = None


@dataclass
class TaskContext:
    """Context information for task execution"""

    files: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    thinking_patterns: list[str] = field(default_factory=list)
    memory_keys: list[str] = field(default_factory=list)


@dataclass
class Task:
    """
    Represents a single task with all its metadata
    """

    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)
    dependencies: list[TaskDependency] = field(default_factory=list)
    context: TaskContext = field(default_factory=TaskContext)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "dependencies": [
                {"task_id": dep.task_id, "type": dep.dependency_type, "notes": dep.notes} for dep in self.dependencies
            ],
            "context": {
                "files": self.context.files,
                "commands": self.context.commands,
                "notes": self.context.notes,
                "thinking_patterns": self.context.thinking_patterns,
                "memory_keys": self.context.memory_keys,
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        task = cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", "medium")),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            completed_at=data.get("completed_at"),
            estimated_hours=data.get("estimated_hours"),
            actual_hours=data.get("actual_hours"),
            tags=data.get("tags", []),
        )

        # Parse dependencies
        for dep_data in data.get("dependencies", []):
            task.dependencies.append(
                TaskDependency(
                    task_id=dep_data["task_id"],
                    dependency_type=dep_data.get("type", "requires"),
                    notes=dep_data.get("notes"),
                )
            )

        # Parse context
        context_data = data.get("context", {})
        task.context = TaskContext(
            files=context_data.get("files", []),
            commands=context_data.get("commands", []),
            notes=context_data.get("notes", []),
            thinking_patterns=context_data.get("thinking_patterns", []),
            memory_keys=context_data.get("memory_keys", []),
        )

        return task


class TodoParser:
    """
    Parses TODO files and extracts task information
    """

    # Regex patterns for parsing
    TASK_PATTERN = re.compile(r"^(\s*)-\s*\[([ xX])\]\s*(.+)$", re.MULTILINE)
    PRIORITY_PATTERN = re.compile(r"\[([!]{1,3})\]")  # [!] low, [!!] medium, [!!!] high
    TAG_PATTERN = re.compile(r"#(\w+)")
    TIME_PATTERN = re.compile(r"\((\d+(?:\.\d+)?)\s*h(?:ours?)?\)")
    EMOJI_PATTERN = re.compile(r"^([🔍🧠📝💾🏗️✅🧪📋👀🐛🤔🔢🚀📚🔄🎯💡❓🌟💬🤝🎉📊📈🔔⚡🗄️🛡️🎭])\s*")

    # Emoji to tag mapping
    EMOJI_TAGS = {
        "🔍": "investigation",
        "🧠": "thinking",
        "📝": "documentation",
        "💾": "storage",
        "🏗️": "architecture",
        "✅": "testing",
        "🧪": "experiment",
        "📋": "planning",
        "👀": "review",
        "🐛": "debugging",
        "🤔": "analysis",
        "🔢": "versioning",
        "🚀": "deployment",
        "📚": "learning",
        "🔄": "refactoring",
        "🎯": "milestone",
        "💡": "idea",
        "❓": "question",
        "🌟": "feature",
        "💬": "communication",
        "🤝": "collaboration",
        "🎉": "celebration",
        "📊": "analytics",
        "📈": "performance",
        "🔔": "notification",
        "⚡": "optimization",
        "🗄️": "database",
        "🛡️": "security",
        "🎭": "simulation",
    }

    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.task_counter = 0

    def parse_file(self, file_path: Union[str, Path]) -> list[Task]:
        """
        Parse a TODO file and extract tasks

        Args:
            file_path: Path to the TODO file

        Returns:
            List of parsed tasks
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"TODO file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        return self.parse_content(content)

    def parse_content(self, content: str) -> list[Task]:
        """
        Parse TODO content and extract tasks

        Args:
            content: TODO file content

        Returns:
            List of parsed tasks
        """
        self.tasks.clear()
        self.task_counter = 0
        self.task_title_map = {}  # Map task titles to IDs for dependency parsing

        lines = content.split("\n")
        current_section = None
        task_stack = []  # Stack to track task hierarchy
        in_dependencies_section = False

        # First pass: parse tasks
        for _i, line in enumerate(lines):
            # Check for Dependencies section
            if line.strip().lower() in ["## dependencies", "### dependencies"]:
                in_dependencies_section = True
                continue

            # Check for section headers
            if line.startswith("##") or line.startswith("###"):
                current_section = line.strip("#").strip()
                if not line.strip().lower().endswith("dependencies"):
                    in_dependencies_section = False
                continue

            # Skip dependency lines during task parsing
            if in_dependencies_section:
                continue

            # Check for task lines
            match = self.TASK_PATTERN.match(line)
            if match:
                indent = len(match.group(1))
                checked = match.group(2).lower() == "x"
                task_text = match.group(3)

                # Create task
                task = self._create_task(task_text, checked, current_section)

                # Determine parent based on indentation
                while task_stack and task_stack[-1][1] >= indent:
                    task_stack.pop()

                if task_stack:
                    parent_task = task_stack[-1][0]
                    task.parent_id = parent_task.id
                    parent_task.children_ids.append(task.id)

                task_stack.append((task, indent))
                self.tasks[task.id] = task

                # Store title mapping for dependency parsing
                clean_title = self._clean_task_title(task.title)
                self.task_title_map[clean_title.lower()] = task.id

        # Second pass: parse dependencies
        self._parse_dependencies(lines)

        return list(self.tasks.values())

    def _create_task(self, text: str, completed: bool, section: Optional[str]) -> Task:
        """Create a task from parsed text"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"

        # Extract emoji and tags
        tags = []
        emoji_match = self.EMOJI_PATTERN.match(text)
        if emoji_match:
            emoji = emoji_match.group(1)
            if emoji in self.EMOJI_TAGS:
                tags.append(self.EMOJI_TAGS[emoji])
            text = text[len(emoji_match.group(0)) :]

        # Extract hashtags
        hashtags = self.TAG_PATTERN.findall(text)
        tags.extend(hashtags)

        # Extract priority
        priority = TaskPriority.MEDIUM
        priority_match = self.PRIORITY_PATTERN.search(text)
        if priority_match:
            exclamations = len(priority_match.group(1))
            if exclamations >= 3:
                priority = TaskPriority.HIGH
            elif exclamations == 2:
                priority = TaskPriority.MEDIUM
            else:
                priority = TaskPriority.LOW
            text = self.PRIORITY_PATTERN.sub("", text)

        # Extract time estimate
        estimated_hours = None
        time_match = self.TIME_PATTERN.search(text)
        if time_match:
            estimated_hours = float(time_match.group(1))
            text = self.TIME_PATTERN.sub("", text)

        # Clean up the title
        title = text.strip()

        # Add section as tag if present
        if section:
            tags.append(section.lower().replace(" ", "_"))

        # Create task
        task = Task(
            id=task_id,
            title=title,
            status=TaskStatus.COMPLETED if completed else TaskStatus.PENDING,
            priority=priority,
            tags=list(set(tags)),  # Remove duplicates
            estimated_hours=estimated_hours,
        )

        if completed:
            task.completed_at = datetime.now(timezone.utc).isoformat()

        return task

    def _clean_task_title(self, title: str) -> str:
        """Clean task title for matching"""
        # Remove emojis, tags, and extra whitespace
        clean = re.sub(self.EMOJI_PATTERN, "", title)
        clean = re.sub(self.TAG_PATTERN, "", clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def _parse_dependencies(self, lines: list[str]):
        """Parse dependency declarations from TODO file"""
        in_dependencies = False
        dependency_pattern = re.compile(
            r'^\s*-\s*(?:Task\s+)?["\']?(.+?)["\']?\s+(requires?|blocks?|depends?\s+on|after)\s+["\']?(.+?)["\']?\s*$',
            re.IGNORECASE,
        )

        for line in lines:
            # Check if we're in dependencies section
            if line.strip().lower() in ["## dependencies", "### dependencies", "dependencies:"]:
                in_dependencies = True
                continue
            elif line.startswith("##") or line.startswith("###"):
                in_dependencies = False
                continue

            if not in_dependencies:
                continue

            # Parse dependency line
            match = dependency_pattern.match(line)
            if match:
                task_name = match.group(1).strip()
                relation = match.group(2).strip().lower()
                dependency_name = match.group(3).strip()

                # Normalize relation
                if relation in ["requires", "depends on", "after"]:
                    dep_type = "requires"
                elif relation == "blocks":
                    dep_type = "blocks"
                else:
                    dep_type = "requires"

                # Find tasks by title
                task_id = self._find_task_by_title(task_name)
                dep_task_id = self._find_task_by_title(dependency_name)

                if task_id and dep_task_id and task_id in self.tasks:
                    task = self.tasks[task_id]
                    # Check if dependency already exists
                    existing = any(dep.task_id == dep_task_id for dep in task.dependencies)
                    if not existing:
                        task.dependencies.append(
                            TaskDependency(
                                task_id=dep_task_id, dependency_type=dep_type, notes="Parsed from Dependencies section"
                            )
                        )

    def _find_task_by_title(self, title: str) -> Optional[str]:
        """Find task ID by title (fuzzy matching)"""
        title_lower = title.lower().strip()
        clean_title = self._clean_task_title(title).lower()

        # Try exact match first
        if title_lower in self.task_title_map:
            return self.task_title_map[title_lower]
        if clean_title in self.task_title_map:
            return self.task_title_map[clean_title]

        # Try partial matches
        for stored_title, task_id in self.task_title_map.items():
            if (
                clean_title in stored_title
                or stored_title in clean_title
                or self._fuzzy_title_match(clean_title, stored_title)
            ):
                return task_id

        return None

    def _fuzzy_title_match(self, title1: str, title2: str) -> bool:
        """Fuzzy matching for task titles"""
        words1 = {w for w in title1.split() if len(w) > 2}
        words2 = {w for w in title2.split() if len(w) > 2}

        if not words1 or not words2:
            return False

        common = words1.intersection(words2)
        return len(common) >= min(2, min(len(words1), len(words2)))


class TaskManager:
    """
    Manages tasks with dependency tracking and intelligent workflow
    """

    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.active_branch: Optional[str] = "main"
        self.branches: dict[str, list[str]] = {"main": []}  # branch -> task_ids
        self.context_stack: list[str] = []  # Stack of task contexts
        self.dependency_analyzer = DependencyAnalyzer()
        self.context_manager = TaskContextManager()

    def add_task(self, task: Task) -> str:
        """Add a task to the manager"""
        self.tasks[task.id] = task

        # Add to current branch
        if self.active_branch and self.active_branch in self.branches:
            self.branches[self.active_branch].append(task.id)

        # Save to memory
        self._save_task_to_memory(task)

        # Update dependency analyzer
        self.dependency_analyzer.add_tasks([task])

        return task.id

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update task status"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = status
        task.updated_at = datetime.now(timezone.utc).isoformat()

        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc).isoformat()
            # Recommend thinking patterns for completed tasks
            self._recommend_patterns_for_next_tasks(task)

        # Save update to memory
        self._save_task_to_memory(task)

        return True

    def get_task_dependencies(self, task_id: str) -> list[Task]:
        """Get all dependencies for a task"""
        if task_id not in self.tasks:
            return []

        task = self.tasks[task_id]
        dependencies = []

        for dep in task.dependencies:
            if dep.task_id in self.tasks:
                dependencies.append(self.tasks[dep.task_id])

        return dependencies

    def get_blocked_tasks(self) -> list[Task]:
        """Get all tasks that are blocked by dependencies"""
        blocked = []

        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                dependencies = self.get_task_dependencies(task.id)
                if any(dep.status != TaskStatus.COMPLETED for dep in dependencies):
                    blocked.append(task)

        return blocked

    def get_ready_tasks(self) -> list[Task]:
        """Get tasks that are ready to be worked on"""
        ready = []

        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                dependencies = self.get_task_dependencies(task.id)
                if all(dep.status == TaskStatus.COMPLETED for dep in dependencies):
                    ready.append(task)

        # Sort by priority
        ready.sort(key=lambda t: (t.priority.value, t.created_at), reverse=True)

        return ready

    def create_branch(self, branch_name: str, from_branch: Optional[str] = None) -> bool:
        """Create a new task branch"""
        if branch_name in self.branches:
            return False

        if from_branch and from_branch in self.branches:
            # Copy tasks from source branch
            self.branches[branch_name] = self.branches[from_branch].copy()
        else:
            self.branches[branch_name] = []

        return True

    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different task branch"""
        if branch_name not in self.branches:
            return False

        # Save current context
        if self.active_branch:
            self._save_branch_context(self.active_branch)

        self.active_branch = branch_name

        # Restore new branch context
        self._restore_branch_context(branch_name)

        return True

    def push_context(self, task_id: str) -> dict[str, Any]:
        """Push task context onto the stack with full context capture"""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}

        # Switch context using context manager
        switch_result = self.context_manager.switch_context(task_id, self.active_branch)

        # Update stack
        self.context_stack.append(task_id)

        return {"success": True, "task_id": task_id, "switch_details": switch_result}

    def pop_context(self) -> dict[str, Any]:
        """Pop task context from the stack and restore previous"""
        if not self.context_stack:
            return {"success": False, "error": "No context to pop"}

        # Remove current context
        current_task_id = self.context_stack.pop()

        # Restore previous context if exists
        if self.context_stack:
            previous_task_id = self.context_stack[-1]
            switch_result = self.context_manager.switch_context(previous_task_id, self.active_branch)

            return {
                "success": True,
                "popped_task": current_task_id,
                "restored_task": previous_task_id,
                "switch_details": switch_result,
            }
        else:
            return {"success": True, "popped_task": current_task_id, "restored_task": None}

    def get_current_context(self) -> Optional[Task]:
        """Get the current task context"""
        if not self.context_stack:
            return None

        task_id = self.context_stack[-1]
        return self.tasks.get(task_id)

    def get_progress_report(self) -> dict[str, Any]:
        """Generate a progress report"""
        total_tasks = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        blocked = len(self.get_blocked_tasks())

        # Calculate time metrics
        total_estimated = sum(t.estimated_hours or 0 for t in self.tasks.values())
        total_actual = sum(t.actual_hours or 0 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "pending": total_tasks - completed - in_progress,
            "blocked": blocked,
            "completion_percentage": (completed / total_tasks * 100) if total_tasks > 0 else 0,
            "time_metrics": {
                "total_estimated_hours": total_estimated,
                "total_actual_hours": total_actual,
                "efficiency": (total_estimated / total_actual * 100) if total_actual > 0 else None,
            },
            "by_priority": {
                priority.value: sum(1 for t in self.tasks.values() if t.priority == priority)
                for priority in TaskPriority
            },
            "by_tag": self._count_by_tag(),
        }

    def _count_by_tag(self) -> dict[str, int]:
        """Count tasks by tag"""
        tag_counts = {}
        for task in self.tasks.values():
            for tag in task.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts

    def _save_task_to_memory(self, task: Task):
        """Save task to memory system"""
        save_memory(
            content=json.dumps(task.to_dict()),
            layer="project",
            metadata={"type": "task", "task_id": task.id, "status": task.status.value, "branch": self.active_branch},
            key=f"task_{task.id}",
        )

    def _save_branch_context(self, branch_name: str):
        """Save branch context to memory"""
        context = {
            "branch": branch_name,
            "task_ids": self.branches[branch_name],
            "context_stack": self.context_stack.copy(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        save_memory(
            content=json.dumps(context),
            layer="session",
            metadata={"type": "branch_context", "branch": branch_name},
            key=f"branch_context_{branch_name}",
        )

    def _restore_branch_context(self, branch_name: str):
        """Restore branch context from memory"""
        memories = recall_memory(
            query=f"branch_context_{branch_name}", filters={"type": "branch_context", "branch": branch_name}, limit=1
        )

        if memories:
            content = memories[0].get("content", {})
            if isinstance(content, str):
                content = json.loads(content)

            self.context_stack = content.get("context_stack", [])

    def _recommend_patterns_for_next_tasks(self, completed_task: Task):
        """Recommend thinking patterns for next tasks based on completed task"""
        # Get ready tasks
        ready_tasks = self.get_ready_tasks()

        for next_task in ready_tasks[:3]:  # Top 3 priority tasks
            # Infer problem type from task
            problem_type = self._infer_problem_type(next_task)

            # Get recommended patterns
            patterns = thinking_registry.select_patterns(
                context=next_task.title, problem_type=problem_type, max_patterns=2
            )

            # Save recommendations
            if patterns:
                next_task.context.thinking_patterns = [p.name for p in patterns]
                save_memory(
                    content=f"Recommended patterns for '{next_task.title}': {', '.join(p.name for p in patterns)}",
                    layer="session",
                    metadata={
                        "type": "pattern_recommendation",
                        "task_id": next_task.id,
                        "patterns": [p.name for p in patterns],
                    },
                )

    def _infer_problem_type(self, task: Task) -> str:
        """Infer problem type from task"""
        title_lower = task.title.lower()
        tags_str = " ".join(task.tags).lower()

        if any(word in title_lower or word in tags_str for word in ["bug", "fix", "error", "debug"]):
            return "debugging"
        elif any(word in title_lower or word in tags_str for word in ["design", "architecture", "structure"]):
            return "architecture"
        elif any(word in title_lower or word in tags_str for word in ["optimize", "performance", "speed"]):
            return "optimization"
        elif any(word in title_lower or word in tags_str for word in ["test", "verify", "validate"]):
            return "testing"
        elif any(word in title_lower or word in tags_str for word in ["plan", "organize", "schedule"]):
            return "planning"
        else:
            return "general"

    def analyze_dependencies(self) -> dict[str, Any]:
        """Analyze task dependencies and provide insights"""
        # Rebuild dependency analyzer with all tasks
        self.dependency_analyzer = DependencyAnalyzer()
        self.dependency_analyzer.add_tasks(list(self.tasks.values()))

        # Detect implicit dependencies
        self.dependency_analyzer.detect_implicit_dependencies()

        # Get execution insights
        try:
            execution_order = self.dependency_analyzer.get_execution_order()
            critical_path, critical_time = self.dependency_analyzer.find_critical_path()
            parallel_stages = self.dependency_analyzer.get_parallel_execution_plan()
        except ValueError as e:
            # Handle circular dependencies
            cycles = self.dependency_analyzer.detect_circular_dependencies()
            return {"error": "circular_dependencies", "cycles": cycles, "message": str(e)}

        return {
            "execution_order": execution_order,
            "critical_path": {"tasks": critical_path, "total_time": critical_time},
            "parallel_stages": parallel_stages,
            "stats": {
                "total_tasks": len(self.tasks),
                "can_start_now": len(parallel_stages[0]) if parallel_stages else 0,
                "critical_path_length": len(critical_path),
                "estimated_completion_time": critical_time,
            },
        }

    def get_task_impact(self, task_id: str) -> dict[str, Any]:
        """Get impact analysis for a specific task"""
        if task_id not in self.tasks:
            return {"error": "Task not found"}

        # Ensure dependency analyzer is up to date
        self.dependency_analyzer = DependencyAnalyzer()
        self.dependency_analyzer.add_tasks(list(self.tasks.values()))

        return self.dependency_analyzer.analyze_task_impact(task_id)

    def get_optimal_next_tasks(self, max_tasks: int = 3) -> list[Task]:
        """Get optimal tasks to work on next based on dependencies and priority"""
        # Get ready tasks
        ready_tasks = self.get_ready_tasks()

        if not ready_tasks:
            return []

        # Analyze impact for each ready task
        task_scores = []
        for task in ready_tasks:
            impact = self.get_task_impact(task.id)

            # Calculate score based on:
            # - Priority (40%)
            # - Blocking score (30%)
            # - Time estimate (20%)
            # - Tag relevance (10%)
            priority_score = self._get_priority_value(task.priority) / 4.0
            blocking_score = min(impact.get("blocking_score", 0) / 10.0, 1.0)
            time_score = 1.0 - min((task.estimated_hours or 1) / 10.0, 0.9)
            tag_score = 0.5 if any(tag in ["critical", "urgent", "blocker"] for tag in task.tags) else 0.0

            total_score = priority_score * 0.4 + blocking_score * 0.3 + time_score * 0.2 + tag_score * 0.1

            task_scores.append((task, total_score, impact))

        # Sort by score
        task_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top tasks
        return [item[0] for item in task_scores[:max_tasks]]

    def _get_priority_value(self, priority) -> int:
        """Convert priority enum to numeric value"""
        priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        return priority_map.get(priority.value, 2)

    def get_context_diff(self, task1_id: str, task2_id: str) -> dict[str, Any]:
        """Get differences between two task contexts"""
        return self.context_manager.get_context_diff(task1_id, task2_id)

    def track_file_modification(self, file_path: str):
        """Track that a file has been modified in current task context"""
        self.context_manager.track_file_modification(file_path)
