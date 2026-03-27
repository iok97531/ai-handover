from typing import AsyncIterator
from ai.provider import get_current_provider, AIProvider, ChatMessage
from vector_store.chroma import get_vector_store, VectorStore

SYSTEM_PROMPT = """You are an AI assistant helping a team member understand a software project.
You answer questions based on the project's source code and documentation.
Always cite the specific file paths when referencing code.
If you are unsure or the retrieved context does not contain enough information,
say so honestly rather than guessing.
Always answer in Korean using polite formal speech (존댓말, -습니다/-요 style)."""


class RAGService:
    def __init__(self, provider: AIProvider, vector_store: VectorStore):
        self.provider = provider
        self.vs = vector_store

    @classmethod
    async def create(cls) -> "RAGService":
        provider = await get_current_provider()
        vs = get_vector_store()
        return cls(provider, vs)

    def _format_context(self, results: dict) -> str:
        """Format retrieved chunks into a context string."""
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return "관련 코드를 찾을 수 없습니다."

        parts = []
        for doc, meta in zip(documents, metadatas):
            file_path = meta.get("file_path", "unknown")
            language = meta.get("language", "text")
            line_start = meta.get("line_start", "?")
            line_end = meta.get("line_end", "?")

            parts.append(
                f"--- File: {file_path} (lines {line_start}-{line_end}) ---\n"
                f"```{language}\n{doc}\n```"
            )

        return "\n\n".join(parts)

    async def query_stream(
        self,
        project_id: str,
        question: str,
        chat_history: list[dict],
        n_results: int = 8,
    ) -> AsyncIterator[str]:
        """RAG query with streaming response."""
        # 1. Embed the question
        q_embedding = await self.provider.embed([question])
        query_vector = q_embedding[0].vector

        # 2. Retrieve relevant chunks
        results = self.vs.query(project_id, query_vector, n_results=n_results)

        # 3. Build messages
        context = self._format_context(results)

        messages = [ChatMessage(role="system", content=SYSTEM_PROMPT)]

        # Add chat history
        for msg in chat_history[-10:]:  # Last 10 messages for context window
            messages.append(ChatMessage(role=msg["role"], content=msg["content"]))

        # Add current question with context
        user_content = (
            f"프로젝트 코드에서 검색된 관련 내용:\n\n{context}\n\n"
            f"질문: {question}"
        )
        messages.append(ChatMessage(role="user", content=user_content))

        # 4. Stream response
        async for token in self.provider.chat_stream(messages):
            yield token
