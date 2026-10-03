---
name: infra-principle-design-recovery-first
description: Apply before approving infrastructure changes with availability, storage, data, or external side effects. Define a verified recovery destination, prerequisites, owner, and limits before execution; source reversion is not proof of data or service restoration.
disable-model-invocation: true
---

# Design recovery first

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Recovery preparation grants no authority to restore, destroy, fail over, or rehearse live operations. Restores that overwrite data, destroys, and failovers are irreversible and user-executed.

## Why

Google emphasizes actual end-to-end recovery evidence, including usable backups, resources, timing, and dependencies. AWS verifies rollback compatibility before deployment. [Data Integrity](https://sre.google/sre-book/data-integrity/), [Rollback safety](https://d1.awsstatic.com/builderslibrary/pdfs/ensuring-rollback-safety-during-deployments.pdf).

## Pattern

1. Define the recovery destination and correct consumer behavior. Name owner, prerequisites, access dependencies, and accepted time/data-loss limits.
2. Enumerate reversible state and irreversible external effects. A previous config cannot recover removed data or unsend a webhook.
3. Find current recovery evidence applicable to this artifact, data format, target, and dependencies. Backup existence alone is insufficient. If rehearsal is needed, propose a scoped plan; it runs under the contract's authority rule.
4. Describe recovery steps, stop conditions, residual risk, and bounded verification. Distinguish rollback, restore, roll-forward repair, and compensation when their effects differ.
5. Mark unsupported recovery capability unverified. A change without verified recovery fails the reversibility checklist, so it is user-executed, and the user explicitly accepts the limits or picks a safer alternative.

The test: when was this recovery path last exercised for this data format and size, and what did it restore? "We have backups" with no answer is `unverified`.

You skipped this when a handoff's `## Recovery` or a journal entry's revert says "revert" or "restore from backup" without naming what that restores, what it cannot, and the evidence it works.

## Stop and limit

Do not promise restoration from an untested procedure or stale evidence. Recovery testing can itself mutate systems and reveal sensitive data. An honest recovery limit may rule out a proposed rollout; it never authorizes destructive improvisation during an incident.
