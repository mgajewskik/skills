# Principles

A principle is a separate skill: one rule, with its reason, its steps, a test question, and a sign that it was skipped. work-mode's router indexes 37 of them in one line each. The agent reads a leaf in full, by path (`<catalog>/<name>/SKILL.md`), only when its trigger fires, and cites only leaves it read.

## Where they come from

```text
source                       count   model list   loaded by
--------------------------   -----   ----------   --------------------------------------
pstack principle-* leaves    24      no           work-mode (23, by path),
                                                  other pstack skills that name them
infra-principle-* leaves     14      no           work-mode (by path)
```

Pstack leaves come from `github.com/cursor/plugins` through `scripts/update-skills.sh`, unchanged; the script only adds `agents/openai.yaml` so Codex honors the same user-only setting, and `user-invocable: false` so the `/` menu does not list them. They are written for application code. When one applies to a live system, the router's index line adds its limit after "Live:", for example:

> **principle-fix-root-causes**. Debugging. Live: containment can precede root cause, and a restart that restores service establishes nothing about cause.

`principle-experience-first` (product and UX tradeoffs) stays installed but is not in the index.

The infra leaves were written for this setup, grounded in Google SRE, the AWS Builders' Library, and Kubernetes and Terraform documentation. Each one opens by pointing at work-mode's contract, so its authority rules hold even when you invoke a leaf by name outside work-mode.

## The index

| Group | Leaves | Fires when |
| --- | --- | --- |
| Core | laziness-protocol, foundational-thinking, redesign-from-first-principles, attack-the-premise, subtract-before-you-add, minimize-reader-load, outcome-oriented-execution, exhaust-the-design-space, build-the-lever | Shaping a change: sizing it, sequencing it, choosing between designs, or after repeated failed fixes. |
| Architecture | model-the-domain, boundary-discipline, type-system-discipline, make-operations-idempotent, migrate-callers-then-delete-legacy-apis, separate-before-serializing-shared-state | Writing logic, types, adapters, retries, or anything concurrent actors share. |
| Verification | prove-it-works, fix-root-causes, sequence-verifiable-units, test-behavior-not-implementation, explain-the-number | Before saying done, while debugging, writing tests, or reporting a number. |
| Delegation and Meta | guard-the-context-window, never-block-on-the-human, encode-lessons-in-structure | Context filling up, tempted to ask about reversible work, or repeating an instruction. |
| Infra | act-through-the-narrowest-identity, prove-consumer-outcomes, bind-evidence-to-context, verify-the-negative-space, leave-no-residue, reconcile-before-retrying, bound-retries, assign-one-state-owner, preserve-compatible-transitions, bound-change-exposure, design-recovery-first, inventory-before-destroy, prefer-reversible-removal, separate-containment-from-cause | Any live change, rollout, deletion, incident, drift, retry, or evidence reused across contexts. |

One tension is worth knowing. `principle-never-block-on-the-human` says to proceed on reversible work without asking. In work-mode, "reversible" is decided by the contract's checklist with evidence, not by the agent's feeling. The index line says so.

## Anatomy of an infra leaf

```text
description      "Apply when ..."  (the trigger; work-mode's index summarizes it)
# Title          the rule in one paragraph, then the contract pointer
## Why           the source, linked
## Pattern       numbered steps
The test:        one question that shows whether the rule was applied
You skipped this when ...   an observable sign it was not
## Stop and limit            where the rule stops applying
```

`scripts/check_work_mode.py` fails when an infra leaf misses any of these parts, when its Why has no link, when its description does not start with "Apply", or when it is not user-only on both hosts and hidden from the `/` menu.

## Why user-only

Upstream ships every pstack skill with `disable-model-invocation: true`: Poteto Mode loads them from its router when a trigger fires, so they never sit in every session's skill list. work-mode keeps that intent. None of the 38 leaves costs context until work-mode reads one. All 38 also carry `user-invocable: false`, so Claude Code keeps them out of the `/` menu and loads them only by path, never with `/name` or the Skill tool. When a vendored skill tells the agent to use another one (`teach` runs `how` and `why`), the agent reads that skill's `SKILL.md` by path too; `references/host-notes.md` says so.
