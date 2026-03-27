"""Tests for file watcher service."""
import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from services.file_watcher import FileWatcherService, FileChangeEvent, ProjectFileHandler


@pytest.fixture
def watcher():
    svc = FileWatcherService()
    yield svc
    svc.stop_all()


def test_initial_state(watcher):
    assert watcher.watching_project_ids == []
    assert watcher.is_watching("any") is False
    assert watcher.get_recent_events() == []


def test_start_stop_watching(watcher, tmp_path):
    callback = AsyncMock()
    watcher.start_watching("proj-1", str(tmp_path), callback)

    assert watcher.is_watching("proj-1")
    assert "proj-1" in watcher.watching_project_ids

    watcher.stop_watching("proj-1")
    assert not watcher.is_watching("proj-1")


def test_stop_watching_nonexistent(watcher):
    # Should not raise
    watcher.stop_watching("does-not-exist")


def test_stop_all(watcher, tmp_path):
    callback = AsyncMock()
    watcher.start_watching("p1", str(tmp_path), callback)
    watcher.start_watching("p2", str(tmp_path), callback)

    assert len(watcher.watching_project_ids) == 2

    watcher.stop_all()
    assert watcher.watching_project_ids == []


def test_start_watching_replaces_existing(watcher, tmp_path):
    callback = AsyncMock()
    watcher.start_watching("proj-1", str(tmp_path), callback)
    watcher.start_watching("proj-1", str(tmp_path), callback)

    assert watcher.watching_project_ids == ["proj-1"]


def test_start_watching_nonexistent_folder(watcher):
    callback = AsyncMock()
    watcher.start_watching("proj-1", "/nonexistent/path/xyz", callback)
    # Should silently skip
    assert not watcher.is_watching("proj-1")


def test_event_log_max_size():
    svc = FileWatcherService()
    # Manually push events beyond max
    for i in range(150):
        svc._event_log.append(FileChangeEvent(
            project_id="proj",
            event_type="modified",
            file_path=f"file_{i}.py",
        ))
    assert len(svc._event_log) == svc.MAX_LOG_SIZE


def test_get_recent_events_filters_by_project():
    svc = FileWatcherService()
    svc._event_log.append(FileChangeEvent("p1", "modified", "a.py"))
    svc._event_log.append(FileChangeEvent("p2", "created", "b.py"))
    svc._event_log.append(FileChangeEvent("p1", "deleted", "c.py"))

    p1_events = svc.get_recent_events("p1")
    assert len(p1_events) == 2
    assert all(e.project_id == "p1" for e in p1_events)

    all_events = svc.get_recent_events()
    assert len(all_events) == 3


def test_get_recent_events_limit():
    svc = FileWatcherService()
    for i in range(10):
        svc._event_log.append(FileChangeEvent("proj", "modified", f"f{i}.py"))

    events = svc.get_recent_events(limit=3)
    assert len(events) == 3
    # Should be the last 3
    assert events[0].file_path == "f7.py"


def test_handler_should_ignore():
    handler = ProjectFileHandler.__new__(ProjectFileHandler)
    handler.folder = Path("/project")

    from config import EXCLUDED_DIRS

    # Path inside excluded dir
    handler.folder = Path("/project")
    assert handler._should_ignore(str(Path("/project/node_modules/pkg/index.js"))) is True
    assert handler._should_ignore(str(Path("/project/.git/HEAD"))) is True

    # Normal path
    assert handler._should_ignore(str(Path("/project/src/main.py"))) is False


def test_handler_should_ignore_outside_folder():
    handler = ProjectFileHandler.__new__(ProjectFileHandler)
    handler.folder = Path("/project")
    # Path outside the project folder
    assert handler._should_ignore(str(Path("/other/file.py"))) is True


def test_file_change_event_defaults():
    before = time.time()
    evt = FileChangeEvent(project_id="p1", event_type="created", file_path="test.py")
    after = time.time()

    assert evt.project_id == "p1"
    assert evt.event_type == "created"
    assert evt.file_path == "test.py"
    assert before <= evt.timestamp <= after
