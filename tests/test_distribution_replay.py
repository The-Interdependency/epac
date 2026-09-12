"""Check dependency selection in the real artifact replay shell."""
# === CHECKS ===
# id: check_epac_replay_uses_candidate_lock
#   proves: epac_distribution_replay_preserves_artifact_identity
#   call: self::check_epac_replay_uses_candidate_lock
#   requires: python3, bash
#   mutates: temporary fixture archives, virtual environment, and installer trace
#   cleanup: temporary directory context removes all fixture state
# === END CHECKS ===
from pathlib import Path
import io
import json
import os
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
import importlib.util
import base64
import csv
import hashlib
import zipfile
from types import SimpleNamespace
from unittest.mock import patch


def _write_fixture_dist(dist, contents, wheel_payload):
    info = "interdependency_epac-0.1.0.dist-info/"
    payload = dict(wheel_payload)
    rows = []
    for name, value in payload.items():
        hashed = base64.urlsafe_b64encode(hashlib.sha256(value).digest()).decode().rstrip("=")
        rows.append((name, "sha256=" + hashed, str(len(value))))
    rows.append((info + "RECORD", "", ""))
    record = io.StringIO()
    csv.writer(record).writerows(rows)
    payload[info + "RECORD"] = record.getvalue().encode()
    with zipfile.ZipFile(dist / "fixture.whl", "w") as archive:
        for name, value in payload.items():
            archive.writestr(name, value)
    generated = {"PKG-INFO": payload[info + "METADATA"],
                 "setup.cfg": b"[egg_info]\ntag_build = \ntag_date = 0\n\n"}
    egg = "interdependency_epac.egg-info/"
    for name in ("PKG-INFO", "SOURCES.txt", "dependency_links.txt", "requires.txt", "top_level.txt"):
        generated[egg + name] = payload[info + "METADATA"] if name == "PKG-INFO" else b""
    with tarfile.open(dist / "fixture.tar.gz", "w:gz") as archive:
        for name, value in {**contents, **generated}.items():
            member = tarfile.TarInfo("fixture/" + name)
            member.size = len(value)
            archive.addfile(member, io.BytesIO(value))


