# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.10.0b1] - 2026-07-12

### Changed

- Align program-wide PyPI version line to **0.10.0b1** (unified release matrix).
- `stubborn-watch` now expects `stubborn-stub>=0.10.0b1`, matching the unified core release line.

## [0.1.0b3] - 2026-07-12

### Added

- **`stubborn-watch doctor`** — read-only watch-loop setup diagnostics per [ADR-015](https://github.com/stubborn-ai/stubborn/blob/main/docs/adr/ADR-015-federated-doctor-diagnostics.md) (`--json`).

### Fixed

- **`stubborn-watch doctor`** no longer migrates legacy `symbols.db` schema during inspection (`read_info(..., migrate=False)`).

### Changed

- `stubborn-watch` now expects `stubborn-stub>=0.9.0b6`, matching the bundled-fixture and doctor release line.

## [0.1.0b2] - 2026-07-05

### Added

- Workspace manifest watch mode for supervising multiple repo roots into one shared workspace `symbols.db`.
- `--workspace` / `--repo` forwarding for repo-scoped incremental merges.

### Changed

- `stubborn-watch` now expects `stubborn-stub>=0.9.0b5`, matching the current core release line.

## [0.1.0b1] - 2026-07-04

### Added

- `stubborn-watch` CLI with `watch` and `merge-once` commands.
- Debounced Java file watch -> external SCIP indexer -> `stubborn index --merge` orchestration.
- Package-level smoke tests for path normalization, subprocess invocation, debounce queueing, and merge CLI behavior.
- CI: pytest + ruff on Python 3.11-3.13.

[0.10.0b1]: https://github.com/stubborn-ai/stubborn-watch/compare/v0.1.0b3...v0.10.0b1
[0.1.0b1]: https://github.com/stubborn-ai/stubborn-watch/releases/tag/v0.1.0b1
[0.1.0b3]: https://github.com/stubborn-ai/stubborn-watch/compare/v0.1.0b2...v0.1.0b3
[0.1.0b2]: https://github.com/stubborn-ai/stubborn-watch/compare/v0.1.0b1...v0.1.0b2
