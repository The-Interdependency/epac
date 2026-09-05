---
name: a0p-instancing
description: Methodology for instancing agents in a0-betatest (the a0p research instrument), whose model diverges from canonical a0. Load this when adding or changing an AgentInstance / CharacterSheet CRUD path, a per-instance native ZFAE weight bank or its training/distillation loop, a ZFAE inference mode, a sentinel evaluation or pending-override gate, a per-agent safetensors checkpoint, or volatile sub-context memory — anywhere under a0-betatest `backend/`. Use it before writing code that creates, addresses, trains, runs, governs, or persists an a0p agent, so the code follows a0p's per-user CRUD + native-ZFAE + sentinel model instead of a0's spawn/fork/merge model. For canonical a0 and its mirror a0ucns, use `agent-instantiation` instead — a0p does NOT have `sub_agent_spawn`, a spawn executor, or `InstanceMerge`.
---

# a0p-instancing — How a0-betatest brings agents into being

a0-betatest (the **a0p** research instrument) replaced a0's single-persistent
+ fork model with a **multi-agent, per-user model**: an agent is a persistent
CRUD entity (`AgentInstance`) bound to an editable `CharacterSheet`, and each
instance **owns its own trained native ZFAE weight bank**. The LLM is optional
energy; once an instance's native core is trained, it can run with no LLM at
all. This skill captures that model so a coding agent extends it instead of
reaching for a0's spawn/fork/merge machinery, which **does not exist here**.

This skill is the **peer** of `agent-instantiation` (which documents a0 /
a0ucns). They describe genuinely different architectures; do not mix them.

## Load this when

- Adding/editing an `AgentInstance` or `CharacterSheet` **CRUD** path.
- Touching the **native ZFAE weight bank**, its **teacher-distillation
  training**, or the native **inference** engine / modes.
- Adding/changing a **sentinel** evaluation or a **pending-override** gate.
- Persisting per-agent state (**safetensors checkpoints**, Mongo metadata,
  **FIQ** audit events) or volatile **sub-context** memory.

Do not load this for canonical a0 / a0ucns work (use `agent-instantiation`),
or for ordinary LLM-prompt work that creates no instance.

## Scope and source boundary

The **canonical source is `a0-betatest/backend/`** (the a0p package per its
`CLAUDE.md`). `a0-betatest/_legacy_a0/` is a **reference copy of canonical a0**
and follows `agent-instantiation`, not this skill — keep that boundary. This is
**repo-specific runtime doctrine**: it transfers no UCNS / PCNA / ZFAE theorem
status. The constants below (core shape, scalar counts, readiness thresholds,
sentinel count) are a0p's **current** values — read them from source, don't
reproduce them from memory. Where a mechanism is unclear or unwired, write
`hmmm` rather than inventing it.

## The model: agent = CRUD entity + native weight bank

- **`AgentInstance`** (`backend/agents/schema.py`) — the persistent entity:
  `id` (UUID), `user_id`, `sheet: CharacterSheet`, timestamps, `archived`,
  `zfae_metrics`. Stored in Mongo `agent_instances` plus a per-agent
  filesystem directory.
- **`CharacterSheet`** (`backend/agents/schema.py`) — the editable context
  template: `mode`, `base_model`, system prompt, persona, memory seeds,
  P/X resolution, boundaries, sentinel modes/weights, gonal assignment.
- **Native ZFAE weight bank** (`backend/interdependent_lib/zfae/weights.py`,
  `weight_init.py`) — three 157-seed cores (Φ/Ψ/Ω) of shape `[157,53,7,7]`
  (≈407,729 scalars each; ≈1,223,187 total). `A0ZFAEWeightBank` is created
  **fresh per agent** at creation (`backend/agents/store.py`).

There is **one weight bank per agent**, not a shared singleton engine. Never
share or fork a bank between instances.

## Instancing sequence (dependency order — follow it top to bottom)

1. **Author the CharacterSheet, not hardcoded behavior.** Define/extend
   `CharacterSheet` (mode, base_model, persona, boundaries, sentinel
   modes/weights). The sheet is the unit of customization and is editable
   post-creation.
2. **Create via `AgentStore.create()`** (`backend/agents/store.py`) — it
   mints a UUID, writes the Mongo record, makes the per-agent directory, and
   **initializes a fresh `A0ZFAEWeightBank`**. Never construct an instance or
   its bank by hand outside the store.
3. **Train the native core by teacher distillation** (`ZFAELearner`,
   `backend/interdependent_lib/zfae/trainer.py`) — text-signature MSE loss
   accumulates into the bank; track `zfae_training_step`, `zfae_last_loss`,
   and the per-`(core, seed)` touched bitset.
4. **Gate native readiness before answering natively** (`_is_trained_enough`,
   `backend/interdependent_lib/zfae/runtime.py`) — a0p requires enough teacher
   rounds, low enough loss, AND every `(core, seed)` pair touched
   (471 = 157×3). An undertrained `zfae_native` agent must NOT fabricate a
   native answer; it stays gated.
