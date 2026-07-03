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

## Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--root` | `.` | Project root |
| `--db` | (required) | SQLite symbol graph |
| `--scip` | `index.scip` | SCIP index path |
| `--debounce` | `2.0` | Seconds to coalesce events |
| `--pattern` | `**/*.java` | Watched file glob |
| `--scip-cmd` | `scip-java index` | External indexer command |

## Related

- [stubborn](https://github.com/stubborn-ai/stubborn) — core compiler + `--merge`
- [stubborn-mcp](https://github.com/stubborn-ai/stubborn-mcp) — MCP server over the same `symbols.db`
- [stubborn-hub](https://github.com/stubborn-ai/stubborn-hub) — program architecture

## License

MIT — see [LICENSE](LICENSE).
