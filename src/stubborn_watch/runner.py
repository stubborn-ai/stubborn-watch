"""Run SCIP indexer and merge changed paths into SQLite."""

from __future__ import annotations

import subprocess
from pathlib import Path

from stubborn.ingest.scip import load_scip_index
from stubborn.store.writer import IndexWriter

DEFAULT_SCIP_COMMAND: tuple[str, ...] = ("scip-java", "index")


def run_scip_indexer(
    project_root: Path,
    *,
    command: list[str] | None = None,
) -> None:
    """Invoke an external SCIP indexer in the project root."""
    cmd = command or list(DEFAULT_SCIP_COMMAND)
    if not cmd:
        raise ValueError("SCIP indexer command must not be empty")
    subprocess.run(cmd, cwd=project_root, check=True)


def merge_changed_paths(
    *,
    project_root: Path,
    db_path: Path,
    scip_path: Path,
    changed_paths: set[str],
    workspace: str | None = None,
    repo_key: str | None = None,
) -> int:
    """Load SCIP output and merge only the given document paths."""
    snapshot = load_scip_index(scip_path, project_root=str(project_root))
    return IndexWriter(db_path).merge(
        snapshot,
        paths=changed_paths,
        workspace=workspace,
        repo_key=repo_key,
    )


def relative_source_path(project_root: Path, file_path: Path) -> str:
    """Normalize a changed file to SCIP relative_path form."""
    return file_path.resolve().relative_to(project_root.resolve()).as_posix()
