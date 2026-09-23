"""Regression coverage for pytest subtest accounting in installed replay evidence."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


VERIFIER_PATH = Path(__file__).resolve().parents[1] / "tools" / "verify_installed.py"
SPEC = spec_from_file_location("epac_installed_junit_fixture", VERIFIER_PATH)
VERIFIER = module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


def _write_xml(path, tests):
    path.write_text(
        f'<testsuite tests="{tests}" failures="0" errors="0" skipped="0">'
        '<testcase name="a"/><testcase name="b"/></testsuite>',
        encoding="utf-8",
    )


def test_junit_total_accepts_explicit_successful_subtest_count(tmp_path):
    xml = tmp_path / "results.xml"
    _write_xml(xml, 3)
    assert VERIFIER.verify_test_evidence(xml, ["a", "b"], ["a", "b"], passed_subtests=1) == 2


def test_junit_total_rejects_unexplained_extra_results(tmp_path):
    xml = tmp_path / "results.xml"
    _write_xml(xml, 3)
    with pytest.raises(AssertionError, match="aggregate"):
        VERIFIER.verify_test_evidence(xml, ["a", "b"], ["a", "b"], passed_subtests=0)


def test_junit_total_rejects_inflated_subtest_claim(tmp_path):
    xml = tmp_path / "results.xml"
    _write_xml(xml, 3)
    with pytest.raises(AssertionError, match="aggregate"):
        VERIFIER.verify_test_evidence(xml, ["a", "b"], ["a", "b"], passed_subtests=2)
