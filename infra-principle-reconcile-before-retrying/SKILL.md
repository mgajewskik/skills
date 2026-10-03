---
name: infra-principle-reconcile-before-retrying
description: Apply when desired infrastructure differs from runtime, a deploy or API call times out, or a previous run may have partially completed. Establish observed progress and operation semantics before retrying; separate convergent state changes from one-shot effects.
disable-model-invocation: true
---

# Reconcile before retrying

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Observe within scope. Reconciliation and retries are live changes under the contract's authority rule, and a retry needs a current inventory first. Never execute destructive cleanup.

## Why

Kubernetes controllers compare desired and current state. An AWS timeout example shows that a missing response can leave creation uncertain and a blind retry can duplicate resources. [Controllers](https://kubernetes.io/docs/concepts/architecture/controller/), [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

## Pattern

1. Name desired state, observed state, known completed steps, unknown steps, and evidence tying them to this operation and owner.
2. Distinguish absent response from failed mutation. Use bounded existing inventory or completion records before proposing another attempt.
3. Inspect exact operation/version semantics. For verified idempotent APIs, establish caller intent, token scope/lifetime, and safe repetition. A tool's label does not cover arbitrary hooks.
4. Separate repeat-safe reconciliation from one-shot effects such as notifications, payments, or migrations. Identify residual effects and possible compensation without executing it.
5. Present a bounded resume/recovery option, preconditions, stop signals, and verification. The live actions then follow the contract's authority rule; a retry of a user-executed step needs the user's renewed approval.

The test: what happens if the operation runs twice in a row, and what if the previous run stopped at each possible step? If any answer is "it depends on what was left behind", reconcile first.

You skipped this when a retry, executed or handed over, follows a timeout or partial run without a current inventory of what completed.

## Stop and limit

Unresolved completion state or changed intent halts a blind retry. Verified safe repetition may avoid additional reconciliation only within that operation's proven contract. Controller convergence is not consumer acceptance; persistent failure may reflect permissions, dependencies, or conflicting writers. No retry token or controller grants authority.
