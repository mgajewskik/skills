---
name: infra-principle-separate-containment-from-cause
description: Apply during production incidents when reducing impact cannot wait for complete causal diagnosis, or when a restart or workaround restored service. Track containment success separately from root-cause confidence and preserve evidence without expanding agent authority.
disable-model-invocation: true
user-invocable: false
---

# Separate containment from cause

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Diagnosis remains read-only. Containment is a live change: outside production a reversible option may be journaled and executed; production containment needs the user or a grant. Urgency never expands authority or permits destructive action.

## Why

Google prioritizes reducing major-outage impact while preserving evidence for later analysis. [Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) supports this ordering. The separate evidence records below are our adaptation.

## Pattern

1. Establish consumer impact, incident owner, known constraints, and the smallest useful sanitized evidence. Do not worsen an outage merely to reproduce it.
2. Surface bounded containment mechanisms with risks and recovery limits. In production, prepare an executable action only after the user selects it; use the contract's command disclosure.
3. After execution, yours or the user's, verify the containment outcome from the affected consumer. Record artifact, target, time, and residual impact.
4. Keep cause confidence separate. Preserve competing hypotheses and interrupted evidence; do not treat improvement after an intervention as complete causal proof.
5. Continue or hand off a scoped causal investigation and an authorized durable prevention task. Preserve the temporary workaround's owner, expiry/revisit condition, and limits.

The test: does the incident record hold two separate answers, "is impact contained?" and "what caused it, with what confidence?" If one sentence answers both, they have been merged.

You skipped this when an incident closes with "fixed by restarting X" and no cause confidence, or when a containment option was held back waiting for the diagnosis.

## Stop and limit

Do not delay surfacing an appropriate containment option until diagnosis is complete. Do not label a successful restart as a root-cause repair. Avoid unsupported single-cause certainty when interacting failures remain possible. Evidence preservation must not become an unrestricted log or secret dump.
