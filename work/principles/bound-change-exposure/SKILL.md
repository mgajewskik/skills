---
name: bound-change-exposure
description: "Apply before rolling out an infrastructure change, pushing config or a flag, running a bulk change, or re-running a step that timed out. Representative unit first, stop signals set in advance, widen only after it bakes."
disable-model-invocation: true
---

# Bound Change Exposure

Ship every change to the smallest representative unit, watch it, then widen. A config or flag push is a rollout too. When no isolated unit exists, say so instead of calling something a canary.

- Name the consumers and failure domains the change can reach. A shared dependency (database, control plane, identity, network) carries a "small" change to every consumer.
- Set the stop thresholds, observation window, and baseline before exposure, each with a reason tied to this workload, not a habitual percentage or wait.
- Let each unit bake before the next change lands on the same target.
- Run a bulk change against a counted list of identifiers, capped per batch and per minute.
- A step that timed out or partly ran has an unknown outcome. Observe what completed before running it again.
- On a failed gate, a contaminated comparison, or missing evidence, halt and roll the unit back. Never push forward to see if it settles.

The test: if the change is broken in the way you fear most, would the first unit show it before the second starts? If not, the unit is not representative or the gate watches the wrong signal.
