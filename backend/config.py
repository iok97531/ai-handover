import os
from pathlib import Path

# Server
HOST = "127.0.0.1"
PORT = 8932

# Data directory
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = DATA_DIR / "app.db"

# ChromaDB
CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Indexing
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
EMBEDDING_BATCH_SIZE = 50
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1MB

EXCLUDED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "target", ".idea", ".vscode",
    "out", ".cache", ".tox", "eggs", "*.egg-info",
}

SUPPORTED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".md", ".txt", ".json", ".yaml", ".yml",
    ".toml", ".xml", ".html", ".css", ".scss", ".sql", ".sh",
    ".bat", ".ps1", ".dockerfile", ".env.example", ".gitignore",
    ".conf", ".cfg", ".ini", ".vue", ".svelte",
}
