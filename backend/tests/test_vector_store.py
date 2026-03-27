import pytest
import tempfile
import os
from unittest.mock import patch


@pytest.fixture
def temp_chroma_dir(tmp_path):
    """Use a temp directory for ChromaDB to avoid polluting project data."""
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    with patch("vector_store.chroma.CHROMA_DIR", chroma_dir):
        with patch("vector_store.chroma._client", None):
            with patch("vector_store.chroma._store", None):
                yield chroma_dir


def test_create_and_query_empty_collection(temp_chroma_dir):
    from vector_store.chroma import VectorStore
    vs = VectorStore()
    result = vs.query("test-project", [0.1, 0.2, 0.3], n_results=5)
    assert result["documents"] == [[]]


def test_upsert_and_query(temp_chroma_dir):
    from vector_store.chroma import VectorStore
    vs = VectorStore()
    project_id = "test-proj"

    vs.upsert(
        project_id=project_id,
        ids=["file1::0", "file1::1"],
        embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        documents=["def hello():", "def world():"],
        metadatas=[
            {"file_path": "a.py", "language": "python", "line_start": 1, "line_end": 5},
            {"file_path": "a.py", "language": "python", "line_start": 6, "line_end": 10},
        ],
    )

    assert vs.get_chunk_count(project_id) == 2

    result = vs.query(project_id, [0.9, 0.1, 0.0], n_results=1)
    assert len(result["documents"][0]) == 1
    assert "hello" in result["documents"][0][0]


def test_delete_by_file(temp_chroma_dir):
    from vector_store.chroma import VectorStore
    vs = VectorStore()
    project_id = "del-test"

    vs.upsert(
        project_id=project_id,
        ids=["a::0", "b::0"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        documents=["file a content", "file b content"],
        metadatas=[
            {"file_path": "a.py", "language": "python", "line_start": 1, "line_end": 1},
            {"file_path": "b.py", "language": "python", "line_start": 1, "line_end": 1},
        ],
    )

    assert vs.get_chunk_count(project_id) == 2
    vs.delete_by_file(project_id, "a.py")
    assert vs.get_chunk_count(project_id) == 1


def test_delete_collection(temp_chroma_dir):
    from vector_store.chroma import VectorStore
    vs = VectorStore()
    project_id = "to-delete"

    vs.upsert(
        project_id=project_id,
        ids=["x::0"],
        embeddings=[[1.0]],
        documents=["content"],
        metadatas=[{"file_path": "x.py", "language": "python", "line_start": 1, "line_end": 1}],
    )

    assert vs.get_chunk_count(project_id) == 1
    vs.delete_collection(project_id)
    # After deletion, creating a new collection should be empty
    assert vs.get_chunk_count(project_id) == 0


def test_delete_nonexistent_collection(temp_chroma_dir):
    from vector_store.chroma import VectorStore
    vs = VectorStore()
    # Should not raise
    vs.delete_collection("nonexistent-id")


def test_upsert_overwrites_existing(temp_chroma_dir):
    from vector_store.chroma import VectorStore
    vs = VectorStore()
    project_id = "upsert-test"

    vs.upsert(
        project_id=project_id,
        ids=["f::0"],
        embeddings=[[1.0, 0.0]],
        documents=["old content"],
        metadatas=[{"file_path": "f.py", "language": "python", "line_start": 1, "line_end": 1}],
    )

    vs.upsert(
        project_id=project_id,
        ids=["f::0"],
        embeddings=[[0.0, 1.0]],
        documents=["new content"],
        metadatas=[{"file_path": "f.py", "language": "python", "line_start": 1, "line_end": 1}],
    )

    assert vs.get_chunk_count(project_id) == 1
    result = vs.query(project_id, [0.0, 1.0], n_results=1)
    assert "new content" in result["documents"][0][0]
