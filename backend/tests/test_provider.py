import pytest
from ai.provider import create_provider, ChatMessage, EmbeddingResult, ChatResponse


def test_create_openai_provider():
    provider = create_provider("openai", "sk-test-key")
    assert provider is not None
    assert provider.embedding_dimension() == 1536


def test_create_openai_provider_large_model():
    provider = create_provider("openai", "sk-test", embedding_model="text-embedding-3-large")
    assert provider.embedding_dimension() == 3072


def test_create_claude_provider():
    # Claude provider import requires anthropic package
    provider = create_provider("claude", "sk-ant-test")
    assert provider is not None
    assert provider.embedding_dimension() == 384


def test_create_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        create_provider("gemini", "key")


def test_chat_message_dataclass():
    msg = ChatMessage(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"


def test_embedding_result_dataclass():
    result = EmbeddingResult(vector=[0.1, 0.2], token_count=5)
    assert len(result.vector) == 2
    assert result.token_count == 5


def test_chat_response_dataclass():
    resp = ChatResponse(content="answer", finish_reason="stop", usage={"tokens": 10})
    assert resp.content == "answer"
    assert resp.finish_reason == "stop"
