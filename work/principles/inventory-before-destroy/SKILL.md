---
name: inventory-before-destroy
description: "Apply before any delete, destroy, decommission, prune, or cleanup of a live resource. Resolve selectors to a counted list of exact identifiers, then remove through a reversible stage before the irreversible one."
disable-model-invocation: true
---

# Inventory Before Destroy

Destroy only an explicit, finite list of exact identifiers, and remove in stages that keep a way back until the evidence says nobody needs the thing. A selector is not a target.

- Resolve the selector with a bounded read-only query. Record the query, its scope, and the time.
- Assert the count: non-zero and no larger than the owner expects. An empty or unexpectedly large set is an error, never "nothing to do" or "all of them".
- For each identifier, find the owner, cascaded dependents, live consumers (access logs, DNS, policies, mounts), and retention obligations. Platform cascade rules (garbage collection, finalizers, dependent resources) decide what a delete removes. An unknown owner or dependent shrinks the list.
- First run a reversible stage that makes hidden consumers fail loudly (deny access, disable, scale to zero, detach, stop managing without destroying), watched over a window matched to the usage pattern, such as a monthly batch job. When no reversible stage exists, as with revoking a leaked credential, say so.
- Re-run the inventory and confirm recovery right before the irreversible step.

The test: could the owner, reading only your list, name every object that will stop existing, cascaded dependents included? If a consumer still depends on it, at which stage would you find out, and could you undo that stage?
