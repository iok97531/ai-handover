import uuid
from fastapi import APIRouter, HTTPException
from models.database import get_db
from models.schemas import ProjectCreate, ProjectResponse
from config import FREE_PLAN_MAX_PROJECTS

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects():
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, name, folder_path, file_count, chunk_count, last_indexed, status FROM projects ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.post("", response_model=ProjectResponse)
async def create_project(data: ProjectCreate):
    db = await get_db()

    # Check free plan project limit
    cursor = await db.execute("SELECT COUNT(*) FROM projects")
    count = (await cursor.fetchone())[0]
    if count >= FREE_PLAN_MAX_PROJECTS:
        raise HTTPException(
            403,
            f"무료 플랜은 프로젝트를 {FREE_PLAN_MAX_PROJECTS}개까지만 등록할 수 있습니다.",
        )

    # Check duplicate
    cursor = await db.execute("SELECT id FROM projects WHERE folder_path = ?", (data.folder_path,))
    if await cursor.fetchone():
        raise HTTPException(400, "이 폴더는 이미 등록되어 있습니다.")

    project_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO projects (id, name, folder_path) VALUES (?, ?, ?)",
        (project_id, data.name, data.folder_path),
    )
    await db.commit()

    return ProjectResponse(
        id=project_id,
        name=data.name,
        folder_path=data.folder_path,
        file_count=0,
        chunk_count=0,
        last_indexed=None,
        status="pending",
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    db = await get_db()

    cursor = await db.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
    if not await cursor.fetchone():
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")

    # Stop file watching
    from services.file_watcher import get_file_watcher
    get_file_watcher().stop_watching(project_id)

    # Delete from ChromaDB
    from vector_store.chroma import get_vector_store
    vs = get_vector_store()
    vs.delete_collection(project_id)

    await db.execute("DELETE FROM chat_history WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    await db.commit()

    return {"status": "deleted"}
