"""Executable checks for loaded-code-aware UCNS provenance and cache reuse."""

# === CHECKS ===
# id: check_epac_ucns_pin_matches_loaded_code
#   proves: epac_ucns_pin_matches_loaded_code
#   call: self::test_loaded_code_mismatch_returns_hmmm
#   mutates: none
#   cleanup: clears verification cache
#
# id: check_epac_ucns_verification_reuses_only_identical_witness
#   proves: epac_ucns_verification_reuses_only_identical_witness
#   call: self::test_unchanged_witness_runs_git_once
#   mutates: in-memory verification cache
#   cleanup: clears verification cache
# === END CHECKS ===

from __future__ import annotations

import inspect
import subprocess
import unittest

from epac_ucns_provenance import (
    clear_ucns_verification_cache,
    ucns_verification_cache_info,
    verify_loaded_ucns_commit,
)
from epac_public_gonol import PINNED_UCNS_COMMIT
from ucns import native_mobius_state, public_gonol_function


class UcnsProvenanceTest(unittest.TestCase):
    def tearDown(self) -> None:
        clear_ucns_verification_cache()

    def test_loaded_code_mismatch_returns_hmmm(self) -> None:
        namespace: dict[str, object] = {}
        exec(
            compile(
                "def public_gonol_function(value):\n    return value\n",
                inspect.getfile(public_gonol_function),
                "exec",
            ),
            namespace,
        )
        stale_function = namespace["public_gonol_function"]

        observed = verify_loaded_ucns_commit(
            pinned_commit=PINNED_UCNS_COMMIT,
            dependencies=(stale_function, native_mobius_state),
        )

        self.assertEqual(observed, "hmmm")

    def test_unchanged_witness_runs_git_once(self) -> None:
        calls: list[tuple[str, ...]] = []

        def counting_runner(command, **kwargs):
            calls.append(tuple(command))
            return subprocess.run(command, **kwargs)

        clear_ucns_verification_cache()
        first = verify_loaded_ucns_commit(
            pinned_commit=PINNED_UCNS_COMMIT,
            dependencies=(public_gonol_function, native_mobius_state),
            runner=counting_runner,
        )
        first_call_count = len(calls)
        second = verify_loaded_ucns_commit(
            pinned_commit=PINNED_UCNS_COMMIT,
            dependencies=(public_gonol_function, native_mobius_state),
            runner=counting_runner,
        )

        self.assertEqual(first, PINNED_UCNS_COMMIT)
        self.assertEqual(second, PINNED_UCNS_COMMIT)
        self.assertGreater(first_call_count, 0)
        self.assertEqual(len(calls), first_call_count)
        self.assertEqual(ucns_verification_cache_info().hits, 1)


if __name__ == "__main__":
    unittest.main()
