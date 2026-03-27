from fastapi import APIRouter
from models.database import get_db
from models.schemas import SettingsUpdate, SettingsResponse
from services.crypto import encrypt, decrypt

router = APIRouter(prefix="/api/settings", tags=["settings"])

_ENCRYPTED_KEYS = {"api_key"}


@router.get("", response_model=SettingsResponse)
async def get_settings():
    db = await get_db()
    cursor = await db.execute("SELECT key, value FROM settings")
    rows = await cursor.fetchall()
    settings = {}
    for row in rows:
        key, value = row["key"], row["value"]
        if key in _ENCRYPTED_KEYS:
            value = decrypt(value)
        settings[key] = value
    return SettingsResponse(
        ai_provider=settings.get("ai_provider", "openai"),
        api_key=settings.get("api_key", ""),
        chat_model=settings.get("chat_model", ""),
        embedding_model=settings.get("embedding_model", ""),
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(data: SettingsUpdate):
    db = await get_db()

    # Check if provider is changing (requires re-indexing due to different embedding dimensions)
    provider_changed = False
    if data.ai_provider is not None:
        cursor = await db.execute("SELECT value FROM settings WHERE key = 'ai_provider'")
        row = await cursor.fetchone()
        if row and row["value"] != data.ai_provider:
            provider_changed = True

    for key, value in data.model_dump(exclude_none=True).items():
        if key in _ENCRYPTED_KEYS and value:
            value = encrypt(value)
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
    await db.commit()

    result = await get_settings()
    response = result.model_dump()
    if provider_changed:
        response["provider_changed"] = True
    return response
