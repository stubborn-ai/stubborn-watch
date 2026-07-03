"""Tests for stubborn-watch orchestration."""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from stubborn_watch.cli import app
from stubborn_watch.manifest import load_workspace_manifest
from stubborn_watch.runner import merge_changed_paths, relative_source_path, run_scip_indexer
from stubborn_watch.watcher import WatchConfig, _DebouncedMergeHandler

RUNNER = CliRunner()


def test_relative_source_path_uses_posix(tmp_path: Path) -> None:
    root = tmp_path / "project"
    file_path = root / "com" / "example" / "Foo.java"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("class Foo {}", encoding="utf-8")

    assert relative_source_path(root, file_path) == "com/example/Foo.java"


@patch("stubborn_watch.runner.subprocess.run")
def test_run_scip_indexer_invokes_command(mock_run: MagicMock, tmp_path: Path) -> None:
    run_scip_indexer(tmp_path, command=["echo", "index"])
    mock_run.assert_called_once_with(["echo", "index"], cwd=tmp_path, check=True)


def test_merge_changed_paths_updates_db(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    project_root = tmp_path / "project"
    project_root.mkdir()
    db = tmp_path / "symbols.db"
    scip = fixtures / "two_documents_merged.json"

    from stubborn.ingest.scip import load_scip_index
    from stubborn.store.writer import IndexWriter

    base = load_scip_index(fixtures / "two_documents.json")
    IndexWriter(db).write(base, workspace="acme", repo_key="orders")

    run_id = merge_changed_paths(
        project_root=project_root,
        db_path=db,
        scip_path=scip,
        changed_paths={"com/example/OrderService.java"},
    )
    assert run_id == 1

    from stubborn.store.writer import read_info

    info = read_info(db)
    assert info.mode == "merged"
    assert info.symbol_count == 4
    assert info.edge_count == 2

    from stubborn.store.reader import list_symbols

    names = {s.display_name for s in list_symbols(db, limit=20)}
    assert "PaymentService" in names
    assert "Order" in names


def test_merge_once_cli_skip_index(tmp_path: Path) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    project_root = tmp_path / "project"
    project_root.mkdir()
    db = tmp_path / "symbols.db"

    from stubborn.ingest.scip import load_scip_index
    from stubborn.store.writer import IndexWriter, read_info

    base = load_scip_index(fixtures / "two_documents.json")
    IndexWriter(db).write(base, workspace="acme", repo_key="orders")

    result = RUNNER.invoke(
        app,
        [
            "merge-once",
            "--root",
            str(project_root),
            "--db",
            str(db),
            "--scip",
            str(fixtures / "two_documents_merged.json"),
            "--paths",
            "com/example/OrderService.java",
            "--skip-index",
            "--workspace",
            "acme",
            "--repo",
            "orders",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "Merged 1 path(s)" in result.stdout

    info = read_info(db)
    assert info.mode == "merged"
    assert info.merge_count == 1
    assert info.symbol_count == 4
    assert info.edge_count == 2
    assert info.workspace == "acme"
    assert info.repo_key == "orders"


def test_load_workspace_manifest_resolves_repo_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo-a"
    repo.mkdir()
    manifest = tmp_path / "stubborn-workspace.json"
    manifest.write_text(
        """
        {
          "workspace": "acme",
          "db": "symbols.db",
          "debounce": 1.5,
          "repos": [
            {
              "repo_key": "repo-a",
              "root": "repo-a",
              "scip": "target/index.scip",
              "pattern": "src/**/*.java",
              "scip_cmd": "echo index"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    loaded = load_workspace_manifest(manifest)
    assert loaded.workspace == "acme"
    assert loaded.db_path == (tmp_path / "symbols.db").resolve()
    assert loaded.debounce_seconds == 1.5
    assert loaded.repos[0].repo_key == "repo-a"
    assert loaded.repos[0].root == repo.resolve()
    assert loaded.repos[0].scip_path == repo.resolve() / "target" / "index.scip"
    assert loaded.repos[0].glob_pattern == "src/**/*.java"
    assert loaded.repos[0].scip_command == ["echo", "index"]


def test_workspace_handlers_can_share_write_lock(tmp_path: Path) -> None:
    root_a = tmp_path / "repo-a"
    root_b = tmp_path / "repo-b"
    root_a.mkdir()
    root_b.mkdir()
    lock = threading.Lock()

    handler_a = _DebouncedMergeHandler(
        WatchConfig(
            project_root=root_a,
            db_path=tmp_path / "symbols.db",
            scip_path=root_a / "index.scip",
            workspace="acme",
            repo_key="repo-a",
        ),
        write_lock=lock,
    )
    handler_b = _DebouncedMergeHandler(
        WatchConfig(
            project_root=root_b,
            db_path=tmp_path / "symbols.db",
            scip_path=root_b / "index.scip",
            workspace="acme",
            repo_key="repo-b",
        ),
        write_lock=lock,
    )

    assert handler_a._write_lock is lock
    assert handler_b._write_lock is lock


def test_debounced_handler_queues_paths(tmp_path: Path) -> None:
    root = tmp_path / "project"
    java = root / "com" / "example" / "Foo.java"
    java.parent.mkdir(parents=True)
    java.write_text("class Foo {}", encoding="utf-8")

    config = WatchConfig(
        project_root=root,
        db_path=tmp_path / "symbols.db",
        scip_path=root / "index.scip",
        debounce_seconds=3600,
    )
    handler = _DebouncedMergeHandler(config)

    class Event:
        is_directory = False
        src_path = str(java)

    handler.on_any_event(Event())
    assert "com/example/Foo.java" in handler._pending
