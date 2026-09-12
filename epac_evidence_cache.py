"""Internal cache boundary for independently returned EPAC evidence.

Usage: decorate a deterministic builder with ``@_independent_cached(maxsize=1)``.
The cached canonical result remains private; every call receives an independent
copy. Builders with immutable receipt objects may supply a copier for their
mutable evidence fields. Cache controls and uncached execution remain available.
"""
# === MODULE_BUILD ===
# id: epac_evidence_cache
#   module_name: epac_evidence_cache
#   module_kind: library
#   summary: keeps canonical cached evidence private from caller annotations
#   owner: The Interdependency
#   public_surface: none; internal decorator for package evidence builders
#   internal_surface: _independent_cached
#   auth_boundary: none
#   storage_boundary: memory
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests/test_evidence_cache.py
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: epac_cached_evidence_returns_independent_values
#   given: a caller mutates returned construction or audit evidence
#   then: later calls retain the canonical cached evidence
#   class: correctness
# === END CONTRACTS ===
from copy import deepcopy
from functools import lru_cache, wraps


def _independent_cached(*, maxsize, copier=deepcopy):
    def decorate(function):
        cached = lru_cache(maxsize=maxsize)(function)

        @wraps(function)
        def independent(*args, **kwargs):
            return copier(cached(*args, **kwargs))

        independent.cache_clear = cached.cache_clear
        independent.cache_info = cached.cache_info
        return independent

    return decorate


__all__ = ()
