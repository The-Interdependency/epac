"""Executable checks for loaded-code-aware UCNS provenance and cache reuse."""

# === CHECKS ===
# id: check_epac_ucns_pin_matches_loaded_code
#   proves: epac_ucns_pin_matches_loaded_code
#   call: self::check_epac_ucns_pin_matches_loaded_code
#   mutates: ucns.public_gonol module global public_gonol_position; in-memory verification cache
#   cleanup: restores public_gonol_position; clears verification cache
#
# id: check_epac_ucns_verification_reuses_only_identical_witness
#   proves: epac_ucns_verification_reuses_only_identical_witness
#   call: self::check_epac_ucns_verification_reuses_only_identical_witness
#   mutates: in-memory verification cache
#   cleanup: clears verification cache
#
# id: check_epac_ucns_pin_compares_pinned_blob_bytes
#   proves: epac_ucns_pin_matches_loaded_code
#   call: self::check_epac_ucns_pin_compares_pinned_blob_bytes
#   mutates: in-memory verification cache
#   cleanup: clears verification cache
# === END CHECKS ===

from __future__ import annotations

import inspect
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import tempfile
from types import FunctionType
import unittest
from unittest.mock import patch

from epac_ucns_provenance import (
    _git_blob_mode,
    _head_and_index_witness,
    _transitive_fingerprint,
    _verify_witness,
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
        self.assertEqual(_git_blob_mode(0o100655), "100644")
        self.assertEqual(_git_blob_mode(0o100664), "100644")
        self.assertEqual(_git_blob_mode(0o100744), "100755")
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

    def test_effective_builtins_are_part_of_loaded_state(self) -> None:
        forged_globals = dict(public_gonol_function.__globals__)
        forged_builtins = dict(public_gonol_function.__builtins__)
        forged_builtins["len"] = sum
        forged_globals["__builtins__"] = forged_builtins
        forged = FunctionType(
            public_gonol_function.__code__,
            forged_globals,
            public_gonol_function.__name__,
            public_gonol_function.__defaults__,
            public_gonol_function.__closure__,
        )
        forged.__kwdefaults__ = public_gonol_function.__kwdefaults__
        forged.__annotations__ = public_gonol_function.__annotations__
        self.assertNotEqual(
            _transitive_fingerprint(forged),
            _transitive_fingerprint(public_gonol_function),
        )

    def test_unchanged_witness_runs_git_once(self) -> None:
        calls: list[tuple[str, ...]] = []

        def counting_runner(command, **kwargs):
            self.assertNotIn("timeout", kwargs)
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

    def test_staged_blob_mismatch_returns_hmmm(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            git_dir = Path(directory) / ".git"
            git_dir.mkdir()
            (git_dir / "HEAD").write_text(PINNED_UCNS_COMMIT, encoding="utf-8")
            (git_dir / "index").write_bytes(b"default-index")
            alternate_index = Path(directory) / "alternate-index"
            alternate_index.write_bytes(b"alternate-index-v1")
            with patch.dict(os.environ, {"GIT_INDEX_FILE": "alternate-index"}):
                first_witness = _head_and_index_witness(Path(directory))
                alternate_index.write_bytes(b"alternate-index-v2")
                second_witness = _head_and_index_witness(Path(directory))
            self.assertIsNotNone(first_witness)
            self.assertIsNotNone(second_witness)
            self.assertNotEqual(first_witness[1], second_witness[1])

            path = Path(directory) / "public_gonol.py"
            source = b"def public_gonol_function(value): return value\n"
            path.write_bytes(source)
            pinned_blob = "a" * 40
            staged_blob = "b" * 40
            calls: list[tuple[str, ...]] = []

            def staged_runner(command, **_kwargs):
                calls.append(tuple(command))
                if "rev-parse" in command:
                    return subprocess.CompletedProcess(command, 0, stdout=PINNED_UCNS_COMMIT + "\n")
                if "ls-tree" in command:
                    line = f"100644 blob {pinned_blob}\tpublic_gonol.py\n"
                    return subprocess.CompletedProcess(command, 0, stdout=line)
                if "ls-files" in command:
                    line = f"100644 {staged_blob} 0\tpublic_gonol.py\n"
                    return subprocess.CompletedProcess(command, 0, stdout=line)
                raise AssertionError(command)

            observed = _verify_witness(
                PINNED_UCNS_COMMIT, directory, PINNED_UCNS_COMMIT,
                sha256(b"index").hexdigest(),
                (("public_gonol.py", str(path), "public_gonol_function",
                  "loaded", sha256(source).hexdigest(), 0o100644),),
                staged_runner,
            )
        self.assertEqual(observed, "hmmm")
        self.assertTrue(any("ls-files" in call for call in calls))


def _run_provenance_cases(*names: str) -> None:
    suite = unittest.TestSuite(UcnsProvenanceTest(name) for name in names)
    result = suite.run(unittest.TestResult())
    if not result.wasSuccessful():
        raise AssertionError(f"provenance checks failed: {result.failures!r} {result.errors!r}")


def check_epac_ucns_pin_matches_loaded_code() -> None:
    _run_provenance_cases(
        "test_loaded_code_mismatch_returns_hmmm",
        "test_effective_builtins_are_part_of_loaded_state",
    )


def check_epac_ucns_verification_reuses_only_identical_witness() -> None:
    _run_provenance_cases("test_unchanged_witness_runs_git_once")


def check_epac_ucns_pin_compares_pinned_blob_bytes() -> None:
    _run_provenance_cases(
        "test_pinned_blob_mismatch_returns_hmmm",
        "test_staged_blob_mismatch_returns_hmmm",
    )


if __name__ == "__main__":
    unittest.main()
