import json
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from models.database import get_db
from models.schemas import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest):
    db = await get_db()
    cursor = await db.execute("SELECT id, status, folder_path FROM projects WHERE id = ?", (request.project_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")
    if row["status"] != "ready":
        raise HTTPException(400, "프로젝트 인덱싱이 아직 완료되지 않았습니다.")

    git_context: str | None = None
    if request.include_git_history:
        from services.git_service import get_git_context
        git_context = get_git_context(row["folder_path"]) or None

    from services.rag import RAGService
    rag = await RAGService.create()

    async def generate():
        try:
            async for token in rag.query_stream(
                project_id=request.project_id,
                question=request.question,
                chat_history=request.chat_history,
                git_context=git_context,
            ):
                yield {"data": json.dumps({"token": token})}
            yield {"data": "[DONE]"}
        except Exception as e:
            yield {"data": json.dumps({"error": str(e)})}

    return EventSourceResponse(generate())
