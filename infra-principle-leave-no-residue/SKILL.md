---
name: infra-principle-leave-no-residue
description: Apply before a diagnostic that opens, mounts, starts, or repairs something, and before closing any diagnosis, repair, rollout, or incident. Preserve state the diagnostic could destroy, keep a list of everything the work created or left changed, and remove or hand over each item before calling the work done.
disable-model-invocation: true
---

# Leave no residue

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Removing residue follows the contract's authority rule: journaled changes revert through the journal, and deleting any live resource or data is a user-executed destroy.

Work is done when the system holds the intended change and nothing else the work introduced. A repair that leaves a debug flag on, a tunnel open, or an incident marker set has a second, unreviewed effect.

## Why

InfraBench measured agents on infrastructure tasks: "Cleanup checks pass only 38.9% of the time (189/486): agents routinely leave behind exactly the residue the task asks them to remove", while functional checks passed 91.5% of the time. It also found "Tool-destructive diagnosis" in 72% of configurations: "agents open the database before preserving the write-ahead log, so SQLite auto-checkpoints and discards the very pages needed for recovery" ([InfraBench](https://arxiv.org/html/2608.11234)).

## Pattern

1. Start a residue list with the first action. It covers what the journal records and what diagnosis started: temporary resources, port-forwards and tunnels, debug log levels and flags, scaled replicas, cordons, alert silences, maintenance and incident markers, temporary files and copies on hosts, leftover config files from package or config tools.
2. Before a diagnostic that can write (opening a database, mounting a volume, starting a service, running a repair tool), preserve what it could destroy: copy the write-ahead log, journal, or logs, snapshot the volume, or use a read-only mode. When preserving needs a write on the target, it is a live change under the contract.
3. Before closing, walk the list. Revert journaled changes with `journal.py revert-plan`, end local processes you started, and hand over each live deletion as a destroy.
4. Re-check each item with the same probe that showed it, and record the result beside the negative-space claims (`infra-principle-verify-the-negative-space`).
5. Name anything kept on purpose in the reply with its owner and a revisit date or expiry.

The test: if someone read `journal.py list` and the platform's own listings after you left, would they find anything you created, enabled, scaled, or marked that your reply does not name?

You skipped this when a closing reply names no cleanup, or a diagnostic opened stateful data before its fragile state was preserved.

## Stop and limit

The list covers what this work created or changed. Things you found and did not create go to Teardown, never into cleanup. Some residue should stay, such as debug logging during an open incident; keep it with an owner and an expiry. Preserved copies can hold sensitive data, so keep them inside the target's own scope.
