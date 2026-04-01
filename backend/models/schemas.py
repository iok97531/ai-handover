from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    folder_path: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    folder_path: str
    file_count: int
    chunk_count: int
    last_indexed: str | None
    status: str


class ChatRequest(BaseModel):
    project_id: str
    question: str
    chat_history: list[dict] = []
    include_git_history: bool = False


class IndexStatusResponse(BaseModel):
    project_id: str
    status: str
    files_total: int
    files_indexed: int
    progress_percent: float


class SettingsUpdate(BaseModel):
    ai_provider: str | None = None
    api_key: str | None = None
    chat_model: str | None = None
    embedding_model: str | None = None


class SettingsResponse(BaseModel):
    ai_provider: str
    api_key: str
    chat_model: str
    embedding_model: str
