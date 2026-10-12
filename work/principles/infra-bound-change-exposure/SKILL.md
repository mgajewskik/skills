---
name: infra-bound-change-exposure
description: "Apply before rolling out an infrastructure change, pushing config or a flag, running a bulk change, or re-running a step that timed out. Expose a representative unit first, watch it against stop signals chosen in advance, and widen only after it bakes."
disable-model-invocation: true
---

# Bound Change Exposure

Limit the blast radius of every change: ship to the smallest representative unit, watch it, then widen. A config or flag push is a rollout too.

**Why:** Most outages are changes. A canary only helps when the unit exercises the risky path and the gate watches the right signal. Shared dependencies (database, control plane, identity, network) can carry a "small" change to every consumer.

**Pattern:**
- Name the consumers and failure domains the change can reach before claiming isolation
- Define stop thresholds, observation window, and baseline before exposure, each with a reason tied to this workload, not a habitual percentage or wait
- Let each unit bake before the next change lands on the same target, so changes don't mask each other
- Run a bulk change against a counted list, per [infra-inventory-before-destroy](../infra-inventory-before-destroy/SKILL.md), and cap targets per batch and per minute
- A step that timed out or partly ran has an unknown outcome, not a failed one. Observe what completed before running it again
- On a failed gate, a contaminated comparison, or missing evidence, halt and roll the unit back. Never push forward to see if it settles

**The test:** if the change is broken in the way you fear most, would the first unit show it before the second starts? If not, the unit is not representative or the gate watches the wrong signal.

When no isolated unit exists, say so rather than calling something a canary.
