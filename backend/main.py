import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import HOST, PORT
from models.database import init_db, close_db, get_db
from routers import projects, chat, index, settings
from routers.index import start_watching_project
from services.file_watcher import get_file_watcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    # Restore file watchers for all 'ready' projects
    try:
        db = await get_db()
        cursor = await db.execute("SELECT id, folder_path FROM projects WHERE status = 'ready'")
        rows = await cursor.fetchall()
        loop = asyncio.get_running_loop()
        for row in rows:
            start_watching_project(row["id"], row["folder_path"], loop)
        if rows:
            print(f"[FileWatcher] Restored watchers for {len(rows)} project(s)")
    except Exception as e:
        print(f"[FileWatcher] Failed to restore watchers: {e}")

    yield

    get_file_watcher().stop_all()
    await close_db()


app = FastAPI(title="AI Handover Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(chat.router)
app.include_router(index.router)
app.include_router(settings.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