def _replay_fixture(tmp_path):
    source = Path(__file__).resolve().parents[1]
    caller, dist, binary = (tmp_path / name for name in ("caller", "dist", "bin"))
    for directory in (caller, dist, binary):
        directory.mkdir(parents=True)
    contents = {
        "uv.lock": b"exact archived lock",
        "pyproject.toml": b"exact archived project",
        "epac_fixture.py": b'VALUE = "candidate"\n',
        "data/__init__.py": b"", "subatomic/__init__.py": b"", "viz/__init__.py": b"",
        "tests/test_probe.py": b"def test_probe():\n    assert False\n",
    }
    for name in ("verify_installed.py", "verify_replay_inputs.py", "replay_distributions.sh"):
        contents["tools/" + name] = (source / "tools" / name).read_bytes()
    for name, value in contents.items():
        path = caller / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    subprocess.run(["git", "init", "-q", str(caller)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(caller), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(caller), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-qm", "candidate"], check=True, capture_output=True)
    info = "interdependency_epac-0.1.0.dist-info/"
    wheel_payload = {"epac_fixture.py": contents["epac_fixture.py"],
                     "epac_data/__init__.py": b"", "epac_subatomic/__init__.py": b"", "epac_viz/__init__.py": b"",
                     info + "METADATA": b"Metadata-Version: 2.4\nName: interdependency-epac\nVersion: 0.1.0\n\nfixture\n",
                     info + "WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"}
    _write_fixture_dist(dist, contents, wheel_payload)
    trace = tmp_path / "export.json"
    uv = binary / "uv"
    uv.write_text("#!" + sys.executable + "\n" + '''
import json, os
from pathlib import Path
import subprocess, sys
if sys.argv[1] == "venv":
    raise SystemExit(subprocess.run([sys.executable, "-m", "venv", "--without-pip", sys.argv[-1]]).returncode)
if sys.argv[1] == "export":
    project = Path(sys.argv[sys.argv.index("--project") + 1])
    Path(os.environ["EXPORT_TRACE"]).write_text(json.dumps({
        "project": str(project), "lock": (project / "uv.lock").read_text(),
        "pyproject": (project / "pyproject.toml").read_text()}))
    raise SystemExit(73)
raise SystemExit("unexpected installer operation")
''')
    uv.chmod(0o755)
    output = tmp_path / "replay"
    environment = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"], EXPORT_TRACE=str(trace))
    command = ["bash", str(caller / "tools/replay_distributions.sh"), str(caller), str(dist), str(output), sys.executable]
    return caller, dist, output, trace, environment, command, contents, wheel_payload


def test_replay_exports_the_archived_dependency_lock(tmp_path):
    caller, dist, output, trace, environment, command, contents, wheel_payload = _replay_fixture(tmp_path)
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 73, result.stderr
    record = json.loads(trace.read_text())
    assert Path(record["project"]) == output / "source/fixture"
    assert record["lock"] == "exact archived lock"
    assert record["pyproject"] == "exact archived project"
    binding = json.loads((output / "candidate-source.json").read_text())
    assert binding["source_commit"] == subprocess.check_output(["git", "-C", str(caller), "rev-parse", "HEAD"], text=True).strip()
    assert binding["git_source_files_sha256"] == {name: hashlib.sha256(value).hexdigest() for name, value in contents.items()}
    final = [sys.executable, str(caller / "tools/verify_replay_inputs.py"), str(caller), str(dist), str(output), "--final"]
    result = subprocess.run(final, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    (output / "source/fixture/tests/test_probe.py").write_text("changed after replay")
    result = subprocess.run(final, capture_output=True, text=True)
    assert result.returncode != 0 and "extracted source changed" in result.stderr
    (output / "source/fixture/tests/test_probe.py").write_bytes(contents["tests/test_probe.py"])
    subprocess.run(["git", "-C", str(caller), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "new identity"], check=True, capture_output=True)
    result = subprocess.run(final, capture_output=True, text=True)
    assert result.returncode != 0 and "candidate binding changed" in result.stderr


def test_replay_rejects_mismatched_source_and_artifacts(tmp_path):
    for case in ("stale test", "stale verifier", "missing source", "extra source", "wrong wheel", "wrong manifest source", "wrong manifest hash", "dirty root"):
        caller, dist, output, trace, environment, command, contents, wheel_payload = _replay_fixture(tmp_path / case)
        marker = tmp_path / case / "archived-verifier-executed"
        expected = "archived source differs from candidate Git"
        if case == "stale test":
            contents["tests/test_probe.py"] = b"def test_probe():\n    assert True\n"
        elif case == "stale verifier":
            original = contents["tools/verify_installed.py"]
            assert b"import hashlib\n" in original
            contents["tools/verify_installed.py"] = original.replace(b"import hashlib\n",
                ("import hashlib\nfrom pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('executed')\n").encode(), 1)
        elif case == "missing source":
            contents.pop("tests/test_probe.py")
            expected = "source archive coverage differs"
        elif case == "extra source":
            contents["tests/conftest.py"] = b"raise RuntimeError('unapproved collection hook')\n"
            expected = "source archive coverage differs"
        elif case == "wrong wheel":
            wheel_payload["epac_fixture.py"] = b'VALUE = "wrong candidate"\n'
            expected = "wheel package bytes differ from candidate Git"
        elif case == "dirty root":
            (caller / "uv.lock").write_text("unrelated caller lock")
            expected = "candidate Git source must be clean"
        _write_fixture_dist(dist, contents, wheel_payload)
        if case.startswith("wrong manifest"):
            hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in dist.iterdir()}
            manifest = {"source_commit": subprocess.check_output(["git", "-C", str(caller), "rev-parse", "HEAD"], text=True).strip(),
                        "source_tree": subprocess.check_output(["git", "-C", str(caller), "rev-parse", "HEAD^{tree}"], text=True).strip(),
                        "artifacts_sha256": hashes}
            if case == "wrong manifest source":
                manifest["source_commit"] = "0" * 40
                expected = "release manifest source differs"
            else:
                manifest["artifacts_sha256"]["fixture.whl"] = "0" * 64
                expected = "release manifest artifact hashes differ"
            (dist / "release-manifest.json").write_text(json.dumps(manifest))
        result = subprocess.run(command, env=environment, capture_output=True, text=True)
        assert result.returncode not in (0, 73) and expected in result.stderr, (case, result.stderr)
        assert not trace.exists(), case
        assert not marker.exists(), case


def check_epac_replay_uses_candidate_lock():
    with TemporaryDirectory() as directory:
        test_replay_exports_the_archived_dependency_lock(Path(directory))


def test_release_builder_requires_documented_python_runtime():
    path = Path(__file__).resolve().parents[1] / "tools/build_release.py"
    spec = importlib.util.spec_from_file_location("epac_release_builder_fixture", path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    with patch.object(builder, "sys", SimpleNamespace(implementation=SimpleNamespace(name="cpython"), version_info=(3, 11, 15))):
        assert builder.check_runtime() == {"implementation": "cpython", "version": "3.11.15"}
    for implementation, version in (("cpython", (3, 10, 20)), ("cpython", (3, 12, 3)), ("cpython", (3, 11, 14)), ("pypy", (3, 11, 15))):
        with patch.object(builder, "sys", SimpleNamespace(implementation=SimpleNamespace(name=implementation), version_info=version)):
            try:
                builder.check_runtime()
            except RuntimeError as error:
                assert "require CPython 3.11.15" in str(error)
            else:
                raise AssertionError("unqualified release runtime was accepted")
