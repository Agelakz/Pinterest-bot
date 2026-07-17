import importlib
import logging
from typing import Dict, Any

from providers.base_provider import SearchProvider

logger = logging.getLogger(__name__)

class ProviderFactory:
    """Factory to instantiate search providers based on configuration."""

    _PROVIDERS = {
        'microservice': 'providers.microservice_provider.MicroserviceProvider',
        'mock': 'providers.mock_provider.MockProvider'
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> SearchProvider:
        """Dynamically load and instantiate the configured provider."""
        provider_name = provider_name.lower().strip()
        if provider_name not in cls._PROVIDERS:
            logger.warning(f"Provider '{provider_name}' not found. Falling back to mock provider.")
            provider_name = "mock"

        module_path, class_name = cls._PROVIDERS[provider_name].rsplit('.', 1)
        
        try:
            module = importlib.import_module(module_path)
            provider_class = getattr(module, class_name)
            return provider_class()
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load provider '{provider_name}': {e}")
            raise ValueError(f"Invalid provider configuration: {provider_name}")