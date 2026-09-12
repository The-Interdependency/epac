# EPAC

EPAC is the independent repository for The Interdependency's elementary/particle-scale energy-and-arity coupling research program that originated in `The-Interdependency/stack`.

`EPAC` is the stable project handle. No fixed lexical expansion is required for the handle; historical expansions are provenance, not identity.

## Standing

- Repository state: independently graduated; MPL-2.0 `v0.1.0` published and reconsumed by Stack.
- Authority: EPAC owns its implementation and public contracts. The [scoped transition receipt](docs/graduation.json) binds qualification, public reconsumption and retirement of the forge implementation.
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

## Published release and graduation

[EPAC v0.1.0](https://github.com/The-Interdependency/epac/releases/tag/v0.1.0) contains the exact candidate
that passed six clean 209-test installations and pre-publication Stack verification.
Public reconsumption passed, the 37 forge Python files were retired, and the
[authority-transition receipt](https://github.com/The-Interdependency/stack/blob/c81d807142d3f0fe3968a6879888afa00352eaff/integration/epac/authority-transition.json) records the scoped ownership event.
The immutable release source is `949cb1cb304927942966c9fb396caf6227120e7f`. Its archived
graduation record describes qualification time; the [current record](docs/graduation.json)
records the later completed event without changing the published bytes.

## Usage guidance

The released distribution is `interdependency-epac` version `0.1.0`. Its public
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

GitHub release assets are the selected distribution surface. EPAC is licensed
under MPL-2.0. Install `requirements-build.txt` and run
`python tools/build_release.py /tmp/epac-candidate` from a clean commit using
uv-managed CPython 3.11.15 and `requirements-build.txt`. The builder enforces that Python implementation/version plus
zlib 1.3.1 at compile time and runtime and records both identities. Test
those exact hashes in both the clean installation and stack before publishing.
Download the published assets and verify `SHA256SUMS` before reconsumption.
The release includes the MPL-2.0 license and the complete source distribution.
Source is also available from https://github.com/The-Interdependency/epac at the
commit bound by the release manifest. Package tests do not complete graduation.

Do not treat successful execution as empirical validation. Constructors establish reproducible declared structures; comparison tests determine the standing of the claims they actually test.

## hmmm

- unmeasured operation effects and canonical compositional descriptors
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

Release qualification requires an owner-selected `LICENSE`, its explicit SPDX expression and `license-files = ["LICENSE"]` in `pyproject.toml`, and removal of the unresolved `LICENSE_STATUS.md` (its history remains in Git). Adding license text alongside a status that still prohibits publication does not pass the gate. The replay shell bootstraps the hash-pinned Python 3.10 TOML parser from `requirements-replay.txt`, then validates all source-derived core metadata and every optional release-manifest field before archived code runs. To call `tools/verify_replay_inputs.py` directly on Python 3.10, first install that requirements file with `uv pip install --python /path/to/python --no-deps --require-hashes -r requirements-replay.txt`.

## License

EPAC source code is subject to the Mozilla Public License, version 2.0
(SPDX: `MPL-2.0`); see [LICENSE](LICENSE). Changes to MPL-covered files remain
subject to that license when distributed. Dependencies retain their own rights
and licensing status; this selection grants no rights to UCNS or other upstream
projects. [License provenance](docs/license-selection.json) records the owner
instruction and its resolution using the organization’s weak-copyleft convention.
