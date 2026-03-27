from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from config import EXCLUDED_DIRS


@dataclass
class FileChangeEvent:
    project_id: str
    event_type: str  # "created" | "modified" | "deleted"
    file_path: str
    timestamp: float = field(default_factory=time.time)


class ProjectFileHandler(FileSystemEventHandler):
    """Handles file system events for a project folder with debouncing."""

    def __init__(self, project_id: str, folder: Path, callback, event_log: deque):
        self.project_id = project_id
        self.folder = folder
        self.callback = callback
        self.event_log = event_log
        self._pending: dict[str, asyncio.TimerHandle] = {}
        self._lock = Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def _set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def _should_ignore(self, path: str) -> bool:
        try:
            rel = Path(path).relative_to(self.folder)
            return any(part in EXCLUDED_DIRS for part in rel.parts)
        except ValueError:
            return True

    def _schedule(self, event_type: str, path: str):
        if self._should_ignore(path):
            return
        if self._loop is None or self._loop.is_closed():
            return

        with self._lock:
            if path in self._pending:
                self._pending[path].cancel()

            def fire():
                rel_path = str(Path(path).relative_to(self.folder))
                self.event_log.append(FileChangeEvent(
                    project_id=self.project_id,
                    event_type=event_type,
                    file_path=rel_path,
                ))
                asyncio.run_coroutine_threadsafe(
                    self.callback(self.project_id, event_type, Path(path)),
                    self._loop,
                )
                with self._lock:
                    self._pending.pop(path, None)

            self._pending[path] = self._loop.call_later(0.5, fire)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._schedule("created", event.src_path)

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._schedule("modified", event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory:
            self._schedule("deleted", event.src_path)


class FileWatcherService:
    """Manages file watchers for all registered projects."""

    MAX_LOG_SIZE = 100

    def __init__(self):
        self._observers: dict[str, Observer] = {}
        self._handlers: dict[str, ProjectFileHandler] = {}
        self._event_log: deque[FileChangeEvent] = deque(maxlen=self.MAX_LOG_SIZE)

    @property
    def watching_project_ids(self) -> list[str]:
        return list(self._observers.keys())

    def is_watching(self, project_id: str) -> bool:
        return project_id in self._observers

    def get_recent_events(self, project_id: str | None = None, limit: int = 20) -> list[FileChangeEvent]:
        events = list(self._event_log)
        if project_id:
            events = [e for e in events if e.project_id == project_id]
        return events[-limit:]

    def start_watching(self, project_id: str, folder_path: str, callback, loop: asyncio.AbstractEventLoop | None = None):
        if project_id in self._observers:
            self.stop_watching(project_id)

        folder = Path(folder_path)
        if not folder.exists():
            return

        handler = ProjectFileHandler(project_id, folder, callback, self._event_log)
        if loop:
            handler._set_loop(loop)
        else:
            try:
                handler._set_loop(asyncio.get_running_loop())
            except RuntimeError:
                pass

        observer = Observer()
        observer.schedule(handler, str(folder), recursive=True)
        observer.daemon = True
        observer.start()

        self._observers[project_id] = observer
        self._handlers[project_id] = handler

    def stop_watching(self, project_id: str):
        observer = self._observers.pop(project_id, None)
        self._handlers.pop(project_id, None)
        if observer:
            observer.stop()
            observer.join(timeout=5)

    def stop_all(self):
        for project_id in list(self._observers.keys()):
            self.stop_watching(project_id)


_watcher: FileWatcherService | None = None


def get_file_watcher() -> FileWatcherService:
    global _watcher
    if _watcher is None:
        _watcher = FileWatcherService()
    return _watcher
