import asyncio
from pathlib import Path
from datetime import datetime, timezone

import pathspec

from ai.provider import get_current_provider, AIProvider
from vector_store.chroma import get_vector_store, VectorStore
from services.parser import parse_file, detect_language, is_supported_file
from services.chunker import chunk_text, Chunk
from config import EXCLUDED_DIRS, EMBEDDING_BATCH_SIZE, DB_PATH


class IndexerService:
    def __init__(self, provider: AIProvider, vector_store: VectorStore):
        self.provider = provider
        self.vs = vector_store

    @classmethod
    async def create(cls) -> "IndexerService":
        provider = await get_current_provider()
        vs = get_vector_store()
        return cls(provider, vs)

    def _load_gitignore(self, folder: Path) -> pathspec.PathSpec | None:
        gitignore_path = folder / ".gitignore"
        if gitignore_path.exists():
            patterns = gitignore_path.read_text(errors="replace").splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return None

    def _walk_files(self, folder: Path) -> list[Path]:
        """Walk folder and return supported files, respecting exclusions."""
        gitignore = self._load_gitignore(folder)
        files = []

        for path in folder.rglob("*"):
            if not path.is_file():
                continue

            # Check excluded directories
            rel = path.relative_to(folder)
            parts = rel.parts
            if any(part in EXCLUDED_DIRS for part in parts):
                continue

            # Check gitignore
            if gitignore and gitignore.match_file(str(rel)):
                continue

            if is_supported_file(path):
                files.append(path)

        return files

    async def full_index(
        self,
        project_id: str,
        folder_path: str,
        progress: dict | None = None,
    ):
        """Full indexing of a project folder."""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {folder_path}")

        # Clear existing data
        self.vs.delete_collection(project_id)

        files = self._walk_files(folder)
        total_files = len(files)

        if progress is not None:
            progress[project_id] = {
                "status": "indexing",
                "files_total": total_files,
                "files_indexed": 0,
            }

        all_chunks: list[Chunk] = []
        indexed_count = 0

        for file_path in files:
            content = parse_file(file_path)
            if content is None:
                indexed_count += 1
                if progress is not None:
                    progress[project_id]["files_indexed"] = indexed_count
                continue

            language = detect_language(file_path)
            rel_path = str(file_path.relative_to(folder))
            chunks = chunk_text(content, rel_path, language)
            all_chunks.extend(chunks)

            indexed_count += 1
            if progress is not None:
                progress[project_id]["files_indexed"] = indexed_count

        # Embed and store in batches
        if all_chunks:
            for i in range(0, len(all_chunks), EMBEDDING_BATCH_SIZE):
                batch = all_chunks[i:i + EMBEDDING_BATCH_SIZE]
                texts = [c.text for c in batch]
                embeddings = await self.provider.embed(texts)

                ids = [f"{c.metadata['file_path']}::{i + j}" for j, c in enumerate(batch)]
                vectors = [e.vector for e in embeddings]
                documents = texts
                metadatas = [c.metadata for c in batch]

                self.vs.upsert(project_id, ids, vectors, documents, metadatas)

        # Update project in DB
        import aiosqlite
        async with aiosqlite.connect(str(DB_PATH)) as db:
            chunk_count = self.vs.get_chunk_count(project_id)
            now = datetime.now(timezone.utc).isoformat()
            await db.execute(
                "UPDATE projects SET status = 'ready', file_count = ?, chunk_count = ?, last_indexed = ? WHERE id = ?",
                (total_files, chunk_count, now, project_id),
            )
            await db.commit()

        if progress is not None:
            progress[project_id]["status"] = "ready"

    async def index_file(self, project_id: str, file_path: Path, folder: Path):
        """Index a single file (for incremental updates)."""
        rel_path = str(file_path.relative_to(folder))

        # Remove old chunks for this file
        self.vs.delete_by_file(project_id, rel_path)

        content = parse_file(file_path)
        if content is None:
            return

        language = detect_language(file_path)
        chunks = chunk_text(content, rel_path, language)

        if chunks:
            texts = [c.text for c in chunks]
            embeddings = await self.provider.embed(texts)

            ids = [f"{rel_path}::{j}" for j in range(len(chunks))]
            vectors = [e.vector for e in embeddings]
            documents = texts
            metadatas = [c.metadata for c in chunks]

            self.vs.upsert(project_id, ids, vectors, documents, metadatas)

    async def remove_file(self, project_id: str, file_path: Path, folder: Path):
        """Remove a file from the index."""
        rel_path = str(file_path.relative_to(folder))
        self.vs.delete_by_file(project_id, rel_path)
