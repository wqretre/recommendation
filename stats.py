"""Per-category hit counters for the recommendation service.

Added to answer "which catalog category are we recommending most" without a
real metrics backend — a plain in-process counter, incremented on every
`get_recommendations` call and exposed via `/metrics`.
"""
from __future__ import annotations

import threading

_category_hits: dict[str, int] = {}

# Guards every access to _category_hits. The counters are touched from the
# ThreadingHTTPServer's per-request threads, and a read-modify-write ("read the
# current value, add one, write it back") is not atomic under the GIL — the two
# halves are separate bytecode sequences and a thread switch in between makes
# both threads write back the same value, silently dropping one increment.
_lock = threading.Lock()


def record_hit(category: str) -> None:
    """Increment the hit counter for `category`."""
    with _lock:
        _category_hits[category] = _category_hits.get(category, 0) + 1


def hit_count(category: str) -> int:
    with _lock:
        return _category_hits.get(category, 0)


def total_hits() -> int:
    # Sum under the lock so the iteration can't observe a concurrent insert
    # ("dict changed size during iteration") or a half-applied update.
    with _lock:
        return sum(_category_hits.values())
