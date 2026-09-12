"""Bind both EPAC distributions to clean Git source before archived code runs.

Usage: python tools/verify_replay_inputs.py ROOT DIST NEW_REPLAY_OUTPUT [--final]
The output directory must already exist and contain no source/ or candidate-source.json.
This gate is specific to EPAC's declared root modules and three package roots.
Changing that layout requires updating this gate alongside the package contract.
"""
# === MODULE_BUILD ===
# id: epac_replay_source_binding
#   module_name: verify_replay_inputs
#   module_kind: instrument
#   summary: verifies complete source and wheel bytes against the candidate Git identity
#   owner: The Interdependency
#   public_surface: python tools/verify_replay_inputs.py ROOT DIST NEW_REPLAY_OUTPUT
#   internal_surface: verify_inputs
#   auth_boundary: none
#   storage_boundary: write
#   storage_notes: extracts validated source and writes an input-binding receipt
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests/test_distribution_replay.py
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: epac_replay_inputs_match_exact_git
#   given: a wheel and source distribution presented for a clean candidate checkout
#   then: all archived source and packaged files match Git before any archived verifier or test executes
#   class: provenance
# === END CONTRACTS ===
from pathlib import Path, PurePosixPath
import base64
import csv
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import zipfile


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    require(name and not path.is_absolute() and ".." not in path.parts and "\\" not in name,
            "unsafe artifact path: " + name)


def tar_files(payload, *, one_root=False):
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        members = archive.getmembers()
        require(len({m.name for m in members}) == len(members), "duplicate source member")
        if one_root:
            require(len({PurePosixPath(m.name).parts[0] for m in members}) == 1,
                    "source archive must have one root")
        values = {}
        for member in members:
            safe_name(member.name)
            require(member.isfile() or member.isdir(), "unsupported source member")
            if member.isfile():
                values[member.name] = archive.extractfile(member).read()
        return values


