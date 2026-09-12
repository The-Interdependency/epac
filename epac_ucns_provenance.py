"""Loaded-code-aware UCNS provenance verification shared by EPAC constructors.

The verifier stamps a UCNS commit only when each executing function and its
transitively referenced UCNS runtime state match the declared source. A checkout
uses its exact clean Git commit; an installed distribution uses the complete
UCNS Python-source map shipped in epac_data/ucns-source-lock.json. The latter
establishes source-byte equivalence to the pin; installation artifact hashes are
verified separately by the clean-install and consumer receipts.

Caches bind source bytes and loaded state. Git witnesses also bind HEAD, index,
and modes. Runtime aliasing stays explicit; incidental bytecode string sharing
does not change a witness. No Git checkout is required for a verified wheel.

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
#   then: each executing dependency function and its transitively referenced UCNS helpers, classes, defaults, closures, and globals match either clean tracked source at that exact HEAD or the complete installed source map owned by EPAC for that commit; otherwise the identity is hmmm
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
from importlib import metadata, resources
import inspect
import json
import marshal
import os
from pathlib import Path
import re
import subprocess
import sys
from dataclasses import fields, is_dataclass
from enum import Enum
from types import BuiltinFunctionType, CodeType, FunctionType, ModuleType
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


def _head_and_index_witness(root: Path) -> tuple[str, str] | None:
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
    configured_index = os.environ.get("GIT_INDEX_FILE")
    if configured_index:
        index = Path(configured_index)
        if not index.is_absolute():
            index = root / index
        index = index.resolve()
    else:
        index = git_dir / "index"
        if not index.exists():
            index = common_dir / "index"
    return head, sha256(index.read_bytes()).hexdigest()


def _normalized_code(code: CodeType) -> tuple[object, ...]:
    def constant(item):
        if isinstance(item, CodeType):
            return ("code", _normalized_code(item))
        if isinstance(item, tuple):
            return ("tuple", tuple(constant(value) for value in item))
        if isinstance(item, frozenset):
            return ("frozenset", tuple(sorted((constant(value) for value in item), key=repr)))
        return item
    constants = tuple(constant(item) for item in code.co_consts)
    return (
        code.co_name,
        getattr(code, "co_qualname", code.co_name),
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
        getattr(code, "co_exceptiontable", b""),
    )


def _referenced_names(code: CodeType) -> set[str]:
    names = set(code.co_names)
    for constant in code.co_consts:
        if isinstance(constant, CodeType):
            names.update(_referenced_names(constant))
    return names


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
    if isinstance(value, BuiltinFunctionType):
        return (
            "builtin-function",
            getattr(value, "__module__", ""),
            getattr(value, "__qualname__", getattr(value, "__name__", "")),
        )
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
        builtin_state = []
        effective_builtins = value.__builtins__
        if isinstance(effective_builtins, ModuleType):
            effective_builtins = vars(effective_builtins)
        for name in sorted(_referenced_names(value.__code__)):
            if name in value.__globals__:
                global_state.append(
                    (name, _freeze_loaded_state(value.__globals__[name], owner_module, seen))
                )
            elif isinstance(effective_builtins, dict) and name in effective_builtins:
                builtin_state.append(
                    (name, _freeze_loaded_state(effective_builtins[name], owner_module, seen))
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
            tuple(builtin_state),
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
        bases = tuple(_freeze_loaded_state(base, owner_module, seen) for base in value.__bases__)
        return ("class", value.__qualname__, tuple(attributes), members, bases)
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
    # v3+ records incidental sharing of immutable serialization objects. Loaded
    # bytecode and fresh compilation can share equal strings differently on 3.10.
    # Runtime aliasing is already explicit in the frozen state's "ref" records.
    return sha256(marshal.dumps(frozen, 2)).hexdigest()


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
            if inspect.ismethod(item):
                item = item.__func__
            if not isinstance(item, (FunctionType, type)):
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


def _dependency_closure(dependencies: Sequence[Callable[..., object]]) -> tuple[Callable[..., object], ...]:
    """Give UCNS-owned cross-module state its own fresh-source comparison.

    A freshly compiled entry module still imports from the live interpreter.
    Separate records prevent a patched imported helper from validating itself.
    Module-valued references conservatively include that UCNS module's exports.
    """
    records = {id(value): value for value in dependencies}
    seen: set[int] = set()

    def owned(name: str) -> bool:
        return name == "ucns" or name.startswith("ucns.")

    def visit(value: object, owner: str) -> None:
        module_name = getattr(value, "__module__", "")
        if isinstance(value, (FunctionType, type)) and module_name != owner:
            if not owned(module_name):
                return
            records[id(value)] = value
            owner = module_name
        if id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, FunctionType):
            builtins = value.__builtins__
            if isinstance(builtins, ModuleType):
                builtins = vars(builtins)
            for name in sorted(_referenced_names(value.__code__)):
                if name in value.__globals__:
                    visit(value.__globals__[name], owner)
                elif isinstance(builtins, dict) and name in builtins:
                    visit(builtins[name], owner)
            for item in (value.__defaults__, value.__kwdefaults__, value.__annotations__):
                visit(item, owner)
            for cell in value.__closure__ or ():
                visit(cell.cell_contents, owner)
        elif isinstance(value, type):
            for item in vars(value).values():
                if isinstance(item, (staticmethod, classmethod)):
                    item = item.__func__
                if isinstance(item, property):
                    item = (item.fget, item.fset, item.fdel)
                visit(item, owner)
            for base in value.__bases__:
                visit(base, owner)
        elif isinstance(value, ModuleType):
            if owned(value.__name__):
                for item in vars(value).values():
                    visit(item, "")
        elif isinstance(value, dict):
            for key, item in value.items():
                visit(key, owner)
                visit(item, owner)
        elif isinstance(value, (tuple, list, set, frozenset)):
            for item in value:
                visit(item, owner)
        elif isinstance(value, Enum) and owned(type(value).__module__):
            visit(type(value), owner)
            visit(value.value, owner)
        elif is_dataclass(value) and owned(type(value).__module__):
            visit(type(value), owner)
            for field in fields(value):
                visit(getattr(value, field.name), owner)

    for dependency in dependencies:
        visit(dependency, getattr(dependency, "__module__", ""))
    return tuple(records.values())


def _source_records(dependencies: Sequence[Callable[..., object]], *, installed_root: Path | None = None) -> tuple[Path, tuple[tuple[object, ...], ...]] | None:
    records: list[tuple[object, ...]] = []
    root: Path | None = None
    for dependency in _dependency_closure(dependencies):
        code = getattr(dependency, "__code__", None)
        qualname = getattr(dependency, "__qualname__", None)
        if not (isinstance(code, CodeType) or isinstance(dependency, type)) or not isinstance(qualname, str):
            return None
        try:
            path = Path(inspect.getfile(dependency)).resolve()
            data = path.read_bytes()
            stat = path.stat()
        except (OSError, TypeError):
            return None
        dependency_root = installed_root or _git_root(path)
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
def _verify_installed_witness(
    pinned_commit: str,
    lock_bytes: bytes,
    source_files: tuple[tuple[str, str], ...],
    records: tuple[tuple[object, ...], ...],
) -> str:
    """Compare installed source to an EPAC-owned exact upstream source map."""
    lock = json.loads(lock_bytes)
    if lock.get("repository") != "The-Interdependency/ucns" or lock.get("commit") != pinned_commit:
        return "hmmm"
    if dict(source_files) != lock.get("installed_source_sha256") or not records:
        return "hmmm"
    for relative, absolute, qualname, loaded_digest, disk_digest, _mode in records:
        if lock["installed_source_sha256"].get(relative) != disk_digest:
            return "hmmm"
        expected = _fresh_dependency_fingerprints(Path(absolute), disk_digest, (qualname,))
        if expected is None or expected.get(qualname) != loaded_digest:
            return "hmmm"
    return pinned_commit


def _installed_identity(pinned_commit: str, dependencies: Sequence[Callable[..., object]]) -> str | None:
    """Return None for a checkout, hmmm for an unverified installed runtime."""
    try:
        distribution = metadata.distribution("ucns")
        listed = {str(path) for path in distribution.files or ()}
        if "ucns/__init__.py" not in listed:
            return None  # Editable installations retain the existing Git witness.
        root = Path(distribution.locate_file("")).resolve()
        source = _source_records(dependencies, installed_root=root)
        if source is None:
            return None  # Functions from an independent checkout use Git.
        _, records = source
        # Enumerate disk files as well as RECORD entries, detecting added modules.
        files = []
        for path in sorted((root / "ucns").rglob("*.py")):
            relative = path.relative_to(root).as_posix()
            if relative not in listed or not path.resolve().is_relative_to(root / "ucns"):
                return "hmmm"
            files.append((relative, sha256(path.read_bytes()).hexdigest()))
        lock_bytes = resources.files("epac_data").joinpath("ucns-source-lock.json").read_bytes()
        return _verify_installed_witness(pinned_commit, lock_bytes, tuple(files), records)
    except metadata.PackageNotFoundError:
        return None
    except (OSError, ValueError, TypeError, KeyError):
        return "hmmm"


def _git_blob_mode(filesystem_mode: int) -> str:
    """Collapse permissions to Git's owner-executable regular-file modes."""

    return "100755" if filesystem_mode & 0o100 else "100644"


