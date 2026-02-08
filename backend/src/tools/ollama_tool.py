"""Ollama LLM tool for text generation."""

import asyncio
from collections.abc import AsyncIterator

import ollama
import structlog

from src.core import LLMError, Settings
from src.prompts import RAG_SYSTEM_PROMPT

logger = structlog.get_logger()


class OllamaTool:
    """Tool for LLM inference using Ollama."""

    def __init__(self, settings: Settings | None = None):
        """Initialize Ollama client.

        Args:
            settings: Application settings.
        """
        self._settings = settings or Settings()
        self._client = ollama.AsyncClient(host=self._settings.ollama_base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: str | None = None,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate text using Ollama.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            context: Optional context to include.
            stream: Whether to stream the response.

        Returns:
            Generated text or async iterator of chunks.

        Raises:
            LLMError: If generation fails.
        """
        # Build full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}\n\nAnswer:"

        # Use default RAG system prompt if not provided
        if system_prompt is None:
            system_prompt = RAG_SYSTEM_PROMPT

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt},
        ]

        try:
            if stream:
                return self._generate_stream(messages)
            else:
                response = await self._client.chat(
                    model=self._settings.ollama_model,
                    messages=messages,
                    options={
                        "num_ctx": self._settings.ollama_context_length,
                    },
                )
                return response.message.content

        except Exception as e:
            logger.error("ollama_generation_failed", error=str(e))
            raise LLMError(f"LLM generation failed: {e}") from e

    async def _generate_stream(self, messages: list[dict]) -> AsyncIterator[str]:
        """Generate streaming response.

        Args:
            messages: Chat messages.

        Yields:
            Text chunks as they are generated.
        """
        try:
            async for chunk in await self._client.chat(
                model=self._settings.ollama_model,
                messages=messages,
                stream=True,
                options={
                    "num_ctx": self._settings.ollama_context_length,
                },
            ):
                if chunk.message and chunk.message.content:
                    yield chunk.message.content
        except Exception as e:
            logger.error("ollama_stream_failed", error=str(e))
            raise LLMError(f"LLM streaming failed: {e}") from e

    async def check_health(self) -> bool:
        """Check if Ollama is reachable.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            await self._client.list()
            return True
        except Exception as e:
            logger.warning("ollama_health_check_failed", error=str(e))
            return False
