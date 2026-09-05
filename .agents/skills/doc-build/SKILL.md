---
name: doc-build
description: Self-declaring documentation coverage built on msdmd. Each module declares the public, developer, operator, or agent-facing documentation it owns in a `# === DOCS ===` block; a runner verifies linked docs and anchors exist, reports stale or missing documentation, and surfaces visible coverage gaps. Load this when adding or auditing module documentation, when tying code surfaces to docs, or when wiring documentation coverage checks into CI.
---

# doc-build — Documentation contracts on msdmd

`doc-build` is an application of [msdmd](../msdmd/SKILL.md). It turns a
module's documentation obligations into colocated metadata so docs drift is
observable instead of discovered by surprise.

Implementation status: this skill defines the `DOCS` block and runner contract.
This repo does not currently ship a DOCS runner script; consuming repos should
implement the contract below against their own documentation tree.

Read `msdmd/SKILL.md` first if you have not. The block syntax, parser
contract, and visible gap rule are inherited.

## The block

Every module with user, developer, operator, or agent-facing behavior may
declare one or more documentation contracts:

```python
# === DOCS ===
# id: chat_api_public_docs
#   summary: public documentation for creating and reading chat conversations
#   audience: developer
#   source: docs/chat.md#conversations
#   covers: create_conversation, get_conversation
#   status: current
# === END DOCS ===
```

## Field schema

Required:

| Field | Meaning |
|---|---|
| `id` | Stable documentation contract id. |
| `summary` | One-sentence description of what the docs promise to explain. |
| `audience` | One of `user`, `developer`, `operator`, `agent`, `internal`, or `hmmm`. |
| `source` | Path to the documentation file, optionally with an anchor (`docs/file.md#heading`). Use `hmmm` if the target is not resolved yet. |
| `status` | `current`, `draft`, `deprecated`, or `hmmm`. |

Optional:

| Field | Meaning |
|---|---|
| `covers` | Comma-separated module surfaces, routes, functions, components, or concepts covered by the doc. |
| `examples` | Comma-separated example ids, files, or anchors the doc depends on. |
| `requires` | Comma-separated ids this documentation contract depends on. |
| `owner` | Person, role, or team responsible for doc freshness. |
| `since` | Version or date the contract was added. |

## Runner contract

A DOCS runner MUST:

1. Parse every `DOCS` block with the universal msdmd parser.
2. Verify each non-`hmmm` `source` path exists.
3. If `source` includes an anchor, verify the target heading or anchor
   exists when the file format supports anchors.
4. Report `status: draft` and `source: hmmm` as pending, not passing.
5. Report modules with no `DOCS` block as documentation coverage gaps.
6. Exit non-zero for missing files, missing anchors, malformed required
   fields, or deprecated docs referenced as current. Coverage gaps fail only
   in strict mode.

## Reporting shape

Normal output should group results as:

- `PASS`: docs target exists and required fields are valid.
- `PENDING`: `hmmm` or `draft` documentation contracts.
- `DRIFT`: source path, anchor, or covered surface no longer resolves.
- `GAP`: source modules with no DOCS block.

## Anti-patterns

- Putting documentation ownership only in a separate docs index.
- Marking docs `current` when the source is `hmmm`.
- Treating missing DOCS blocks as invisible because the code has comments.
- Letting generated docs replace the source-owned declaration.

hmmm
- whether examples listed in `examples` must execute or only resolve
- whether public exported surfaces without DOCS should fail strict mode by default
- how to normalize anchors across Markdown renderers
