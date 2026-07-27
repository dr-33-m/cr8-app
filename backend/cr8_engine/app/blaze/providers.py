"""
AI Providers for B.L.A.Z.E Agent
Support for both cloud (OpenRouter) and local (Ollama) AI providers.
"""

import os
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)

# OpenRouter app attribution — puts cr8-xyz on the public rankings at
# openrouter.ai/rankings and unlocks per-app analytics at
# openrouter.ai/apps?url=<HTTP-Referer>.
#
# HTTP-Referer is the required key: it is the app's unique identifier, and
# without it no app page is created at all. The title only renames an app that
# the referer already established.
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "https://cr8-xyz.art")
OPENROUTER_APP_TITLE = os.getenv("OPENROUTER_APP_TITLE", "Cr8-xyz")
# Comma-separated, max 2 per request, lowercase and hyphenated. Unrecognised
# values are silently dropped by OpenRouter.
OPENROUTER_APP_CATEGORIES = os.getenv("OPENROUTER_APP_CATEGORIES", "image-gen")


def build_openrouter_headers() -> Dict[str, str]:
    """Attribution headers sent on every OpenRouter request."""
    headers = {
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-OpenRouter-Title": OPENROUTER_APP_TITLE,
    }
    if OPENROUTER_APP_CATEGORIES:
        headers["X-OpenRouter-Categories"] = OPENROUTER_APP_CATEGORIES
    return headers


class ProviderConfig:
    """Configuration for AI providers"""
    
    # Provider types
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    
    def __init__(self, provider_type: str = None, model_name: str = None):
        self.provider_type = provider_type or os.getenv("AI_PROVIDER", self.OPENROUTER)
        self.model_name = model_name or os.getenv("AI_MODEL_NAME", "qwen2.5-coder:7b")
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY")
        
    def is_valid(self) -> bool:
        """Check if the configuration is valid"""
        if self.provider_type == self.OPENROUTER:
            return bool(self.api_key)
        elif self.provider_type == self.OLLAMA:
            return True  # Ollama doesn't require API key for local instances
        return False


class OpenRouterProviderFactory:
    """Factory for creating OpenRouter providers"""
    
    @staticmethod
    def create_provider(config: ProviderConfig) -> OpenAIModel:
        """Create OpenRouter provider with OpenAI model"""
        if not config.api_key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouter provider")

        # OpenRouterProvider takes no headers argument, so build the underlying
        # client ourselves to attach the attribution headers. base_url matches
        # what the provider would have used.
        headers = build_openrouter_headers()
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.api_key,
            default_headers=headers,
        )
        provider = OpenRouterProvider(openai_client=client)
        model = OpenAIModel(
            model_name=config.model_name,
            provider=provider
        )
        logger.info(
            f"Created OpenRouter provider with model: {config.model_name} "
            f"(attributed to {headers['HTTP-Referer']} as '{headers['X-OpenRouter-Title']}')"
        )
        return model


class OllamaProviderFactory:
    """Factory for creating Ollama providers"""
    
    @staticmethod
    def create_provider(config: ProviderConfig) -> OpenAIModel:
        """Create Ollama provider with OpenAI model interface"""
        provider = OllamaProvider(
            base_url=config.ollama_base_url,
            api_key=config.ollama_api_key
        )
        model = OpenAIModel(
            model_name=config.model_name,
            provider=provider
        )
        logger.info(f"Created Ollama provider with model: {config.model_name} at {config.ollama_base_url}")
        return model


class ProviderFactory:
    """Main factory for creating AI providers"""
    
    _factories = {
        ProviderConfig.OPENROUTER: OpenRouterProviderFactory,
        ProviderConfig.OLLAMA: OllamaProviderFactory,
    }
    
    @classmethod
    def create_provider(cls, config: ProviderConfig) -> OpenAIModel:
        """Create the appropriate provider based on configuration"""
        if not config.is_valid():
            raise ValueError(f"Invalid provider configuration for {config.provider_type}")
            
        factory = cls._factories.get(config.provider_type)
        if not factory:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")
            
        return factory.create_provider(config)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider types"""
        return list(cls._factories.keys())


def create_provider_from_env() -> OpenAIModel:
    """Create provider based on environment variables"""
    config = ProviderConfig()
    return ProviderFactory.create_provider(config)


# Convenience functions for specific providers
def create_openrouter_provider(model_name: str = None) -> OpenAIModel:
    """Create OpenRouter provider"""
    config = ProviderConfig(
        provider_type=ProviderConfig.OPENROUTER,
        model_name=model_name
    )
    return OpenRouterProviderFactory.create_provider(config)


def create_ollama_provider(model_name: str = None, base_url: str = None) -> OpenAIModel:
    """Create Ollama provider"""
    config = ProviderConfig(
        provider_type=ProviderConfig.OLLAMA,
        model_name=model_name
    )
    if base_url:
        config.ollama_base_url = base_url
    return OllamaProviderFactory.create_provider(config)
