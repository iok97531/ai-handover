"""Tests for the RAG query pipeline with mock AI provider."""
import pytest
from unittest.mock import patch, AsyncMock

from ai.provider import AIProvider, ChatMessage, EmbeddingResult, ChatResponse


class MockProvider(AIProvider):
    """Mock AI provider for testing without API keys."""

    def __init__(self):
        self.embed_calls = []
        self.chat_calls = []

    async def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        self.embed_calls.append(texts)
        # Return deterministic fake embeddings
        return [
            EmbeddingResult(vector=[float(i) / max(len(texts), 1) for i in range(8)], token_count=10)
            for _ in texts
        ]

    async def chat(self, messages, temperature=0.1, max_tokens=2048) -> ChatResponse:
        self.chat_calls.append(messages)
        return ChatResponse(content="Mock response", finish_reason="stop", usage={})

    async def chat_stream(self, messages, temperature=0.1, max_tokens=2048):
        self.chat_calls.append(messages)
        for word in ["이 ", "프로젝트는 ", "테스트용 ", "입니다."]:
            yield word

    def embedding_dimension(self) -> int:
        return 8


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def temp_vector_store(tmp_path):
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    with patch("vector_store.chroma.CHROMA_DIR", chroma_dir), \
         patch("vector_store.chroma._client", None), \
         patch("vector_store.chroma._store", None):
        from vector_store.chroma import VectorStore
        yield VectorStore()


def test_rag_format_context():
    from services.rag import RAGService
    rag = RAGService.__new__(RAGService)

    results = {
        "documents": [["def hello():", "def world():"]],
        "metadatas": [[
            {"file_path": "main.py", "language": "python", "line_start": 1, "line_end": 3},
            {"file_path": "utils.py", "language": "python", "line_start": 5, "line_end": 8},
        ]],
    }

    context = rag._format_context(results)
    assert "main.py" in context
    assert "utils.py" in context
    assert "def hello():" in context
    assert "lines 1-3" in context


def test_rag_format_context_empty():
    from services.rag import RAGService
    rag = RAGService.__new__(RAGService)

    results = {"documents": [[]], "metadatas": [[]]}
    context = rag._format_context(results)
    assert "찾을 수 없습니다" in context


async def test_rag_query_stream(mock_provider, temp_vector_store):
    """Test full RAG query pipeline with mock provider."""
    from services.rag import RAGService

    # Seed vector store with some data
    temp_vector_store.upsert(
        project_id="test-project",
        ids=["main.py::0", "utils.py::0"],
        embeddings=[[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                     [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]],
        documents=[
            "def main():\n    print('hello')",
            "def add(a, b):\n    return a + b",
        ],
        metadatas=[
            {"file_path": "main.py", "language": "python", "line_start": 1, "line_end": 2},
            {"file_path": "utils.py", "language": "python", "line_start": 1, "line_end": 2},
        ],
    )

    rag = RAGService(provider=mock_provider, vector_store=temp_vector_store)

    tokens = []
    async for token in rag.query_stream(
        project_id="test-project",
        question="이 프로젝트가 뭐하는 거야?",
        chat_history=[],
    ):
        tokens.append(token)

    # Should have received tokens
    assert len(tokens) > 0
    full_response = "".join(tokens)
    assert "프로젝트" in full_response

    # Should have called embed (for the question)
    assert len(mock_provider.embed_calls) == 1

    # Should have called chat_stream
    assert len(mock_provider.chat_calls) == 1
    messages = mock_provider.chat_calls[0]
    # Should have system + user messages
    assert any(m.role == "system" for m in messages)
    assert any(m.role == "user" for m in messages)
    # User message should contain retrieved context
    user_msg = [m for m in messages if m.role == "user"][-1]
    assert "main.py" in user_msg.content or "utils.py" in user_msg.content


async def test_rag_with_chat_history(mock_provider, temp_vector_store):
    """Test that chat history is included in the prompt."""
    from services.rag import RAGService

    temp_vector_store.upsert(
        project_id="hist-test",
        ids=["a::0"],
        embeddings=[[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]],
        documents=["some code"],
        metadatas=[{"file_path": "a.py", "language": "python", "line_start": 1, "line_end": 1}],
    )

    rag = RAGService(provider=mock_provider, vector_store=temp_vector_store)

    history = [
        {"role": "user", "content": "이전 질문"},
        {"role": "assistant", "content": "이전 답변"},
    ]

    tokens = []
    async for token in rag.query_stream("hist-test", "후속 질문", history):
        tokens.append(token)

    # Chat history should be in messages
    messages = mock_provider.chat_calls[0]
    roles = [m.role for m in messages]
    assert "user" in roles
    assert "assistant" in roles


async def test_rag_empty_collection(mock_provider, temp_vector_store):
    """Test RAG with no indexed documents."""
    from services.rag import RAGService

    rag = RAGService(provider=mock_provider, vector_store=temp_vector_store)

    tokens = []
    async for token in rag.query_stream("empty-project", "질문", []):
        tokens.append(token)

    # Should still get a response (the LLM handles empty context)
    assert len(tokens) > 0
