"""Usage: install requirements-build.txt, then python tools/build_release.py NEW_OUTPUT.

Builds a candidate from clean Git source after license selection. Publication and
stack acceptance are separate operations over the resulting immutable hashes.
"""
# === MODULE_BUILD ===
# id: epac_release_build
#   module_name: build_release
#   module_kind: instrument
#   summary: builds an immutable candidate from licensed exact Git source
#   owner: The Interdependency
#   public_surface: python tools/build_release.py NEW_OUTPUT
#   internal_surface: main, check_runtime, check_compressor, normalize_sdist, normalize_wheel
#   auth_boundary: none
#   storage_boundary: write
#   storage_notes: temporary source archive and new caller-selected output directory
#   network_boundary: none
#   network_notes: none; install the pinned build requirements first
#   user_data_boundary: none
#   admin_only: false
#   tests: clean wheel/sdist replay and pre-publication stack integration
#   rollout: explicit candidate qualification command
#   rollback: retain the previously accepted immutable artifact
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: epac_candidate_binds_licensed_source
#   given: clean source with selected license and the exact build toolchain
#   then: candidate artifacts bind Git source, license, UCNS source lock, and toolchain identities without claiming release acceptance
#   class: provenance
# === END CONTRACTS ===
from __future__ import annotations

import gzip
import hashlib
from importlib import metadata
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
import zlib


def check_runtime() -> dict[str, str]:
    actual = {"implementation": sys.implementation.name,
              "version": ".".join(map(str, sys.version_info[:3]))}
    if actual != {"implementation": "cpython", "version": "3.11.15"}:
        raise RuntimeError(f"release builds require CPython 3.11.15: {actual}")
    return actual


def check_compressor() -> dict[str, str]:
    expected = "1.3.1"
    actual = {"implementation": "zlib", "compile_version": zlib.ZLIB_VERSION, "runtime_version": zlib.ZLIB_RUNTIME_VERSION}
    if actual["compile_version"] != expected or actual["runtime_version"] != expected:
        raise RuntimeError(f"release builds require zlib {expected} at compile time and runtime: {actual}")
    return actual


def normalize_sdist(path: Path, destination: Path, epoch: int) -> None:
    with path.open("rb") as raw, tarfile.open(fileobj=raw, mode="r:gz") as source:
        with destination.open("wb") as output, gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as target:
                for member in sorted(source.getmembers(), key=lambda item: item.name):
                    if not (member.isfile() or member.isdir()):
                        raise ValueError(f"unexpected sdist member: {member.name}")
                    member.uid = member.gid = 0
                    member.uname = member.gname = ""
                    member.mtime = epoch
                    member.pax_headers = {}
                    member.mode = 0o755 if member.isdir() or member.mode & 0o111 else 0o644
                    if member.isfile():
                        with source.extractfile(member) as stream:
                            target.addfile(member, stream)
                    else:
                        target.addfile(member)



def normalize_wheel(path: Path, destination: Path, epoch: int) -> None:
    """Fix archive metadata while retaining payload and RECORD bytes."""
    with zipfile.ZipFile(path) as original, zipfile.ZipFile(destination, "w") as normalized:
        for entry in sorted(original.infolist(), key=lambda item: item.filename):
            header = zipfile.ZipInfo(entry.filename, time.gmtime(epoch)[:6])
            header.create_system = 3
            executable = bool((entry.external_attr >> 16) & 0o111)
            mode = 0o40755 if entry.is_dir() else 0o100755 if executable else 0o100644
            header.external_attr = (mode << 16) | (0x10 if entry.is_dir() else 0)
            normalized.writestr(header, original.read(entry), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = Path(sys.argv[1]).resolve()
    if out.exists() or out.is_relative_to(root):
        raise ValueError("output must be new and outside source")
    def git(*arguments):
        return subprocess.check_output(("git", "-C", str(root), *arguments), text=True).strip()
    if git("status", "--porcelain"):
        raise ValueError("release source must be clean")
    runtime = check_runtime()
    compressor = check_compressor()
    commit = git("rev-parse", "HEAD")
    def source_bytes(path):
        return subprocess.check_output(("git", "-C", str(root), "show", f"{commit}:{path}"))
    source_files = {path: source_bytes(path) for path in git("ls-tree", "-r", "--name-only", commit).splitlines()}
    contract_path = root / "tools/release_contract.py"
    contract = {"__name__": "epac_source_release_contract", "__file__": str(contract_path)}
    exec(compile(source_files["tools/release_contract.py"], str(contract_path), "exec", dont_inherit=True), contract)
    contract["release_license"](source_files)
    versions = {}
    for line in git("show", f"{commit}:requirements-build.txt").splitlines():
        name, version = line.split("==")
        if metadata.version(name) != version:
            raise ValueError(f"install pinned build requirement {line}")
        versions[name] = version
    epoch = git("show", "-s", "--format=%ct", commit)
    archive = subprocess.check_output(("git", "-C", str(root), "archive", commit))
    with tempfile.TemporaryDirectory(prefix="epac-release-") as directory:
        source = Path(directory) / "source"
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
            for member in contents:
                if not (member.isfile() or member.isdir()) or member.name.startswith("/") or ".." in Path(member.name).parts:
                    raise ValueError("unsupported source archive member")
            if not hasattr(tarfile, "data_filter"):
                raise SystemExit("release builds require tarfile.data_filter support")
            contents.extractall(source, filter="data")
        environment = dict(os.environ, SOURCE_DATE_EPOCH=epoch, PYTHONHASHSEED="0")
        environment.pop("PYTHONPATH", None)
        subprocess.run((sys.executable, "-m", "build", "--no-isolation", "--outdir", str(out), str(source)), check=True, env=environment)
    sdist = next(out.glob("*.tar.gz"))
    with tempfile.TemporaryDirectory(prefix="epac-sdist-") as directory:
        normalized = Path(directory) / sdist.name
        normalize_sdist(sdist, normalized, int(epoch))
        sdist.write_bytes(normalized.read_bytes())
        wheel = next(out.glob("*.whl"))
        normalized_wheel = Path(directory) / wheel.name
        normalize_wheel(wheel, normalized_wheel, int(epoch))
        wheel.write_bytes(normalized_wheel.read_bytes())
    artifacts = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
    if len(artifacts) != 2 or not any(name.endswith(".whl") for name in artifacts) or not any(name.endswith(".tar.gz") for name in artifacts):
        raise ValueError("expected one wheel and one sdist")
    manifest = contract["expected_release_manifest"](source_files, commit, git("rev-parse", f"{commit}^{{tree}}"), epoch, artifacts)
    if manifest["python_runtime"] != runtime or manifest["compressor"] != compressor or manifest["build_toolchain"] != versions:
        raise ValueError("observed build toolchain differs from release contract")
    receipt = out / "release-manifest.json"
    receipt.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    artifacts[receipt.name] = hashlib.sha256(receipt.read_bytes()).hexdigest()
    (out / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(artifacts.items())))


if __name__ == "__main__":
    main()
