#!/usr/bin/env bash
set -euo pipefail
audit_scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
audit_root=$(mktemp -d "${TMPDIR:-/tmp}/epac-refinement-replay.XXXXXX")
git clone --quiet --no-checkout https://github.com/The-Interdependency/epac.git "$audit_root/epac"
git -C "$audit_root/epac" checkout --quiet 949cb1cb304927942966c9fb396caf6227120e7f
git clone --quiet --no-checkout https://github.com/The-Interdependency/ucns.git "$audit_root/ucns"
git -C "$audit_root/ucns" checkout --quiet 6eea1828a34ed8ec99879f8090ea5d48352d8c2d
python3 - "$audit_root" <<'PY'
import hashlib, json, sys
from pathlib import Path
root = Path(sys.argv[1])
lock = json.loads((root/'epac/data/ucns-source-lock.json').read_text())
for rel, expected in lock['installed_source_sha256'].items():
    actual = hashlib.sha256((root/'ucns/src'/rel).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit('UCNS source mismatch: '+rel)
print('Verified', len(lock['installed_source_sha256']), 'locked UCNS sources')
PY
mkdir "$audit_root/aliases" "$audit_root/results"
ln -s "$audit_root/epac/subatomic" "$audit_root/aliases/epac_subatomic"
ln -s "$audit_root/epac/data" "$audit_root/aliases/epac_data"
ln -s "$audit_root/epac/viz" "$audit_root/aliases/epac_viz"
cp "$audit_scripts/verified_refinement.py" "$audit_scripts/verify_cached_refinement.py" \
   "$audit_scripts/ternary_refinement_search.py" "$audit_root/results/"
export PYTHONPATH="$audit_root/aliases:$audit_root/epac:$audit_root/ucns/src"
python3 "$audit_root/results/verified_refinement.py" --output "$audit_root/results/verified-refinement.json"
python3 "$audit_root/results/verify_cached_refinement.py"
python3 "$audit_root/results/ternary_refinement_search.py"
python3 - "$audit_scripts" "$audit_root/results" <<'PY'
import json, sys
from pathlib import Path
old, new = map(Path, sys.argv[1:])
for filename in ('verified-refinement.json', 'ternary-refinement-search.json'):
    reference = json.loads((old/filename).read_text())
    replay = json.loads((new/filename).read_text())
    # Execution location is provenance; it is the only expected difference.
    if filename == 'verified-refinement.json':
        reference.pop('epac_source')
        replay.pop('epac_source')
    if replay != reference:
        raise SystemExit('Replay differs from archived evidence: '+filename)
print('Both regenerated results match archived evidence')
PY
printf 'Replay artifacts: %s\n' "$audit_root/results"