5. **Run inference through the mode** (`AgentMode`, `A0ZFAEInferenceEngine`,
   `backend/interdependent_lib/zfae/inference.py`). The five modes
   (`ZFAE_NATIVE`, `ZFAE_ASSISTED`, `MODEL_OBSERVED_BY_ZFAE`,
   `MODEL_PLUS_CRITIC`, `BARE_MODEL`) decide whether the native core, an LLM,
   or both produce/judge the reply. `zfae_native` refuses LLM fallback.
6. **Evaluate sentinels and honor the override halt** (`sentinel_eval.py`,
   `sentinels.py`, `overrides.py`). Resolve per-agent sentinel modes/weights,
   compute the `Verdict13`; on a blocking flag, create a `PendingOverride`
   and **halt** until approved. Do not bypass the halt.
7. **Checkpoint to safetensors, not a DB blob.** Persist the bank to
   `storage/agents/{id}/zfae_core.safetensors` (+ `…meta.json`: digest,
   `training_step`, `last_loss`, seeds-touched) via the bank's `save()` /
   `AgentStore`. Emit trace events to the hash-chained **FIQ audit log**
   (`zfae_sentinel_verdict`, `zfae_override_created`, `zfae_chat_reply`, …).
8. **CRUD, don't fork.** Read/update/archive/delete instances through the
   agent routes (`backend/agents/routes.py`, `/api/instances/{id}`). There is
   no sub-agent spawning; the only "spawn/merge" is **volatile sub-context
   memory** — `MemoryCore.spawn_sub(sub_id)` / `merge_sub(sub_id)`
   (`backend/interdependent_lib/pcna/memory_core.py`), which scopes items
   within one agent's memory and flushes to short-term on merge.

## Inference modes

| Mode | Who answers / judges |
|---|---|
| `ZFAE_NATIVE` | Native core only; refuses LLM fallback (requires readiness). |
| `ZFAE_ASSISTED` | Native core with LLM assistance. |
| `MODEL_OBSERVED_BY_ZFAE` | LLM answers; ZFAE observes/measures. |
| `MODEL_PLUS_CRITIC` | LLM answers; ZFAE critiques. |
| `BARE_MODEL` | LLM only. |

Modes are per-agent on the `CharacterSheet`; read the enum from
`backend/agents/schema.py` rather than hardcoding strings.

## Identity, persistence, governance

- **Identity.** The durable handle is `AgentInstance.id` (UUID) + the
  character-sheet name, scoped by `user_id`. The human-facing label follows
  the canonical grammar `username( a0( <energy> ) <auditor/teacher> )` (see
  `agent-instantiation`): the `username( … )` wrapper is the owning `user_id`,
  the energy inside `a0( … )` is the sheet's `base_model` (or `zfae` for the
  native core), and the auditor/teacher maps to the sheet's mode / outer model
  — e.g. `a0(zfae)` is `ZFAE_NATIVE`, `a0(zfae)gpt5.5` is native energy with a
  gpt5.5 teacher (`ZFAE_ASSISTED` / `MODEL_PLUS_CRITIC`), and `a0(gpt5.5)` is
  `BARE_MODEL`. a0p does **not** use a0's `zeta{n}` sub-agent suffix.
- **Persistence** is three-part: Mongo `agent_instances` (metadata),
  per-agent filesystem `storage/agents/{id}/` (safetensors + meta), and the
  FIQ hash-chained audit log (events). Not `system_toggles` / `agent_logs`.
- **Governance** is sentinel verdict + pending-override halt (human-in-loop),
  plus skill compliance: every `backend/` module declares `MODULE_BUILD`,
  `BOUNDARIES`, `CAPABILITIES` (and where applicable `CONTRACTS`, `RATIOS`)
  blocks, enforced by the vendored `a0p_skills` runners
  (`module_build_runner`, `boundaries_runner`, `capabilities_runner`,
  `ratios_runner`, `test_build_runner`).

## Anti-patterns (refuse these)

- Reaching for a0's `sub_agent_spawn`, spawn executor, `agent_runs` rows, or
  `InstanceMerge.fork/absorb/converge` — **none exist in a0p**.
- Sharing or forking one agent's weight bank into another instead of creating
  a fresh bank per `AgentInstance`.
- Letting a `zfae_native` agent answer before `_is_trained_enough` passes.
- Bypassing the sentinel verdict / pending-override halt on a side-effecting
  path.
- Persisting bank state to a DB blob instead of the per-agent safetensors
  file, or skipping the FIQ audit event.
- Adding a `backend/` module without its `MODULE_BUILD` / `BOUNDARIES`
  blocks (unknown fields are `hmmm`, not guessed).

## hmmm

- **No parallel sub-agent decomposition.** a0p dropped a0's fork/merge swarm
  capability entirely (only volatile memory scoping remains). Whether this is
  a deliberate trade or a gap to re-add (fork = clone-and-diverge a bank;
  merge = distill/average banks) is unresolved — do not assume it exists.
- **Native-inference quality is unproven.** The native engine is a
  template-grammar decoder trained by distillation; readiness thresholds
  (`min_steps`, `max_loss`, all-seeds-touched) are tunable, not validated
  optima. Treat them as repo-local.
- **Spawn/concurrency caps** are not clearly present as in a0; any limits may
  live in sentinels. Verify against source before relying on a limit.
- See `agent-instantiation` for the canonical a0 / a0ucns model this one
  diverged from.
