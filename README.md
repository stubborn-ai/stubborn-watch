# stubborn-watch

Debounced file watch → external SCIP indexer (scip-java) → [`stubborn index --merge`](https://github.com/stubborn-ai/stubborn/blob/main/docs/adr/ADR-009-incremental-index-merge.md).

Stubborn does **not** parse Java source. This package only orchestrates the dev loop described in [ADR-009](https://github.com/stubborn-ai/stubborn/blob/main/docs/adr/ADR-009-incremental-index-merge.md).

## Install

```bash
pip install stubborn-watch
```

Requires `scip-java` on `PATH` for the default indexer command.

## Usage

### Watch mode (dev loop)

```bash
stubborn index --scip index.scip --out symbols.db   # initial full snapshot
stubborn-watch watch --root . --db symbols.db
```

On save (debounced, default 2s):

1. `scip-java index`
2. `stubborn index --merge` for changed `relative_path` values

### One-shot merge (hooks / CI helpers)

```bash
stubborn-watch merge-once --root . --db symbols.db \
  --paths com/example/Foo.java,com/example/Bar.java
```

Use `--skip-index` when `index.scip` is already fresh.

### Workspace watch (multi-repo)

For source-available internal repos, use a workspace manifest so each repo can
index and merge independently into one shared workspace DB:

```json
{
  "workspace": "acme",
  "db": "symbols.db",
  "repos": [
    { "repo_key": "orders-api", "root": "../orders-api", "scip": "index.scip" },
    { "repo_key": "orders-core", "root": "../orders-core", "scip": "index.scip" }
  ]
}
```

```bash
stubborn-watch workspace-watch --manifest stubborn-workspace.json
stubborn context symbols.db --workspace acme --target "<stable_id>"
```

## Validation scope

This repo owns **orchestration-focused** validation:

- CLI smoke for `merge-once`
- debounce and path normalization
- subprocess invocation contracts around `scip-java`

The canonical ADR-009 runnable demo lives in `stubborn-demo`:

- [`stubborn-demo/demo-spring/scripts/run-merge-e2e.sh`](https://github.com/stubborn-ai/stubborn-demo/blob/main/demo-spring/scripts/run-merge-e2e.sh)

That keeps `stubborn-watch` focused on watch behavior, while `stubborn-demo` owns runnable demo assets and black-box validation projects.

## Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--root` | `.` | Project root |
| `--db` | (required) | SQLite symbol graph |
| `--scip` | `index.scip` | SCIP index path |
| `--debounce` | `2.0` | Seconds to coalesce events |
| `--pattern` | `**/*.java` | Watched file glob |
| `--scip-cmd` | `scip-java index` | External indexer command |
| `--workspace` | — | Workspace name for repo-scoped merges |
| `--repo` | — | Repo key for repo-scoped merges |

## Related

- [stubborn](https://github.com/stubborn-ai/stubborn) — core compiler + `--merge`
- [stubborn-mcp](https://github.com/stubborn-ai/stubborn-mcp) — MCP server over the same `symbols.db`
- [stubborn-demo](https://github.com/stubborn-ai/stubborn-demo) — runnable demos and validation projects
- [stubborn-hub](https://github.com/stubborn-ai/stubborn-hub) — program architecture

## License

MIT — see [LICENSE](LICENSE).
