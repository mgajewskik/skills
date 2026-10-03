---
name: infra-principle-preserve-compatible-transitions
description: Apply to protocol, endpoint, schema, serialization, or configuration changes across mixed versions or persisted data. Verify intermediate reader/writer states and the permitted recovery version before activation or retiring an old contract.
disable-model-invocation: true
user-invocable: false
---

# Preserve compatible transitions

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Live migration phases follow the contract's authority rule. Retiring an old path or its data is a deletion and stays user-executed.

## Why

AWS describes preparing readers before activating new writers and limits rollback once new-format data exists. [Rollback safety](https://d1.awsstatic.com/builderslibrary/pdfs/ensuring-rollback-safety-during-deployments.pdf). The following compact contract applies that reasoning to infrastructure changes.

## Pattern

1. Inventory readers, writers, deployed versions, stored formats, and independently deployed consumers.
2. Specify allowed mixed states, activation prerequisites, and the recovery version for each stage.
3. Verify compatibility before activation. Keep old contracts while relevant consumers or data require them.
4. Prove retirement coverage before removing compatibility. Missing inventory is unverified, not permission to remove.

The test: at every intermediate stage, if you had to recover to the previous version right now, would it read the data and requests that exist at that moment?

You skipped this when the plan names the old and new versions but no intermediate state, or retires the old path on a source search alone.

## Stop and limit

Individual endpoints passing independently does not prove safe transition. An old artifact may be incompatible with new persisted state. Two phases are one mechanism, not a requirement for every change. A coordinated local refactor may retire its old path immediately when every consumer is owned and verified.
