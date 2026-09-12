"""Usage: run from outside the source tree: python verify_installed.py SOURCE WHEEL RECEIPT.

The tests come from the source archive; EPAC imports and data must come from the
clean installation. This receipt measures reproducibility, not domain validity.
"""
# === MODULE_BUILD ===
# id: epac_installed_replay
#   module_name: verify_installed
#   module_kind: instrument
#   summary: verifies installed EPAC payloads, imports, tests, and preserved falsification standing
#   owner: The Interdependency
#   public_surface: python tools/verify_installed.py SOURCE WHEEL RECEIPT
#   internal_surface: main
#   auth_boundary: none
#   storage_boundary: write
#   storage_notes: selected receipt path
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: full repository suite under clean wheel and sdist installations
#   rollout: explicit candidate qualification command
#   rollback: retain the previously accepted immutable artifact
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: epac_installation_replays_independently
#   given: EPAC and its pinned UCNS dependency are installed in a clean environment
#   then: installed source matches the candidate wheel, all tests pass without skips, imports remain in the environment, and existing falsification standing is preserved
#   class: evidence
# === END CONTRACTS ===
from __future__ import annotations

import hashlib
from importlib import metadata
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

import pytest


def main() -> None:
    source, wheel, receipt_path = (Path(value).resolve() for value in sys.argv[1:])
    assert not Path.cwd().is_relative_to(source), "run outside the extracted source tree"
    assert not receipt_path.is_relative_to(source), "write receipts outside source"
    sys.path[:] = [path for path in sys.path if not Path(path or ".").resolve().is_relative_to(source)]
    with zipfile.ZipFile(wheel) as archive:
        expected = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()
                    if name.startswith("epac_") and not name.endswith("/")}
    assert expected
    distribution = metadata.distribution("interdependency-epac")

    def payload():
        files = {str(path): Path(distribution.locate_file(path)).resolve() for path in distribution.files or ()
                 if str(path).startswith("epac_") and "__pycache__" not in path.parts}
        assert all(path.is_relative_to(Path(sys.prefix)) for path in files.values())
        return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}

    assert payload() == expected, "installed payload differs from candidate wheel"
    import epac_public_gonol
    import ucns
    from epac_comparison import compare_after_construction
    from epac_ucns_provenance import verify_loaded_ucns_commit
    assert Path(epac_public_gonol.__file__).resolve().is_relative_to(Path(sys.prefix))
    identity = verify_loaded_ucns_commit(pinned_commit=epac_public_gonol.PINNED_UCNS_COMMIT,
                                        dependencies=(ucns.public_gonol_function, ucns.native_mobius_state))
    assert identity == epac_public_gonol.PINNED_UCNS_COMMIT
    xml_path = receipt_path.with_suffix(".xml")
    result = pytest.main([str(source / "tests"), "--junitxml=" + str(xml_path), "-q"])
    assert result == 0, result
    cases = list(ET.parse(xml_path).getroot().iter("testcase"))
    assert cases and not any(c.find(tag) is not None for c in cases for tag in ("skipped", "failure", "error"))
    assert payload() == expected
    origins = {name: str(Path(module.__file__).resolve()) for name, module in sys.modules.items()
               if name.startswith("epac_") and getattr(module, "__file__", None)}
    assert all(Path(path).is_relative_to(Path(sys.prefix)) for path in origins.values()), origins
    standings = compare_after_construction()["standings"]
    assert len(standings) == 4 and set(standings.values()) == {"FALSIFIED"}, standings
    receipt = {"schema": "epac.installed-replay", "version": 1, "status": "passed", "python": sys.version,
               "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(), "ucns_source_commit": identity,
               "installed_payload_sha256": expected, "imported_origins": origins, "tests": len(cases),
               "skips": 0, "comparison_standings": standings, "empirical_status_transfer": False}
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
