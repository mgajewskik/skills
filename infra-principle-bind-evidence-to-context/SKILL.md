---
name: infra-principle-bind-evidence-to-context
description: Apply when comparing infrastructure observations, reusing deployment evidence, or diagnosing across hosts, namespaces, identities, revisions, or time windows. Bind every consequential claim to the context actually observed; reject stale or mismatched evidence.
disable-model-invocation: true
user-invocable: false
---

# Bind evidence to context

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Keep evidence narrowly scoped and non-sensitive. Unknown targets are production; context gathering grants no mutation authority.

## Why

Google explains that server measurements can miss client problems and aggregation can hide bursts and tail latency. [Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) supports the importance of observation location and window. The context record and renewal rule below are our adaptation, not a prescribed Google schema.

## Pattern

1. Attach target/environment, artifact revision where relevant, caller identity, namespace/process instance, probe location, timestamp, window, and coverage to consequential observations.
2. Before joining two observations, establish that their contexts answer the same claim. Mark uncontrolled differences explicitly.
3. Distinguish source revision from the running revision. Bind process IDs to instance/start information when reuse matters.
4. On a changed target, artifact, dependency, identity, or relevant baseline, identify which evidence, review, and approval need renewal. Never silently reuse a verdict for another revision.
5. Keep the sanitized signal and resolving pointer. Missing context limits the claim; request the smallest missing metadata rather than raw environments or unrestricted logs.
6. Bind approvals and grants the same way. The user approves an exact handoff, identified by its fingerprint (`work-mode` `scripts/check_handoff.py fingerprint`), and the approval is a journal `approval` entry keyed by that fingerprint (`scripts/journal.py`). An edited handoff, or a fresh plan in place of the reviewed one, has a new key and starts unapproved. A production grant covers only the environment, scope, and change types it names, and only this session.

The test: if this observation, verdict, or approval had come from the neighbouring host, the previous revision, or yesterday, would anything in the record show it? If not, the record cannot be joined to the claim.

You skipped this when an evidence pointer or journal entry has no target, revision, or time, or when an approval is recorded against anything other than the fingerprint the user read.

## Stop and limit

A successful request from host B/r16 cannot validate host A/r17. An average may conceal a failing caller population. Do not invent a universal evidence expiry time; freshness depends on the change and claim. Context improves applicability, not truth by itself. Evidence from a broken collector remains suspect.
