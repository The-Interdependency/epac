# Local agent skills

This directory contains repo-local copies of canonical skills from
`The-Interdependency/skill-lib`.

Source commit: `321e721fb660e0fea5bb8c37d943611963039a57`

Repo-local copies are not the source of truth. Edit `skill-lib` first,
then propagate from the canonical source.

Skills refreshed from the source commit above:

- `wdll/`
- `a0p-instancing/`
- `agent-instantiation/`

Other installed skills (not refreshed by this propagation):

Their existing files retain their own authority/provenance; the source
commit above does not assert that these copies were refreshed.

- `action-calibration/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `canon/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `cap-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `char-compress/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `data-visualization/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `deps-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `distributed-publication/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `doc-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `domain-claims/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `epac-selection-display/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `explore-data/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `fresh-making/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `gonol-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `interdependent-work-graph/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `llms-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `loop-eng/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `manifest/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `meta/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `meta-module-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `msdmd/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `owner-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `plain-lens/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `project-incubation-graduation/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `ratios/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `repo-audit-repair/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `risk-boundary-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `skill-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `skill-usage/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `sql-queries/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `ssh-automation/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `statistical-analysis/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `test-build/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `the-interdependency/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `thought-lens/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `typed-meta-frontend/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `ucns-option-selection/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `validate-data/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `visitor-intro/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]
- `vm-mcp/` [not refreshed; prior source: `38c64332b840b2bbe1c07e53aeee8996644548e9`]

## Lifecycle propagation usage

Read `agent-instantiation/SKILL.md` for a0/a0ucns and the a0p legacy copy;
read `a0p-instancing/SKILL.md` for a0-betatest backend. Load `wdll/SKILL.md`
when consequential spawned work needs its scope or completion proof resolved.
These are source-owned instructions, not evidence that EPAC deploys either runtime.

To reproduce this bounded refresh from skill-lib commit
`321e721fb660e0fea5bb8c37d943611963039a57`, run:

```sh
python tools/propagate_skills.py /path/to/epac --skills agent-instantiation
python tools/propagate_skills.py /path/to/epac --skills agent-instantiation --apply
```

The canonical dependency closure is `wdll`, `a0p-instancing`, and
`agent-instantiation`; no other skill refresh is implied. Full-library drift and
older MSDMD runtime/projection work remain separate. Preserve release locks,
scientific pins, sealed results, and accepted release-consumption evidence.

The scoped work graph is `docs/work-graphs/lifecycle-skills-321e721.json`.
The snapshot statements in `docs/PROVENANCE.md` and `docs/work-graph.json`
remain at their qualification-time identities because sealed join-term evidence
binds those exact bytes. This README and the scoped graph describe the current
lifecycle installation without rewriting that historical evidence.
