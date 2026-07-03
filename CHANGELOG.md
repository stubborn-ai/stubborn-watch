# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Workspace manifest watch mode for supervising multiple repo roots into one shared workspace `symbols.db`.
- `--workspace` / `--repo` forwarding for repo-scoped incremental merges.

## [0.1.0b1] - 2026-07-04

### Added

- `stubborn-watch` CLI with `watch` and `merge-once` commands.
- Debounced Java file watch -> external SCIP indexer -> `stubborn index --merge` orchestration.
- Package-level smoke tests for path normalization, subprocess invocation, debounce queueing, and merge CLI behavior.
- CI: pytest + ruff on Python 3.11-3.13.

[0.1.0b1]: https://github.com/stubborn-ai/stubborn-watch/releases/tag/v0.1.0b1
