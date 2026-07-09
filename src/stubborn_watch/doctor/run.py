"""Run stubborn-watch doctor."""

from __future__ import annotations

from pathlib import Path

from stubborn_watch import __version__
from stubborn_watch.doctor.checks import (
    delegation_checks,
    indexer_checks,
    manifest_checks,
    project_checks,
    runtime_checks,
)
from stubborn_watch.doctor.models import DoctorReport


def run_doctor(
    project_root: Path,
    *,
    db_path: Path | None = None,
    scip_path: Path | None = None,
    manifest: Path | None = None,
    scip_cmd: list[str] | None = None,
    fix_hint: bool = True,
) -> DoctorReport:
    root = project_root.resolve()
    scip = scip_path if scip_path is not None else (root / "index.scip")
    report = DoctorReport(version=__version__, cwd=str(root))
    report.checks.extend(runtime_checks())
    report.checks.extend(indexer_checks(scip_cmd))
    report.checks.extend(project_checks(root, db_path, scip))
    report.checks.extend(manifest_checks(manifest))
    if fix_hint:
        report.checks.extend(delegation_checks())
    return report
