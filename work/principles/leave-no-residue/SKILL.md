---
name: leave-no-residue
description: "Apply before a diagnostic that opens, mounts, starts, or repairs something, and before closing any diagnosis, repair, rollout, or incident. Preserve what the probe could destroy; remove or name everything the work left behind."
disable-model-invocation: true
---

# Leave No Residue

Done means the system holds the intended change and nothing else your work introduced. A debug flag left on, an open port-forward, or a silenced alert is a second, unreviewed change.

- Keep a residue list from the first action: temporary resources, tunnels and port-forwards, debug log levels and flags, scaled replicas, cordons, alert silences, maintenance markers, temporary files and copies on hosts.
- Before a diagnostic that can write (opening a database, mounting a volume, starting a service, running a repair tool), copy the WAL, journal, or logs, take a snapshot, or use a read-only mode. Closing a SQLite database checkpoints its write-ahead log and deletes the frames a forensic recovery needed.
- Before closing, revert or stop each item and hand over deletions you may not run. Re-check each with the probe that showed it.
- Name anything kept on purpose, with an owner and an expiry. Report what you found but did not create; it is not yours to clean.

The test: if someone listed the platform's state after you left, would they find anything you created, enabled, scaled, or silenced that your report does not name?