def verify_inputs(repo, dist, output, *, final=False):
    repo, dist, output = (Path(value).resolve() for value in (repo, dist, output))
    require(not output.is_relative_to(repo), "replay output must be outside source")
    require(output.is_dir(), "replay output directory is missing")
    if not final:
        require(not (output / "source").exists() and not (output / "candidate-source.json").exists(),
                "replay input output is not new")

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args])

    require(Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() == repo,
            "ROOT must be the candidate repository root")
    require(not git("status", "--porcelain", "--untracked-files=all"), "candidate Git source must be clean")
    commit = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    source = tar_files(git("archive", commit))
    require(source.get("tools/verify_replay_inputs.py") == Path(__file__).read_bytes(),
            "executing source gate differs from candidate Git")
    contract_path = Path(__file__).with_name("release_contract.py")
    require(source["tools/release_contract.py"] == contract_path.read_bytes(), "release contract differs from candidate Git")
    contract = {"__name__": "epac_source_release_contract", "__file__": str(contract_path)}
    exec(compile(source["tools/release_contract.py"], str(contract_path), "exec", dont_inherit=True), contract)
    wheels, sdists = list(dist.glob("*.whl")), list(dist.glob("*.tar.gz"))
    require(len(wheels) == len(sdists) == 1, "expected one wheel and one source distribution")
    wheel, sdist = wheels[0], sdists[0]
    sdist_bytes, wheel_bytes = sdist.read_bytes(), wheel.read_bytes()
    raw = tar_files(sdist_bytes, one_root=True)
    roots = {name.split("/")[0] for name in raw}
    require(len(roots) == 1 and all("/" in name for name in raw), "source archive must have one root")
    archived = {name.split("/", 1)[1]: value for name, value in raw.items()}
    egg = "interdependency_epac.egg-info/"
    generated = {"PKG-INFO", "setup.cfg"} | {egg + name for name in
        ("PKG-INFO", "SOURCES.txt", "dependency_links.txt", "requires.txt", "top_level.txt")}
    require(set(archived) == set(source) | generated, "source archive coverage differs from candidate Git")
    for name, value in source.items():
        require(archived[name] == value, "archived source differs from candidate Git: " + name)
    require(archived["setup.cfg"] == b"[egg_info]\ntag_build = \ntag_date = 0\n\n", "unexpected generated setup configuration")

    with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as archive:
        entries = archive.infolist()
        require(len({entry.filename for entry in entries}) == len(entries), "duplicate wheel member")
        payload = {}
        for entry in entries:
            safe_name(entry.filename)
            require((entry.external_attr >> 16) & 0o170000 != 0o120000, "wheel symlink")
            if not entry.is_dir():
                payload[entry.filename] = archive.read(entry)
    packages = {"data": "epac_data", "subatomic": "epac_subatomic", "viz": "epac_viz"}
    expected = {}
    for name, value in source.items():
        if "/" not in name and name.startswith("epac_") and name.endswith(".py"):
            expected[name] = value
        elif "/" in name and name.split("/", 1)[0] in packages:
            root, relative = name.split("/", 1)
            expected[packages[root] + "/" + relative] = value
    info = "interdependency_epac-0.1.0.dist-info/"
    metadata = {name for name in payload if name.startswith(info)}
    project, license_names = contract["validate_core_metadata"](source, archived, payload, info)
    # This package declares no scripts or entry points and uses setuptools' default
    # root license-file discovery. Unknown installer metadata is not inert data.
    expected_metadata = {info + name for name in ("METADATA", "WHEEL", "top_level.txt", "RECORD")}
    expected_metadata |= {info + "licenses/" + name for name in license_names}
    require(metadata == expected_metadata, "undeclared or missing wheel metadata")
    setuptools_pins = {value.removeprefix("setuptools==") for value in project["build-system"]["requires"] if value.startswith("setuptools==")}
    require(len(setuptools_pins) == 1, "expected one exact setuptools source pin")
    wheel_header = ("Wheel-Version: 1.0\nGenerator: setuptools (" + next(iter(setuptools_pins))
                    + ")\nRoot-Is-Purelib: true\nTag: py3-none-any\n\n").encode()
    require(payload[info + "WHEEL"] == wheel_header, "wheel installer semantics differ from source build contract")
    top_levels = sorted({name.split("/")[0].removesuffix(".py") for name in expected})
    expected_top_levels = ("\n".join(top_levels) + "\n").encode()
    require(payload[info + "top_level.txt"] == archived[egg + "top_level.txt"] == expected_top_levels,
            "top-level metadata differs from source packages")
    require(set(payload) - metadata == set(expected), "wheel package coverage differs from candidate Git")
    require(all(payload[name] == value for name, value in expected.items()), "wheel package bytes differ from candidate Git")
    require(payload[info + "METADATA"] == archived["PKG-INFO"] == archived[egg + "PKG-INFO"],
            "wheel and source metadata differ")
    for name in metadata:
        if name.startswith(info + "licenses/"):
            original = name[len(info + "licenses/"):]
            require(original in source and payload[name] == source[original], "license/status bytes differ from Git")
    records = list(csv.reader(io.StringIO(payload[info + "RECORD"].decode())))
    require(all(len(row) == 3 for row in records) and len({row[0] for row in records}) == len(records)
            and {row[0] for row in records} == set(payload), "wheel RECORD coverage differs")
    for name, recorded_digest, size in records:
        if name == info + "RECORD":
            require(not recorded_digest and not size, "invalid RECORD self-entry")
        else:
            encoded = base64.urlsafe_b64encode(hashlib.sha256(payload[name]).digest()).decode().rstrip("=")
            require(recorded_digest == "sha256=" + encoded and size == str(len(payload[name])), "wheel RECORD digest differs")
    hashes = {wheel.name: digest(wheel_bytes), sdist.name: digest(sdist_bytes)}
    manifest_path = dist / "release-manifest.json"
    manifest_digest = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(), object_pairs_hook=contract["reject_duplicate_keys"])
        require(manifest["source_commit"] == commit and manifest["source_tree"] == tree,
                "release manifest source differs from candidate Git")
        require(manifest["artifacts_sha256"] == hashes, "release manifest artifact hashes differ")
        expected_manifest = contract["expected_release_manifest"](source, commit, tree,
            git("show", "-s", "--format=%ct", commit).decode().strip(), hashes)
        require(json.dumps(manifest, sort_keys=True) == json.dumps(expected_manifest, sort_keys=True),
                "release manifest fields differ from source release contract")
        manifest_digest = digest(manifest_path.read_bytes())
    expected_files = {wheel.name, sdist.name}
    if manifest_digest is not None:
        expected_files.update({"release-manifest.json", "SHA256SUMS"})
    require({path.name for path in dist.iterdir()} == expected_files
            and all(path.is_file() and not path.is_symlink() for path in dist.iterdir()),
            "distribution file set differs from candidate contract")
    if manifest_digest is not None:
        checksum_hashes = {**hashes, "release-manifest.json": manifest_digest}
        expected_sums = "".join(f"{value}  {name}\n" for name, value in sorted(checksum_hashes.items())).encode()
        require((dist / "SHA256SUMS").read_bytes() == expected_sums,
                "SHA256SUMS differs from actual candidate digests")
    require(git("rev-parse", "HEAD").decode().strip() == commit
            and not git("status", "--porcelain", "--untracked-files=all"), "candidate source changed during input verification")
    require(wheel.read_bytes() == wheel_bytes and sdist.read_bytes() == sdist_bytes, "artifacts changed during input verification")
    record = {"schema": "epac.candidate-inputs", "version": 1, "status": "passed",
              "source_commit": commit, "source_tree": tree,
              "git_source_files_sha256": {name: digest(value) for name, value in source.items()},
              "archived_source_files_sha256": {name: digest(value) for name, value in archived.items()},
              "wheel_files_sha256": {name: digest(value) for name, value in payload.items()},
              "artifacts_sha256": hashes, "release_manifest_sha256": manifest_digest,
              "verifier_sha256": digest(Path(__file__).read_bytes()),
              "test_verifier_sha256": digest(source["tools/verify_installed.py"])}
    if final:
        require(json.loads((output / "candidate-source.json").read_text()) == record,
                "candidate binding changed during replay")
        extracted = output / "source" / next(iter(roots))
        paths = list(extracted.rglob("*"))
        require(not any(path.is_symlink() for path in paths), "extracted source contains a symlink")
        actual = {path.relative_to(extracted).as_posix(): digest(path.read_bytes())
                  for path in paths if path.is_file()}
        require(actual == record["archived_source_files_sha256"], "extracted source changed during replay")
    else:
        destination = output / "source"
        destination.mkdir()
        with tarfile.open(fileobj=io.BytesIO(sdist_bytes)) as archive:
            archive.extractall(destination, filter="data")
        (output / "candidate-source.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


if __name__ == "__main__":
    if sys.flags.optimize:
        raise SystemExit("optimized Python mode cannot authorize replay inputs")
    require(len(sys.argv) == 4 or (len(sys.argv) == 5 and sys.argv[4] == "--final"),
            "usage: ROOT DIST OUTPUT [--final]")
    verify_inputs(*sys.argv[1:4], final=len(sys.argv) == 5)
