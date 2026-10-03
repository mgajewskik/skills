# Diagnostic lenses

Use this reference in the Debug playbook when the same source configuration can behave differently across hosts, processes, callers, containers, clusters, or namespaces. Everything here is read-only and governed by [the contract](contract.md).

## Follow the consumer

Locate the exact failing consumer before interpreting fleet-wide summaries. Record its host, container, or pod identity, process instance, caller identity, namespace or account, artifact revision, and observation time. Identifiers get reused (process IDs, pod names, IPs); bind an observation to a start time or another instance marker when that matters.

Trace source intent, effective input, loaded state, and consumer behavior, and ask where the first supported divergence occurs. Check precedence in the installed version rather than assuming the nearest file wins. Configuration can come from included files, service-manager or controller settings, command arguments, environment inputs, generated files, templates, defaults, and admission mutation.

Inspect only the non-secret setting or metadata the hypothesis needs. Process arguments, environment values, rendered manifests, and state files can contain credentials. Prefer sanitized selected fields or a user-provided signal when the source cannot be inspected safely.

Loaded state can differ from what is on disk or in the API because the process predates an edit, reads another path, inherited an older value, reads configuration only at startup, or a controller has not reconciled yet. These are hypotheses until instance-bound evidence supports them. Do not reload, restart, or resync to find out what was loaded.

## Choose the lens

Select the lens that separates the leading hypothesis from its strongest alternative. Inspect one boundary at a time rather than collecting an inventory.

| Lens | Discriminating questions | False shortcut |
| --- | --- | --- |
| Identity and permissions | Which user, group, service account, role, capability, or policy performs the failing operation? Which exact object denies it? | An administrator's success proves the service can act. |
| Isolation and namespace | Does the caller share the process's mount, network, user, cluster, or account context? Does the name resolve to the same object there? | A host observation proves container or pod behavior. |
| State and storage | Which resolved path, volume, mount, object version, lock, or lease does the consumer use? Which storage limit applies? | The object exists, so the consumer can use it; deleting it tests a stale-state theory. |
| Network and protocol | At which boundary do resolution, routing, connection, TLS, protocol, or authorization fail for this caller? | A listener or one successful probe from elsewhere proves the consumer path. |
| Resource pressure | Does a scoped window show the relevant process or quota limit coinciding with failure? | A global average proves or excludes a short local event. |
| Concurrency and ownership | Which writer last changed the shared object? Are observations from different revisions or actors? | A retry is safe because the operation looks idempotent. |
| Time | Do the failure, the change, the cache TTL, the certificate validity, and the reconcile interval line up? | Correlation in time proves cause. |

Match the observation method to the boundary. Resolution from the agent's machine does not establish resolution inside the consumer's namespace. Liveness does not establish readiness or useful work. An open port does not prove the expected revision serves it. A permission failure does not authorize changing permissions.

## Reproduce and compare

Use the original symptom and exact recurrence when available. For an absent or intermittent failure, take the smallest authorized comparison between a failing and a succeeding actor. Hold request, artifact, target, and timing as constant as practical, and list what changed and what stayed uncontrolled.

If a failure follows a restart, inspect the instance and selected persistent-state metadata before blaming code. Do not clear caches, locks, leases, files, or other state; existence does not prove staleness, and staleness does not prove removal is safe.

When repeated remedies fail under one premise, compare who holds the mismatch. A bounded count per affected actor can separate assignment, version, identity, timing, and shared-state explanations. An even distribution weakens an actor-specific hypothesis; it does not establish another cause.

Prefer existing telemetry with a scoped target, window, fields, and output limit. New logging, tracing, packet capture, traffic generation, profilers, or debuggers can write data, change performance, or capture secrets. If their effects are uncertain, describe the missing signal instead of collecting it.

## Worked example (offline)

Sanitized inputs supplied for inspection; not a command recipe.

| Evidence | Value |
| --- | --- |
| Source at revision `r12` | `timeout = 30` |
| Documented precedence for the installed loader | The override file wins over the source. |
| Override at `r12` | `timeout = 5` |
| Loaded-state record for instance `worker-41` | Loaded `timeout = 5` after `r12` became effective. |
| Consumer observation, same instance and window | Request times out after 5 seconds. |

The chain supports the override explaining this instance's 5-second timeout. It does not show every worker loaded the same value or that nothing else contributes. Without the loaded-state record, effective input is established and loaded state unverified. If the consumer observation came from another instance, the records cannot be joined into one chain. The next step is to find the override's owner and intended value, not to patch, delete, or restart.

## Reusable collectors

For repeated diagnosis, define the smallest evidence record a safe collector returns: the selected non-secret setting, its source revision, the consuming instance, its namespace or account, the probe location, the timestamp, the observed signal, and the claim it answers. Reuse a collector only after reading its implementation, version, target handling, writes, remote calls, and output bounds. A collector's exit code proves it ran; check its fields for relevance, freshness, and gaps.

Stop once another observation is unlikely to change the user's decision.
