"""Tests for auto mode functionality"""

import importlib
import os
from unittest.mock import patch

import pytest

from tools.chat import ChatTool


class TestAutoMode:
    """Test auto mode configuration and behavior"""

    def test_auto_mode_detection(self):
        """Test that auto mode is detected correctly"""
        # Save original
        original = os.environ.get("DEFAULT_MODEL", "")

        try:
            # Test auto mode
            os.environ["DEFAULT_MODEL"] = "auto"
            import config

            importlib.reload(config)

            assert config.DEFAULT_MODEL == "auto"
            assert config.IS_AUTO_MODE is True

            # Test non-auto mode
            os.environ["DEFAULT_MODEL"] = "pro"
            importlib.reload(config)

            assert config.DEFAULT_MODEL == "pro"
            assert config.IS_AUTO_MODE is False

        finally:
            # Restore
            if original:
                os.environ["DEFAULT_MODEL"] = original
            else:
                os.environ.pop("DEFAULT_MODEL", None)
            importlib.reload(config)

    def test_model_capabilities_descriptions(self):
        """Test that model capabilities are properly defined in providers"""
        from providers.registry import ModelProviderRegistry

        # Get all providers with valid API keys and check their model descriptions
        enabled_provider_types = ModelProviderRegistry.get_available_providers_with_keys()
        models_with_descriptions = {}

        for provider_type in enabled_provider_types:
            provider = ModelProviderRegistry.get_provider(provider_type)
            if provider:
                for model_name, config in provider.SUPPORTED_MODELS.items():
                    # Skip alias entries (string values)
                    if isinstance(config, str):
                        continue

                    # Check that model has description
                    description = config.description if hasattr(config, "description") else ""
                    if description:
                        models_with_descriptions[model_name] = description

        # Check all expected models are present with meaningful descriptions
        expected_models = ["flash", "pro", "o3", "o3-mini", "o3-pro", "o4-mini"]
        for model in expected_models:
            # Model should exist somewhere in the providers
            # Note: Some models might not be available if API keys aren't configured
            if model in models_with_descriptions:
                assert isinstance(models_with_descriptions[model], str)
                assert len(models_with_descriptions[model]) > 50  # Meaningful description

    def test_tool_schema_in_auto_mode(self):
        """Test that tool schemas require model in auto mode"""
        # Save original
        original = os.environ.get("DEFAULT_MODEL", "")

        try:
            # Enable auto mode
            os.environ["DEFAULT_MODEL"] = "auto"
            import config

            importlib.reload(config)

            tool = ChatTool()
            schema = tool.get_input_schema()

            # Model should be required
            assert "model" in schema["required"]

            # Model field should have detailed descriptions
            model_schema = schema["properties"]["model"]
            assert "enum" in model_schema
            assert "flash" in model_schema["enum"]
            assert "select the most suitable model" in model_schema["description"]

        finally:
            # Restore
            if original:
                os.environ["DEFAULT_MODEL"] = original
            else:
                os.environ.pop("DEFAULT_MODEL", None)
            importlib.reload(config)

    def test_tool_schema_in_normal_mode(self):
        """Test that tool schemas don't require model in normal mode"""
        # This test uses the default from conftest.py which sets non-auto mode
        # The conftest.py mock_provider_availability fixture ensures the model is available
        tool = ChatTool()
        schema = tool.get_input_schema()

        # Model should not be required
        assert "model" not in schema["required"]

        # Model field should have simpler description
        model_schema = schema["properties"]["model"]
        assert "enum" not in model_schema
        assert "Native models:" in model_schema["description"]
        assert "Defaults to" in model_schema["description"]

    @pytest.mark.asyncio
    async def test_auto_mode_requires_model_parameter(self):
        """Test that auto mode enforces model parameter"""
        # Save original
        original = os.environ.get("DEFAULT_MODEL", "")

        try:
            # Enable auto mode
            os.environ["DEFAULT_MODEL"] = "auto"
            import config

            importlib.reload(config)

            tool = ChatTool()

            # Mock the provider to avoid real API calls
            with patch.object(tool, "get_model_provider"):
                # Execute without model parameter
                result = await tool.execute({"prompt": "Test prompt"})

            # Should get error
            assert len(result) == 1
            response = result[0].text
            assert "error" in response
            assert "Model parameter is required" in response or "Model 'auto' is not available" in response

        finally:
            # Restore
            if original:
                os.environ["DEFAULT_MODEL"] = original
            else:
                os.environ.pop("DEFAULT_MODEL", None)
            importlib.reload(config)

    @pytest.mark.asyncio
    async def test_unavailable_model_error_message(self):
        """Test that unavailable model shows helpful error with available models using real integration testing"""
        # Save original environment
        original_env = {}
        api_keys = ["GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY"]
        for key in api_keys:
            original_env[key] = os.environ.get(key)
        original_default = os.environ.get("DEFAULT_MODEL", "")

        try:
            # Set up environment with a real API key but test an unavailable model
            # This simulates a user trying to use a model that's not available with their current setup
            os.environ["OPENAI_API_KEY"] = "sk-test-key-unavailable-model-test-not-real"
            os.environ["DEFAULT_MODEL"] = "auto"

            # Clear other provider keys to isolate to OpenAI
            for key in ["GEMINI_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY"]:
                os.environ.pop(key, None)

            # Reload config and registry to pick up new environment
            import config

            importlib.reload(config)

            # Clear registry singleton to force re-initialization with new environment
            from providers.registry import ModelProviderRegistry

            ModelProviderRegistry._instance = None

            tool = ChatTool()

            # Test with real provider resolution - this should attempt to use a model
            # that doesn't exist in the OpenAI provider's model list
            try:
                result = await tool.execute(
                    {
                        "files": ["/tmp/test.py"],
                        "prompt": "Analyze this",
                        "model": "nonexistent-model-xyz",  # This model definitely doesn't exist
                    }
                )

                # If we get here, check that it's an error about model availability
                assert len(result) == 1
                response = result[0].text
                assert "error" in response

                # Should be about model not being available
                assert any(
                    phrase in response
                    for phrase in [
                        "Model 'nonexistent-model-xyz' is not available",
                        "No provider found",
                        "not available",
                        "not supported",
                    ]
                )

            except Exception as e:
                # Expected: Should fail with provider resolution or model validation error
                error_msg = str(e)
                # Should NOT be a mock-related error
                assert "MagicMock" not in error_msg
                assert "'<' not supported between instances" not in error_msg

                # Should be a real provider error about model not being available
                assert any(
                    phrase in error_msg
                    for phrase in [
                        "Model 'nonexistent-model-xyz'",
                        "not available",
                        "not found",
                        "not supported",
                        "provider",
                        "model",
                    ]
                ) or any(phrase in error_msg for phrase in ["API", "key", "authentication", "network", "connection"])

        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)

            if original_default:
                os.environ["DEFAULT_MODEL"] = original_default
            else:
                os.environ.pop("DEFAULT_MODEL", None)

            # Reload config and clear registry singleton
            importlib.reload(config)
            ModelProviderRegistry._instance = None

    def test_model_field_schema_generation(self):
        """Test the get_model_field_schema method"""
        from tools.shared.base_tool import BaseTool

        # Create a minimal concrete tool for testing
        class TestTool(BaseTool):
            def get_name(self):
                return "test"

            def get_description(self):
                return "test"

            def get_input_schema(self):
                return {}

            def get_system_prompt(self):
                return ""

            def get_request_model(self):
                return None

            async def prepare_prompt(self, request):
                return ""

        tool = TestTool()

        # Save original
        original = os.environ.get("DEFAULT_MODEL", "")

        try:
            # Test auto mode
            os.environ["DEFAULT_MODEL"] = "auto"
            import config

            importlib.reload(config)

            schema = tool.get_model_field_schema()
            assert "enum" in schema
            # Test that some basic models are available (those that should be available with dummy keys)
            available_models = schema["enum"]
            # Check for models that should be available with basic provider setup
            expected_basic_models = ["flash", "pro"]  # Gemini models from conftest.py
            for model in expected_basic_models:
                if model not in available_models:
                    print(f"Missing expected model: {model}")
                    print(f"Available models: {available_models}")
            assert any(model in available_models for model in expected_basic_models), (
                f"None of {expected_basic_models} found in {available_models}"
            )
            assert "select the most suitable model" in schema["description"]

            # Test normal mode
            os.environ["DEFAULT_MODEL"] = "pro"
            importlib.reload(config)

            schema = tool.get_model_field_schema()
            assert "enum" not in schema
            # Check for the new schema format
            assert "Model to use." in schema["description"]
            assert "'pro'" in schema["description"]
            assert "Defaults to" in schema["description"]

        finally:
            # Restore
            if original:
                os.environ["DEFAULT_MODEL"] = original
            else:
                os.environ.pop("DEFAULT_MODEL", None)
            importlib.reload(config)
