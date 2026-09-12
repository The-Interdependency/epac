"""Usage: run from outside the source tree: python verify_installed.py SOURCE WHEEL RECEIPT ARTIFACT.

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



EXPECTED_STANDINGS = {
    "atomic_shells_as_sealed_shape_prediction": "FALSIFIED",
    "boundary_capacity_as_sealed_shape_prediction": "FALSIFIED",
    "charged_3_structure_as_sealed_shape_prediction": "FALSIFIED",
    "harmonic_survival_as_sealed_shape_prediction": "FALSIFIED",
    "lifted_spiral_as_sealed_shape_prediction": "FALSIFIED",
    "per_symbol_harmonic_survival_as_sealed_shape_prediction": "FALSIFIED",
    "periodic_element_boundary_capacity_as_sealed_shape_prediction": "FALSIFIED",
    "periodic_element_harmonic_survival_as_sealed_shape_prediction": "FALSIFIED",
    "periodic_element_lifted_spiral_as_sealed_shape_prediction": "FALSIFIED",
    "subatomic_boundary_capacity_as_sealed_shape_prediction": "FALSIFIED",
    "subatomic_harmonic_survival_as_sealed_shape_prediction": "FALSIFIED",
    "subatomic_lifted_spiral_as_sealed_shape_prediction": "FALSIFIED",
    "topology_3_structure_as_sealed_shape_prediction": "FALSIFIED",
    "ucns_mobius_as_sealed_shape_prediction": "FALSIFIED"
}


def source_snapshot(root):
    entries = tuple(root.rglob("*"))
    assert not root.is_symlink() and not any(path.is_symlink() for path in entries)
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in entries if path.is_file() and "__pycache__" not in path.relative_to(root).parts}


def main() -> None:
    if sys.flags.optimize:
        raise SystemExit("optimized Python mode cannot produce replay evidence")
    if sys.argv[1] in {"snapshot", "verify-snapshot"}:
        root, output = map(Path, sys.argv[2:])
        current = source_snapshot(root)
        if sys.argv[1] == "snapshot":
            output.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        else:
            assert current == json.loads(output.read_text()), "archived source changed during replay"
        return
    import pytest
    source, wheel, receipt_path, artifact = (Path(value).resolve() for value in sys.argv[1:])
    artifact_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact_kind = "wheel" if artifact.suffix == ".whl" else "sdist"
    assert artifact_kind == "wheel" or artifact.name.endswith(".tar.gz")
    verifier_bytes = Path(__file__).read_bytes()
    assert verifier_bytes == (source / "tools/verify_installed.py").read_bytes(), "verifier differs from archived candidate"
    archived_inputs = source_snapshot(source)
    assert not Path.cwd().is_relative_to(source), "run outside the extracted source tree"
    assert not receipt_path.is_relative_to(source), "write receipts outside source"
    sys.path[:] = [path for path in sys.path if not Path(path or ".").resolve().is_relative_to(source)]
    with zipfile.ZipFile(wheel) as archive:
        expected = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()
                    if not name.endswith("/")}
    assert expected
    distribution = metadata.distribution("interdependency-epac")

    record_name, = [name for name in expected if name.endswith(".dist-info/RECORD")]
    info = record_name.rsplit("/", 1)[0]
    generated = {info + "/" + name for name in ("RECORD", "INSTALLER", "REQUESTED", "direct_url.json", "uv_cache.json", "uv_build.json")}
    immutable = {name: digest for name, digest in expected.items() if name != record_name}

    def payload():
        files = {str(path): Path(distribution.locate_file(path)) for path in distribution.files or ()
                 if "__pycache__" not in path.parts}
        assert all(not path.is_symlink() and path.resolve().is_relative_to(Path(sys.prefix)) and not Path(name).is_absolute() and ".." not in Path(name).parts for name, path in files.items())
        base = Path(distribution.locate_file(""))
        for entry in base.iterdir():
            if entry.name.startswith("epac_") or entry.name == info:
                entries = tuple(entry.rglob("*")) if entry.is_dir() else (entry,)
                assert not entry.is_symlink() and not any(path.is_symlink() for path in entries)
                assert all(path.relative_to(base).as_posix() in files for path in entries if path.is_file() and "__pycache__" not in path.parts)
        actual = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
        assert not set(actual) - set(expected) - generated
        assert all(actual.get(name) == digest for name, digest in immutable.items()), "installed distribution differs from candidate wheel"
        assert (base / info / "INSTALLER").read_bytes() == b"uv"
        return actual

    before = payload()
    import epac_public_gonol
    import ucns
    from epac_comparison import compare_after_construction
    from epac_ucns_provenance import verify_loaded_ucns_commit
    assert Path(epac_public_gonol.__file__).resolve().is_relative_to(Path(sys.prefix))
    identity = verify_loaded_ucns_commit(pinned_commit=epac_public_gonol.PINNED_UCNS_COMMIT,
                                        dependencies=(ucns.public_gonol_function, ucns.native_mobius_state))
    assert identity == epac_public_gonol.PINNED_UCNS_COMMIT
    xml_path = receipt_path.with_suffix(".xml")
    result = pytest.main([str(source / "tests"), "--junitxml=" + str(xml_path), "-q", "-x", "-p", "no:cacheprovider", "-o", "xfail_strict=true"])
    assert result == 0, result
    cases = list(ET.parse(xml_path).getroot().iter("testcase"))
    assert len(cases) == 181 and not any(c.find(tag) is not None for c in cases for tag in ("skipped", "failure", "error"))
    assert payload() == before
    origins = {name: str(Path(module.__file__).resolve()) for name, module in sys.modules.items()
               if name.startswith("epac_") and getattr(module, "__file__", None)}
    assert all(Path(path).is_relative_to(Path(sys.prefix)) for path in origins.values()), origins
    standings = compare_after_construction()["standings"]
    assert standings == EXPECTED_STANDINGS, standings
    assert source_snapshot(source) == archived_inputs, "source changed during replay"
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == artifact_digest
    receipt = {"artifact_kind": artifact_kind, "artifact_sha256": artifact_digest, "artifact_name": artifact.name, "schema": "epac.installed-replay", "version": 1, "status": "passed", "python": sys.version,
               "verifier_sha256": hashlib.sha256(verifier_bytes).hexdigest(), "source_files_sha256": archived_inputs, "outcomes_xml_sha256": hashlib.sha256(xml_path.read_bytes()).hexdigest(),
               "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(), "ucns_source_commit": identity,
               "installed_payload_sha256": immutable, "installed_distribution_sha256": before, "imported_origins": origins, "tests": len(cases),
               "skips": 0, "comparison_standings": standings, "empirical_status_transfer": False}
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
