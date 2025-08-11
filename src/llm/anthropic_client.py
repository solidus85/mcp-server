import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator
import anthropic
from anthropic import AsyncAnthropic

from .base import BaseLLMClient, LLMConfig, LLMResponse, ChatMessage, LLMProvider, LLMClientFactory
from ..utils import retry_async


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.retry_attempts,
        )
    
    @retry_async(max_attempts=3, delay=1.0)
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text from a prompt"""
        # For Claude, we use the messages API with a user message
        messages = [ChatMessage(role="user", content=prompt)]
        return await self.chat(messages, max_tokens, temperature, **kwargs)
    
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate text with streaming"""
        messages = [ChatMessage(role="user", content=prompt)]
        async for chunk in self.chat_stream(messages, max_tokens, temperature, **kwargs):
            yield chunk
    
    @retry_async(max_attempts=3, delay=1.0)
    async def chat(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from chat messages"""
        try:
            # Convert messages to Anthropic format
            # Separate system message if present
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Ensure alternating user/assistant messages
            if anthropic_messages and anthropic_messages[0]["role"] != "user":
                anthropic_messages.insert(0, {"role": "user", "content": "Hello"})
            
            response = await self.client.messages.create(
                model=self.config.model,
                messages=anthropic_messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                system=system_message,
                top_p=kwargs.get("top_p", self.config.top_p),
                **{k: v for k, v in kwargs.items() if k not in ["top_p"]}
            )
            
            # Calculate total tokens (input + output)
            total_tokens = response.usage.input_tokens + response.usage.output_tokens
            
            return LLMResponse(
                text=response.content[0].text if response.content else "",
                model=response.model,
                tokens_used=total_tokens,
                finish_reason=response.stop_reason or "stop",
                metadata={
                    "id": response.id,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": total_tokens,
                    },
                    "stop_sequence": response.stop_sequence,
                }
            )
        except Exception as e:
            self.logger.error(f"Anthropic chat failed: {e}")
            raise
    
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate chat response with streaming"""
        try:
            # Convert messages to Anthropic format
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Ensure alternating user/assistant messages
            if anthropic_messages and anthropic_messages[0]["role"] != "user":
                anthropic_messages.insert(0, {"role": "user", "content": "Hello"})
            
            async with self.client.messages.stream(
                model=self.config.model,
                messages=anthropic_messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                system=system_message,
                **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            self.logger.error(f"Anthropic streaming failed: {e}")
            raise
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            # Use Anthropic's token counting
            # This is an approximation as Anthropic doesn't provide a direct API
            # Claude uses a similar tokenization to GPT models
            import tiktoken
            
            # Use cl100k_base encoding as approximation
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            return len(tokens)
        except ImportError:
            # Fallback to approximate count
            self.logger.warning("tiktoken not installed, using approximate token count")
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        # Anthropic doesn't provide embeddings API
        raise NotImplementedError("Anthropic does not provide embeddings API")
    
    def estimate_cost(self, tokens: int, is_input: bool = True) -> float:
        """Estimate cost for token usage"""
        # Anthropic Claude pricing (as of 2024)
        pricing = {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "claude-2.1": {"input": 0.008, "output": 0.024},
            "claude-2": {"input": 0.008, "output": 0.024},
            "claude-instant": {"input": 0.00080, "output": 0.00240},
        }
        
        # Find matching model
        for model_key in pricing:
            if model_key in self.config.model.lower():
                price_type = "input" if is_input else "output"
                return (tokens / 1000) * pricing[model_key][price_type]
        
        # Default pricing
        return super().estimate_cost(tokens, is_input)


# Register with factory
LLMClientFactory.register(LLMProvider.ANTHROPIC, AnthropicClient)