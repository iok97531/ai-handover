# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AI Handover is an Electron desktop application that indexes codebases and enables AI-powered chat about project structure and code. It combines a React frontend, Electron shell, and Python FastAPI backend with ChromaDB vector storage.

## Commands

### Frontend / Electron
```bash
npm install          # Install Node dependencies
npm run dev          # Start Electron app in development mode
npm run build        # Build with electron-vite
npm run build:win    # Build Windows installer (NSIS)
npm run build:unpack # Build and unpack for inspection
```

### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-optional.txt  # sentence-transformers for local embeddings
python -m uvicorn main:app --host 127.0.0.1 --port 8932  # Run backend standalone
pytest tests/ -v                          # Run all backend tests
pytest tests/test_rag.py -v               # Run a single test file
```

## Architecture

The app has three runtime layers:

1. **Electron main process** (`src/main/`) — Manages the BrowserWindow, spawns/monitors the Python backend process (`src/main/backend.ts`), handles IPC for folder dialogs and backend port exposure.

2. **React renderer** (`src/renderer/src/`) — Single-page app using Zustand for state (project list + chat per project), React Query for async ops, and SSE for streaming chat responses. API base URL is `http://127.0.0.1:8932`.

3. **FastAPI backend** (`backend/`) — Runs on port 8932, localhost only. Owns all AI logic, file indexing, and data persistence.

### Backend Data Flow

**Indexing:**
`Indexer` (walks folders, respects `.gitignore`) → `Parser` (encoding detection, language detection) → `Chunker` (800-char chunks, 200-char overlap) → AI provider embedding → ChromaDB upsert

**Chat (RAG):**
Question → embedding → ChromaDB similarity search (top 8 chunks) → format context with file paths/line numbers → stream LLM response via SSE

### Key Backend Services

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app entry, lifespan (DB init, watcher restore) |
| `backend/config.py` | All constants: port 8932, chunk sizes, excluded dirs, data paths |
| `backend/models/database.py` | SQLite schema: `projects`, `chat_history`, `settings` |
| `backend/services/rag.py` | RAG pipeline: embed query → retrieve → stream LLM |
| `backend/services/indexer.py` | File walking, incremental indexing, status tracking |
| `backend/services/file_watcher.py` | watchdog-based watchers with debounce |
| `backend/ai/provider.py` | Abstract AI provider interface + factory function |
| `backend/ai/openai_provider.py` | OpenAI embeddings + chat |
| `backend/ai/claude_provider.py` | Anthropic chat + local sentence-transformers for embeddings |

### Storage

- **SQLite** at `{userData}/data/app.db` — projects, chat history, encrypted settings
- **ChromaDB** at `{userData}/data/chroma` — one collection per project (`project_{id}`)
- API keys encrypted at rest using the `cryptography` library

### API Routes

- `GET/POST /api/projects`, `DELETE /api/projects/{id}`
- `POST /api/chat` — SSE streaming response
- `POST /api/index/trigger/{id}`, `GET /api/index/status/{id}`
- `GET/PUT /api/settings`
- `GET /health` — used by Electron to verify backend is ready

### Frontend Structure

- `src/renderer/src/stores/` — Zustand: `projectStore.ts`, `chatStore.ts`
- `src/renderer/src/components/` — Layout, Chat, Projects, Settings subdirectories
- `src/renderer/src/api/client.ts` — Axios-based API client
- `src/preload/index.ts` — IPC bridge: exposes `selectFolder()` and `getBackendPort()` to renderer

### Build Configuration

- `electron.vite.config.ts` — Vite config for all three entry points (main, preload, renderer)
- `@renderer` alias → `src/renderer/src`
- Electron builder: app ID `com.ai-handover.app`, Windows NSIS installer
