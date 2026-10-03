---
name: infra-principle-inventory-before-destroy
description: Apply before preparing any delete, destroy, decommission, prune, or cleanup of a live resource, however it is phrased. Resolve every selector to a finite list of exact identifiers with owners, dependents, and retention status before any destroy command is drafted.
disable-model-invocation: true
user-invocable: false
---

# Inventory before destroy

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Building the inventory is read-only; a deletion is always irreversible and user-executed.

A destroy command is drafted only against an explicit, finite list of exact identifiers. The selector, tag query, or "old ones" description is input to the inventory, never the target of the command.

## Why

Google's Diskerase outage came from automation that treated an empty target set as "everything" and sent almost every machine to disk erase. [The Evolution of Automation at Google](https://sre.google/sre-book/automation-at-google/). Kubernetes deletes dependents in the background by default unless foreground deletion or orphaning is chosen, and finalizers can hold an object in a terminating state. [Garbage collection](https://kubernetes.io/docs/concepts/architecture/garbage-collection/), [Finalizers](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/). What a delete removes is decided by the platform's cascade rules, not by the name in the command.

## Pattern

1. Resolve the selector with a bounded read-only query and save the result as the inventory artifact. Record the query, its scope (account, cluster, namespace, project), and the time.
2. Assert the count: non-zero, and no larger than the owner's stated expectation. An empty or unexpectedly large result is an error to report, never "nothing to do" and never "all of them".
3. For each identifier, record the owner, the dependents that the platform will cascade to or orphan, the consumers that still reference it (access logs, DNS, policies, mounts), and its retention or backup obligation.
4. Exclude anything whose owner or dependents cannot be established. An unknown dependency is a reason to shrink the list, not to proceed.
5. Put the final list and its count in the handoff's `## Targets` and the per-target facts in `## Inventory`. Prefer a small rerunnable script that regenerates the list so the owner can rerun it immediately before execution.

The test: could the owner, reading only the handoff, name every object that will stop existing, including cascaded dependents? If not, the inventory is incomplete.

You skipped this when the handoff's command contains a selector, glob, label query, or `--all` and the `## Targets` count was never compared with a fresh query.

## Stop and limit

Halt when the selector resolves differently on two reads, when ownership is disputed, or when a dependent's deletion behavior cannot be established for the installed version. Inventory proves what existed at the observation time; re-run it right before execution because state drifts. This leaf decides what is in scope; recovery is `infra-principle-design-recovery-first` and staging is `infra-principle-prefer-reversible-removal`.
