"""Workspace manifest loading for multi-repo watch mode."""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RepoManifest:
    repo_key: str
    root: Path
    scip_path: Path
    glob_pattern: str = "**/*.java"
    scip_command: list[str] | None = None


@dataclass(frozen=True)
class WorkspaceManifest:
    workspace: str
    db_path: Path
    repos: list[RepoManifest]
    debounce_seconds: float = 2.0


def _resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def _command(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return shlex.split(value)
    if isinstance(value, list) and all(isinstance(part, str) for part in value):
        return value
    raise ValueError("scip_cmd must be a string or list of strings")


def load_workspace_manifest(
    path: str | Path, *, db_override: Path | None = None
) -> WorkspaceManifest:
    manifest_path = Path(path)
    base = manifest_path.parent
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    workspace = str(payload.get("workspace") or "default")
    db_value = db_override or payload.get("db")
    if db_value is None:
        raise ValueError("workspace manifest requires 'db' or --db")

    repos: list[RepoManifest] = []
    for item in payload.get("repos", []):
        repo_key = item.get("repo_key") or item.get("repo")
        root = item.get("root")
        if not repo_key or not root:
            raise ValueError("each repo entry requires repo_key and root")
        repo_root = _resolve_path(base, root).resolve()
        scip = item.get("scip", "index.scip")
        repos.append(
            RepoManifest(
                repo_key=str(repo_key),
                root=repo_root,
                scip_path=_resolve_path(repo_root, scip),
                glob_pattern=str(item.get("pattern", "**/*.java")),
                scip_command=_command(item.get("scip_cmd")),
            )
        )

    if not repos:
        raise ValueError("workspace manifest requires at least one repo")

    return WorkspaceManifest(
        workspace=workspace,
        db_path=_resolve_path(base, db_value).resolve(),
        repos=repos,
        debounce_seconds=float(payload.get("debounce", 2.0)),
    )
