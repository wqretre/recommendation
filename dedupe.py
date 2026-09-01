"""Dedupe helper for recommendation candidate ids.

Added so a single response never lists the same product twice, even if the
scoring step produced overlapping candidates from multiple sources (catalog +
personalized model).
"""
from __future__ import annotations


def dedupe_ids(product_ids: list[str]) -> list[str]:
    """Return product_ids with exact duplicates removed, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for pid in product_ids:
        key = pid
        if key not in seen:
            seen.add(key)
            out.append(pid)
    return out