@lru_cache(maxsize=32)
def _verify_witness(
    pinned_commit: str,
    root_text: str,
    head: str,
    index_digest: str,
    records: tuple[tuple[object, ...], ...],
    runner: Runner,
) -> str:
    del index_digest  # Its presence binds cache reuse to the complete index bytes.
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
        mode = _git_blob_mode(int(_mode))
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
            )
            fields = getattr(tree_entry, "stdout", "").strip().split(None, 3)
            if len(fields) != 4 or fields[0] != disk_mode or fields[1] != "blob":
                return "hmmm"
            index_entry = runner(
                ("git", "-C", str(root), "ls-files", "--stage", "--", relative_path),
                check=True,
                capture_output=True,
                text=True,
            )
            index_fields = getattr(index_entry, "stdout", "").strip().split(None, 3)
            if (
                len(index_fields) != 4
                or index_fields[0] != fields[0]
                or index_fields[1] != fields[2]
                or index_fields[2] != "0"
                or index_fields[3] != relative_path
            ):
                return "hmmm"
            pinned_blob = runner(
                ("git", "-C", str(root), "cat-file", "blob", fields[2]),
                check=True,
                capture_output=True,
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
    installed = _installed_identity(pinned_commit, dependencies)
    if installed is not None:
        return installed
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
    head, index_digest = git_witness
    return _verify_witness(
        pinned_commit,
        str(root),
        head,
        index_digest,
        records,
        runner,
    )


def clear_ucns_verification_cache() -> None:
    """Clear cached witnesses; intended for isolated tests and process repair."""

    _verify_witness.cache_clear()
    _verify_installed_witness.cache_clear()


def ucns_verification_cache_info():
    """Expose cache counters for provenance/performance regression tests."""

    git = _verify_witness.cache_info()
    installed = _verify_installed_witness.cache_info()
    return type(git)(git.hits + installed.hits, git.misses + installed.misses,
                     git.maxsize + installed.maxsize, git.currsize + installed.currsize)


__all__ = [
    "clear_ucns_verification_cache",
    "ucns_verification_cache_info",
    "verify_loaded_ucns_commit",
]
