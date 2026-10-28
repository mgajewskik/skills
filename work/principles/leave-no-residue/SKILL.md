---
name: leave-no-residue
description: "Apply before a diagnostic that opens, mounts, starts, or repairs something, and before closing any diagnosis, repair, rollout, or incident. Preserve what the probe could destroy; remove or name everything the work left behind."
disable-model-invocation: true
---

# Leave No Residue

Done means the system holds the intended change and nothing else your work introduced. The functional check passes while the debug flag stays on, the port-forward stays open, and the alert stays silenced; each is a second, unreviewed change.

- Keep a residue list from the first action: temporary resources, tunnels and port-forwards, debug log levels and flags, scaled replicas, cordons, alert silences, maintenance markers, temporary files and copies on hosts.
- Before a diagnostic that can write (opening a database, mounting a volume, starting a service, running a repair tool), copy the WAL, journal, or logs, take a snapshot, or use a read-only mode. Diagnosis destroys evidence too: reading a SQLite database and closing it checkpoints the write-ahead log into the main file and deletes it, along with the frames a forensic recovery needed.
- Before closing, walk the list: revert, stop what you started, hand over deletions you may not run. Re-check each item with the same probe that showed it.
- Name anything kept on purpose, with an owner and an expiry.

**The test:** if someone listed the platform's state after you left, would they find anything you created, enabled, scaled, or silenced that your report does not name?

Things you found but did not create are not yours to clean; report them.
