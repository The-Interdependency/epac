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

- exact Git comparisons for both artifact payloads and the complete archived
  source before running any archived verifier or tests; release-manifest hashes
  are checked when present, and the input binding is checked again at the end;
- all repository and subatomic tests against separate clean wheel and source installs;
- complete installed-distribution byte maps, import origins, exact UCNS source maps,
  and complete source snapshots before and after each replay;
- the preregistered molecular comparison, requiring all 14 current standings (including the original four) to remain `FALSIFIED`;
- deterministic work-graph digest verification.

CI resolves UCNS through the source URL and SHA-256 in `pyproject.toml` and `uv.lock`. Python 3.10, 3.11, and 3.12 are the declared verification matrix. Package tests establish the checked construction and replay behavior; reproducible immutable candidate qualification, exact candidate stack verification, licensing, stable release, and reconsumption remain separate gates.

## Usage guidance

The candidate distribution is `interdependency-epac` version `0.1.0`. Its public
modules remain `epac_atomic`, `epac_periodic`, `epac_public_gonol`,
`epac_dimensional_arity`, `epac_molecular`, and `epac_comparison`. Subatomic
candidate modules are imported through `epac_subatomic`. Names beginning with
`_` are implementation details. The only runtime project dependency is the
exact UCNS archive; METAPAT supplies recorded semantic provenance, and stack
supplies extraction provenance. Neither is a hidden runtime import.

The verification commands require Git and a clean committed checkout. Use new
output directories. The replay gate records the exact source and artifact binding
in `candidate-source.json`; a stale or incomplete sdist is rejected before its
code can run. Source distributions include every tracked repository file,
including CI definitions and the complete local operational skill snapshot.

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
`python tools/build_release.py /tmp/epac-candidate` from a clean commit using
uv-managed CPython 3.11.15 and `requirements-build.txt`. The builder enforces that Python implementation/version plus
zlib 1.3.1 at compile time and runtime and records both identities. Test
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

## Continued forge research

The handoff also preserves the EPAC research present in stack commit
`0e8384bbb60e4c2189016a212bdd0030d04aed7d`: nine declared molecular
formulas, subatomic coverage through krypton, boundary-capacity and refinement
audits, and carried spiral visualization. These remain research constructions
and scoped internal evidence; packaging does not promote their empirical status.

- [Cross-scale closure](docs/cross_scale_compositional_closure.md)
- [Boundary capacity](docs/boundary_capacity_principle.md)
- [Descriptor non-degeneracy](docs/boundary_descriptor_nondegeneracy.md)
- [Capacity quotient](docs/boundary_capacity_quotient.md)
- [Probe completeness](docs/boundary_probe_completeness.md)
- [Minimal refinement](docs/boundary_minimal_refinement.md)
- [Spiral visualization](viz/README.md)

After installing the package, run a scoped audit through its public module:

```bash
python -c "from epac_cross_scale_closure import cross_scale_compositional_closure; print(cross_scale_compositional_closure()['statuses'])"
python -m epac_viz --help
```
