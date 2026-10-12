---
name: infra-verify-the-negative-space
description: "Apply when accepting any live change, rollout, or destruction. Prove nothing outside the approved targets changed by diffing a bounded neighbour set before and after, and that the change survives the next reconcile."
disable-model-invocation: true
---

# Verify the Negative Space

A live change is accepted when the target changed and nothing else in its neighbourhood did. Checking only the target proves the action happened, not that it was the only thing that happened.

**Why:** A positive check on the intended set passes even when the blast radius was the whole fleet.

**Pattern:**
- Before the change, snapshot a bounded neighbour set: the same state file, namespace, project, tag scope, or host group, plus consumers of shared dependencies
- After it, take the same snapshot with the same query and diff. Exactly the approved identifiers should differ
- Write "must not change" as counts and named neighbours, never as "nothing else is affected"
- An unobserved neighbour is unverified, not unchanged. Attribute concurrent unrelated changes with evidence before calling them harmless
- Check again after the next reconcile cycle. A GitOps sync, controller, or autoscaler that owns the field silently undoes a change made anywhere else, so make the change at its owner

**The test:** if the action had touched one extra resource, or the owner's next reconcile had reverted it, which check would fail? If none, the verification is incomplete.

The positive half, checking the consumer's real result rather than a status code, is [prove-it-works](../prove-it-works/SKILL.md).
