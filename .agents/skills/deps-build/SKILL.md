---
name: deps-build
description: Self-declaring dependency topology built on msdmd. Each module declares dependency edges it owns in a `# === DEPENDENCIES ===` block; a runner builds an import/call/capability graph, detects unresolved edges and cycles, and surfaces visible dependency coverage gaps. Load this when declaring module dependencies, auditing architecture drift, checking graph cycles, or wiring dependency topology checks into CI.
---

# deps-build — Dependency topology on msdmd

`deps-build` is an application of [msdmd](../msdmd/SKILL.md). It makes a
module's dependency edges visible beside the code that creates them, so
architecture drift becomes inspectable instead of hidden in imports.

Implementation status: this skill defines the `DEPENDENCIES` block and runner
contract. This repo does not currently ship a DEPENDENCIES graph runner;
consuming repos should implement the contract below with local resolvers.

Read `msdmd/SKILL.md` first if you have not. The block syntax, parser
contract, and visible gap rule are inherited.

## The block

```python
# === DEPENDENCIES ===
# id: chat_route_dependency_edges
#   summary: chat API route depends on auth context and chat repository
#   imports: auth.user_context, repositories.chat
#   calls: ChatRepository.get_by_owner
#   requires: auth_user_context, chat_repository
#   class: runtime
# === END DEPENDENCIES ===
```

## Field schema

Required:

| Field | Meaning |
|---|---|
| `id` | Stable dependency declaration id. |
| `summary` | One-sentence description of why these edges exist. |

At least one edge field is required unless the entry records `hmmm`:

| Edge field | Meaning |
|---|---|
| `imports` | Comma-separated modules/packages imported by this module. |
| `calls` | Comma-separated functions, methods, routes, commands, or capabilities called by this module. |
| `requires` | Comma-separated msdmd ids this module depends on. |
| `provides` | Comma-separated ids or surfaces this module provides to others. |
| `external` | Comma-separated external services, APIs, or packages this module depends on. |

Optional:

| Field | Meaning |
|---|---|
| `class` | Dependency class (`runtime`, `build`, `test`, `docs`, `ops`, `agent`). |
| `direction` | `inbound`, `outbound`, `bidirectional`, or `hmmm`. |
| `owner` | Person, role, or team responsible for this dependency shape. |
| `since` | Version or date the declaration was added. |
| `deprecated` | If present, marks an edge scheduled for removal. |

## Runner contract

A DEPENDENCIES runner MUST:

1. Parse every `DEPENDENCIES` block with the universal msdmd parser.
2. Build a graph from `imports`, `calls`, `requires`, `provides`, and
   `external` fields where resolvers exist.
3. Report unresolved non-`hmmm` edges as drift.
4. Report cycles in classes where cycles are disallowed by local policy.
5. Report modules with imports/calls but no DEPENDENCIES block as visible
   coverage gaps when the runner can detect them.
6. Exit non-zero for malformed required fields, unresolved resolvable edges,
   or forbidden cycles. Coverage gaps fail only in strict mode.

## Reporting shape

- `EDGE`: declared edge and source module.
- `UNRESOLVED`: declared edge no longer resolves.
- `CYCLE`: graph cycle detected.
- `PENDING`: edge or direction recorded as `hmmm`.
- `GAP`: dependency-bearing module without DEPENDENCIES metadata.

## Anti-patterns

- Treating an import list as architecture without explaining why edges exist.
- Declaring dependencies only in a central graph file.
- Hiding unresolved dependencies by omitting them; use `hmmm`.
- Failing all cycles blindly; some test or plugin graphs may intentionally cycle.

hmmm
- exact resolver syntax for cross-language call and route edges
- which dependency classes disallow cycles by default
- whether package-manager dependencies should be declared here or only source-level edges
