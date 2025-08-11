import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator
import openai
from openai import AsyncOpenAI

from .base import BaseLLMClient, LLMConfig, LLMResponse, ChatMessage, LLMProvider, LLMClientFactory
from ..utils import retry_async


class OpenAIClient(BaseLLMClient):
    """OpenAI API client implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncOpenAI(
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
        try:
            response = await self.client.completions.create(
                model=self.config.model,
                prompt=prompt,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                top_p=kwargs.get("top_p", self.config.top_p),
                frequency_penalty=kwargs.get("frequency_penalty", self.config.frequency_penalty),
                presence_penalty=kwargs.get("presence_penalty", self.config.presence_penalty),
                **{k: v for k, v in kwargs.items() if k not in ["top_p", "frequency_penalty", "presence_penalty"]}
            )
            
            choice = response.choices[0]
            
            return LLMResponse(
                text=choice.text,
                model=response.model,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=choice.finish_reason or "stop",
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "usage": response.usage.model_dump() if response.usage else {},
                }
            )
        except Exception as e:
            self.logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate text with streaming"""
        try:
            stream = await self.client.completions.create(
                model=self.config.model,
                prompt=prompt,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].text:
                    yield chunk.choices[0].text
        except Exception as e:
            self.logger.error(f"OpenAI streaming failed: {e}")
            raise
    
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
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                top_p=kwargs.get("top_p", self.config.top_p),
                frequency_penalty=kwargs.get("frequency_penalty", self.config.frequency_penalty),
                presence_penalty=kwargs.get("presence_penalty", self.config.presence_penalty),
                **{k: v for k, v in kwargs.items() if k not in ["top_p", "frequency_penalty", "presence_penalty"]}
            )
            
            choice = response.choices[0]
            
            return LLMResponse(
                text=choice.message.content or "",
                model=response.model,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=choice.finish_reason or "stop",
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "usage": response.usage.model_dump() if response.usage else {},
                    "role": choice.message.role,
                }
            )
        except Exception as e:
            self.logger.error(f"OpenAI chat failed: {e}")
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
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            self.logger.error(f"OpenAI chat streaming failed: {e}")
            raise
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            import tiktoken
            
            # Get encoding for model
            try:
                encoding = tiktoken.encoding_for_model(self.config.model)
            except KeyError:
                # Fallback to cl100k_base encoding
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
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",  # Default embedding model
                input=text
            )
            
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    def estimate_cost(self, tokens: int, is_input: bool = True) -> float:
        """Estimate cost for token usage"""
        # OpenAI pricing (as of 2024)
        pricing = {
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-16k": {"input": 0.001, "output": 0.002},
        }
        
        # Find matching model
        for model_key in pricing:
            if model_key in self.config.model.lower():
                price_type = "input" if is_input else "output"
                return (tokens / 1000) * pricing[model_key][price_type]
        
        # Default pricing
        return super().estimate_cost(tokens, is_input)


# Register with factory
LLMClientFactory.register(LLMProvider.OPENAI, OpenAIClient)