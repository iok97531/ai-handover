import subprocess
from pathlib import Path


def is_git_repo(folder_path: str) -> bool:
    return (Path(folder_path) / ".git").exists()


def get_git_context(folder_path: str, max_commits: int = 30) -> str:
    """
    Returns a formatted string of recent git commit history for LLM context.
    Returns empty string if not a git repo or git is unavailable.
    """
    if not is_git_repo(folder_path):
        return ""

    try:
        result = subprocess.run(
            [
                "git", "log",
                f"--max-count={max_commits}",
                "--pretty=format:커밋: %h | 날짜: %ad | 작성자: %an%n메시지: %s",
                "--date=format:%Y-%m-%d",
                "--name-status",
            ],
            cwd=folder_path,
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""

    if result.returncode != 0 or not result.stdout.strip():
        return ""

    lines = result.stdout.strip().splitlines()
    blocks: list[str] = []
    current: list[str] = []

    for line in lines:
        if line.startswith("커밋:"):
            if current:
                blocks.append("\n".join(current))
            current = [line]
        elif line.strip():
            # Translate git status letters for readability
            if len(line) >= 2 and line[0] in ("M", "A", "D", "R", "C") and line[1] == "\t":
                status_map = {"M": "수정", "A": "추가", "D": "삭제", "R": "이름변경", "C": "복사"}
                status = status_map.get(line[0], line[0])
                current.append(f"  [{status}] {line[2:]}")
            else:
                current.append(line)

    if current:
        blocks.append("\n".join(current))

    if not blocks:
        return ""

    return "=== Git 변경 이력 ===\n\n" + "\n\n---\n\n".join(blocks)
