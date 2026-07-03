"""Debounced filesystem watch for incremental SCIP merge."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from stubborn_watch.manifest import WorkspaceManifest
from stubborn_watch.runner import merge_changed_paths, relative_source_path, run_scip_indexer


@dataclass
class WatchConfig:
    project_root: Path
    db_path: Path
    scip_path: Path
    debounce_seconds: float = 2.0
    glob_pattern: str = "**/*.java"
    scip_command: list[str] | None = None
    workspace: str | None = None
    repo_key: str | None = None


class _DebouncedMergeHandler(FileSystemEventHandler):
    def __init__(self, config: WatchConfig, *, write_lock: threading.Lock | None = None) -> None:
        self._config = config
        self._lock = threading.Lock()
        self._write_lock = write_lock or threading.Lock()
        self._pending: set[str] = set()
        self._timer: threading.Timer | None = None
        self._matcher = _glob_matcher(config.project_root, config.glob_pattern)

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not self._matcher(path):
            return
        rel = relative_source_path(self._config.project_root, path)
        with self._lock:
            self._pending.add(rel)
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._config.debounce_seconds, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            paths = set(self._pending)
            self._pending.clear()
            self._timer = None
        if not paths:
            return

        with self._write_lock:
            run_scip_indexer(self._config.project_root, command=self._config.scip_command)
            merge_changed_paths(
                project_root=self._config.project_root,
                db_path=self._config.db_path,
                scip_path=self._config.scip_path,
                changed_paths=paths,
                workspace=self._config.workspace,
                repo_key=self._config.repo_key,
            )


def _glob_matcher(project_root: Path, pattern: str):
    root = project_root.resolve()

    def matches(path: Path) -> bool:
        try:
            rel = path.resolve().relative_to(root)
        except ValueError:
            return False
        return rel.match(pattern)

    return matches


def run_watch(config: WatchConfig) -> None:
    """Block until interrupted, merging on debounced file changes."""
    handler = _DebouncedMergeHandler(config)
    observer = Observer()
    observer.schedule(handler, str(config.project_root), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def run_workspace_watch(manifest: WorkspaceManifest) -> None:
    """Block until interrupted, watching every repo in a workspace manifest."""
    observer = Observer()
    write_lock = threading.Lock()
    for repo in manifest.repos:
        config = WatchConfig(
            project_root=repo.root,
            db_path=manifest.db_path,
            scip_path=repo.scip_path,
            debounce_seconds=manifest.debounce_seconds,
            glob_pattern=repo.glob_pattern,
            scip_command=repo.scip_command,
            workspace=manifest.workspace,
            repo_key=repo.repo_key,
        )
        observer.schedule(
            _DebouncedMergeHandler(config, write_lock=write_lock),
            str(repo.root),
            recursive=True,
        )
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
