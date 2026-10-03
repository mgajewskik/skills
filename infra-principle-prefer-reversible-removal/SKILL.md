---
name: infra-principle-prefer-reversible-removal
description: Apply when a deletion or decommission has been selected and a reversible step exists first, such as disable, deny access, scale to zero, detach, retain, snapshot, or stop managing without destroying. Stage removal so consumer breakage surfaces while it can still be undone.
disable-model-invocation: true
user-invocable: false
---

# Prefer reversible removal

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. The reversible stage follows the contract's authority rule: when it passes the reversibility checklist, outside production or inside a session grant, the agent may execute it with a journal entry written first; otherwise it is a handoff. The destroy stage is always user-executed.

Remove in stages that keep a way back until the evidence says nobody needs the thing: stop its use, watch, then destroy. Name the exact step after which there is no way back.

## Why

Google's data-integrity practice uses soft deletion, where deleted data is marked unusable but kept, and lazy deletion that keeps it for weeks before destruction, so user and operator mistakes stay recoverable. [Data Integrity](https://sre.google/sre-book/data-integrity/). Terraform's `prevent_destroy` blocks a plan that would destroy the object, but does not apply once the resource block itself is removed from configuration; removing an object from management without destroying it is a separate operation. [lifecycle meta-argument](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle).

## Pattern

1. Ask what the owner actually wants gone: the object, its cost, its exposure, or its management. "Stop managing it" and "make it unreachable" are often enough and are reversible.
2. Choose the first reversible stage that makes every consumer fail loudly if it still depends on the target: deny access, disable, scale to zero, detach, or stop the instance. Keep data intact.
3. Define the observation window and the signal that would reveal a hidden consumer. Pick the window from the target's usage pattern, such as monthly batch jobs, not from a habit.
4. Confirm a recovery artifact applicable to this data format exists before the irreversible stage, as `infra-principle-design-recovery-first` requires.
5. Only then hand over the irreversible stage, as its own handoff, with the observation result as evidence.

The test: if a consumer still depends on this, at which stage would we find out, and could we undo that stage?

You skipped this when the first step of a removal is a `destroy` handoff, or its `## Reversible first` section has no observation window.

## Stop and limit

Some removals have no reversible stage, such as revoking a leaked credential or deleting data under a legal deadline; say so and let the owner accept that. A reversible stage can still cause an outage, so it gets its own journal entry or handoff, stop conditions, and recovery. Staging costs time and keeps paying for the resource; the owner may choose a shorter window with the risk stated.
