"""Loaded-code-aware UCNS provenance verification shared by EPAC constructors.

The verifier stamps a UCNS commit only when the executing function bytecode
matches the clean source at the declared commit. Verification is cached by a
witness containing HEAD, index state, source bytes, file modes, and loaded code,
so repeated nested construction avoids Git subprocesses without preserving a
stale answer.

Usage guidance:

    commit = verify_loaded_ucns_commit(
        pinned_commit=PINNED_UCNS_COMMIT,
        dependencies=(public_gonol_function, native_mobius_state),
    )
    # commit is the exact pin or "hmmm"; never promote "hmmm" to the pin.
"""

# === MODULE_BUILD ===
# id: epac_ucns_loaded_provenance
#   module_name: epac_ucns_provenance
#   module_kind: service
#   summary: binds UCNS receipt provenance to clean pinned source and the function code actually executing
#   owner: The Interdependency
#   public_surface: verify_loaded_ucns_commit, clear_ucns_verification_cache, ucns_verification_cache_info
#   internal_surface: source witness, Git metadata resolution, code fingerprint, cached verification
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_epac_ucns_provenance
#   rollout: called by both EPAC Public Gonol construction paths
#   rollback: callers preserve ucns identity as hmmm rather than bypassing verification
#   since: 2026-09-09
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: epac_ucns_pin_matches_loaded_code
#   given: EPAC is about to stamp a pinned UCNS dependency identity
#   then: each executing dependency function matches the clean tracked source at that exact HEAD; otherwise the identity is hmmm
#   class: provenance
#
# id: epac_ucns_verification_reuses_only_identical_witness
#   given: repeated construction uses unchanged HEAD, index, relevant source bytes, modes, and loaded code
#   then: Git verification executes once; any witness change selects a new verification result
#   class: performance
# === END CONTRACTS ===

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import inspect
import marshal
from pathlib import Path
import re
import subprocess
from types import CodeType
from typing import Callable, Sequence


HEX40 = re.compile(r"^[0-9a-f]{40}$")
Runner = Callable[..., object]


