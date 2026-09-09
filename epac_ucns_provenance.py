"""Loaded-code-aware UCNS provenance verification shared by EPAC constructors.

The verifier stamps a UCNS commit only when each executing function and its
transitively referenced UCNS runtime state match the clean source at the
declared commit. Verification is cached by a witness containing HEAD, index
state, source bytes, file modes, and loaded state, so repeated nested
construction avoids Git subprocesses without preserving a stale answer.

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
#   summary: binds UCNS receipt provenance to clean pinned source and the transitive UCNS runtime state actually executing
#   owner: The Interdependency
#   public_surface: verify_loaded_ucns_commit, clear_ucns_verification_cache, ucns_verification_cache_info
#   internal_surface: source witness, Git metadata resolution, transitive loaded-state fingerprint, cached verification
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
#   then: each executing dependency function and its transitively referenced UCNS helpers, classes, defaults, closures, and globals match the clean tracked source at that exact HEAD; otherwise the identity is hmmm
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
import sys
from dataclasses import fields, is_dataclass
from enum import Enum
from types import CodeType, FunctionType, ModuleType
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


def _freeze_loaded_state(
    value: object,
    owner_module: str,
    seen: dict[int, int],
) -> tuple[object, ...]:
    """Normalize one transitive callable state without module-name noise."""

    if isinstance(value, Enum):
        return ("enum-member", value.name, _freeze_loaded_state(value.value, owner_module, seen))
    if value is None or isinstance(value, (bool, int, str, bytes)):
        return ("literal", type(value).__name__, value)
    if isinstance(value, float):
        return ("float", value.hex())
    identity = id(value)
    if identity in seen:
        return ("ref", seen[identity])
    seen[identity] = len(seen)
    if isinstance(value, tuple):
        return ("tuple", *(_freeze_loaded_state(item, owner_module, seen) for item in value))
    if isinstance(value, list):
        return ("list", *(_freeze_loaded_state(item, owner_module, seen) for item in value))
    if isinstance(value, (set, frozenset)):
        items = [_freeze_loaded_state(item, owner_module, seen) for item in value]
        return ("set", *sorted(items, key=repr))
    if isinstance(value, dict):
        items = [
            (
                _freeze_loaded_state(key, owner_module, seen),
                _freeze_loaded_state(item, owner_module, seen),
            )
            for key, item in value.items()
        ]
        return ("dict", *sorted(items, key=repr))
    if isinstance(value, ModuleType):
        return ("external-module", value.__name__)
    if isinstance(value, CodeType):
        return ("code", _normalized_code(value))
    if isinstance(value, FunctionType):
        module_name = getattr(value, "__module__", "")
        if module_name != owner_module:
            return ("external-function", module_name, value.__qualname__)
        global_state = []
        for name in sorted(set(value.__code__.co_names)):
            if name in value.__globals__:
                global_state.append(
                    (name, _freeze_loaded_state(value.__globals__[name], owner_module, seen))
                )
        closure = tuple(
            _freeze_loaded_state(cell.cell_contents, owner_module, seen)
            for cell in (value.__closure__ or ())
        )
        return (
            "function",
            value.__qualname__,
            _normalized_code(value.__code__),
            _freeze_loaded_state(value.__defaults__, owner_module, seen),
            _freeze_loaded_state(value.__kwdefaults__, owner_module, seen),
            _freeze_loaded_state(value.__annotations__, owner_module, seen),
            tuple(global_state),
            closure,
        )
    if isinstance(value, type):
        module_name = getattr(value, "__module__", "")
        if module_name != owner_module:
            return ("external-class", module_name, value.__qualname__)
        attributes = []
        for name, item in sorted(vars(value).items()):
            if name in {"__module__", "__doc__", "__dict__", "__weakref__"}:
                continue
            if isinstance(item, (staticmethod, classmethod)):
                item = item.__func__
            if isinstance(item, property):
                item = (item.fget, item.fset, item.fdel)
            if (
                name.startswith("__")
                and name not in {"__annotations__", "__match_args__", "__slots__"}
                and not callable(item)
            ):
                continue
            attributes.append((name, _freeze_loaded_state(item, owner_module, seen)))
        members = tuple(
            (name, _freeze_loaded_state(item.value, owner_module, seen))
            for name, item in getattr(value, "__members__", {}).items()
        )
        return ("class", value.__qualname__, tuple(attributes), members)
    value_type = type(value)
    if value_type.__module__ == owner_module and is_dataclass(value):
        return (
            "dataclass-instance",
            value_type.__qualname__,
            tuple(
                (field.name, _freeze_loaded_state(getattr(value, field.name), owner_module, seen))
                for field in fields(value)
            ),
        )
    if value_type.__module__ == "fractions" and hasattr(value, "numerator"):
        return ("fraction", int(value.numerator), int(value.denominator))
    return ("external-object", value_type.__module__, value_type.__qualname__)


def _transitive_fingerprint(dependency: Callable[..., object]) -> str:
    owner_module = getattr(dependency, "__module__", "")
    frozen = _freeze_loaded_state(dependency, owner_module, {})
    return sha256(marshal.dumps(frozen)).hexdigest()


def _fresh_dependency_fingerprints(
    path: Path,
    disk_digest: str,
    qualnames: Sequence[str],
) -> dict[str, str] | None:
    module_name = f"_epac_ucns_verified_{disk_digest[:20]}"
    module = ModuleType(module_name)
    module.__file__ = str(path)
    module.__package__ = ""
    prior = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        source = path.read_bytes()
        if sha256(source).hexdigest() != disk_digest:
            return None
        code = compile(source, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
        result: dict[str, str] = {}
        for qualname in qualnames:
            item: object = module
            for part in qualname.split("."):
                item = getattr(item, part)
            if not isinstance(item, FunctionType):
                return None
            result[qualname] = _transitive_fingerprint(item)
        return result
    except (AttributeError, ImportError, OSError, RuntimeError, TypeError, ValueError):
        return None
    finally:
        if prior is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = prior


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
                _transitive_fingerprint(dependency),
                sha256(data).hexdigest(),
                stat.st_mode,
            )
        )
    if root is None:
        return None
    return root, tuple(records)


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
    disk_records: dict[str, tuple[Path, str, str, list[tuple[str, str]]]] = {}
    for relative, absolute, qualname, loaded_digest, disk_digest, _mode in records:
        path = Path(str(absolute))
        try:
            if sha256(path.read_bytes()).hexdigest() != disk_digest:
                return "hmmm"
        except OSError:
            return "hmmm"
        relative_text = str(relative)
        mode = f"{int(_mode) & 0o177777:06o}"
        existing = disk_records.get(relative_text)
        if existing is None:
            disk_records[relative_text] = (
                path,
                mode,
                str(disk_digest),
                [(str(qualname), str(loaded_digest))],
            )
        else:
            existing_path, existing_mode, existing_digest, dependencies = existing
            if (
                existing_path != path
                or existing_mode != mode
                or existing_digest != disk_digest
            ):
                return "hmmm"
            dependencies.append((str(qualname), str(loaded_digest)))
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
        for relative_path, (path, disk_mode, _disk_digest, _dependencies) in sorted(
            disk_records.items()
        ):
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
    for path, _disk_mode, disk_digest, dependencies in disk_records.values():
        expected = _fresh_dependency_fingerprints(
            path,
            disk_digest,
            tuple(qualname for qualname, _loaded_digest in dependencies),
        )
        if expected is None:
            return "hmmm"
        if any(
            expected.get(qualname) != loaded_digest
            for qualname, loaded_digest in dependencies
        ):
            return "hmmm"
    return pinned_commit


def verify_loaded_ucns_commit(
    *,
    pinned_commit: str,
    dependencies: Sequence[Callable[..., object]],
    runner: Runner = subprocess.run,
) -> str:
    """Return ``pinned_commit`` only for a clean, loaded-state-matched runtime."""

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
