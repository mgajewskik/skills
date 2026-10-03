---
name: infra-principle-bound-retries
description: Apply to any retry or polling loop, whether the agent runs it or writes it into IaC, scripts, pipelines, or services. Repeat only transient errors of repeat-safe operations, with exponential backoff, jitter, and a cap, at one layer; a permanent error goes to diagnosis.
disable-model-invocation: true
---

# Bound retries

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. This leaf governs read-only polling and probes, and the retry logic in code the agent writes. Repeating a live change is a new decision for the user under the contract.

A retry spends the dependency's capacity to buy one more chance. Make the purchase only for errors that can resolve by themselves, space the attempts so they cannot synchronize, and stop at a cap chosen in advance.

## Why

AWS Well-Architected: "Use exponential backoff to retry requests at progressively longer intervals between each retry. Introduce jitter between retries to randomize retry intervals. Limit the maximum number of retries." Its anti-patterns include retrying "errors with a clear cause that indicates lack of permission, configuration error, or another condition that predictably will not resolve without manual intervention" and "Retrying at multiple layers of your application stack in a manner which compounds retry attempts" ([REL05-BP03](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html)). Google SRE: "Always use randomized exponential backoff when scheduling retries", "Limit retries per request", and "avoid amplifying retries by issuing retries at multiple levels" ([Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)).

## Pattern

1. Classify the failure before repeating anything. Transient: timeout, throttling, connection reset, a documented retryable status. Permanent: permission denied, validation or configuration error, not found, quota exhausted. Read the tool's documented error codes; a permanent error goes to diagnosis.
2. Confirm the operation is safe to repeat: read-only, or idempotent under its documented contract for this version. A mutation whose completion is unknown goes to `infra-principle-reconcile-before-retrying` first.
3. Space attempts with exponential backoff and jitter, and cap attempts or elapsed time. Derive the cap from how long the operation normally takes; a rollout that converges in two minutes gets minutes of polling, not an hour.
4. Retry at one layer. Check what the SDK, CLI, provider, controller, or pipeline already retries before adding a loop around it.
5. At the cap, stop and report the last error, the attempt count, and the elapsed time. The next step is diagnosis.

The test: if the dependency stayed down for an hour, how many calls would this make, from how many layers?

You skipped this when a loop has no cap or a fixed sleep, a permission or validation error was repeated, or a retry wrapper sits around a tool that already retries.

## Stop and limit

An error that signals overload or throttling calls for longer backoff or stopping; more attempts add the load that caused it. A retry token or idempotency key covers only the operation it was issued for. This leaf decides how many times and how fast; whether a repeat is safe after a partial run is `infra-principle-reconcile-before-retrying`.
