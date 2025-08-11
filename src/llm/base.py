from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator, Union
from dataclasses import dataclass
from enum import Enum
import logging

from ..utils import setup_logging


logger = setup_logging("LLM.Base")


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """Configuration for LLM client"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class LLMResponse:
    """Response from LLM"""
    text: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: Dict[str, Any]


@dataclass
class ChatMessage:
    """Chat message for conversation"""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = setup_logging(f"LLM.{config.provider.value}")
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text from a prompt"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate text from a prompt with streaming"""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from chat messages"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate response from chat messages with streaming"""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text (if supported)"""
        pass
    
    def estimate_cost(self, tokens: int, is_input: bool = True) -> float:
        """Estimate cost for token usage"""
        # Default implementation - override in subclasses
        # Prices in USD per 1K tokens (approximate)
        price_per_1k = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        }
        
        # Find matching model pricing
        for model_prefix, prices in price_per_1k.items():
            if model_prefix in self.config.model.lower():
                price_type = "input" if is_input else "output"
                return (tokens / 1000) * prices[price_type]
        
        # Default pricing if model not found
        return (tokens / 1000) * (0.001 if is_input else 0.002)
    
    def validate_config(self) -> bool:
        """Validate client configuration"""
        if not self.config.api_key and self.config.provider != LLMProvider.LOCAL:
            self.logger.error(f"API key required for {self.config.provider.value}")
            return False
        
        if self.config.max_tokens < 1:
            self.logger.error("max_tokens must be positive")
            return False
        
        if not 0 <= self.config.temperature <= 2:
            self.logger.error("temperature must be between 0 and 2")
            return False
        
        return True


class LLMClientFactory:
    """Factory for creating LLM clients"""
    
    _clients: Dict[str, type] = {}
    
    @classmethod
    def register(cls, provider: LLMProvider, client_class: type):
        """Register a client class for a provider"""
        cls._clients[provider.value] = client_class
    
    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLMClient:
        """Create an LLM client from config"""
        client_class = cls._clients.get(config.provider.value)
        
        if not client_class:
            raise ValueError(f"Unknown provider: {config.provider.value}")
        
        client = client_class(config)
        
        if not client.validate_config():
            raise ValueError(f"Invalid configuration for {config.provider.value}")
        
        return client
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List registered providers"""
        return list(cls._clients.keys())


class LLMManager:
    """Manager for multiple LLM clients"""
    
    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.default_client: Optional[str] = None
        self.logger = setup_logging("LLMManager")
    
    def add_client(self, name: str, client: BaseLLMClient, is_default: bool = False):
        """Add an LLM client"""
        self.clients[name] = client
        if is_default or self.default_client is None:
            self.default_client = name
        self.logger.info(f"Added LLM client: {name}")
    
    def get_client(self, name: Optional[str] = None) -> BaseLLMClient:
        """Get an LLM client by name or default"""
        name = name or self.default_client
        
        if not name:
            raise ValueError("No client name provided and no default set")
        
        client = self.clients.get(name)
        if not client:
            raise ValueError(f"Client '{name}' not found")
        
        return client
    
    async def generate(
        self,
        prompt: str,
        client_name: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text using specified or default client"""
        client = self.get_client(client_name)
        return await client.generate(prompt, **kwargs)
    
    async def chat(
        self,
        messages: List[ChatMessage],
        client_name: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Chat using specified or default client"""
        client = self.get_client(client_name)
        return await client.chat(messages, **kwargs)
    
    def list_clients(self) -> List[str]:
        """List available clients"""
        return list(self.clients.keys())
    
    def get_client_info(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a client"""
        client = self.get_client(name)
        return {
            "provider": client.config.provider.value,
            "model": client.config.model,
            "max_tokens": client.config.max_tokens,
            "temperature": client.config.temperature,
        }