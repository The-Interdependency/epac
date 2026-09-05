---
name: owner-build
description: Self-declaring module stewardship built on msdmd. Each module declares who owns, reviews, and escalates changes in a `# === OWNERS ===` block; a runner reports unowned modules, unresolved `hmmm` owners, and missing review coverage for sensitive modules. Load this when assigning module ownership, routing reviews, auditing unowned code, or wiring stewardship coverage into CI.
---

# owner-build — Module stewardship on msdmd

`owner-build` is an application of [msdmd](../msdmd/SKILL.md). It records
who is responsible for a module in the same file as the implementation, so
agents do not invent authority or edit sensitive code without a review path.

Implementation status: this skill defines the `OWNERS` block and runner
contract. This repo does not currently ship an OWNERS runner script; consuming
repos should implement the contract below against their review policy.

Read `msdmd/SKILL.md` first if you have not. The block syntax, parser
contract, and visible gap rule are inherited.

## The block

```python
# === OWNERS ===
# id: chat_route_owner
#   owner: platform-runtime
#   steward: erin
#   review_required_for: auth, storage, user_data
#   escalation: platform-runtime
#   since: 2026-06-04
# === END OWNERS ===
```

## Field schema

Required:

| Field | Meaning |
|---|---|
| `id` | Stable ownership declaration id. |
| `owner` | Person, role, team, or `hmmm` if unresolved. |

Optional:

| Field | Meaning |
|---|---|
| `steward` | Person or role currently tending the module; use `hmmm` if unresolved. |
| `review_required_for` | Comma-separated change classes requiring review (`auth`, `storage`, `network`, `user_data`, `admin`, `public_api`, `docs`, etc.). |
| `escalation` | Person, role, team, channel, or `hmmm` for unresolved escalation. |
| `backup_owner` | Secondary owner or team. |
| `requires` | Comma-separated ids whose ownership affects this module. |
| `since` | Version or date the owner declaration was added. |
| `deprecated` | If present, marks ownership as scheduled for replacement. |

## Runner contract

An OWNERS runner MUST:

1. Parse every `OWNERS` block with the universal msdmd parser.
2. Report `owner: hmmm`, `steward: hmmm`, or `escalation: hmmm` as pending.
3. Report modules without OWNERS blocks as visible stewardship gaps.
4. Cross-check sensitive modules against `review_required_for` when
   BOUNDARIES metadata is available.
5. Exit non-zero for malformed required fields or missing owners in strict
   mode. Coverage gaps fail only in strict mode.

## Agent behavior

When this skill is loaded before edits:

- Read OWNERS before making changes.
- If the intended edit touches a class named in `review_required_for`, call
  out the review requirement in the handoff or PR summary.
- Do not replace `hmmm` with a guessed person, role, or team.
- If ownership is absent, preserve the gap in output rather than pretending
  the committer or agent owns the file.

## Reporting shape

- `OWNED`: owner is declared.
- `PENDING`: owner, steward, or escalation is `hmmm`.
- `REVIEW_REQUIRED`: edit class requires explicit review.
- `GAP`: module has no OWNERS block.

## Anti-patterns

- Treating Git author, last committer, or PR opener as owner.
- Recording owner only in a central CODEOWNERS-like file while omitting the module-local declaration.
- Using ownership metadata to bypass review; it routes review, not permission.
- Guessing a team from a filename. Unknown is `hmmm`.

hmmm
- whether repo-level CODEOWNERS should generate suggested OWNERS blocks
- whether strict mode should require owners for all modules or only public/sensitive ones
- how to represent temporary stewardship during incidents
