"""CLI entry point for stubborn-watch."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from stubborn_watch.manifest import load_workspace_manifest
from stubborn_watch.runner import merge_changed_paths, run_scip_indexer
from stubborn_watch.watcher import WatchConfig, run_watch, run_workspace_watch

app = typer.Typer(
    name="stubborn-watch",
    help="Dev orchestration: file watch → SCIP indexer → stubborn index --merge",
    no_args_is_help=True,
)


def _parse_paths(paths: str) -> set[str]:
    return {part.strip() for part in paths.split(",") if part.strip()}


@app.command("watch")
def watch_cmd(
    root: Path = typer.Option(
        Path.cwd(),
        "--root",
        "-r",
        help="Project root to watch and pass to the SCIP indexer",
    ),
    db: Path = typer.Option(..., "--db", help="SQLite symbol graph path (merge target)"),
    scip: Path = typer.Option(
        Path("index.scip"),
        "--scip",
        help="SCIP index path relative to --root unless absolute",
    ),
    debounce: float = typer.Option(2.0, "--debounce", help="Seconds to debounce file events"),
    pattern: str = typer.Option("**/*.java", "--pattern", help="Glob for watched source files"),
    scip_cmd: Optional[str] = typer.Option(
        None,
        "--scip-cmd",
        help='Indexer command (default: "scip-java index"), shell-split',
    ),
    workspace: Optional[str] = typer.Option(None, "--workspace", help="Workspace name"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repo key in the workspace"),
) -> None:
    """Watch source files, re-index with scip-java, and merge into symbols.db."""
    root = root.resolve()
    scip_path = scip if scip.is_absolute() else root / scip
    indexer = scip_cmd.split() if scip_cmd else None
    config = WatchConfig(
        project_root=root,
        db_path=db.resolve(),
        scip_path=scip_path,
        debounce_seconds=debounce,
        glob_pattern=pattern,
        scip_command=indexer,
        workspace=workspace,
        repo_key=repo,
    )
    run_watch(config)


@app.command("workspace-watch")
def workspace_watch_cmd(
    manifest: Path = typer.Option(..., "--manifest", "-m", help="Workspace manifest JSON"),
    db: Optional[Path] = typer.Option(None, "--db", help="Override manifest db path"),
) -> None:
    """Watch all repos listed in a workspace manifest."""
    run_workspace_watch(load_workspace_manifest(manifest, db_override=db.resolve() if db else None))


@app.command("merge-once")
def merge_once_cmd(
    root: Path = typer.Option(Path.cwd(), "--root", "-r", help="Project root"),
    db: Path = typer.Option(..., "--db", help="SQLite symbol graph path"),
    scip: Path = typer.Option(Path("index.scip"), "--scip", help="SCIP index path"),
    paths: str = typer.Option(..., "--paths", help="Comma-separated relative_path values"),
    skip_index: bool = typer.Option(
        False,
        "--skip-index",
        help="Skip running the SCIP indexer (use existing --scip file)",
    ),
    scip_cmd: Optional[str] = typer.Option(None, "--scip-cmd", help="Indexer command override"),
    workspace: Optional[str] = typer.Option(None, "--workspace", help="Workspace name"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repo key in the workspace"),
) -> None:
    """Run indexer once and merge the given paths (for hooks and tests)."""
    root = root.resolve()
    scip_path = scip if scip.is_absolute() else root / scip
    changed = _parse_paths(paths)
    if not changed:
        raise typer.BadParameter("--paths must list at least one relative path")

    indexer = scip_cmd.split() if scip_cmd else None
    if not skip_index:
        run_scip_indexer(root, command=indexer)
    index_run_id = merge_changed_paths(
        project_root=root,
        db_path=db.resolve(),
        scip_path=scip_path,
        changed_paths=changed,
        workspace=workspace,
        repo_key=repo,
    )
    typer.echo(f"Merged {len(changed)} path(s) into {db} (index_run_id={index_run_id})")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
