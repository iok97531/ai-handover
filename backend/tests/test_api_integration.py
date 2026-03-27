"""Integration tests for FastAPI endpoints using httpx TestClient."""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock

import httpx
from httpx import ASGITransport


@pytest.fixture
def sample_project_dir(tmp_path):
    """Create a sample project directory with test files."""
    proj = tmp_path / "sample_project"
    proj.mkdir()

    (proj / "main.py").write_text(
        "def main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()\n",
        encoding="utf-8",
    )
    (proj / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n",
        encoding="utf-8",
    )
    (proj / "README.md").write_text(
        "# Sample Project\n\nThis is a test project for integration testing.\n",
        encoding="utf-8",
    )

    sub = proj / "src"
    sub.mkdir()
    (sub / "app.ts").write_text(
        "export function greet(name: string): string {\n  return `Hello, ${name}!`\n}\n",
        encoding="utf-8",
    )

    # Files that should be skipped
    node_modules = proj / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.json").write_text("{}", encoding="utf-8")

    return proj


@pytest.fixture
async def test_client(tmp_path):
    """Create a test client with isolated DB and ChromaDB."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    chroma_dir = data_dir / "chroma"
    chroma_dir.mkdir()
    db_path = data_dir / "app.db"

    with patch("config.DATA_DIR", data_dir), \
         patch("config.DB_PATH", db_path), \
         patch("config.CHROMA_DIR", chroma_dir), \
         patch("vector_store.chroma._client", None), \
         patch("vector_store.chroma._store", None), \
         patch("models.database._db", None):

        from main import app
        from models.database import init_db, close_db

        await init_db()

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        await close_db()


@pytest.mark.asyncio
async def test_health(test_client):
    resp = await test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_settings_get_defaults(test_client):
    resp = await test_client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_provider"] == "openai"
    assert data["api_key"] == ""


@pytest.mark.asyncio
async def test_settings_update(test_client):
    resp = await test_client.put("/api/settings", json={
        "ai_provider": "claude",
        "api_key": "sk-ant-test"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_provider"] == "claude"
    assert data["api_key"] == "sk-ant-test"


@pytest.mark.asyncio
async def test_project_crud(test_client, sample_project_dir):
    # Create
    resp = await test_client.post("/api/projects", json={
        "name": "Test Project",
        "folder_path": str(sample_project_dir)
    })
    assert resp.status_code == 200
    project = resp.json()
    assert project["name"] == "Test Project"
    assert project["status"] == "pending"
    project_id = project["id"]

    # List
    resp = await test_client.get("/api/projects")
    assert resp.status_code == 200
    projects = resp.json()
    assert len(projects) == 1
    assert projects[0]["id"] == project_id

    # Duplicate should fail
    resp = await test_client.post("/api/projects", json={
        "name": "Duplicate",
        "folder_path": str(sample_project_dir)
    })
    assert resp.status_code == 400

    # Delete
    resp = await test_client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 200

    # Verify deleted
    resp = await test_client.get("/api/projects")
    assert resp.json() == []


@pytest.mark.asyncio
async def test_project_delete_nonexistent(test_client):
    resp = await test_client.delete("/api/projects/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_index_status_no_project(test_client):
    resp = await test_client.get("/api/index/status/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_requires_ready_project(test_client, sample_project_dir):
    # Create a project (status = pending)
    resp = await test_client.post("/api/projects", json={
        "name": "Not Indexed",
        "folder_path": str(sample_project_dir)
    })
    project_id = resp.json()["id"]

    # Try to chat - should fail because not indexed
    resp = await test_client.post("/api/chat", json={
        "project_id": project_id,
        "question": "What does this project do?",
        "chat_history": []
    })
    assert resp.status_code == 400
