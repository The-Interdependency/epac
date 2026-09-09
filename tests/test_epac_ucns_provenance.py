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
#
# id: check_epac_ucns_pin_compares_pinned_blob_bytes
#   proves: epac_ucns_pin_matches_loaded_code
#   call: self::test_pinned_blob_mismatch_returns_hmmm
#   mutates: none
#   cleanup: clears verification cache
# === END CHECKS ===

from __future__ import annotations

import inspect
import subprocess
import unittest

from epac_ucns_provenance import (
    _git_blob_mode,
    clear_ucns_verification_cache,
    ucns_verification_cache_info,
    verify_loaded_ucns_commit,
)
from epac_public_gonol import PINNED_UCNS_COMMIT
from ucns import native_mobius_state, public_gonol_function


class UcnsProvenanceTest(unittest.TestCase):
    def tearDown(self) -> None:
        clear_ucns_verification_cache()

    def test_filesystem_permissions_normalize_to_git_blob_modes(self) -> None:
        self.assertEqual(_git_blob_mode(0o100600), "100644")
        self.assertEqual(_git_blob_mode(0o100644), "100644")
        self.assertEqual(_git_blob_mode(0o100664), "100644")
        self.assertEqual(_git_blob_mode(0o100755), "100755")
        self.assertEqual(_git_blob_mode(0o100775), "100755")

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

        helper_namespace: dict[str, object] = {
            "__name__": public_gonol_function.__module__
        }
        exec(
            compile(
                "def public_gonol_position(value):\n    return None\n",
                inspect.getfile(public_gonol_function),
                "exec",
            ),
            helper_namespace,
        )
        loaded_globals = public_gonol_function.__globals__
        original_helper = loaded_globals["public_gonol_position"]
        try:
            loaded_globals["public_gonol_position"] = helper_namespace[
                "public_gonol_position"
            ]
            transitive_observed = verify_loaded_ucns_commit(
                pinned_commit=PINNED_UCNS_COMMIT,
                dependencies=(public_gonol_function, native_mobius_state),
            )
        finally:
            loaded_globals["public_gonol_position"] = original_helper

        self.assertEqual(transitive_observed, "hmmm")

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

    def test_pinned_blob_mismatch_returns_hmmm(self) -> None:
        def mismatched_blob_runner(command, **kwargs):
            if "cat-file" in command:
                return subprocess.CompletedProcess(command, 0, stdout=b"not-the-pinned-source")
            return subprocess.run(command, **kwargs)

        observed = verify_loaded_ucns_commit(
            pinned_commit=PINNED_UCNS_COMMIT,
            dependencies=(public_gonol_function, native_mobius_state),
            runner=mismatched_blob_runner,
        )

        self.assertEqual(observed, "hmmm")


if __name__ == "__main__":
    unittest.main()
