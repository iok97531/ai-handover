from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class EmbeddingResult:
    vector: list[float]
    token_count: int


@dataclass
class ChatResponse:
    content: str
    finish_reason: str
    usage: dict


class AIProvider(ABC):
    """Abstract interface for AI model providers."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for a list of texts."""
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        """Generate a chat completion."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Stream a chat completion token by token."""
        ...

    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of the embedding model's output vectors."""
        ...


def create_provider(provider_name: str, api_key: str, **kwargs) -> AIProvider:
    """Factory function to instantiate the correct provider."""
    if provider_name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key, **kwargs)
    elif provider_name == "claude":
        from .claude_provider import ClaudeProvider
        return ClaudeProvider(api_key=api_key, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


async def get_current_provider() -> AIProvider:
    """Get the currently configured AI provider from settings."""
    from models.database import get_db

    db = await get_db()
    cursor = await db.execute("SELECT key, value FROM settings")
    rows = await cursor.fetchall()
    settings = {row["key"]: row["value"] for row in rows}

    from services.crypto import decrypt

    provider_name = settings.get("ai_provider", "openai")
    api_key = decrypt(settings.get("api_key", ""))

    if not api_key:
        raise ValueError("API 키가 설정되지 않았습니다. 설정에서 API 키를 입력해주세요.")

    kwargs = {}
    chat_model = settings.get("chat_model")
    embedding_model = settings.get("embedding_model")
    if chat_model:
        kwargs["chat_model"] = chat_model
    if embedding_model:
        kwargs["embedding_model"] = embedding_model

    return create_provider(provider_name, api_key, **kwargs)
