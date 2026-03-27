from typing import AsyncIterator
import anthropic
from .provider import AIProvider, ChatMessage, EmbeddingResult, ChatResponse


class ClaudeProvider(AIProvider):
    """Claude provider implementation.

    Note: Anthropic does not provide an embedding API.
    This provider uses a local sentence-transformers model for embeddings
    while using Claude for chat completion.
    """

    def __init__(
        self,
        api_key: str,
        chat_model: str = "claude-sonnet-4-20250514",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.chat_model = chat_model
        self._embedding_model_name = embedding_model
        self._embedder = None

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self._embedding_model_name)
        return self._embedder

    async def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        embedder = self._get_embedder()
        vectors = embedder.encode(texts).tolist()
        return [EmbeddingResult(vector=v, token_count=0) for v in vectors]

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        system = next((m.content for m in messages if m.role == "system"), "")
        user_msgs = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]

        response = await self.client.messages.create(
            model=self.chat_model,
            system=system,
            messages=user_msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return ChatResponse(
            content=response.content[0].text,
            finish_reason=response.stop_reason or "end_turn",
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        system = next((m.content for m in messages if m.role == "system"), "")
        user_msgs = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]

        async with self.client.messages.stream(
            model=self.chat_model,
            system=system,
            messages=user_msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def embedding_dimension(self) -> int:
        return 384  # all-MiniLM-L6-v2
