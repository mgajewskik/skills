---
name: infra-design-recovery-first
description: "Apply before a change that touches availability, storage, data, access, or external side effects. Name the recovery path, what it restores and what it cannot, and the evidence it works, before executing."
disable-model-invocation: true
---

# Design Recovery First

Before changing anything you cannot trivially undo, know how you would get back, and prove that path works for this data and this target.

**Why:** Reverting source does not restore data, unsend a webhook, or undo a migration. A backup never restored is a hope. A recovery path that needs the thing you are changing (the firewall rule, the IAM policy, the control plane) fails exactly when you need it.

**Pattern:**
- Name the recovery destination, its owner, and the accepted time and data-loss limits
- Split reversible state from irreversible effects, and say which recovery covers which: rollback, restore, roll-forward fix, or compensation
- Find current evidence the path works for this artifact, data format, and size. A backup's existence alone is unverified
- Check what the recovery path depends on. A change must never cut off its own way back (locked out of SSH, IAM, or the API)
- With no verified recovery, state the limit and let the owner accept it or pick a safer change

**The test:** when was this recovery path last exercised for this data format and size, and what did it restore? "We have backups" with no answer is unverified.
