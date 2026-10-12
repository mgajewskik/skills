---
name: infra-preserve-compatible-transitions
description: "Apply to protocol, endpoint, schema, serialization, or config changes that live through mixed versions or persisted data. Expand, migrate, then contract: readers before writers, and a recovery version that can read every intermediate state."
disable-model-invocation: true
---

# Preserve Compatible Transitions

When old and new versions run side by side, or old data persists, change contracts by expand and contract: add the new form beside the old, move readers then writers, and remove the old form only after proving nothing needs it.

**Why:** Deploys are never atomic. During a rollout, old and new code read each other's requests and data. Once new-format data exists, rolling back to code that cannot read it is no longer a rollback.

**Pattern:**
- Inventory readers, writers, deployed versions, stored formats, and independently deployed consumers
- Ship readers that understand the new form before any writer produces it
- For each stage, name the allowed mixed states and the version you would recover to
- Retire the old contract only on evidence: consumers migrated, old-format data gone. A source search alone is not coverage

**The test:** at every intermediate stage, if you had to roll back right now, would that version read the data and requests that exist at that moment?

This is the deployed-system counterpart of [migrate-callers-then-delete-legacy-apis](../migrate-callers-then-delete-legacy-apis/SKILL.md): when every consumer is owned and ships together, delete in one wave; when they deploy independently, transition.
