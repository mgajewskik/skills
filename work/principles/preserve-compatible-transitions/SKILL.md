---
name: preserve-compatible-transitions
description: "Apply to protocol, endpoint, schema, serialization, or config changes that live through mixed versions or persisted data. Expand, migrate, then contract, readers before writers; every stage keeps a version you can roll back to."
disable-model-invocation: true
---

# Preserve Compatible Transitions

When old and new versions run side by side, or old data persists, change contracts by expand and contract. Add the new form beside the old, ship readers that understand it before any writer produces it, and remove the old form only after proving nothing needs it. Once new-format data exists, rolling back to code that cannot read it is no longer a rollback.

- Inventory readers, writers, deployed versions, stored formats, and independently deployed consumers.
- For each stage, name the allowed mixed states and the version you would recover to.
- Retire the old contract only on evidence: consumers migrated, old-format data gone. A source search alone is not coverage.

**The test:** at every intermediate stage, if you had to roll back right now, would that version read the data and requests that exist at that moment?

When every consumer is owned and ships together, delete the old form in one wave instead; transition only when they deploy independently.
