"""Debounced file watch → SCIP indexer → stubborn index --merge."""

__version__ = "0.1.0b3"

from stubborn_watch.runner import merge_changed_paths, run_scip_indexer
from stubborn_watch.watcher import WatchConfig, run_watch

__all__ = ["WatchConfig", "merge_changed_paths", "run_scip_indexer", "run_watch"]
