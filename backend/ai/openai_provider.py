from typing import AsyncIterator
from openai import AsyncOpenAI
from .provider import AIProvider, ChatMessage, EmbeddingResult, ChatResponse


class OpenAIProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        chat_model: str = "gpt-4o",
        embedding_model: str = "text-embedding-3-small",
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.chat_model = chat_model
        self.embedding_model = embedding_model

    async def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        response = await self.client.embeddings.create(
            input=texts, model=self.embedding_model
        )
        return [
            EmbeddingResult(
                vector=e.embedding,
                token_count=response.usage.total_tokens,
            )
            for e in response.data
        ]

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        response = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            finish_reason=choice.finish_reason or "stop",
            usage=response.usage.model_dump() if response.usage else {},
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def embedding_dimension(self) -> int:
        if "3-large" in self.embedding_model:
            return 3072
        return 1536  # text-embedding-3-small default
