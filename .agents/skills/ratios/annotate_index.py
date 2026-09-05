# ratios: loc_comments=232:33 imports_exports=7:4 calls_definitions=83:14
"""Portable computer for the canonical ratios seal — a0's `N:M C:D I:O`.

This is the shared, stdlib port of `The-Interdependency/a0`'s
`scripts/annotate.py`. The compact positional line

    # N:M C:D I:O        (Python)
    // N:M C:D I:O       (TypeScript / TSX)

is the *canonical* ratios seal (see `ratios/SKILL.md`). Unlike the portable
per-file `loc_comments=…` form (verified by `ratios_check.py`), the canonical
`C:D` and `I:O` are **not single-file computable** — they need a repo-wide
inverted index. This module builds that index in a single linear pass and can
recompute or stamp the seal for any repo, not just a0.

Metric definitions (identical to a0):

    N  code lines : M  comment/docstring lines            (internal density)
    C  consumed   : D  declared                           (surface utility)
    I  fan-in     : O  fan-out                            (graph position)

    D  = declared `# DOC endpoint:` routes (.py); exported symbols (.ts/.tsx)
    C  = declared routes referenced in the consumer dirs (.py); fan-in (.ts)
    I  = repo files that import this module (relative-import stem match)
    O  = distinct project-internal modules this file imports (relative imports)

Honest scope note: `C:D` is route/surface-oriented. A pure library that
declares no `# DOC endpoint:` routes and no TS exports reads `C:D = 0:0` — that
is the correct canonical value, not a gap. Fan-in/out follow a0's relative-
import stem graph; modules wired purely by absolute import are not counted
(that mirrors a0's own annotator). The consumer dirs are the one a0-specific
bit made configurable here.

Public API:
    build_index(files, root, *, consumer_dirs=("client/src", "server")) -> dict
    seal_line(metrics, marker="#") -> str
    collect_files(root, *, skip=None, extensions=(".py",".ts",".tsx")) -> list[Path]

Pure stdlib; safe to copy verbatim into any consuming repo.
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Iterable

DEFAULT_SKIP = {
    ".git", "node_modules", "__pycache__", "dist", ".cache", ".local",
    ".venv", "venv", ".agents", "attached_assets", ".pythonlibs", "build",
    ".next", ".nuxt", "target", ".pytest_cache", ".mypy_cache", ".tox",
}
DEFAULT_CONSUMER_DIRS = ("client/src", "server")
_ANN_PY = re.compile(r"^#\s*\d+:\d+(\s+\d+:\d+){0,2}\s*$")
_ANN_TS = re.compile(r"^//\s*\d+:\d+(\s+\d+:\d+){0,2}\s*$")


def _is_seal(line: str, ext: str) -> bool:
    s = line.strip()
    return bool((_ANN_PY if ext == ".py" else _ANN_TS).match(s))


def _strip_seal(lines: list[str], ext: str) -> list[str]:
    w = lines[:]
    if w and _is_seal(w[0], ext):
        w = w[1:]
    if w and _is_seal(w[-1], ext):
        w = w[:-1]
    return w


def _count_python(lines: list[str]) -> tuple[int, int]:
    code = comment = 0
    in_triple = False
    triple = None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if in_triple:
            comment += 1
            if triple in s:
                in_triple = False
        elif s.startswith('"""') or s.startswith("'''"):
            comment += 1
            t = s[:3]
            if s.count(t) < 2:
                in_triple = True
                triple = t
        elif s.startswith("#"):
            comment += 1
        else:
            code += 1
    return code, comment


def _count_ts(lines: list[str]) -> tuple[int, int]:
    code = comment = 0
    in_block = False
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if in_block:
            comment += 1
            if "*/" in s:
                in_block = False
        elif s.startswith("/*"):
            comment += 1
            if "*/" not in s[2:]:
                in_block = True
        elif s.startswith("//"):
            comment += 1
        else:
            code += 1
    return code, comment


def _py_endpoints(lines: list[str]) -> list[str]:
    paths = []
    for line in lines:
        m = re.match(r"\s*#\s*DOC\s+endpoint:\s+\w+\s+(/[^\s|]+)", line)
        if m:
            paths.append(m.group(1).rstrip("/"))
    return paths


def _py_fanout(lines: list[str]) -> int:
    mods: set[str] = set()
    for line in lines:
        m = re.match(r"\s*from\s+(\.[\w.]*)\s+import", line)
        if m:
            mods.add(m.group(1))
    return len(mods)


def _ts_declared(lines: list[str]) -> int:
    count = 0
    for line in lines:
        s = line.strip()
        if re.match(
            r"^export\s+(default\s+)?(function|const|class|interface|type|enum)\b", s
        ):
            count += 1
        elif re.match(r"^export default [^{]", s):
            count += 1
    return count


def _ts_fanout(lines: list[str]) -> int:
    mods: set[str] = set()
    for line in lines:
        m = re.match(r"""\s*import\s+.*\s+from\s+['"]([.@][^'"]+)['"]""", line)
        if m:
            mods.add(m.group(1))
    return len(mods)


