---
name: canon
description: Canonical-source and doctrine maintenance for The Interdependency skill library. Use this when deciding whether a claim, pattern, ratio, workflow, or repo-local practice should become canon; when moving source-backed behavior into a SKILL.md; when reconciling canonical skill-lib with repo-local `.agents/skills/` copies; or when preserving unresolved doctrine as `hmmm` instead of guessing.
---

# canon — Maintaining source-backed doctrine

`canon` is a procedural skill for turning observed practice into honest,
source-backed doctrine. It protects the boundary between what the org has
actually made canonical and what an agent merely inferred.

## Load this when

- A user asks whether something should be canon.
- You are promoting a repo-local pattern into `skill-lib`.
- You are reconciling copied `.agents/skills/` directories with this repo.
- You are editing descriptions that decide when skills load.
- A claim is useful but not yet source-backed and needs a `hmmm` boundary.

## Canon test

Before writing a canonical claim, identify its backing class:

| Class | Meaning | How to write it |
|---|---|---|
| `declared` | Already stated in this repo's README, AGENTS, ORG_DISTRIBUTION, skills.json, or a SKILL.md. | Cite or preserve directly. |
| `implemented` | Proven by code, parser behavior, runner behavior, or checked artifacts. | State only what the artifact does. |
| `repo-local` | Present in a target repo copy or local convention but not yet canonical here. | Name the repo-local source and avoid generalizing. |
| `inferred` | Reasonable conclusion but not declared or implemented. | Do not canonize; write `hmmm` or propose a decision. |
| `desired` | A design goal or request. | Mark as proposed until accepted into a skill. |

|∆|Only `declared` and `implemented` claims are canon without qualification.|∆|
Repo-local and desired claims can motivate a skill change, but the skill must
say where the claim came from or leave the unresolved part as `hmmm`.

## Canonization workflow

1. **Find the source.** Prefer files in this repo. For repo-local copies,
   record the repo/path/commit when available.
2. **Separate shape from meaning.** If examples show a pattern but do not
   define semantics, canonize only the pattern and write semantic meaning as
   `hmmm`.
3. **Choose the right home.** Foundational parser/block rules belong in
   `msdmd`; application-specific blocks belong in their own skill; org
   distribution rules belong in `ORG_DISTRIBUTION.md`; onboarding narrative
   belongs in `visitor-intro`.
4. **Update indexes.** When adding a skill, update `skills.json`, README,
   AGENTS, ORG_DISTRIBUTION, and CLAUDE when those files list installed skills.
5. **Preserve uncertainty.** Unknown fields and unresolved doctrine are
   written `hmmm`, with enough context for the next agent to continue.
6. **Avoid retroactive authority.** Do not describe old repo-local practice as
   canonical unless this repo adopts it in the same change.

## Output rubric

When answering canon questions, include:

- **Canonical now:** source-backed facts.
- **Proposed canon:** useful changes that need acceptance or implementation.
- **hmmm:** unresolved constraints or missing sources.
- **Next patch:** the smallest change that makes the desired canon true.

## Anti-patterns

- Inferring semantics from examples and writing them as doctrine.
- Citing target-repo copies as source of truth after this repo has a contrary rule.
- Updating a skill without updating the machine-readable index.
- Treating `hmmm` as failure. It is the honest boundary object.

hmmm
- whether canon claims should eventually live in a `CANON` metadata block
- whether target repo propagation should be verified by a dedicated runner
- whether accepted design chat should be archived as a source-backed artifact
