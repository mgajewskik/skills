---
name: infra-principle-bound-change-exposure
description: Apply before expanding an infrastructure rollout or running a production experiment. Choose representative exposure, observation gates, and stop signals from the real workload and failure domains; do not assume a small canary isolates shared dependencies.
disable-model-invocation: true
---

# Bound change exposure

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Preparation and read-only assessment may proceed within scope. Live changes follow the contract: reversible non-production changes are journaled, then executed; production needs a session grant; irreversible ones are user-executed.

## Why

Google describes canaries as partial deployments evaluated over time. Population, workload diversity, duration, metrics, and shared failure domains determine whether the comparison is meaningful. [Canarying Releases](https://sre.google/workbook/canarying-releases/).

## Pattern

1. Name the changed artifact, affected consumers/dependencies, possible failure propagation, and the owner's accepted risk.
2. Choose the smallest representative rollout unit. Check shared databases, control planes, identity, network, and storage before claiming isolation.
3. Define consumer acceptance, forbidden outcomes, baseline/control, observation window, coverage, and explicit stop thresholds before exposure. Explain why those choices fit this workload.
4. Observe the approved unit before expanding it. Check common degradation as well as canary/control differences. Bind the gate to the current target/revision.
5. Halt expansion on failed criteria, contaminated comparison, drift, uncertain outcome, or missing evidence. No automatic retry follows. A unit you executed is reverted from the journal when its stop condition fires; the user chooses any other recovery.

The same logic applies to batch destruction: delete the smallest representative batch, verify, then widen.

The test: if this change is broken in the way you fear most, would the first unit show it before the second unit starts? If not, the unit is not representative or the gate watches the wrong signal.

You skipped this when the stop thresholds or observation window carry no reason tied to this workload, or the next unit starts, or its handoff exists, before the current unit's journal claims check `established`.

## Stop and limit

Do not copy a universal percentage, sample count, or waiting period. A quiet canary may never exercise a risky path. A shared dependency can affect every consumer even with one changed worker. If no isolated unit exists, state that limit and require an owner-selected strategy; do not fabricate a canary.
