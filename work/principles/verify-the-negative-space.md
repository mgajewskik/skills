# Verify the Negative Space

A live change is accepted when the target changed and nothing else in its neighbourhood did. A check on the intended set passes even when the blast radius was the whole fleet.

- Before the change, snapshot a bounded neighbour set: the same state file, namespace, project, tag scope, or host group, plus consumers of shared dependencies. After it, rerun the same query and diff. Only the approved identifiers may differ.
- Write "must not change" as counts and named neighbours, never as "nothing else is affected".
- An unobserved neighbour is unverified, not unchanged. Attribute concurrent unrelated changes with evidence before calling them harmless.
- Check again after the next reconcile. A GitOps sync, controller, or autoscaler that owns the field silently undoes a change made elsewhere, so make the change at its owner.

The test: if the action had touched one extra resource, or the owner's next reconcile had reverted it, which check would fail? If none, the verification is incomplete.
