"""
Task Context Management System

This module provides advanced context switching capabilities for the TODO-driven
development system. It can capture and restore complete task execution contexts
including file states, environment variables, command history, and more.
"""

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from utils.conversation_memory import recall_memory, save_memory


def get_file_hash(file_path: str) -> str:
    """Calculate hash of a file"""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


@dataclass
class FileContext:
    """Represents the context of a file being worked on"""

    path: str
    hash: str
    last_modified: str
    cursor_position: Optional[tuple[int, int]] = None  # line, column
    open_in_editor: bool = False
    unsaved_changes: Optional[str] = None


@dataclass
class EnvironmentContext:
    """Represents environment state"""

    working_directory: str
    python_path: Optional[str] = None
    virtual_env: Optional[str] = None
    env_vars: dict[str, str] = field(default_factory=dict)
    installed_packages: list[str] = field(default_factory=list)


@dataclass
class CommandContext:
    """Represents command execution context"""

    history: list[str] = field(default_factory=list)
    last_exit_code: Optional[int] = None
    shell_type: str = "bash"
    aliases: dict[str, str] = field(default_factory=dict)


@dataclass
class TaskExecutionContext:
    """Complete context for task execution"""

    task_id: str
    branch_id: Optional[str]
    environment: EnvironmentContext
    files: list[FileContext] = field(default_factory=list)
    commands: CommandContext = field(default_factory=CommandContext)
    thinking_patterns: list[str] = field(default_factory=list)
    memory_keys: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "task_id": self.task_id,
            "branch_id": self.branch_id,
            "environment": {
                "working_directory": self.environment.working_directory,
                "python_path": self.environment.python_path,
                "virtual_env": self.environment.virtual_env,
                "env_vars": self.environment.env_vars,
                "installed_packages": self.environment.installed_packages,
            },
            "files": [
                {
                    "path": f.path,
                    "hash": f.hash,
                    "last_modified": f.last_modified,
                    "cursor_position": f.cursor_position,
                    "open_in_editor": f.open_in_editor,
                    "unsaved_changes": f.unsaved_changes,
                }
                for f in self.files
            ],
            "commands": {
                "history": self.commands.history,
                "last_exit_code": self.commands.last_exit_code,
                "shell_type": self.commands.shell_type,
                "aliases": self.commands.aliases,
            },
            "thinking_patterns": self.thinking_patterns,
            "memory_keys": self.memory_keys,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskExecutionContext":
        """Create context from dictionary"""
        env_data = data.get("environment", {})
        environment = EnvironmentContext(
            working_directory=env_data.get("working_directory", os.getcwd()),
            python_path=env_data.get("python_path"),
            virtual_env=env_data.get("virtual_env"),
            env_vars=env_data.get("env_vars", {}),
            installed_packages=env_data.get("installed_packages", []),
        )

        files = []
        for f_data in data.get("files", []):
            files.append(
                FileContext(
                    path=f_data["path"],
                    hash=f_data["hash"],
                    last_modified=f_data["last_modified"],
                    cursor_position=f_data.get("cursor_position"),
                    open_in_editor=f_data.get("open_in_editor", False),
                    unsaved_changes=f_data.get("unsaved_changes"),
                )
            )

        cmd_data = data.get("commands", {})
        commands = CommandContext(
            history=cmd_data.get("history", []),
            last_exit_code=cmd_data.get("last_exit_code"),
            shell_type=cmd_data.get("shell_type", "bash"),
            aliases=cmd_data.get("aliases", {}),
        )

        return cls(
            task_id=data["task_id"],
            branch_id=data.get("branch_id"),
            environment=environment,
            files=files,
            commands=commands,
            thinking_patterns=data.get("thinking_patterns", []),
            memory_keys=data.get("memory_keys", []),
            notes=data.get("notes", []),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )


