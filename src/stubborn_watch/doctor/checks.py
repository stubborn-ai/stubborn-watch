"""Watch package doctor checks (ADR-015)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from stubborn.store.writer import read_info

from stubborn_watch import __version__
from stubborn_watch.doctor.models import Check
from stubborn_watch.runner import DEFAULT_SCIP_COMMAND


def runtime_checks() -> list[Check]:
    checks: list[Check] = []
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 11):
        checks.append(
            Check(
                id="runtime.python",
                status="fail",
                message=f"Python {major}.{minor} is below the required 3.11+",
            )
        )
    else:
        checks.append(Check(id="runtime.python", status="pass", message=f"Python {major}.{minor}"))

    try:
        import stubborn_watch  # noqa: F401
    except ImportError as exc:
        checks.append(
            Check(
                id="watch.import",
                status="fail",
                message=f"stubborn-watch not importable: {exc}",
                hint="pip install stubborn-watch",
            )
        )
        return checks

    checks.append(Check(id="watch.import", status="pass", message="stubborn-watch importable"))
    checks.append(Check(id="watch.version", status="info", message=f"stubborn-watch {__version__}"))
    return checks


def indexer_checks(scip_cmd: list[str] | None) -> list[Check]:
    command = scip_cmd or list(DEFAULT_SCIP_COMMAND)
    if not command:
        return [
            Check(
                id="watch.indexer",
                status="fail",
                message="SCIP indexer command is empty",
            )
        ]
    executable = command[0]
    if shutil.which(executable):
        return [
            Check(
                id="watch.indexer",
                status="pass",
                message=f"indexer on PATH: {' '.join(command)}",
            )
        ]
    return [
        Check(
            id="watch.indexer",
            status="warn",
            message=f"indexer not found on PATH: {executable}",
            hint="Install scip-java and ensure it is on PATH (stubborn-watch)",
        )
    ]


def project_checks(root: Path, db_path: Path | None, scip_path: Path) -> list[Check]:
    checks: list[Check] = []
    if not root.is_dir():
        checks.append(Check(id="watch.root", status="fail", message=f"project root missing: {root}"))
        return checks
    checks.append(Check(id="watch.root", status="pass", message=f"project root: {root}"))

    if scip_path.is_file():
        checks.append(Check(id="watch.scip", status="pass", message=f"SCIP index: {scip_path}"))
    else:
        checks.append(
            Check(
                id="watch.scip",
                status="warn",
                message=f"SCIP index not found: {scip_path}",
                hint="Run scip-java index in the project root before watch merge (stubborn-watch)",
            )
        )

    if db_path is None:
        checks.append(
            Check(
                id="watch.db",
                status="warn",
                message="no --db provided; cannot verify merge target",
                hint="stubborn-watch watch --db metadata/symbols.db --root . (stubborn-watch)",
            )
        )
        return checks

    if not db_path.is_file():
        checks.append(
            Check(
                id="watch.db",
                status="warn",
                message=f"merge target not found: {db_path}",
                hint="stubborn index --scip index.scip --out <db> before starting watch (stubborn-stub)",
            )
        )
        return checks

    checks.append(Check(id="watch.db", status="pass", message=f"merge target: {db_path}"))
    try:
        info = read_info(db_path, migrate=False)
        checks.append(
            Check(
                id="watch.db_index",
                status="pass",
                message=f"latest run {info.index_run_id}: symbols={info.symbol_count}, mode={info.mode}",
            )
        )
    except ValueError as exc:
        checks.append(
            Check(
                id="watch.db_index",
                status="warn",
                message=str(exc),
            )
        )
    return checks


def manifest_checks(manifest: Path | None) -> list[Check]:
    if manifest is None:
        return []
    if not manifest.is_file():
        return [
            Check(
                id="watch.manifest",
                status="fail",
                message=f"workspace manifest not found: {manifest}",
            )
        ]
    return [
        Check(
            id="watch.manifest",
            status="pass",
            message=f"workspace manifest: {manifest}",
        )
    ]


def delegation_checks() -> list[Check]:
    return [
        Check(
            id="delegate.core",
            status="info",
            message="ingest and graph health are diagnosed by stubborn-stub",
            hint="Run: stubborn doctor (stubborn-stub package)",
        )
    ]
