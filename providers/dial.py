"""DIAL (Data & AI Layer) model provider implementation."""

import logging
import os
import threading
import time
from typing import Optional

from .base import (
    ModelCapabilities,
    ModelResponse,
    ProviderType,
    create_temperature_constraint,
)
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class DIALModelProvider(OpenAICompatibleProvider):
    """DIAL provider using OpenAI-compatible API.

    DIAL provides access to various AI models through a unified API interface.
    Supports GPT, Claude, Gemini, and other models via DIAL deployments.
    """

    FRIENDLY_NAME = "DIAL"

    # Retry configuration for API calls
    MAX_RETRIES = 4
    RETRY_DELAYS = [1, 3, 5, 8]  # seconds

    # Model configurations using ModelCapabilities objects
    SUPPORTED_MODELS = {
        "o3-2025-04-16": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="o3-2025-04-16",
            friendly_name="DIAL (O3)",
            context_window=200_000,
            max_output_tokens=100_000,
            supports_extended_thinking=False,
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # DIAL may not expose function calling
            supports_json_mode=True,
            supports_images=True,
            max_image_size_mb=20.0,
            supports_temperature=False,  # O3 models don't accept temperature
            temperature_constraint=create_temperature_constraint("fixed"),
            description="OpenAI O3 via DIAL - Strong reasoning model",
            aliases=["o3"],
        ),
        "o4-mini-2025-04-16": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="o4-mini-2025-04-16",
            friendly_name="DIAL (O4-mini)",
            context_window=200_000,
            max_output_tokens=100_000,
            supports_extended_thinking=False,
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # DIAL may not expose function calling
            supports_json_mode=True,
            supports_images=True,
            max_image_size_mb=20.0,
            supports_temperature=False,  # O4 models don't accept temperature
            temperature_constraint=create_temperature_constraint("fixed"),
            description="OpenAI O4-mini via DIAL - Fast reasoning model",
            aliases=["o4-mini"],
        ),
        "anthropic.claude-sonnet-4-20250514-v1:0": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="anthropic.claude-sonnet-4-20250514-v1:0",
            friendly_name="DIAL (Sonnet 4)",
            context_window=200_000,
            max_output_tokens=64_000,
            supports_extended_thinking=False,
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # Claude doesn't have function calling
            supports_json_mode=False,  # Claude doesn't have JSON mode
            supports_images=True,
            max_image_size_mb=5.0,
            supports_temperature=True,
            temperature_constraint=create_temperature_constraint("range"),
            description="Claude Sonnet 4 via DIAL - Balanced performance",
            aliases=["sonnet-4"],
        ),
        "anthropic.claude-sonnet-4-20250514-v1:0-with-thinking": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="anthropic.claude-sonnet-4-20250514-v1:0-with-thinking",
            friendly_name="DIAL (Sonnet 4 Thinking)",
            context_window=200_000,
            max_output_tokens=64_000,
            supports_extended_thinking=True,  # Thinking mode variant
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # Claude doesn't have function calling
            supports_json_mode=False,  # Claude doesn't have JSON mode
            supports_images=True,
            max_image_size_mb=5.0,
            supports_temperature=True,
            temperature_constraint=create_temperature_constraint("range"),
            description="Claude Sonnet 4 with thinking mode via DIAL",
            aliases=["sonnet-4-thinking"],
        ),
        "anthropic.claude-opus-4-20250514-v1:0": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="anthropic.claude-opus-4-20250514-v1:0",
            friendly_name="DIAL (Opus 4)",
            context_window=200_000,
            max_output_tokens=64_000,
            supports_extended_thinking=False,
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # Claude doesn't have function calling
            supports_json_mode=False,  # Claude doesn't have JSON mode
            supports_images=True,
            max_image_size_mb=5.0,
            supports_temperature=True,
            temperature_constraint=create_temperature_constraint("range"),
            description="Claude Opus 4 via DIAL - Most capable Claude model",
            aliases=["opus-4"],
        ),
        "anthropic.claude-opus-4-20250514-v1:0-with-thinking": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="anthropic.claude-opus-4-20250514-v1:0-with-thinking",
            friendly_name="DIAL (Opus 4 Thinking)",
            context_window=200_000,
            max_output_tokens=64_000,
            supports_extended_thinking=True,  # Thinking mode variant
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # Claude doesn't have function calling
            supports_json_mode=False,  # Claude doesn't have JSON mode
            supports_images=True,
            max_image_size_mb=5.0,
            supports_temperature=True,
            temperature_constraint=create_temperature_constraint("range"),
            description="Claude Opus 4 with thinking mode via DIAL",
            aliases=["opus-4-thinking"],
        ),
        "gemini-2.5-pro-preview-03-25-google-search": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="gemini-2.5-pro-preview-03-25-google-search",
            friendly_name="DIAL (Gemini 2.5 Pro Search)",
            context_window=1_000_000,
            max_output_tokens=65_536,
            supports_extended_thinking=False,  # DIAL doesn't expose thinking mode
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # DIAL may not expose function calling
            supports_json_mode=True,
            supports_images=True,
            max_image_size_mb=20.0,
            supports_temperature=True,
            temperature_constraint=create_temperature_constraint("range"),
            description="Gemini 2.5 Pro with Google Search via DIAL",
            aliases=["gemini-2.5-pro-search"],
        ),
        "gemini-2.5-pro-preview-05-06": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="gemini-2.5-pro-preview-05-06",
            friendly_name="DIAL (Gemini 2.5 Pro)",
            context_window=1_000_000,
            max_output_tokens=65_536,
            supports_extended_thinking=False,
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # DIAL may not expose function calling
            supports_json_mode=True,
            supports_images=True,
            max_image_size_mb=20.0,
            supports_temperature=True,
            temperature_constraint=create_temperature_constraint("range"),
            description="Gemini 2.5 Pro via DIAL - Deep reasoning",
            aliases=["gemini-2.5-pro"],
        ),
        "gemini-2.5-flash-preview-05-20": ModelCapabilities(
            provider=ProviderType.DIAL,
            model_name="gemini-2.5-flash-preview-05-20",
            friendly_name="DIAL (Gemini Flash 2.5)",
            context_window=1_000_000,
            max_output_tokens=65_536,
            supports_extended_thinking=False,
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=False,  # DIAL may not expose function calling
            supports_json_mode=True,
            supports_images=True,
            max_image_size_mb=20.0,
            supports_temperature=True,
            temperature_constraint=create_temperature_constraint("range"),
            description="Gemini 2.5 Flash via DIAL - Ultra-fast",
            aliases=["gemini-2.5-flash"],
        ),
    }

    def __init__(self, api_key: str, **kwargs):
        """Initialize DIAL provider with API key and host.

        Args:
            api_key: DIAL API key for authentication
            **kwargs: Additional configuration options
        """
        # Get DIAL API host from environment or kwargs
        dial_host = kwargs.get("base_url") or os.getenv("DIAL_API_HOST") or "https://core.dialx.ai"

        # DIAL uses /openai endpoint for OpenAI-compatible API
        if not dial_host.endswith("/openai"):
            dial_host = f"{dial_host.rstrip('/')}/openai"

        kwargs["base_url"] = dial_host

        # Get API version from environment or use default
        self.api_version = os.getenv("DIAL_API_VERSION", "2024-12-01-preview")

        # Add DIAL-specific headers
        # DIAL uses Api-Key header instead of Authorization: Bearer
        # Reference: https://dialx.ai/dial_api#section/Authorization
        self.DEFAULT_HEADERS = {
            "Api-Key": api_key,
        }

        # Store the actual API key for use in Api-Key header
        self._dial_api_key = api_key

        # Pass a placeholder API key to OpenAI client - we'll override the auth header in httpx
        # The actual authentication happens via the Api-Key header in the httpx client
        super().__init__("placeholder-not-used", **kwargs)

        # Cache for deployment-specific clients to avoid recreating them on each request
        self._deployment_clients = {}
        # Lock to ensure thread-safe client creation
        self._client_lock = threading.Lock()

        # Create a SINGLE shared httpx client for the provider instance
        import httpx

        # Create custom event hooks to remove Authorization header
        def remove_auth_header(request):
            """Remove Authorization header that OpenAI client adds."""
            # httpx headers are case-insensitive, so we need to check all variations
            headers_to_remove = []
            for header_name in request.headers:
                if header_name.lower() == "authorization":
                    headers_to_remove.append(header_name)

            for header_name in headers_to_remove:
                del request.headers[header_name]

        self._http_client = httpx.Client(
            timeout=self.timeout_config,
            verify=True,
            follow_redirects=True,
            headers=self.DEFAULT_HEADERS.copy(),  # Include DIAL headers including Api-Key
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0,
            ),
            event_hooks={"request": [remove_auth_header]},
        )

        logger.info(f"Initialized DIAL provider with host: {dial_host} and api-version: {self.api_version}")

    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get capabilities for a specific model.

        Args:
            model_name: Name of the model (can be shorthand)

        Returns:
            ModelCapabilities object

        Raises:
            ValueError: If model is not supported or not allowed
        """
        resolved_name = self._resolve_model_name(model_name)

        if resolved_name not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported DIAL model: {model_name}")

        # Check restrictions
        from utils.model_restrictions import get_restriction_service

        restriction_service = get_restriction_service()
        if not restriction_service.is_allowed(ProviderType.DIAL, resolved_name, model_name):
            raise ValueError(f"Model '{model_name}' is not allowed by restriction policy.")

        # Return the ModelCapabilities object directly from SUPPORTED_MODELS
        return self.SUPPORTED_MODELS[resolved_name]

    def get_provider_type(self) -> ProviderType:
        """Get the provider type."""
        return ProviderType.DIAL

    def validate_model_name(self, model_name: str) -> bool:
        """Validate if the model name is supported.

        Args:
            model_name: Model name to validate

        Returns:
            True if model is supported and allowed, False otherwise
        """
        resolved_name = self._resolve_model_name(model_name)

        if resolved_name not in self.SUPPORTED_MODELS:
            return False

        # Check against base class allowed_models if configured
        if self.allowed_models is not None:
            # Check both original and resolved names (case-insensitive)
            if model_name.lower() not in self.allowed_models and resolved_name.lower() not in self.allowed_models:
                logger.debug(f"DIAL model '{model_name}' -> '{resolved_name}' not in allowed_models list")
                return False

        # Also check restrictions via ModelRestrictionService
        from utils.model_restrictions import get_restriction_service

        restriction_service = get_restriction_service()
        if not restriction_service.is_allowed(ProviderType.DIAL, resolved_name, model_name):
            logger.debug(f"DIAL model '{model_name}' -> '{resolved_name}' blocked by restrictions")
            return False

        return True

    def _get_deployment_client(self, deployment: str):
        """Get or create a cached client for a specific deployment.

        This avoids recreating OpenAI clients on every request, improving performance.
        Reuses the shared HTTP client for connection pooling.

        Args:
            deployment: The deployment/model name

        Returns:
            OpenAI client configured for the specific deployment
        """
        # Check if client already exists without locking for performance
        if deployment in self._deployment_clients:
            return self._deployment_clients[deployment]

        # Use lock to ensure thread-safe client creation
        with self._client_lock:
            # Double-check pattern: check again inside the lock
            if deployment not in self._deployment_clients:
                from openai import OpenAI

                # Build deployment-specific URL
                base_url = str(self.client.base_url)
                if base_url.endswith("/"):
                    base_url = base_url[:-1]

                # Remove /openai suffix if present to reconstruct properly
                if base_url.endswith("/openai"):
                    base_url = base_url[:-7]

                deployment_url = f"{base_url}/openai/deployments/{deployment}"

                # Create and cache the client, REUSING the shared http_client
                # Use placeholder API key - Authorization header will be removed by http_client event hook
                self._deployment_clients[deployment] = OpenAI(
                    api_key="placeholder-not-used",
                    base_url=deployment_url,
                    http_client=self._http_client,  # Pass the shared client with Api-Key header
                    default_query={"api-version": self.api_version},  # Add api-version as query param
                )

        return self._deployment_clients[deployment]

    def generate_content(
        self,
        prompt: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        images: Optional[list[str]] = None,
        **kwargs,
    ) -> ModelResponse:
        """Generate content using DIAL's deployment-specific endpoint.

        DIAL uses Azure OpenAI-style deployment endpoints:
        /openai/deployments/{deployment}/chat/completions

        Args:
            prompt: User prompt
            model_name: Model name or alias
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_output_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            ModelResponse with generated content and metadata
        """
        # Validate model name against allow-list
        if not self.validate_model_name(model_name):
            raise ValueError(f"Model '{model_name}' not in allowed models list. Allowed models: {self.allowed_models}")

        # Validate parameters
        self.validate_parameters(model_name, temperature)

        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        # Build user message content
        user_message_content = []
        if prompt:
            user_message_content.append({"type": "text", "text": prompt})

        if images and self._supports_vision(model_name):
            for img_path in images:
                processed_image = self._process_image(img_path)
                if processed_image:
                    user_message_content.append(processed_image)
        elif images:
            logger.warning(f"Model {model_name} does not support images, ignoring {len(images)} image(s)")

        # Add user message. If only text, content will be a string, otherwise a list.
        if len(user_message_content) == 1 and user_message_content[0]["type"] == "text":
            messages.append({"role": "user", "content": prompt})
        else:
            messages.append({"role": "user", "content": user_message_content})

        # Resolve model name
        resolved_model = self._resolve_model_name(model_name)

        # Build completion parameters
        completion_params = {
            "model": resolved_model,
            "messages": messages,
        }

        # Check model capabilities
        try:
            capabilities = self.get_capabilities(model_name)
            supports_temperature = capabilities.supports_temperature
        except Exception as e:
            logger.debug(f"Failed to check temperature support for {model_name}: {e}")
            supports_temperature = True

        # Add temperature parameter if supported
        if supports_temperature:
            completion_params["temperature"] = temperature

        # Add max tokens if specified and model supports it
        if max_output_tokens and supports_temperature:
            completion_params["max_tokens"] = max_output_tokens

        # Add additional parameters
        for key, value in kwargs.items():
            if key in ["top_p", "frequency_penalty", "presence_penalty", "seed", "stop", "stream"]:
                if not supports_temperature and key in ["top_p", "frequency_penalty", "presence_penalty"]:
                    continue
                completion_params[key] = value

        # DIAL-specific: Get cached client for deployment endpoint
        deployment_client = self._get_deployment_client(resolved_model)

        # Retry logic with progressive delays
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                # Generate completion using deployment-specific client
                response = deployment_client.chat.completions.create(**completion_params)

                # Extract content and usage
                content = response.choices[0].message.content
                usage = self._extract_usage(response)

                return ModelResponse(
                    content=content,
                    usage=usage,
                    model_name=model_name,
                    friendly_name=self.FRIENDLY_NAME,
                    provider=self.get_provider_type(),
                    metadata={
                        "finish_reason": response.choices[0].finish_reason,
                        "model": response.model,
                        "id": response.id,
                        "created": response.created,
                    },
                )

            except Exception as e:
                last_exception = e

                # Check if this is a retryable error
                is_retryable = self._is_error_retryable(e)

                if not is_retryable:
                    # Non-retryable error, raise immediately
                    raise ValueError(f"DIAL API error for model {model_name}: {str(e)}")

                # If this isn't the last attempt and error is retryable, wait and retry
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt]
                    logger.info(
                        f"DIAL API error (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying in {delay}s: {str(e)}"
                    )
                    time.sleep(delay)
                    continue

        # All retries exhausted
        raise ValueError(
            f"DIAL API error for model {model_name} after {self.MAX_RETRIES} attempts: {str(last_exception)}"
        )

    def _supports_vision(self, model_name: str) -> bool:
        """Check if the model supports vision (image processing).

        Args:
            model_name: Model name to check

        Returns:
            True if model supports vision, False otherwise
        """
        resolved_name = self._resolve_model_name(model_name)

        if resolved_name in self.SUPPORTED_MODELS:
            return self.SUPPORTED_MODELS[resolved_name].supports_images

        # Fall back to parent implementation for unknown models
        return super()._supports_vision(model_name)

    def close(self):
        """Clean up HTTP clients when provider is closed."""
        logger.info("Closing DIAL provider HTTP clients...")

        # Clear the deployment clients cache
        # Note: We don't need to close individual OpenAI clients since they
        # use the shared httpx.Client which we close separately
        self._deployment_clients.clear()

        # Close the shared HTTP client
        if hasattr(self, "_http_client"):
            try:
                self._http_client.close()
                logger.debug("Closed shared HTTP client")
            except Exception as e:
                logger.warning(f"Error closing shared HTTP client: {e}")

        # Also close the client created by the superclass (OpenAICompatibleProvider)
        # as it holds its own httpx.Client instance that is not used by DIAL's generate_content
        if hasattr(self, "client") and self.client and hasattr(self.client, "close"):
            try:
                self.client.close()
                logger.debug("Closed superclass's OpenAI client")
            except Exception as e:
                logger.warning(f"Error closing superclass's OpenAI client: {e}")
