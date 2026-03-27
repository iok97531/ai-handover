from pathlib import Path
import chardet
from config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_BYTES


def is_supported_file(file_path: Path) -> bool:
    """Check if a file should be parsed."""
    if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        return False
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        # Also support extensionless files like Makefile, Dockerfile
        if file_path.name not in {"Makefile", "Dockerfile", "Jenkinsfile", "Procfile"}:
            return False
    return True


def parse_file(file_path: Path) -> str | None:
    """Read a file and return its text content, or None if unsupported/binary."""
    if not file_path.is_file():
        return None
    if not is_supported_file(file_path):
        return None

    try:
        raw = file_path.read_bytes()
    except (OSError, PermissionError):
        return None

    # Detect if binary
    if b"\x00" in raw[:8192]:
        return None

    # Detect encoding
    detected = chardet.detect(raw[:10000])
    encoding = detected.get("encoding") or "utf-8"

    try:
        return raw.decode(encoding, errors="replace")
    except (UnicodeDecodeError, LookupError):
        return raw.decode("utf-8", errors="replace")


def detect_language(file_path: Path) -> str:
    """Detect the programming language from file extension."""
    ext_map = {
        ".py": "python", ".ts": "typescript", ".tsx": "tsx",
        ".js": "javascript", ".jsx": "jsx", ".java": "java",
        ".go": "go", ".rs": "rust", ".c": "c", ".cpp": "cpp",
        ".h": "c", ".hpp": "cpp", ".cs": "csharp", ".rb": "ruby",
        ".php": "php", ".swift": "swift", ".kt": "kotlin",
        ".scala": "scala", ".md": "markdown", ".json": "json",
        ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
        ".xml": "xml", ".html": "html", ".css": "css",
        ".scss": "scss", ".sql": "sql", ".sh": "bash",
        ".vue": "vue", ".svelte": "svelte",
    }
    return ext_map.get(file_path.suffix.lower(), "text")
