import pytest
import tempfile
from pathlib import Path
from services.parser import detect_language, parse_file, is_supported_file


# --- detect_language ---

def test_detect_python():
    assert detect_language(Path("test.py")) == "python"


def test_detect_typescript():
    assert detect_language(Path("app.tsx")) == "tsx"


def test_detect_unknown():
    assert detect_language(Path("file.xyz")) == "text"


def test_detect_markdown():
    assert detect_language(Path("README.md")) == "markdown"


def test_detect_case_insensitive():
    assert detect_language(Path("Main.JAVA")) == "java"


def test_detect_yaml_variants():
    assert detect_language(Path("config.yaml")) == "yaml"
    assert detect_language(Path("config.yml")) == "yaml"


# --- parse_file ---

def test_parse_file_reads_text(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("print('hello')", encoding="utf-8")
    result = parse_file(f)
    assert result == "print('hello')"


def test_parse_file_returns_none_for_missing():
    result = parse_file(Path("/nonexistent/file.py"))
    assert result is None


def test_parse_file_returns_none_for_binary(tmp_path):
    f = tmp_path / "image.py"
    f.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
    result = parse_file(f)
    assert result is None


def test_parse_file_returns_none_for_unsupported_extension(tmp_path):
    f = tmp_path / "data.bin"
    f.write_text("some text")
    result = parse_file(f)
    assert result is None


def test_parse_file_returns_none_for_large_file(tmp_path):
    f = tmp_path / "huge.py"
    f.write_text("x" * (2 * 1024 * 1024))  # 2MB > 1MB limit
    result = parse_file(f)
    assert result is None


def test_parse_file_handles_utf8_bom(tmp_path):
    f = tmp_path / "bom.py"
    f.write_bytes(b"\xef\xbb\xbfprint('hello')")
    result = parse_file(f)
    assert result is not None
    assert "print" in result


def test_parse_file_handles_non_utf8(tmp_path):
    f = tmp_path / "latin.py"
    f.write_bytes("café = 1".encode("latin-1"))
    result = parse_file(f)
    assert result is not None
    assert "caf" in result


# --- is_supported_file ---

def test_is_supported_file_python(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("x = 1")
    assert is_supported_file(f) is True


def test_is_supported_file_unknown_ext(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_text("stuff")
    assert is_supported_file(f) is False


def test_is_supported_file_makefile(tmp_path):
    f = tmp_path / "Makefile"
    f.write_text("all: build")
    assert is_supported_file(f) is True


def test_is_supported_file_dockerfile(tmp_path):
    f = tmp_path / "Dockerfile"
    f.write_text("FROM python:3.11")
    assert is_supported_file(f) is True
