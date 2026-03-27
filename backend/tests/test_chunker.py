import pytest
from services.chunker import chunk_text, Chunk


def test_empty_input():
    chunks = chunk_text("", "test.py", "python")
    assert chunks == []


def test_whitespace_only():
    chunks = chunk_text("   \n\n  ", "test.py", "python")
    assert chunks == []


def test_small_file_single_chunk():
    content = "print('hello world')"
    chunks = chunk_text(content, "test.py", "python", chunk_size=1000)
    assert len(chunks) == 1
    assert chunks[0].text == content
    assert chunks[0].metadata["file_path"] == "test.py"
    assert chunks[0].metadata["language"] == "python"
    assert chunks[0].metadata["line_start"] == 1
    assert chunks[0].metadata["line_end"] == 1


def test_large_file_multiple_chunks():
    lines = [f"line {i}" for i in range(200)]
    content = "\n".join(lines)
    chunks = chunk_text(content, "big.py", "python", chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.metadata["file_path"] == "big.py"
        assert chunk.metadata["line_start"] >= 1
        assert chunk.metadata["line_end"] >= chunk.metadata["line_start"]


def test_metadata_preserved():
    content = "def foo():\n    return 42\n"
    chunks = chunk_text(content, "src/utils.py", "python")
    assert chunks[0].metadata["file_path"] == "src/utils.py"
    assert chunks[0].metadata["language"] == "python"


def test_overlap_contains_shared_content():
    """Consecutive chunks should share overlapping content."""
    # 50 lines of ~20 chars each = ~1000 chars total
    lines = [f"content line {i:04d}xx" for i in range(50)]
    content = "\n".join(lines)
    chunks = chunk_text(content, "a.py", "python", chunk_size=200, chunk_overlap=60)
    assert len(chunks) >= 3

    for i in range(len(chunks) - 1):
        current_lines = set(chunks[i].text.split("\n"))
        next_lines = set(chunks[i + 1].text.split("\n"))
        overlap = current_lines & next_lines
        assert len(overlap) > 0, f"Chunk {i} and {i+1} have no overlapping lines"


def test_line_numbers_cover_entire_file():
    """All lines in the file should be covered by at least one chunk."""
    lines = [f"line {i}" for i in range(100)]
    content = "\n".join(lines)
    chunks = chunk_text(content, "a.py", "python", chunk_size=100, chunk_overlap=20)

    covered = set()
    for chunk in chunks:
        for ln in range(chunk.metadata["line_start"], chunk.metadata["line_end"] + 1):
            covered.add(ln)

    for ln in range(1, 101):
        assert ln in covered, f"Line {ln} not covered by any chunk"


def test_single_line_file():
    content = "x = 1"
    chunks = chunk_text(content, "one.py", "python")
    assert len(chunks) == 1
    assert chunks[0].metadata["line_start"] == 1
    assert chunks[0].metadata["line_end"] == 1


def test_chunk_size_boundary():
    """Content exactly at chunk_size should produce a chunk."""
    content = "a" * 100
    chunks = chunk_text(content, "exact.py", "python", chunk_size=100, chunk_overlap=0)
    assert len(chunks) >= 1


def test_multiline_with_varied_lengths():
    """Lines of different lengths should still chunk correctly."""
    lines = ["short", "a" * 500, "medium length line", "b" * 300, "end"]
    content = "\n".join(lines)
    chunks = chunk_text(content, "varied.py", "python", chunk_size=200, chunk_overlap=50)
    assert len(chunks) >= 2
    full_text = "\n".join(c.text for c in chunks)
    for line in lines:
        assert line in full_text
