"""Regression test for stats.py — concurrent hit recording must not lose
increments. Drives many threads hammering record_hit() at once; against the
unbounded read-modify-write race this reliably undercounts under CPython's
GIL thread switching, and passes once the increment is made atomic (e.g. a
threading.Lock around the read-modify-write)."""
from __future__ import annotations

import sys
import threading

import stats


def test_record_hit_is_thread_safe():
    # Force frequent GIL switches so the read-modify-write race actually
    # interleaves within this short test, instead of relying on scheduling luck.
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    # 50x200 was too little work to interleave reliably — it passed against the
    # racy implementation on every run. 16x50000 loses ~65-75% of the increments
    # without a lock, so this genuinely fails before the fix and passes after.
    threads_n = 16
    increments_per_thread = 50000
    expected_total = threads_n * increments_per_thread

    def worker():
        for _ in range(increments_per_thread):
            stats.record_hit("electronics")

    threads = [threading.Thread(target=worker) for _ in range(threads_n)]
    try:
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        sys.setswitchinterval(old_interval)

    assert stats.hit_count("electronics") == expected_total, (
        f"lost increments under concurrent load: expected {expected_total}, "
        f"got {stats.hit_count('electronics')} (race on the shared counter)"
    )
