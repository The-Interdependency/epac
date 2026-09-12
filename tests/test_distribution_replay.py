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


def test_replay_exports_the_archived_dependency_lock(tmp_path):
    source = Path(__file__).resolve().parents[1]
    caller, dist, binary = (tmp_path / name for name in ("caller", "dist", "bin"))
    for directory in (caller, dist, binary):
        directory.mkdir()
    (caller / "uv.lock").write_text("unrelated caller lock")
    (caller / "pyproject.toml").write_text("unrelated caller project")
    contents = {
        "uv.lock": b"exact archived lock",
        "pyproject.toml": b"exact archived project",
        "tools/verify_installed.py": (source / "tools/verify_installed.py").read_bytes(),
    }
    with tarfile.open(dist / "fixture.tar.gz", "w:gz") as archive:
        for name, payload in contents.items():
            item = tarfile.TarInfo("fixture/" + name)
            item.size = len(payload)
            archive.addfile(item, io.BytesIO(payload))
    (dist / "fixture.whl").write_bytes(b"not consumed before export")
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
    result = subprocess.run(["bash", str(source / "tools/replay_distributions.sh"), str(caller), str(dist), str(output), sys.executable],
                            env=environment, capture_output=True, text=True)
    assert result.returncode == 73, result.stderr
    record = json.loads(trace.read_text())
    assert Path(record["project"]) == output / "source/fixture"
    assert record["lock"] == "exact archived lock"
    assert record["pyproject"] == "exact archived project"


def check_epac_replay_uses_candidate_lock():
    with TemporaryDirectory() as directory:
        test_replay_exports_the_archived_dependency_lock(Path(directory))
