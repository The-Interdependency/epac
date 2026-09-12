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
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import FunctionType, ModuleType, SimpleNamespace
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


@contextmanager
def _git_fixture():
    """Exercise Git verification independently of the UCNS installation mode."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "src/ucns/fixture.py"
        path.parent.mkdir(parents=True)
        path.write_text("def public_gonol_function(value): return value\n")
        for args in (("init", "-q"), ("add", "."), ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")):
            subprocess.run(("git", "-C", directory, *args), check=True, capture_output=True)
        pin = subprocess.check_output(("git", "-C", directory, "rev-parse", "HEAD"), text=True).strip()
        module = ModuleType("ucns_fixture")
        exec(compile(path.read_bytes(), str(path), "exec", dont_inherit=True), module.__dict__)
        yield pin, module.public_gonol_function


class UcnsProvenanceTest(unittest.TestCase):
    def tearDown(self) -> None:
        clear_ucns_verification_cache()

    def test_installed_cross_module_helpers_and_classes_are_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "ucns"
            package.mkdir()
            sources = {
                "ucns/__init__.py": "",
                "ucns/_epac_fixture_helper.py": "def helper(value): return value\nclass Carrier:\n    factor = 2\n",
                "ucns/_epac_fixture_entry.py": "from ucns._epac_fixture_helper import helper, Carrier\nfrom ucns import _epac_fixture_helper as helpers\ndef public(value): return sum(helper(item) for item in (value,)) + helpers.helper(value) + Carrier.factor\n",
            }
            for name, source in sources.items():
                (root / name).write_text(source)
            helper = ModuleType("ucns._epac_fixture_helper")
            entry = ModuleType("ucns._epac_fixture_entry")
            helper.__file__ = str(root / "ucns/_epac_fixture_helper.py")
            entry.__file__ = str(root / "ucns/_epac_fixture_entry.py")
            distribution = SimpleNamespace(files=list(sources), locate_file=lambda name: root / name)
            lock = {"repository": "The-Interdependency/ucns", "commit": PINNED_UCNS_COMMIT,
                    "installed_source_sha256": {name: sha256((root / name).read_bytes()).hexdigest() for name in sources}}
            (root / "ucns-source-lock.json").write_text(json.dumps(lock))
            with patch.dict(sys.modules, {helper.__name__: helper, entry.__name__: entry}), patch("epac_ucns_provenance.metadata.distribution", return_value=distribution), patch("epac_ucns_provenance.resources.files", return_value=root):
                exec(compile(sources["ucns/_epac_fixture_helper.py"], helper.__file__, "exec", dont_inherit=True), helper.__dict__)
                exec(compile(sources["ucns/_epac_fixture_entry.py"], entry.__file__, "exec", dont_inherit=True), entry.__dict__)
                def verify():
                    return verify_loaded_ucns_commit(pinned_commit=PINNED_UCNS_COMMIT, dependencies=(entry.public,))
                self.assertEqual(verify(), PINNED_UCNS_COMMIT)
                forged = {"__name__": helper.__name__}
                exec(compile("def helper(value): return 7\n", helper.__file__, "exec", dont_inherit=True), forged)
                with patch.dict(entry.public.__globals__, helper=forged["helper"]):
                    self.assertEqual(verify(), "hmmm")
                with patch.object(helper, "helper", forged["helper"]):
                    self.assertEqual(verify(), "hmmm")
                with patch.object(helper.Carrier, "factor", 9):
                    self.assertEqual(verify(), "hmmm")
                self.assertEqual(verify(), PINNED_UCNS_COMMIT)

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
        with _git_fixture() as (pin, dependency):
            first = verify_loaded_ucns_commit(pinned_commit=pin, dependencies=(dependency,), runner=counting_runner)
            first_call_count = len(calls)
            second = verify_loaded_ucns_commit(pinned_commit=pin, dependencies=(dependency,), runner=counting_runner)

        self.assertEqual(first, pin)
        self.assertEqual(second, pin)
        self.assertGreater(first_call_count, 0)
        self.assertEqual(len(calls), first_call_count)
        self.assertEqual(ucns_verification_cache_info().hits, 1)

    def test_pinned_blob_mismatch_returns_hmmm(self) -> None:
        def mismatched_blob_runner(command, **kwargs):
            if "cat-file" in command:
                return subprocess.CompletedProcess(command, 0, stdout=b"not-the-pinned-source")
            return subprocess.run(command, **kwargs)

        with _git_fixture() as (pin, dependency):
            observed = verify_loaded_ucns_commit(pinned_commit=pin, dependencies=(dependency,), runner=mismatched_blob_runner)

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

    def test_installed_source_and_loaded_state_changes_invalidate_witness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "ucns"
            package.mkdir()
            (package / "__init__.py").write_text("")
            path = package / "fixture.py"
            original = b"def public_gonol_function(value): return value\n"
            path.write_bytes(original)
            module = ModuleType("ucns_fixture")
            exec(compile(original, str(path), "exec", dont_inherit=True), module.__dict__)
            files = ["ucns/__init__.py", "ucns/fixture.py"]
            distribution = SimpleNamespace(files=files, locate_file=lambda name: root / name)
            lock = {"repository": "The-Interdependency/ucns", "commit": PINNED_UCNS_COMMIT,
                    "installed_source_sha256": {name: sha256((root / name).read_bytes()).hexdigest() for name in files}}
            (root / "ucns-source-lock.json").write_text(json.dumps(lock))
            with patch("epac_ucns_provenance.metadata.distribution", return_value=distribution), patch("epac_ucns_provenance.resources.files", return_value=root):
                def verify():
                    return verify_loaded_ucns_commit(pinned_commit=PINNED_UCNS_COMMIT, dependencies=(module.public_gonol_function,))
                self.assertEqual(verify(), PINNED_UCNS_COMMIT)
                self.assertEqual(verify(), PINNED_UCNS_COMMIT)
                self.assertEqual(ucns_verification_cache_info().hits, 1)
                path.write_bytes(original + b"# drift\n")
                self.assertEqual(verify(), "hmmm")
                path.write_bytes(original)
                exec(compile("def public_gonol_function(value): return 2\n", str(path), "exec", dont_inherit=True), module.__dict__)
                self.assertEqual(verify(), "hmmm")
                exec(compile(original, str(path), "exec", dont_inherit=True), module.__dict__)
                (package / "extra.py").write_text("unexpected = True\n")
                self.assertEqual(verify(), "hmmm")


def _run_provenance_cases(*names: str) -> None:
    suite = unittest.TestSuite(UcnsProvenanceTest(name) for name in names)
    result = suite.run(unittest.TestResult())
    if not result.wasSuccessful():
        raise AssertionError(f"provenance checks failed: {result.failures!r} {result.errors!r}")


def check_epac_ucns_pin_matches_loaded_code() -> None:
    _run_provenance_cases(
        "test_loaded_code_mismatch_returns_hmmm",
        "test_effective_builtins_are_part_of_loaded_state",
        "test_installed_source_and_loaded_state_changes_invalidate_witness",
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
