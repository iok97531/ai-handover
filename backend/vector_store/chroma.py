from __future__ import annotations

import chromadb
from config import CHROMA_DIR

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


class VectorStore:
    def __init__(self):
        self.client = _get_client()

    def get_or_create_collection(self, project_id: str, dimension: int | None = None):
        metadata = {}
        if dimension:
            metadata["dimension"] = dimension
        return self.client.get_or_create_collection(
            name=f"project_{project_id.replace('-', '_')}",
            metadata=metadata or None,
        )

    def delete_collection(self, project_id: str):
        name = f"project_{project_id.replace('-', '_')}"
        try:
            self.client.delete_collection(name)
        except (ValueError, chromadb.errors.NotFoundError):
            pass  # Collection doesn't exist

    def upsert(
        self,
        project_id: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ):
        collection = self.get_or_create_collection(project_id)
        # ChromaDB has batch size limits, process in chunks of 5000
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )

    def delete_by_file(self, project_id: str, file_path: str):
        collection = self.get_or_create_collection(project_id)
        try:
            collection.delete(where={"file_path": file_path})
        except Exception:
            pass  # No documents to delete

    def query(
        self,
        project_id: str,
        query_embedding: list[float],
        n_results: int = 8,
    ) -> dict:
        collection = self.get_or_create_collection(project_id)
        if collection.count() == 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
        )

    def get_chunk_count(self, project_id: str) -> int:
        collection = self.get_or_create_collection(project_id)
        return collection.count()


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
