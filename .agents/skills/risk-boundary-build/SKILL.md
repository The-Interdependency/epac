---
name: risk-boundary-build
description: Self-declaring runtime risk and permission boundaries built on msdmd. Each module records auth, storage, network, user-data, admin, and operational effects in a `# === BOUNDARIES ===` block; a runner audits sensitive files, reports unresolved `hmmm` boundaries, and surfaces visible coverage gaps. Load this when touching code with permissions, persistence, network calls, user data, admin behavior, migrations, or other risk-bearing effects.
---

# risk-boundary-build — Runtime boundaries on msdmd

`risk-boundary-build` is an application of [msdmd](../msdmd/SKILL.md). It
turns hidden permission, storage, network, and user-data effects into
module-local declarations that can be reviewed before an agent edits a
sensitive file.

This complements `meta-module-build`: MODULE_BUILD describes intended
boundaries before new work starts; BOUNDARIES records the actual runtime
boundary of an existing module.

Implementation status: this skill defines the `BOUNDARIES` block and runner
contract. This repo does not currently ship a BOUNDARIES runner script;
consuming repos should implement the contract below with local risk heuristics.

## The block

```python
# === BOUNDARIES ===
# id: chat_route_user_data_boundary
#   summary: reads user-owned chat rows for the authenticated requester
#   auth_boundary: read
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   pii: possible
#   owner: platform-runtime
# === END BOUNDARIES ===
```

## Field schema

Required:

| Field | Meaning |
|---|---|
| `id` | Stable boundary declaration id. |
| `summary` | One-sentence description of the sensitive behavior. |
| `auth_boundary` | `none`, `read`, `write`, `admin`, or `hmmm`. |
| `storage_boundary` | `none`, `read`, `write`, `delete`, `migration`, or `hmmm`. |
| `network_boundary` | `none`, `internal`, `external`, or `hmmm`. |
| `user_data_boundary` | `none`, `read`, `write`, `delete`, or `hmmm`. |
| `admin_only` | `true`, `false`, or `hmmm`. |

Optional:

| Field | Meaning |
|---|---|
| `pii` | `none`, `possible`, `direct`, `sensitive`, or `hmmm`. |
| `secrets` | `none`, `read`, `write`, or `hmmm`. |
| `side_effects` | Comma-separated side effects (`email`, `webhook`, `billing`, `job`, `cache`, etc.). |
| `review_required` | Person, role, team, or condition required before edits. |
| `owner` | Person, role, or team responsible for the boundary declaration. |
| `requires` | Comma-separated BOUNDARIES or MODULE_BUILD ids this declaration depends on. |
| `since` | Version or date the declaration was added. |

## Runner contract

A BOUNDARIES runner MUST:

1. Parse every `BOUNDARIES` block with the universal msdmd parser.
2. Report required fields containing `hmmm` as unresolved boundary objects.
3. Report modules with likely sensitive imports or filenames but no
   BOUNDARIES block as visible gaps.
4. Support strict mode where gaps or any required `hmmm` boundary fail.
5. Exit non-zero for malformed required fields, invalid enum values, or
   strict-mode unresolved boundaries.

Sensitive-file heuristics MAY include auth/session imports, database clients,
network clients, migration filenames, admin routes, payment/billing modules,
secret managers, and user-data models. Heuristics are advisory: they create
review visibility, not proof of risk.

## Agent behavior

When this skill is loaded before editing code:

- Read the BOUNDARIES block before changing implementation.
- If a required boundary is `hmmm`, preserve that uncertainty and call it out.
- Do not relax a boundary value (`admin` → `read`, `external` → `internal`, etc.)
  unless the code change actually removes the effect.
- If the edit adds a new sensitive effect, update the block in the same diff.

## Anti-patterns

- Treating `none` as a default. Unknown is `hmmm`, not `none`.
- Recording intended boundaries in BOUNDARIES before code exists; use MODULE_BUILD first.
- Hiding risk in prose comments instead of structured fields.
- Letting heuristic gap detection replace explicit owner review.

hmmm
- exact sensitive-import heuristic lists per framework
- whether strict mode should fail all `hmmm` boundaries or only user-data/admin ones
- how to represent read-only analytics on anonymized aggregate data
