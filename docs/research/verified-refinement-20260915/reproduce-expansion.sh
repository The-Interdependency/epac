#!/usr/bin/env bash
set -euo pipefail
audit_scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
audit_root=$(mktemp -d "${TMPDIR:-/tmp}/epac-expansion-replay.XXXXXX")
git clone --quiet --no-checkout https://github.com/The-Interdependency/epac.git "$audit_root/epac"
git -C "$audit_root/epac" checkout --quiet 949cb1cb304927942966c9fb396caf6227120e7f
git clone --quiet --no-checkout https://github.com/The-Interdependency/ucns.git "$audit_root/ucns"
git -C "$audit_root/ucns" checkout --quiet 6eea1828a34ed8ec99879f8090ea5d48352d8c2d
python3 - "$audit_root" <<'PY'
import hashlib, json, sys
from pathlib import Path
root=Path(sys.argv[1])
lock=json.loads((root/'epac/data/ucns-source-lock.json').read_text())
for rel,expected in lock['installed_source_sha256'].items():
    if hashlib.sha256((root/'ucns/src'/rel).read_bytes()).hexdigest()!=expected:
        raise SystemExit('UCNS source mismatch: '+rel)
print('Verified',len(lock['installed_source_sha256']),'locked UCNS sources')
PY
mkdir "$audit_root/aliases" "$audit_root/results"
ln -s "$audit_root/epac/subatomic" "$audit_root/aliases/epac_subatomic"
ln -s "$audit_root/epac/data" "$audit_root/aliases/epac_data"
ln -s "$audit_root/epac/viz" "$audit_root/aliases/epac_viz"
# The frozen prior result is a preregistration input; copy it byte-for-byte.
cp "$audit_scripts/verified_refinement.py" "$audit_scripts/verified-refinement.json" \
   "$audit_scripts/expanded_refinement.py" "$audit_scripts/expansion-plan.json" \
   "$audit_scripts/verify_expansion.py" "$audit_root/results/"
export PYTHONPATH="$audit_root/aliases:$audit_root/epac:$audit_root/ucns/src"
python3 "$audit_root/results/expanded_refinement.py" --run "$audit_root/results/expansion-plan.json" \
  --output "$audit_root/results/expansion-results.json"
python3 "$audit_root/results/verify_expansion.py" "$audit_root/epac/data/sealed_known_molecular_geometry.json"
python3 - "$audit_scripts/expansion-results.json" "$audit_root/results/expansion-results.json" <<'PY'
import json,sys
from pathlib import Path
reference,replay=(json.loads(Path(p).read_text()) for p in sys.argv[1:])
if reference!=replay:
    raise SystemExit('Expanded replay differs from archived evidence')
print('Regenerated expansion matches archived evidence, including composition receipts')
PY
printf 'Replay artifacts: %s\n' "$audit_root/results"
