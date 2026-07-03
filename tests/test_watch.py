"""Tests for stubborn-watch orchestration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from stubborn_watch.cli import app
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
    IndexWriter(db).write(base)

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
    IndexWriter(db).write(base)

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
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "Merged 1 path(s)" in result.stdout

    info = read_info(db)
    assert info.mode == "merged"
    assert info.merge_count == 1
    assert info.symbol_count == 4
    assert info.edge_count == 2


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
