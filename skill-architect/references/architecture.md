# Architecture

Use this reference when discovering a skill's contract, choosing its package shape, targeting a runtime, splitting skills, or removing bloat.

## Start from observed use

Inspect the conversation, existing skill, target runtime, and representative requests before proposing structure. Extract:

- the outcome users need and the input they provide
- phrases and situations that should trigger the skill
- adjacent requests that should not trigger it
- required outputs, tools, safety rules, and failure behavior
- concrete success criteria and likely regressions
- corrections or constraints already verified through prior use

Ask for missing information only when it could change the contract, safety posture, or package shape. If answers conflict, name the conflict instead of silently choosing. Examples include a supposedly pass/fail task that needs subjective iteration, or a requested one-pass output that depends on unresolved discovery.

## Define the boundary

Write down:

- **Purpose:** the reusable capability the skill adds.
- **Triggers:** user intents and contexts where loading it helps.
- **Near-misses:** neighboring intents better handled without it or by another skill.
- **Inputs and outputs:** what must exist before and after the workflow.
- **Criteria:** observable facts that prove the skill worked.
- **Anti-criteria:** regressions, false triggers, unsafe behavior, or scope leaks that must not occur.
- **Non-goals:** tempting adjacent work intentionally excluded.

The frontmatter description must say what the skill does and when to use it. Optimize for intent categories, not an exhaustive keyword list. Include an exclusion when a close near-miss would otherwise overtrigger.

## Place each kind of content once

Use the smallest structure justified by actual use:

| Content | Location | Add it when |
|---|---|---|
| Routing, core workflow, guardrails, safe fallback | `SKILL.md` | Needed on nearly every triggered run |
| Branch-specific knowledge or detailed examples | `references/` | Only some workflows need it |
| Repeated deterministic operation | `scripts/` | Reimplementation is wasteful or error-prone |
| Templates or material copied into outputs | `assets/` | The workflow consumes or emits it |

Do not create placeholder directories, maintenance READMEs, schemas without consumers, or automation for a hypothetical future runtime. Keep references shallow and link directly from `SKILL.md`; avoid reference chains.

Apply two pruning tests:

1. **No-op test:** if removing a rule or file would not change representative behavior, validation, or safety, remove it.
2. **Single-source test:** if the same rule appears in multiple places, keep one authoritative version unless repetition is required to prevent a safety failure.

Never use pruning to remove a safety constraint, compliance boundary, fact-preservation rule, or verified historical correction merely because it is uncommon. Preserve the reason or a regression test when its value is not obvious.

## Calibrate instructions to risk

Give creative work principles and review criteria. Give fragile, deterministic, or high-consequence work exact steps, bounded inputs, validation, and safe failure behavior. Do not impose a universal rubric, number of phases, approval gate, memory convention, tool doctrine, or decomposition rule without evidence that it improves this skill.

For transformations, identify source facts that must survive and compare them directly. For high-stakes actions, separate observation from mutation, state uncertainty, and define when the agent must stop or defer to the user. For tool workflows, validate prerequisites before irreversible or dependent actions, pass only required data between steps, and describe rollback where meaningful.

## Split only for a real boundary

Split one skill into multiple skills only when at least one of these is demonstrated:

- each part needs independent invocation or distinct trigger boundaries
- an intermediate artifact is reused by other workflows
- separate context materially improves reliability or cost
- different runtimes, permissions, owners, or safety boundaries require isolation

Keep sequential phases together when they share one trigger, one user outcome, and one short-lived context. File count alone is not a reason to split.

## Target runtimes explicitly

Portable core frontmatter uses:

- required `name` and `description`
- optional `license`, `compatibility`, `metadata`, and `allowed-tools`

Treat `allowed-tools` as runtime-dependent even when structurally accepted. Put runtime-specific root fields, UI metadata, agent manifests such as Codex `agents/openai.yaml`, and Claude Code extensions in optional adapters only after checking current runtime documentation. Do not claim that one runtime's acceptance proves portability elsewhere.

When tools, subagents, browser access, or nested execution are unavailable, preserve the reasoning workflow and report the lower verification level. Do not invent an adapter contract or silently claim an automated check ran.

## Architecture review

Before authoring, confirm:

- every file has a current consumer
- every instruction maps to the contract, a criterion, or a safety boundary
- core guidance is available without loading unrelated branches
- repeated deterministic work is scripted only when the script can be executed and tested
- the description distinguishes positive intents from competitive near-misses
- removed material is either redundant, unsupported, or proven irrelevant
