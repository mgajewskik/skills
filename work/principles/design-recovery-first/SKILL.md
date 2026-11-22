---
name: design-recovery-first
description: "Apply before a change that touches availability, storage, data, access, or external side effects. Name what recovery restores, what it cannot, and the evidence it works."
disable-model-invocation: true
---

# Design Recovery First

Before changing anything you cannot trivially undo, know how you would get back and prove that path works for this data and this target. Reverting source does not restore data, unsend a webhook, or undo a migration.

- Name the recovery destination, its owner, and the accepted time and data-loss limits.
- Split reversible state from irreversible effects, and name the recovery for each: rollback, restore, roll-forward fix, or compensation.
- The recovery path must not need the thing you are changing (the firewall rule, the IAM policy, the control plane). Never cut off your own way back.
- With no verified recovery, state the limit and let the owner accept it or pick a safer change.

The test: when was this path last exercised for this artifact, data format, and size, and what did it restore? "We have backups" with no answer is unverified.
