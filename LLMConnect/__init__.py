"""LLMConnect - A Python HTTP client for LLM providers."""

# Import key classes for easier access
from .top import SyncAPIClient, AsyncAPIClient
from .api_client_factory import (
    APIClientFactory,
    Provider
)

__version__ = "0.1.0"
__author__ = "Moises-Tohias"