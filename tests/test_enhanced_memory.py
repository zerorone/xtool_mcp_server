"""Tests for enhanced memory functionality"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.conversation_memory import (
    _load_memory_layer,
    add_turn_with_memory,
    detect_environment,
    recall_memory,
    save_memory,
)


class TestEnhancedMemory:
    """Test enhanced memory system functionality"""

    @pytest.fixture
    def temp_memory_dir(self):
        """Create a temporary directory for memory storage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_env_vars(self, temp_memory_dir):
        """Mock environment variables for testing"""
        env_vars = {
            "ENABLE_ENHANCED_MEMORY": "true",
            "MEMORY_STORAGE_PATH": temp_memory_dir,
            "MEMORY_AUTO_DETECT_ENV": "true",
            "MEMORY_AUTO_SAVE": "true",
        }
        with patch.dict(os.environ, env_vars):
            # Need to reload the module to pick up new env vars
            import importlib

            import utils.conversation_memory

            importlib.reload(utils.conversation_memory)
            yield
            # Reload again to restore original state
            importlib.reload(utils.conversation_memory)

    def test_save_memory_basic(self, mock_env_vars, temp_memory_dir):
        """Test basic memory saving functionality"""
        # Save to global layer
        key = save_memory(content="This is a test memory", layer="global", metadata={"type": "test"})

        assert key.startswith("mem_")

        # Check that memory was saved to disk
        global_path = Path(temp_memory_dir) / "global_memory.json"
        assert global_path.exists()

        with open(global_path) as f:
            data = json.load(f)
            assert key in data
            assert data[key]["content"] == "This is a test memory"
            assert data[key]["metadata"]["type"] == "test"

    def test_save_memory_with_custom_key(self, mock_env_vars, temp_memory_dir):
        """Test saving memory with a custom key"""
        custom_key = "my_custom_key"
        key = save_memory(content="Custom key memory", layer="project", key=custom_key)

        assert key == custom_key

        # Verify it was saved
        project_path = Path(temp_memory_dir) / "project_memory.json"
        assert project_path.exists()

        with open(project_path) as f:
            data = json.load(f)
            assert custom_key in data

    def test_recall_memory_basic(self, mock_env_vars, temp_memory_dir):
        """Test basic memory recall functionality"""
        # Save some memories
        save_memory("Architecture decision: Use microservices", "global", metadata={"type": "architecture"})
        save_memory("Bug: NPE in UserService", "project", metadata={"type": "bug"})
        save_memory("Current task: Implement auth", "session", metadata={"type": "task"})

        # Recall all memories
        memories = recall_memory()
        assert len(memories) >= 2  # Session might not persist in test

        # Recall with query
        arch_memories = recall_memory(query="architecture")
        assert len(arch_memories) >= 1
        assert "microservices" in arch_memories[0]["content"]

        # Recall with layer filter
        project_memories = recall_memory(layer="project")
        assert all(m["layer"] == "project" for m in project_memories)

        # Recall with metadata filter
        bug_memories = recall_memory(filters={"type": "bug"})
        assert len(bug_memories) >= 1
        assert "NPE" in bug_memories[0]["content"]

    def test_memory_layer_limits(self, mock_env_vars, temp_memory_dir):
        """Test that memory layers respect max item limits"""
        # Patch MEMORY_LAYERS directly in the module
        import utils.conversation_memory

        original_layers = utils.conversation_memory.MEMORY_LAYERS.copy()

        try:
            # Set a small limit for testing
            utils.conversation_memory.MEMORY_LAYERS["global"]["max_items"] = 3

            # Save more than the limit
            keys = []
            for i in range(5):
                key = save_memory(f"Memory {i}", "global")
                keys.append(key)

            # Check that only the last 3 are kept
            memories = _load_memory_layer("global")
            assert len(memories) == 3
            assert keys[0] not in memories  # First one should be removed
            assert keys[1] not in memories  # Second one should be removed
            assert keys[2] in memories  # Last three should remain
            assert keys[3] in memories
            assert keys[4] in memories
        finally:
            # Restore original MEMORY_LAYERS
            utils.conversation_memory.MEMORY_LAYERS = original_layers

    def test_detect_environment(self, mock_env_vars, temp_memory_dir):
        """Test environment detection functionality"""
        with tempfile.TemporaryDirectory() as project_dir:
            # Create some project files
            project_path = Path(project_dir)
            (project_path / "README.md").touch()
            (project_path / "requirements.txt").touch()
            (project_path / "TODO.md").write_text("- [ ] Implement feature X")

            # Create a git directory
            git_dir = project_path / ".git"
            git_dir.mkdir()
            (git_dir / "HEAD").write_text("ref: refs/heads/main")

            # Detect environment
            env_info = detect_environment(str(project_path))

            assert env_info["project_root"] == str(project_path)
            assert env_info["git_info"]["branch"] == "main"
            assert "README.md" in env_info["files"]
            assert "requirements.txt" in env_info["files"]
            assert any("TODO.md" in todo for todo in env_info["todos"])

            # Check that it was saved to memory
            memories = recall_memory(filters={"type": "environment"})
            assert len(memories) >= 1

    def test_add_turn_with_memory(self, mock_env_vars):
        """Test enhanced add_turn functionality"""
        with patch("utils.conversation_memory.add_turn") as mock_add_turn:
            mock_add_turn.return_value = True

            # Add a turn that should go to global memory
            success = add_turn_with_memory(
                thread_id="test-thread",
                role="assistant",
                content="The best practice for this architecture is to use event sourcing",
                tool_name="analyze",
            )

            assert success
            mock_add_turn.assert_called_once()

            # Check that memory was saved
            memories = recall_memory(query="architecture")
            assert any("event sourcing" in m["content"] for m in memories)

    def test_memory_disabled(self):
        """Test that memory functions work gracefully when disabled"""
        with patch.dict(os.environ, {"ENABLE_ENHANCED_MEMORY": "false"}):
            import importlib

            import utils.conversation_memory

            importlib.reload(utils.conversation_memory)

            # These should all return empty/default values
            key = save_memory("Test", "global")
            assert key == ""

            memories = recall_memory()
            assert memories == []

            env_info = detect_environment("/tmp")
            assert env_info == {}

            # Cleanup
            importlib.reload(utils.conversation_memory)

    def test_session_memory(self, mock_env_vars):
        """Test session memory (non-persistent) behavior"""
        # Mock the storage backend
        mock_storage = MagicMock()

        with patch("utils.conversation_memory.get_storage", return_value=mock_storage):
            # Save to session layer
            key = save_memory(content="Session memory test", layer="session", metadata={"session_id": "123"})

            assert key.startswith("mem_")

            # Verify it was stored in the storage backend, not on disk
            mock_storage.setex.assert_called_once()
            call_args = mock_storage.setex.call_args
            assert call_args[0][0] == f"session_memory:{key}"
            assert "Session memory test" in call_args[0][2]
