---
name: llms-build
description: Self-declaring LLM instructions file (llms.txt) built on msdmd. Modules or central files declare LLMS blocks with project overview, key definitions, architecture summary, and agent usage rules. A runner aggregates them into a standardized root llms.txt and surfaces drift/gaps. Load this when creating, updating, or maintaining llms.txt for any repo consumed by LLMs or agents.
---

# llms-build — Self-declaring LLM instructions (llms.txt)

## The doctrine

Every repo intended for consumption by LLMs or agents should maintain a single root file named exactly `llms.txt`.

That file locks four things:

- project overview
- key definitions, using a never-infer-or-expand rule
- architecture summary
- usage rules for agents

The content of `llms.txt` is declared through msdmd `LLMS` blocks. This keeps instructions version-controlled in the same diff as code changes and makes missing or stale instructions visible as drift.

The `llms-build` runner walks the tree, parses all `LLMS` blocks, assembles the canonical `llms.txt`, and reports drift between the generated file and the committed file.

## Block syntax

```markdown
# === LLMS ===
# id: project_overview
#   content: One-sentence tagline plus one or two sentences describing the repo.
#
# id: key_definitions
#   msdmd: exact definition from msdmd/SKILL.md
#   char-compress: exact definition from char-compress/SKILL.md
#   any_other_key: exact one-line canonical text
#
# id: architecture_summary
#   content: Short bullet-point or table version of the core architecture.
#
# id: usage_rules
#   content: Bullet list of rules for LLMs and agents.
# === END LLMS ===
```

Use the language-appropriate comment marker for the file containing the block. Markdown and Python use `#`; TypeScript, JavaScript, Rust, Go, Java, C, C++, Swift, and Kotlin use `//`; SQL, Lua, and Haskell use `--`.

Multiple `LLMS` blocks or multiple `id:` entries are allowed and concatenated. The `content` field supports multi-line markdown when continuation lines remain inside the comment block.

## Required entries

| id | Required fields | Meaning |
|---|---|---|
| `project_overview` | `content` | One-sentence tagline plus one or two sentences describing the repo. |
| `key_definitions` | one field per key term | Canonical definitions. Never infer or expand these. |
| `architecture_summary` | `content` | Short bullet list or table describing the core architecture, skills, pipeline, or module map. |
| `usage_rules` | `content` | Rules for how LLMs and agents should use the repo. |

Unknowns in any section are written as `hmmm`, not guessed.

## The runner protocol

A compliant `llms-build` runner:

1. Uses the shared msdmd parser or an equivalent parser that preserves the same block contract.
2. Walks the source tree while skipping the same conventional paths as other msdmd runners.
3. Collects every `LLMS` block entry.
4. Ignores fenced code examples in Markdown so documentation examples do not become declarations.
5. Falls back gracefully when no explicit `LLMS` blocks exist, while writing unresolved values as `hmmm`.
6. Assembles `llms.txt` using the canonical template.
7. Writes or updates `llms.txt` when `--apply` is passed.
8. Reports drift between generated and committed `llms.txt`, and exits non-zero in `--check` mode.

Reference generator in this repo:

```bash
python -m llms.build --root . --out llms.txt
python -m llms.build --root . --out llms.txt --apply
python -m llms.build --root . --out llms.txt --check
```

## Output template

The runner produces this shape:

```markdown
# LLM Instructions for <repo-name>

## Project Overview
[content from id: project_overview]

## Key Definitions (never infer or expand these)
- **msdmd** = ...
- **char-compress** = ...
- [any other keys you declared]

## Architecture Summary
[content from id: architecture_summary]

## How to Use This Repo with LLMs / Agents
[content from id: usage_rules]

This file is the single source of truth. If something is not explicitly stated in the files listed above, it does not exist in this repository.
```

## Editing doctrine

- Edit declarations in the source `LLMS` blocks first.
- Run the generator to update `llms.txt`.
- Commit both the block and the generated file in the same change.
- Unknowns in any section are written as `hmmm`, never guessed.
- Definitions in `key_definitions` are canonical source text. Do not infer expansions from acronyms, repo names, or neighboring prose.

## Anti-patterns

- Hand-editing `llms.txt` as independent doctrine instead of changing source
  `LLMS` blocks and regenerating.
- Letting Markdown examples become declarations; runners must ignore fenced code
  examples.
- Expanding acronyms or definitions from model memory when the source block did
  not define them.
- Treating missing `LLMS` blocks as proof that no repo instructions exist;
  report the gap and preserve `hmmm`.

## Primary source files for this skill

- `llms-build/SKILL.md` — canonical spec for the skill.
- `llms/build.py` — stdlib reference runner implementing the command declared above.
- `msdmd/SKILL.md` — parser contract and metadata-block doctrine.
- `msdmd/parsers/universal.py` — shared reference parser whose contract this runner follows.

See `AGENTS.md` for loading triggers and `skills.json` for registration.

Last updated: 2026-06-10