def _git_root(path: Path) -> Path | None:
    for candidate in (path.parent, *path.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()
    return None


def _git_directories(root: Path) -> tuple[Path, Path] | None:
    marker = root / ".git"
    if marker.is_dir():
        git_dir = marker.resolve()
    elif marker.is_file():
        line = marker.read_text(encoding="utf-8").strip()
        if not line.startswith("gitdir: "):
            return None
        target = Path(line.removeprefix("gitdir: "))
        git_dir = (target if target.is_absolute() else root / target).resolve()
    else:
        return None
    common_file = git_dir / "commondir"
    if common_file.is_file():
        target = Path(common_file.read_text(encoding="utf-8").strip())
        common_dir = (target if target.is_absolute() else git_dir / target).resolve()
    else:
        common_dir = git_dir
    return git_dir, common_dir


def _packed_ref(common_dir: Path, ref_name: str) -> str | None:
    packed = common_dir / "packed-refs"
    if not packed.is_file():
        return None
    suffix = f" {ref_name}"
    for line in packed.read_text(encoding="utf-8").splitlines():
        if line.startswith(("#", "^")) or not line.endswith(suffix):
            continue
        value = line.split(" ", 1)[0]
        return value if HEX40.fullmatch(value) else None
    return None


def _head_and_index_witness(root: Path) -> tuple[str, int, int] | None:
    directories = _git_directories(root)
    if directories is None:
        return None
    git_dir, common_dir = directories
    head_text = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if HEX40.fullmatch(head_text):
        head = head_text
    elif head_text.startswith("ref: "):
        ref_name = head_text.removeprefix("ref: ")
        values = []
        for base in (git_dir, common_dir):
            ref_path = base / ref_name
            if ref_path.is_file():
                values.append(ref_path.read_text(encoding="utf-8").strip())
        head = next((value for value in values if HEX40.fullmatch(value)), None)
        if head is None:
            head = _packed_ref(common_dir, ref_name)
        if head is None:
            return None
    else:
        return None
    index = git_dir / "index"
    if not index.exists():
        index = common_dir / "index"
    stat = index.stat()
    return head, stat.st_mtime_ns, stat.st_size


def _normalized_code(code: CodeType) -> tuple[object, ...]:
    constants = tuple(
        ("code", _normalized_code(item)) if isinstance(item, CodeType) else item
        for item in code.co_consts
    )
    return (
        code.co_name,
        code.co_qualname,
        code.co_argcount,
        code.co_posonlyargcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        code.co_code,
        constants,
        code.co_names,
        code.co_varnames,
        code.co_freevars,
        code.co_cellvars,
        code.co_exceptiontable,
    )


def _code_fingerprint(code: CodeType) -> str:
    return sha256(marshal.dumps(_normalized_code(code))).hexdigest()


def _find_code(module_code: CodeType, qualname: str) -> CodeType | None:
    matches: list[CodeType] = []

    def walk(code: CodeType) -> None:
        for item in code.co_consts:
            if not isinstance(item, CodeType):
                continue
            if item.co_qualname == qualname:
                matches.append(item)
            walk(item)

    walk(module_code)
    return matches[0] if len(matches) == 1 else None


def _source_records(dependencies: Sequence[Callable[..., object]]) -> tuple[Path, tuple[tuple[object, ...], ...]] | None:
    records: list[tuple[object, ...]] = []
    root: Path | None = None
    for dependency in dependencies:
        code = getattr(dependency, "__code__", None)
        qualname = getattr(dependency, "__qualname__", None)
        if not isinstance(code, CodeType) or not isinstance(qualname, str):
            return None
        try:
            path = Path(inspect.getfile(dependency)).resolve()
            data = path.read_bytes()
            stat = path.stat()
        except (OSError, TypeError):
            return None
        dependency_root = _git_root(path)
        if dependency_root is None or (root is not None and dependency_root != root):
            return None
        root = dependency_root
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            return None
        records.append(
            (
                relative,
                str(path),
                qualname,
                _code_fingerprint(code),
                sha256(data).hexdigest(),
                stat.st_mode,
            )
        )
    if root is None:
        return None
    return root, tuple(records)


def _expected_code_fingerprint(path: Path, qualname: str) -> str | None:
    try:
        module_code = compile(path.read_bytes(), str(path), "exec", dont_inherit=True)
    except (OSError, SyntaxError, ValueError):
        return None
    code = _find_code(module_code, qualname)
    return None if code is None else _code_fingerprint(code)


@lru_cache(maxsize=32)
def _verify_witness(
    pinned_commit: str,
    root_text: str,
    head: str,
    index_mtime_ns: int,
    index_size: int,
    records: tuple[tuple[object, ...], ...],
    runner: Runner,
) -> str:
    del index_mtime_ns, index_size  # Their presence invalidates the cache key.
    if head != pinned_commit:
        return "hmmm"
    root = Path(root_text)
    disk_records: dict[str, tuple[Path, str]] = {}
    for relative, absolute, qualname, loaded_digest, disk_digest, _mode in records:
        path = Path(str(absolute))
        try:
            if sha256(path.read_bytes()).hexdigest() != disk_digest:
                return "hmmm"
        except OSError:
            return "hmmm"
        expected_digest = _expected_code_fingerprint(path, str(qualname))
        if expected_digest is None or expected_digest != loaded_digest:
            return "hmmm"
        disk_records[str(relative)] = (path, f"{int(_mode) & 0o177777:06o}")
    try:
        observed = runner(
            ("git", "-C", str(root), "rev-parse", "HEAD"),
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if getattr(observed, "stdout", "").strip() != pinned_commit:
            return "hmmm"
        for relative_path, (path, disk_mode) in sorted(disk_records.items()):
            tree_entry = runner(
                ("git", "-C", str(root), "ls-tree", pinned_commit, "--", relative_path),
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            )
            fields = getattr(tree_entry, "stdout", "").strip().split(None, 3)
            if len(fields) != 4 or fields[0] != disk_mode or fields[1] != "blob":
                return "hmmm"
            pinned_blob = runner(
                ("git", "-C", str(root), "cat-file", "blob", fields[2]),
                check=True,
                capture_output=True,
                timeout=2,
            )
            if getattr(pinned_blob, "stdout", b"") != path.read_bytes():
                return "hmmm"
    except (OSError, subprocess.SubprocessError):
        return "hmmm"
    return pinned_commit


def verify_loaded_ucns_commit(
    *,
    pinned_commit: str,
    dependencies: Sequence[Callable[..., object]],
    runner: Runner = subprocess.run,
) -> str:
    """Return ``pinned_commit`` only for a clean, loaded-code-matched runtime."""

    if not HEX40.fullmatch(pinned_commit):
        return "hmmm"
    source = _source_records(dependencies)
    if source is None:
        return "hmmm"
    root, records = source
    try:
        git_witness = _head_and_index_witness(root)
    except OSError:
        return "hmmm"
    if git_witness is None:
        return "hmmm"
    head, index_mtime_ns, index_size = git_witness
    return _verify_witness(
        pinned_commit,
        str(root),
        head,
        index_mtime_ns,
        index_size,
        records,
        runner,
    )


def clear_ucns_verification_cache() -> None:
    """Clear cached witnesses; intended for isolated tests and process repair."""

    _verify_witness.cache_clear()


def ucns_verification_cache_info():
    """Expose cache counters for provenance/performance regression tests."""

    return _verify_witness.cache_info()


__all__ = [
    "clear_ucns_verification_cache",
    "ucns_verification_cache_info",
    "verify_loaded_ucns_commit",
]
