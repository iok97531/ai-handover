import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.database import get_db
from models.schemas import IndexStatusResponse
from services.file_watcher import get_file_watcher

router = APIRouter(prefix="/api/index", tags=["index"])

# In-memory indexing progress tracker
_index_progress: dict[str, dict] = {}


async def _on_file_change(project_id: str, event_type: str, file_path: Path):
    """Callback invoked by file watcher when a project file changes."""
    from services.indexer import IndexerService
    from models.database import get_db as _get_db

    try:
        db = await _get_db()
        cursor = await db.execute("SELECT folder_path FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            return

        folder = Path(row["folder_path"])
        indexer = await IndexerService.create()

        if event_type == "deleted":
            await indexer.remove_file(project_id, file_path, folder)
        else:
            # created or modified
            if file_path.exists():
                await indexer.index_file(project_id, file_path, folder)
    except Exception as e:
        print(f"[FileWatcher] Incremental index error for {project_id}: {e}")


def start_watching_project(project_id: str, folder_path: str, loop: asyncio.AbstractEventLoop | None = None):
    """Start file watching for a project."""
    watcher = get_file_watcher()
    watcher.start_watching(project_id, folder_path, _on_file_change, loop=loop)


@router.post("/trigger/{project_id}")
async def trigger_index(project_id: str, background_tasks: BackgroundTasks):
    db = await get_db()
    cursor = await db.execute("SELECT id, folder_path FROM projects WHERE id = ?", (project_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")

    folder_path = row["folder_path"]

    # Stop existing watcher before re-indexing
    watcher = get_file_watcher()
    watcher.stop_watching(project_id)

    # Update status to indexing
    await db.execute("UPDATE projects SET status = 'indexing' WHERE id = ?", (project_id,))
    await db.commit()

    _index_progress[project_id] = {
        "status": "indexing",
        "files_total": 0,
        "files_indexed": 0,
    }

    background_tasks.add_task(_run_indexing, project_id, folder_path)

    return {"status": "indexing started"}


@router.get("/status/{project_id}", response_model=IndexStatusResponse)
async def get_index_status(project_id: str):
    progress = _index_progress.get(project_id)
    if not progress:
        db = await get_db()
        cursor = await db.execute(
            "SELECT status, file_count, chunk_count FROM projects WHERE id = ?", (project_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")
        return IndexStatusResponse(
            project_id=project_id,
            status=row["status"],
            files_total=row["file_count"],
            files_indexed=row["file_count"],
            progress_percent=100.0 if row["status"] == "ready" else 0.0,
        )

    total = progress["files_total"]
    indexed = progress["files_indexed"]
    percent = (indexed / total * 100) if total > 0 else 0

    return IndexStatusResponse(
        project_id=project_id,
        status=progress["status"],
        files_total=total,
        files_indexed=indexed,
        progress_percent=round(percent, 1),
    )


async def _run_indexing(project_id: str, folder_path: str):
    from services.indexer import IndexerService

    try:
        indexer = await IndexerService.create()
        await indexer.full_index(project_id, folder_path, _index_progress)

        # Start file watching after successful indexing
        loop = asyncio.get_running_loop()
        start_watching_project(project_id, folder_path, loop)

    except Exception as e:
        import traceback
        print(f"[Indexer] Error: {e}")
        traceback.print_exc()
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(str(DB_PATH)) as db:
            await db.execute("UPDATE projects SET status = 'error' WHERE id = ?", (project_id,))
            await db.commit()
        _index_progress[project_id] = {"status": "error", "files_total": 0, "files_indexed": 0}
    finally:
        # Clean up progress after some time
        await asyncio.sleep(10)
        _index_progress.pop(project_id, None)


@router.get("/watcher/status")
async def get_watcher_status():
    """Get file watching status for all projects."""
    watcher = get_file_watcher()
    return {
        "watching": watcher.watching_project_ids,
    }


@router.get("/watcher/events/{project_id}")
async def get_watcher_events(project_id: str, limit: int = 20):
    """Get recent file change events for a project."""
    watcher = get_file_watcher()
    events = watcher.get_recent_events(project_id, limit)
    return {
        "is_watching": watcher.is_watching(project_id),
        "events": [
            {
                "event_type": e.event_type,
                "file_path": e.file_path,
                "timestamp": e.timestamp,
            }
            for e in events
        ],
    }
