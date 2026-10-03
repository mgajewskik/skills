---
name: infra-principle-verify-the-negative-space
description: Apply when accepting any live modification, rollout, or destruction. Verify that what must not change did not change, by comparing a bounded neighbour set before and after, not only that the intended target changed.
disable-model-invocation: true
user-invocable: false
---

# Verify the negative space

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Snapshots are read-only observations within established scope.

A change is accepted when the intended target changed and nothing else in its neighbourhood did. Checking only the target proves the action happened, not that it was the only thing that happened.

## Why

A positive check on the intended set passes even when the blast radius was the whole fleet, as in Google's Diskerase outage, where the intended machines were erased along with almost all the others. [The Evolution of Automation at Google](https://sre.google/sre-book/automation-at-google/). The principle itself is our adaptation; it applies the pstack `principle-test-behavior-not-implementation` question (would this check still pass if the code did nothing?) in reverse: would this check still pass if the action did too much?

## Pattern

1. Before execution, choose a bounded neighbour set: the same state file, namespace, project, tag scope, or host group, plus consumers of shared dependencies. Record counts by type and the specific neighbours most likely to be hit by mistake.
2. Write the expectation into the handoff's `## Must not change` or the journal entry's verification: exact counts after the change, named neighbours that stay identical, and paths that must still be refused or still be served.
3. After execution, take the same snapshot with the same query and diff. Expect exactly the approved identifiers to differ.
4. Record each negative-space claim in the journal separately from the positive acceptance claims. A neighbour you could not observe is `unverified`, not assumed unchanged.
5. Count what the work itself left behind (flags, tunnels, temporary resources, scaled replicas) as part of the neighbourhood; `infra-principle-leave-no-residue` keeps that list.

The test: if the action had touched one extra resource, which check would fail? If none, the verification is incomplete.

You skipped this when a handoff's `## Must not change` or a journal entry's verification is a sentence ("nothing else is affected") instead of counts and named neighbours, or no snapshot was taken before execution.

## Stop and limit

Choose the neighbour set by what the action could plausibly reach; a full-account diff is noisy and may expose sensitive data. Concurrent unrelated changes show up as differences; attribute them with evidence before calling them collateral or harmless. Absence of a difference in a bounded set says nothing about objects outside it.
