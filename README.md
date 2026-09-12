# EPAC

EPAC is the independent repository for The Interdependency's elementary/particle-scale energy-and-arity coupling research program that originated in `The-Interdependency/stack`.

`EPAC` is the stable project handle. No fixed lexical expansion is required for the handle; historical expansions are provenance, not identity.

## Standing

- Physical repository state: extracted from the stack incubator; exact candidate/forge verification remains unresolved until a dedicated immutable verification receipt exists.
- Authority transition: incomplete until the release/reconsumption graduation gates are satisfied.
- Research status: provisional / cross-domain hypothesis unless a narrower artifact says otherwise.
- Empirical status: no transfer. Repository independence does not make a physics or chemistry claim true.
- Molecular-shape prediction: **FALSIFIED** for the preregistered comparison carried from the incubator; that negative result is preserved as evidence.
- UCNS Public Gonol position operations beyond carrier identity: `hmmm`.
- Standing-wave / field descriptions: live modeling direction, not established external physics merely by appearing here.

## Origin

Extraction source:

- forge: `The-Interdependency/stack`
- source commit: `ef51f2e8f32ccfd5394525dad72475a61a505bc1`
- source path: `research/epac/`

The extraction preserves the stack research artifacts and their epistemic status. Stack-local statements such as “no independent EPAC repository exists” are migration scaffolding and do not become EPAC doctrine.

## Structure

- `epac_*.py` — executable constructors and comparison surfaces migrated from the incubator.
- `subatomic/` — subatomic construction candidates, receipts, and executable witnesses.
- `tests/` — repository-level regression and falsification tests.
- `data/` — bounded input/comparison data used by the current experiments.
- `docs/` — scope, arity, preregistration, provenance, work graph, and graduation records.
- `.agents/skills/` — repo-local copy of canonical organization skills, sourced from `The-Interdependency/skill-lib`.

## Verification

The package gate executes:

- all repository and subatomic tests against separate clean wheel and source installs;
- installed-byte, import-origin, and exact UCNS source-map checks;
- the preregistered molecular comparison, requiring all four current standings to remain `FALSIFIED`;
- deterministic work-graph digest verification.

CI resolves UCNS through the source URL and SHA-256 in `pyproject.toml` and `uv.lock`. Python 3.10, 3.11, and 3.12 are the declared verification matrix. Package tests establish reproducibility; exact candidate stack verification, licensing, stable release, and reconsumption remain separate gates.

## Usage guidance

The candidate distribution is `interdependency-epac` version `0.1.0`. Its public
modules remain `epac_atomic`, `epac_periodic`, `epac_public_gonol`,
`epac_dimensional_arity`, `epac_molecular`, and `epac_comparison`. Subatomic
candidate modules are imported through `epac_subatomic`. Names beginning with
`_` are implementation details. The only runtime project dependency is the
exact UCNS archive; METAPAT supplies recorded semantic provenance, and stack
supplies extraction provenance. Neither is a hidden runtime import.

```bash
python -m pip install uv==0.11.18
uv sync --locked --extra test --extra build
.venv/bin/python -m pytest
.venv/bin/python -m build --outdir /tmp/epac-dist
.venv/bin/python -m twine check /tmp/epac-dist/*
bash tools/replay_distributions.sh . /tmp/epac-dist /tmp/epac-replay python3.12
```

After installation, construction and replay require no checkout paths:

```python
from epac_public_gonol import construct_public_gonol, replay_public_gonol

receipt = construct_public_gonol(source_id="example:oxygen",
    relation="epac.atomic.element", identity_glyph="O")
assert replay_public_gonol(receipt).receipt_digest == receipt.receipt_digest
```

GitHub release assets are the selected distribution surface. Once the owner
records the license, install `requirements-build.txt` and run
`python tools/build_release.py /tmp/epac-candidate` from a clean commit. Test
those exact hashes in both the clean installation and stack before publishing.
Download the published assets and verify `SHA256SUMS` before reconsumption.
`LICENSE_STATUS.md` retains the current license gate; package builds alone do
not grant redistribution rights or complete graduation.

Do not treat successful execution as empirical validation. Constructors establish reproducible declared structures; comparison tests determine the standing of the claims they actually test.

## hmmm

- exact candidate/forge verification receipt
- distribution surface and first immutable release artifact
- license/distribution-rights selection for this independent repository
- clean package/install dependency contract for UCNS
- downstream forge reconsumption and authority-transition receipt
- whether standing-wave language earns a stronger domain claim after explicit external-physics comparison
