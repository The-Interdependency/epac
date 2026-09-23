"""Check dependency selection in the real artifact replay shell."""
# === CHECKS ===
# id: check_epac_replay_uses_candidate_lock
#   proves: epac_distribution_replay_preserves_artifact_identity
#   call: self::check_epac_replay_uses_candidate_lock
#   requires: python3, bash
#   mutates: temporary fixture archives, virtual environment, and installer trace
#   cleanup: temporary directory context removes all fixture state
#
# id: check_epac_complete_test_evidence
#   proves: epac_installation_replays_independently
#   call: self::test_installed_replay_requires_complete_test_evidence
#   requires: python3
#   mutates: filesystem
#   cleanup: temporary directory context removes fixture state
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
import shutil
from types import SimpleNamespace
from unittest.mock import patch


def test_installed_replay_requires_complete_test_evidence():
    """Usage: pytest tests/test_distribution_replay.py; exercise false-green receipts."""
    path = Path(__file__).resolve().parents[1] / "tools/verify_installed.py"
    spec = importlib.util.spec_from_file_location("epac_installed_fixture", path)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    with TemporaryDirectory() as directory:
        xml = Path(directory) / "results.xml"
        good = '<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase name="a"/><testcase name="b"/></testsuite>'
        xml.write_text(good, encoding="utf-8")
        assert verifier.verify_test_evidence(xml, ["a", "b"], ["a", "b"]) == 2
        for collected, passed, report in (
            ([], [], good),
            (["a", "b"], ["a"], good),
            (["a", "a"], ["a", "a"], good),
            (["a", "b"], ["a", "b"], good.replace('tests="2"', 'tests="3"')),
            (["a", "b"], ["a", "b"], good.replace('failures="0"', 'failures="1"')),
            (["a", "b"], ["a", "b"], good.replace('<testcase name="b"/>', '')),
            (["a", "b"], ["a", "b"], good.replace('<testcase name="b"/>', '<testcase name="b"><skipped/></testcase>')),
        ):
            xml.write_text(report, encoding="utf-8")
            try:
                verifier.verify_test_evidence(xml, collected, passed)
            except AssertionError:
                pass
            else:
                raise AssertionError("incomplete test evidence accepted")


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
        generated[egg + name] = payload[info + "METADATA"] if name == "PKG-INFO" else payload[info + "top_level.txt"] if name == "top_level.txt" else b""
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
        "pyproject.toml": b'[project]\nname = "interdependency-epac"\nversion = "0.1.0"\ndescription = "fixture"\nreadme = "README.md"\nrequires-python = ">=3.10"\nauthors = [{name = "Fixture"}]\ndependencies = ["sample==1"]\n[project.optional-dependencies]\ntest = ["pytest==9.1.1"]\n[build-system]\nrequires = ["setuptools==84.0.0", "wheel==0.48.0"]\n',
        "requirements-replay.txt": (source / "requirements-replay.txt").read_bytes(),
        "requirements-build.txt": (source / "requirements-build.txt").read_bytes(),
        "data/ucns-source-lock.json": b'{"commit":"fixture"}\n',
        "LICENSE_STATUS.md": b"Owner license choice pending.\n",
        "README.md": b"fixture\n",
        "epac_fixture.py": b'VALUE = "candidate"\n',
        "data/__init__.py": b"", "subatomic/__init__.py": b"", "viz/__init__.py": b"",
        "tests/test_probe.py": b"def test_probe():\n    assert False\n",
    }
    for name in ("verify_installed.py", "verify_replay_inputs.py", "replay_distributions.sh", "release_contract.py"):
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
                     "epac_data/ucns-source-lock.json": contents["data/ucns-source-lock.json"],
                     info + "METADATA": b'Metadata-Version: 2.4\nName: interdependency-epac\nVersion: 0.1.0\nSummary: fixture\nAuthor: Fixture\nRequires-Python: >=3.10\nDescription-Content-Type: text/markdown\nLicense-File: LICENSE_STATUS.md\nRequires-Dist: sample==1\nProvides-Extra: test\nRequires-Dist: pytest==9.1.1; extra == "test"\nDynamic: license-file\n\nfixture\n',
                     info + "WHEEL": b"Wheel-Version: 1.0\nGenerator: setuptools (84.0.0)\nRoot-Is-Purelib: true\nTag: py3-none-any\n\n",
                     info + "top_level.txt": b"epac_data\nepac_fixture\nepac_subatomic\nepac_viz\n",
                     info + "licenses/LICENSE_STATUS.md": contents["LICENSE_STATUS.md"]}
    _write_fixture_dist(dist, contents, wheel_payload)
    trace = tmp_path / "export.json"
    uv = binary / "uv"
    uv.write_text("#!" + sys.executable + "\n" + '''
import json, os
from pathlib import Path
import subprocess, sys
if sys.argv[1] == "venv":
    raise SystemExit(subprocess.run([sys.executable, "-m", "venv", "--without-pip", sys.argv[-1]]).returncode)
if sys.argv[1:3] == ["pip", "install"]:
    raise SystemExit(subprocess.run([os.environ["REAL_UV"], *sys.argv[1:]]).returncode)
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
    environment = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"], EXPORT_TRACE=str(trace), REAL_UV=shutil.which("uv"))
    command = ["bash", str(caller / "tools/replay_distributions.sh"), str(caller), str(dist), str(output), sys.executable]
    return caller, dist, output, trace, environment, command, contents, wheel_payload


def test_replay_exports_the_archived_dependency_lock(tmp_path):
    caller, dist, output, trace, environment, command, contents, wheel_payload = _replay_fixture(tmp_path)
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 73, result.stderr
    record = json.loads(trace.read_text())
    assert Path(record["project"]) == output / "source/fixture"
    assert record["lock"] == "exact archived lock"
    assert record["pyproject"] == contents["pyproject.toml"].decode()
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
    for case in ("stale test", "stale verifier", "missing source", "extra source", "wrong wheel", "wrong manifest source", "wrong manifest hash", "dirty root", "entry points", "wheel tag", "wheel purelib", "top level", "missing license metadata", "extra dependency", "python requirement", "extra declaration", "metadata summary"):
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
        elif case in ("extra dependency", "python requirement", "extra declaration", "metadata summary"):
            key = "interdependency_epac-0.1.0.dist-info/METADATA"
            if case == "extra dependency":
                wheel_payload[key] = wheel_payload[key].replace(b"\n\n", b"\nRequires-Dist: undeclared==1\n\n", 1)
            elif case == "python requirement":
                wheel_payload[key] = wheel_payload[key].replace(b"Requires-Python: >=3.10", b"Requires-Python: >=3.12")
            elif case == "extra declaration":
                wheel_payload[key] = wheel_payload[key].replace(b"\n\n", b"\nProvides-Extra: undeclared\n\n", 1)
            else:
                wheel_payload[key] = wheel_payload[key].replace(b"Summary: fixture", b"Summary: false summary")
            expected = "core metadata differs from source"
        elif case == "entry points":
            wheel_payload["interdependency_epac-0.1.0.dist-info/entry_points.txt"] = b"[console_scripts]\nundeclared = epac_fixture:main\n"
            expected = "undeclared or missing wheel metadata"
        elif case in ("wheel tag", "wheel purelib"):
            key = "interdependency_epac-0.1.0.dist-info/WHEEL"
            old, new = (b"py3-none-any", b"cp311-cp311-linux_x86_64") if case == "wheel tag" else (b"Root-Is-Purelib: true", b"Root-Is-Purelib: false")
            wheel_payload[key] = wheel_payload[key].replace(old, new)
            expected = "wheel installer semantics differ"
        elif case == "top level":
            wheel_payload["interdependency_epac-0.1.0.dist-info/top_level.txt"] = b"undeclared\n"
            expected = "top-level metadata differs"
        elif case == "missing license metadata":
            del wheel_payload["interdependency_epac-0.1.0.dist-info/licenses/LICENSE_STATUS.md"]
            expected = "undeclared or missing wheel metadata"
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


def test_release_builder_requires_documented_runtime_and_license(tmp_path):
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

    caller, dist, output, trace, environment, command, contents, wheel_payload = _replay_fixture(tmp_path)
    (caller / "LICENSE").write_text("Synthetic test fixture license; no EPAC distribution authority.\n")
    subprocess.run(["git", "-C", str(caller), "add", "LICENSE"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(caller), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-qm", "license without status transition"], check=True, capture_output=True)
    with patch.object(builder, "__file__", str(caller / "tools/build_release.py")), \
         patch.object(builder.sys, "argv", ["build_release.py", str(output)]), \
         patch.object(builder, "check_runtime", return_value={"implementation":"cpython","version":"3.11.15"}), \
         patch.object(builder, "check_compressor", return_value={"implementation":"zlib","compile_version":"1.3.1","runtime_version":"1.3.1"}):
        try:
            builder.main()
        except ValueError as error:
            assert "remove the unresolved LICENSE_STATUS.md" in str(error)
        else:
            raise AssertionError("builder accepted contradictory license status")
        assert not output.exists()


def test_replay_validates_complete_release_manifest(tmp_path):
    import copy
    cases = (None, "license_sha256", "ucns_source_lock_sha256", "build_toolchain", "acceptance",
             "empirical_status_transfer", "python_runtime", "compressor", "source_date_epoch",
             "license_expression", "schema", "version", "extra field", "unresolved status", "zero empirical flag", "boolean version", "duplicate root key", "duplicate nested key",
             "missing sums", "forged sums", "duplicate sums", "missing checksum entry", "extra checksum entry", "extra asset")
    for case in cases:
        caller, dist, output, trace, environment, command, contents, wheel_payload = _replay_fixture(tmp_path / str(case))
        info = "interdependency_epac-0.1.0.dist-info/"
        contents["LICENSE"] = b"Synthetic test fixture license; no EPAC distribution authority.\n"
        contents.pop("LICENSE_STATUS.md")
        (caller / "LICENSE_STATUS.md").unlink()
        contents["pyproject.toml"] = contents["pyproject.toml"].replace(b"[project.optional-dependencies]",
            b'license = "LicenseRef-GateFixture"\nlicense-files = ["LICENSE"]\n[project.optional-dependencies]')
        wheel_payload.pop(info + "licenses/LICENSE_STATUS.md")
        wheel_payload[info + "licenses/LICENSE"] = contents["LICENSE"]
        wheel_payload[info + "METADATA"] = wheel_payload[info + "METADATA"].replace(
            b"License-File: LICENSE_STATUS.md", b"License-File: LICENSE\nLicense-Expression: LicenseRef-GateFixture"
        )
        if case == "unresolved status":
            contents["LICENSE_STATUS.md"] = b"hmmm: no license selected; stable publication prohibited\n"
        for name, value in contents.items():
            path = caller / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        subprocess.run(["git", "-C", str(caller), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(caller), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "-c", "commit.gpgsign=false", "commit", "-qm", "synthetic license transition"], check=True, capture_output=True)
        _write_fixture_dist(dist, contents, wheel_payload)
        def git(*args):
            return subprocess.check_output(["git", "-C", str(caller), *args], text=True).strip()
        manifest = {"schema": "epac.release-candidate", "version": 1, "source_commit": git("rev-parse", "HEAD"),
                    "source_tree": git("rev-parse", "HEAD^{tree}"), "source_date_epoch": git("show", "-s", "--format=%ct", "HEAD"),
                    "build_toolchain": dict(line.split("==") for line in contents["requirements-build.txt"].decode().splitlines()),
                    "python_runtime": {"implementation": "cpython", "version": "3.11.15"},
                    "compressor": {"implementation": "zlib", "compile_version": "1.3.1", "runtime_version": "1.3.1"},
                    "license_expression": "LicenseRef-GateFixture", "license_sha256": hashlib.sha256(contents["LICENSE"]).hexdigest(),
                    "ucns_source_lock_sha256": hashlib.sha256(contents["data/ucns-source-lock.json"]).hexdigest(),
                    "artifacts_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.iterdir()},
                    "acceptance": "candidate; clean replay and stack acceptance required", "empirical_status_transfer": False}
        corrupted = copy.deepcopy(manifest)
        if case == "zero empirical flag":
            corrupted["empirical_status_transfer"] = 0
        elif case == "boolean version":
            corrupted["version"] = True
        elif case and case not in {"unresolved status", "duplicate root key", "duplicate nested key", "missing sums", "forged sums", "duplicate sums", "missing checksum entry", "extra checksum entry", "extra asset"}:
            corrupted[case] = True if case == "empirical_status_transfer" else "false declaration"
        manifest_text = json.dumps(corrupted)
        if case == "duplicate root key":
            manifest_text = manifest_text.replace('{', '{"empirical_status_transfer": true, ', 1)
        elif case == "duplicate nested key":
            manifest_text = manifest_text.replace('"implementation": "cpython"', '"implementation": "forged", "implementation": "cpython"')
        (dist / "release-manifest.json").write_text(manifest_text)
        checksums = "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
                            for path in sorted(dist.iterdir()))
        if case == "forged sums":
            checksums = "0" * 64 + checksums[64:]
        elif case == "duplicate sums":
            checksums += checksums.splitlines(keepends=True)[0]
        elif case == "missing checksum entry":
            checksums = "".join(checksums.splitlines(keepends=True)[1:])
        elif case == "extra checksum entry":
            checksums += "0" * 64 + "  undeclared.txt\n"
        if case != "missing sums":
            (dist / "SHA256SUMS").write_text(checksums)
        if case == "extra asset":
            (dist / "undeclared.txt").write_text("unapproved release attachment")
        result = subprocess.run(command, env=environment, capture_output=True, text=True)
        if case is None:
            assert result.returncode == 73 and trace.exists(), result.stderr
            binding = json.loads((output / "candidate-source.json").read_text())
            assert binding["release_manifest_sha256"] == hashlib.sha256((dist / "release-manifest.json").read_bytes()).hexdigest()
        else:
            expected = "remove the unresolved LICENSE_STATUS.md" if case == "unresolved status" else "release manifest fields differ"
            if case.startswith("duplicate ") and case.endswith("key"):
                expected = "duplicate release-manifest key"
            elif case in {"missing sums", "extra asset"}:
                expected = "distribution file set differs"
            elif case in {"forged sums", "duplicate sums", "missing checksum entry", "extra checksum entry"}:
                expected = "SHA256SUMS differs"
            assert result.returncode not in (0, 73) and expected in result.stderr, (case, result.stderr)
            assert not trace.exists(), case
