---
name: infra-principle-assign-one-state-owner
description: Apply when Terraform, GitOps, controllers, automation, or operators may write overlapping desired state. Assign ownership at the conflicting resource or field scope, separate independent outputs, and coordinate real shared invariants rather than locking competing intentions.
disable-model-invocation: true
---

# Assign one state owner

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Ownership analysis is not permission to transfer live fields, disable controllers, or force an apply. Live changes follow the contract: reversible non-production changes are journaled, then executed; production needs a session grant; irreversible ones are user-executed.

## Why

Kubernetes Server-Side Apply tracks field managers and detects conflicting apply values. It also permits multiple managers and coordinated ownership transfer. [Server-Side Apply](https://kubernetes.io/docs/reference/using-api/server-side-apply/) supports field-level conflict reasoning, not a universal one-manager-per-object rule.

## Pattern

1. Inventory writers, their exact fields/resources, desired values, and reconciliation cadence. Include human interventions and generated source.
2. Separate independent outputs and scopes. Assign one authoritative desired-state decision for each conflicting scope; document legitimate shared ownership explicitly.
3. Distinguish declared ownership from enforcement. Inspect version-specific controller, API, and backend behavior. Ordinary updates may not have apply conflict protection.
4. For a genuine shared invariant, use an actual lock, exclusive writer, conditional update, or enforced sequence as appropriate. Serialization cannot settle incompatible desired values.
5. Prepare an explicit ownership transfer with old writer retirement, new writer activation, retained fields, and consumer verification. Execute it only under the contract's authority rule, after the user picks the new owner.

The test: for the field you are about to change, can you name every writer and say which one wins after the next reconcile? If not, the change may be silently undone.

You skipped this when a change (journaled or handed over) sets a field and its verification never looks again after the reconciler's next cycle.

## Stop and limit

Halt rollout expansion when competing reconcilers can undo the change. Do not force conflicts to disappear. Multiple managers on different fields, or documented same-value shared ownership, are not automatically defects. A field-manager record is neither an authorization boundary nor a global lock.
