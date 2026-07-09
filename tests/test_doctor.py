"""Tests for stubborn-watch doctor."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from stubborn_watch.cli import app
from stubborn_watch.doctor.models import DOCTOR_REPORT_SCHEMA, PACKAGE_ID
from stubborn_watch.doctor.run import run_doctor


def test_watch_doctor_json_schema(tmp_path: Path) -> None:
    report = run_doctor(tmp_path, fix_hint=False)
    payload = report.to_dict()
    assert payload["schema"] == DOCTOR_REPORT_SCHEMA
    assert payload["package"] == PACKAGE_ID


def test_watch_doctor_warns_without_indexer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("stubborn_watch.doctor.checks.shutil.which", lambda _: None)
    report = run_doctor(tmp_path, fix_hint=False)
    assert report.exit_code() == 2
    assert any(check.id == "watch.indexer" and check.status == "warn" for check in report.checks)


def test_watch_doctor_with_db(tmp_path: Path, monkeypatch) -> None:
    from stubborn.ingest.scip import load_scip_index
    from stubborn.store.writer import IndexWriter

    fixture = (
        Path(__file__).resolve().parents[2]
        / "stubborn"
        / "examples"
        / "fixtures"
        / "minimal.json"
    )
    db = tmp_path / "symbols.db"
    IndexWriter(db).write(load_scip_index(fixture))
    monkeypatch.setattr("stubborn_watch.doctor.checks.shutil.which", lambda name: "/usr/bin/scip-java")
    report = run_doctor(tmp_path, db_path=db, fix_hint=False)
    assert any(check.id == "watch.db" and check.status == "pass" for check in report.checks)


def test_watch_cli_help_lists_doctor() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "doctor" in result.stdout


def test_watch_cli_doctor_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("stubborn_watch.doctor.checks.shutil.which", lambda _: None)
    result = CliRunner().invoke(app, ["doctor", str(tmp_path), "--json", "--no-fix-hint"])
    assert result.exit_code in (0, 2)
    payload = json.loads(result.stdout)
    assert payload["package"] == PACKAGE_ID