class TaskContextManager:
    """Manages task execution contexts with advanced capture and restore"""

    def __init__(self):
        self.active_context: Optional[TaskExecutionContext] = None
        self.context_stack: list[str] = []  # Stack of context IDs
        self.modified_files: set[str] = set()  # Track files modified in current context

    def capture_context(self, task_id: str, branch_id: Optional[str] = None) -> TaskExecutionContext:
        """Capture current execution context"""
        # Capture environment
        environment = self._capture_environment()

        # Capture file states
        files = self._capture_file_states()

        # Capture command history
        commands = self._capture_command_history()

        # Get relevant memory keys
        memory_keys = self._get_relevant_memory_keys(task_id)

        # Create context
        context = TaskExecutionContext(
            task_id=task_id,
            branch_id=branch_id,
            environment=environment,
            files=files,
            commands=commands,
            memory_keys=memory_keys,
        )

        # Save to memory
        self._save_context(context)

        return context

    def restore_context(self, context: TaskExecutionContext) -> dict[str, Any]:
        """Restore a previously captured context"""
        results = {"restored": [], "warnings": [], "errors": []}

        # Restore working directory
        if os.path.exists(context.environment.working_directory):
            os.chdir(context.environment.working_directory)
            results["restored"].append("working_directory")
        else:
            results["warnings"].append(f"Working directory not found: {context.environment.working_directory}")

        # Restore environment variables
        for key, value in context.environment.env_vars.items():
            os.environ[key] = value
        results["restored"].append(f"{len(context.environment.env_vars)} environment variables")

        # Check virtual environment
        if context.environment.virtual_env:
            if os.path.exists(context.environment.virtual_env):
                results["restored"].append("virtual_env_path")
            else:
                results["warnings"].append(f"Virtual env not found: {context.environment.virtual_env}")

        # Check file states
        files_changed = 0
        files_missing = 0
        for file_ctx in context.files:
            if os.path.exists(file_ctx.path):
                current_hash = get_file_hash(file_ctx.path)
                if current_hash != file_ctx.hash:
                    files_changed += 1
            else:
                files_missing += 1

        if files_changed:
            results["warnings"].append(f"{files_changed} files have been modified since context was saved")
        if files_missing:
            results["warnings"].append(f"{files_missing} files are missing")

        # Set active context
        self.active_context = context

        return results

    def switch_context(self, new_task_id: str, branch_id: Optional[str] = None) -> dict[str, Any]:
        """Switch from current context to a new task context"""
        results = {"saved_context": None, "restored_context": None, "status": "success"}

        # Save current context if active
        if self.active_context:
            saved = self.capture_context(self.active_context.task_id, self.active_context.branch_id)
            results["saved_context"] = saved.task_id
            self.context_stack.append(saved.task_id)

        # Try to restore new context
        existing_context = self._load_context(new_task_id)
        if existing_context:
            restore_results = self.restore_context(existing_context)
            results["restored_context"] = new_task_id
            results["restore_details"] = restore_results
        else:
            # Create new context
            new_context = self.capture_context(new_task_id, branch_id)
            self.active_context = new_context
            results["restored_context"] = "new_context_created"

        return results

    def get_context_diff(self, context1_id: str, context2_id: str) -> dict[str, Any]:
        """Compare two contexts and show differences"""
        ctx1 = self._load_context(context1_id)
        ctx2 = self._load_context(context2_id)

        if not ctx1 or not ctx2:
            return {"error": "One or both contexts not found"}

        diff = {
            "environment": {},
            "files": {"added": [], "removed": [], "modified": []},
            "commands": {"new_commands": []},
        }

        # Compare environments
        if ctx1.environment.working_directory != ctx2.environment.working_directory:
            diff["environment"]["working_directory"] = {
                "from": ctx1.environment.working_directory,
                "to": ctx2.environment.working_directory,
            }

        # Compare files
        ctx1_files = {f.path: f for f in ctx1.files}
        ctx2_files = {f.path: f for f in ctx2.files}

        for path in ctx2_files:
            if path not in ctx1_files:
                diff["files"]["added"].append(path)
            elif ctx2_files[path].hash != ctx1_files[path].hash:
                diff["files"]["modified"].append(path)

        for path in ctx1_files:
            if path not in ctx2_files:
                diff["files"]["removed"].append(path)

        # Compare command history
        if len(ctx2.commands.history) > len(ctx1.commands.history):
            diff["commands"]["new_commands"] = ctx2.commands.history[len(ctx1.commands.history) :]

        return diff

    def _capture_environment(self) -> EnvironmentContext:
        """Capture current environment state"""
        env = EnvironmentContext(
            working_directory=os.getcwd(),
            python_path=os.environ.get("PYTHONPATH"),
            virtual_env=os.environ.get("VIRTUAL_ENV"),
            env_vars={},
        )

        # Capture relevant environment variables
        relevant_vars = [
            "PATH",
            "PYTHONPATH",
            "VIRTUAL_ENV",
            "CONDA_DEFAULT_ENV",
            "NODE_ENV",
            "JAVA_HOME",
            "GOPATH",
            "CARGO_HOME",
        ]

        for var in relevant_vars:
            if var in os.environ:
                env.env_vars[var] = os.environ[var]

        # Try to capture installed packages
        try:
            result = subprocess.run(["pip", "freeze"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                env.installed_packages = result.stdout.strip().split("\n")
        except Exception:
            pass

        return env

    def _capture_file_states(self) -> list[FileContext]:
        """Capture states of recently accessed files"""
        files = []

        # Get files from modified set
        for file_path in self.modified_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                files.append(
                    FileContext(
                        path=file_path,
                        hash=get_file_hash(file_path),
                        last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    )
                )

        # Also check common project files
        common_files = [
            "README.md",
            "setup.py",
            "requirements.txt",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
        ]

        for filename in common_files:
            if os.path.exists(filename) and filename not in self.modified_files:
                stat = os.stat(filename)
                files.append(
                    FileContext(
                        path=filename,
                        hash=get_file_hash(filename),
                        last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    )
                )

        return files

    def _capture_command_history(self) -> CommandContext:
        """Capture command execution history"""
        cmd_context = CommandContext()

        # Try to read shell history
        history_files = [os.path.expanduser("~/.bash_history"), os.path.expanduser("~/.zsh_history")]

        for hist_file in history_files:
            if os.path.exists(hist_file):
                try:
                    with open(hist_file, encoding="utf-8", errors="ignore") as f:
                        # Get last 50 commands
                        lines = f.readlines()
                        cmd_context.history = [line.strip() for line in lines[-50:]]
                        cmd_context.shell_type = "zsh" if "zsh" in hist_file else "bash"
                    break
                except Exception:
                    pass

        return cmd_context

    def _get_relevant_memory_keys(self, task_id: str) -> list[str]:
        """Get memory keys relevant to the task"""
        # Query memories related to this task
        memories = recall_memory(query=task_id, filters={"task_id": task_id}, limit=10)

        keys = []
        for memory in memories:
            if "key" in memory:
                keys.append(memory["key"])

        return keys

    def _save_context(self, context: TaskExecutionContext):
        """Save context to memory"""
        save_memory(
            content=json.dumps(context.to_dict()),
            layer="session",
            metadata={"type": "task_context", "task_id": context.task_id, "branch_id": context.branch_id},
            key=f"context_{context.task_id}",
        )

    def _load_context(self, task_id: str) -> Optional[TaskExecutionContext]:
        """Load context from memory"""
        memories = recall_memory(
            query=f"context_{task_id}", filters={"type": "task_context", "task_id": task_id}, limit=1
        )

        if memories:
            content = memories[0].get("content")
            if content:
                if isinstance(content, str):
                    content = json.loads(content)
                return TaskExecutionContext.from_dict(content)

        return None

    def track_file_modification(self, file_path: str):
        """Track that a file has been modified in current context"""
        if self.active_context:
            self.modified_files.add(file_path)
