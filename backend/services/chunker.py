from dataclasses import dataclass
from config import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class Chunk:
    text: str
    metadata: dict


def chunk_text(
    content: str,
    file_path: str,
    language: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split text into overlapping chunks, preserving line number metadata."""
    if not content.strip():
        return []

    lines = content.split("\n")
    chunks = []
    current_chunk_lines: list[str] = []
    current_size = 0
    chunk_start_line = 1

    for i, line in enumerate(lines, start=1):
        line_len = len(line) + 1  # +1 for newline
        current_chunk_lines.append(line)
        current_size += line_len

        if current_size >= chunk_size:
            chunk_text_str = "\n".join(current_chunk_lines)
            chunks.append(Chunk(
                text=chunk_text_str,
                metadata={
                    "file_path": file_path,
                    "language": language,
                    "line_start": chunk_start_line,
                    "line_end": i,
                },
            ))

            # Calculate overlap: keep last N characters worth of lines
            overlap_lines: list[str] = []
            overlap_size = 0
            for ol in reversed(current_chunk_lines):
                overlap_size += len(ol) + 1
                if overlap_size > chunk_overlap:
                    break
                overlap_lines.insert(0, ol)

            current_chunk_lines = overlap_lines
            current_size = sum(len(l) + 1 for l in current_chunk_lines)
            chunk_start_line = i - len(overlap_lines) + 1

    # Remaining content
    if current_chunk_lines:
        chunk_text_str = "\n".join(current_chunk_lines)
        if chunk_text_str.strip():
            chunks.append(Chunk(
                text=chunk_text_str,
                metadata={
                    "file_path": file_path,
                    "language": language,
                    "line_start": chunk_start_line,
                    "line_end": len(lines),
                },
            ))

    return chunks
