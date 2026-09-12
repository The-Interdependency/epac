#!/usr/bin/env bash
# === MODULE_BUILD ===
# id: epac_distribution_replay
#   module_name: replay_distributions
#   module_kind: instrument
#   summary: clean-installs both EPAC artifacts and verifies their installed payload and evidence
#   owner: The Interdependency
#   public_surface: bash tools/replay_distributions.sh ROOT DIST NEW_OUTPUT PYTHON
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: write
#   storage_notes: new output directory, temporary installations, dependency cache, and receipts
#   network_boundary: external
#   network_notes: exact locked dependencies
#   user_data_boundary: none
#   admin_only: false
#   tests: full installed wheel and source suite plus archive hash preservation
#   rollout: explicit candidate qualification and CI
#   rollback: retain previously accepted immutable artifact
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: epac_distribution_replay_preserves_artifact_identity
#   given: one source archive and wheel plus the exact dependency lock
#   then: both artifacts and the complete archived source match clean candidate Git before archived code runs; dependencies come from that lock, and both clean installations match the wheel payload and pass the full suite with verified import origins and unchanged artifact hashes
#   class: evidence
# === END CONTRACTS ===
# Usage: bash tools/replay_distributions.sh ROOT DIST NEW_OUTPUT PYTHON
# Installs both artifacts independently; writes local packaging evidence only.
# License qualification and pre-publication stack acceptance remain separate.
set -euo pipefail
case "${PYTHONOPTIMIZE-}" in ""|0) ;; *) echo "optimized Python mode cannot produce replay evidence" >&2; exit 2;; esac
repo=$(realpath "$1")
dist=$(realpath "$2")
output=$(realpath -m "$3")
runtime=${4:-python3}
case "$output/" in "$repo/"*) echo 'OUTPUT must be outside source' >&2; exit 2;; esac
test ! -e "$output"
mkdir -p "$output"
(cd "$dist"; sha256sum ./*.whl ./*.tar.gz) > "$output/archives.sha256"
uv venv --python "$runtime" "$output/verification-venv"
"$output/verification-venv/bin/python" "$repo/tools/verify_replay_inputs.py" "$repo" "$dist" "$output"
source_root=$(find "$output/source" -mindepth 1 -maxdepth 1 -type d)
"$output/verification-venv/bin/python" "$source_root/tools/verify_installed.py" snapshot "$source_root" "$output/source-snapshot.json"
uv export --project "$source_root" --locked --extra test --extra build --no-emit-project --no-dev --format requirements.txt --output-file "$output/dependencies.txt" >/dev/null
for kind in wheel sdist; do
  "$output/verification-venv/bin/python" "$source_root/tools/verify_installed.py" verify-snapshot "$source_root" "$output/source-snapshot.json"
  environment="$output/$kind-venv"
  uv venv --python "$runtime" "$environment"
  uv pip sync --python "$environment/bin/python" --require-hashes "$output/dependencies.txt"
  if [ "$kind" = wheel ]; then artifact=("$dist"/*.whl); else artifact=("$dist"/*.tar.gz); fi
  uv pip install --python "$environment/bin/python" --no-deps --no-build-isolation "${artifact[0]}"
  (
    cd "$output"
    env -u PYTHONPATH -u PYTHONHOME -u PYTEST_ADDOPTS -u PYTEST_PLUGINS PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
      "$environment/bin/python" "$source_root/tools/verify_installed.py" "$source_root" "$dist"/*.whl "$output/$kind-receipt.json" "${artifact[0]}"
  )
  "$output/verification-venv/bin/python" "$source_root/tools/verify_installed.py" verify-snapshot "$source_root" "$output/source-snapshot.json"
done
(cd "$dist"; sha256sum -c "$output/archives.sha256")
"$output/verification-venv/bin/python" "$repo/tools/verify_replay_inputs.py" "$repo" "$dist" "$output" --final