def _read_consumer_text(root: Path, consumer_dirs: Iterable[str]) -> str:
    parts: list[str] = []
    for subdir in consumer_dirs:
        d = root / subdir
        if not d.exists():
            continue
        for fp in d.rglob("*"):
            if fp.suffix in (".ts", ".tsx", ".js"):
                try:
                    parts.append(fp.read_text(encoding="utf-8"))
                except OSError:
                    pass
    return "\n".join(parts)


def build_index(
    files: list[Path],
    root: Path,
    *,
    consumer_dirs: Iterable[str] = DEFAULT_CONSUMER_DIRS,
) -> dict:
    """Compute N:M C:D I:O for every file. Fan-in via one inverted-index pass."""
    index: dict[str, dict] = {}
    texts: dict[str, str] = {}

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        texts[str(path)] = text
        ext = path.suffix
        working = _strip_seal(text.splitlines(), ext)
        if ext == ".py":
            code, comment = _count_python(working)
            endpoints = _py_endpoints(working)
            fan_out = _py_fanout(working)
            declared = len(endpoints)
        else:
            code, comment = _count_ts(working)
            endpoints = []
            fan_out = _ts_fanout(working)
            declared = _ts_declared(working)
        index[str(path)] = {
            "ext": ext, "code": code, "comment": comment,
            "declared": declared, "consumed": 0,
            "fan_out": fan_out, "fan_in": 0, "endpoints": endpoints,
        }

    # inverted import index: stem -> importer files (relative imports only)
    stem_importers: dict[str, set[str]] = {}
    for src_path in files:
        src_str = str(src_path)
        src_ext = src_path.suffix
        for line in texts.get(src_str, "").splitlines():
            s = line.strip()
            if src_ext == ".py":
                m = re.match(r"from\s+([.]+[\w.]*)\s+import", s)
                if m:
                    parts = [p for p in m.group(1).split(".") if p]
                    if parts:
                        stem_importers.setdefault(parts[-1], set()).add(src_str)
            elif src_ext in (".ts", ".tsx"):
                m = re.match(r"""\s*import\s+.*from\s+['"]([.][^'"]+)['"]""", s)
                if m:
                    seg = m.group(1).rstrip("/").split("/")[-1]
                    stem = re.sub(r"\.\w+$", "", seg)
                    if stem:
                        stem_importers.setdefault(stem, set()).add(src_str)

    for path in files:
        importers = stem_importers.get(path.stem, set()) - {str(path)}
        index[str(path)]["fan_in"] = len(importers)

    consumer_text = _read_consumer_text(root, consumer_dirs)
    for data in index.values():
        if data["ext"] == ".py" and data["endpoints"]:
            data["consumed"] = sum(1 for ep in data["endpoints"] if ep in consumer_text)
        elif data["ext"] in (".ts", ".tsx"):
            data["consumed"] = data["fan_in"]
    return index


def seal_line(metrics: dict, marker: str = "#") -> str:
    """Render the canonical `N:M C:D I:O` seal line for one file's metrics."""
    return (
        f"{marker} {metrics['code']}:{metrics['comment']} "
        f"{metrics['consumed']}:{metrics['declared']} "
        f"{metrics['fan_in']}:{metrics['fan_out']}"
    )


def collect_files(
    root: Path,
    *,
    skip: Iterable[str] | None = None,
    extensions: Iterable[str] = (".py", ".ts", ".tsx"),
) -> list[Path]:
    skip_set = set(skip) if skip is not None else set(DEFAULT_SKIP)
    ext_set = set(extensions)
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_set]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix in ext_set:
                out.append(p)
    return sorted(out)


def _marker_for(ext: str) -> str:
    return "//" if ext in (".ts", ".tsx", ".js", ".jsx") else "#"


def main(argv: list[str] | None = None) -> int:
    import sys
    argv = list(argv if argv is not None else sys.argv[1:])
    write = "--write" in argv
    check = "--check" in argv
    argv = [a for a in argv if a not in ("--write", "--check")]
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path(".")
    root = root.resolve()

    files = collect_files(root)
    index = build_index(files, root)
    drift = 0
    for path in files:
        m = index[str(path)]
        ext = path.suffix
        want = seal_line(m, _marker_for(ext))
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        have = lines[0].strip() if lines else ""
        placed_ok = bool(lines) and _is_seal(lines[0], ext) and _is_seal(lines[-1], ext)
        if write:
            working = _strip_seal(lines, ext)
            new = "\n".join([want] + working + [want]) + "\n"
            if new != path.read_text(encoding="utf-8"):
                path.write_text(new, encoding="utf-8")
                print(f"  stamped {path.relative_to(root)}  [{want}]")
        else:
            if not placed_ok or have != want:
                drift += 1
                print(f"  DRIFT {path.relative_to(root)}: have '{have}' want '{want}'")
    if check:
        print(f"annotate_index: {len(files)} files, {drift} drift/misplaced")
        return 1 if drift else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# ratios: loc_comments=232:33 imports_exports=7:4 calls_definitions=83:14
