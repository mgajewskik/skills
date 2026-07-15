---
name: skill-architect
description: Design, create, audit, evaluate, refactor, and de-bloat portable Agent Skills. Use when defining a skill's scope or trigger boundaries, choosing its files, authoring or validating a skill package, testing behavior, or improving an existing skill. Do not use merely to run, install, or explain an existing skill.
---

# Skill Architect

Build the smallest Agent Skill that measurably improves representative work. Default to the portable Agent Skills specification; add runtime-specific metadata or adapters only when the target runtime is known and requires them.

## Workflow

1. Inspect before designing.
   - Read the target runtime's current skill rules when runtime behavior matters.
   - Inspect existing artifacts, nearby conventions, and concrete examples of intended use.
   - Recover requirements and corrections already present in the conversation before asking questions.
2. Define the contract.
   - State what the skill enables, when it should and should not trigger, expected inputs and outputs, and visible non-goals.
   - Define binary success criteria and at least one anti-criterion that catches a likely regression, false trigger, or scope leak.
   - Ask only when missing information could materially change scope, safety, or structure.
3. Choose the smallest package shape.
   - Keep instructions needed on every triggered run in `SKILL.md`.
   - Add a focused reference only for branch-specific knowledge.
   - Add a script only for repeated deterministic work.
   - Add an asset only when the workflow emits or copies reusable material.
   - Do not create placeholders or speculative files.
4. Author or refactor.
   - Put what the skill does and when to use it in the frontmatter description.
   - Use direct, imperative instructions and explicit safe fallbacks.
   - Preserve safety constraints and verified historical corrections during pruning.
   - Keep each rule in one authoritative location unless repetition is necessary for safety.
5. Validate and evaluate.
   - Validate the package structure and frontmatter.
   - Test trigger boundaries and representative functional, edge, and failure-path requests.
   - For a new skill, compare against no-skill behavior. For a refactor, compare against the prior version with identical prompts in fresh contexts.
   - Inspect artifacts and execution behavior directly; use human review for subjective quality.
6. Iterate only on evidence.
   - Fix observed, generalizable failures rather than patching individual prompts.
   - Re-run affected tests and regression cases.
   - Stop when criteria pass and further changes no longer produce meaningful improvement.

## Conditional guidance

- Read [architecture.md](references/architecture.md) when discovery, content placement, splitting, portability, or de-bloating decisions are material.
- Read [evaluation.md](references/evaluation.md) when auditing, testing triggers or behavior, comparing versions, tuning descriptions, or refining from evidence.
- Read both when creating or substantially refactoring a reusable skill.

Do not load either reference for a narrow edit whose correct shape and validation are already evident.

## Portable scaffold

Create a minimal scaffold with:

```bash
uv run skill-architect/scripts/init_skill.py <name> \
  --path <directory> \
  --description "<what the skill does and when to use it>" \
  [--resources references,scripts,assets]
```

The initializer creates only `SKILL.md` unless resource directories are explicitly requested. Its output is structurally valid, not behaviorally complete.

Validate the portable core with:

```bash
uv run skill-architect/scripts/quick_validate.py <skill-directory>
```

The validator declares PyYAML as a script-local dependency. `uv` resolves and caches it on demand in an isolated environment; it does not require or modify the ambient Python environment. If dependency resolution is unavailable, inspect the frontmatter and package manually or use the target runtime's supported validator.

## Completion

Report:

- scope and files created, changed, or removed
- success criteria and anti-criterion status
- structural, trigger, and functional evidence
- comparison result and regressions for reusable or refactored skills
- runtime-specific assumptions, unknowns, and skipped validation

Do not claim portability beyond the validated core, behavioral improvement without a comparison, or packaging/benchmark support without a tested consumer.
