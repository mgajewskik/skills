# Migration

For changing a contract, data format, platform, or ownership while old and new versions coexist or data persists across the change. The deliverable is a phased plan whose every intermediate state is supported and recoverable, run through Deploy, with the old path retired only on proven coverage. Data conversions and backfills are data writes: always irreversible and user-executed.

1. **Inventory both sides.** Readers, writers, deployed versions, stored formats, and independently deployed consumers, from runtime evidence (access logs, connection data, dependency listings), not only source search. Done when each consumer has an owner and a version.
2. **Design the phases.** Typically expand (new path added, old kept), migrate (writers and data move), contract (old path removed). For each phase name the allowed mixed states, the version you can recover to, and the one-shot effects (data conversions, notifications) that recovery cannot undo. Per **infra-principle-preserve-compatible-transitions**. Mark each step reversible or irreversible per the contract's checklist.
3. **Fix the done predicate.** A countable statement such as "zero reads on the old endpoint for the agreed window and every consumer on the new version". Never relax it.
4. **Pilot one unit end to end.** One consumer, shard, or host through every phase with full verification, to falsify the plan before scaling. Adjust the plan from what the pilot showed.
5. **Run each phase through Deploy.** Reversible non-production steps are journaled and executed; production steps outside a grant and irreversible steps are handed over. Verification covers old and new consumers in the same unit. Keep a decision trail and journal evidence per unit.
6. **Retire only on proof.** The contract phase needs the predicate met on current evidence. Removing the old path or data is a Teardown.

**Reply.** Phases with their state, pilot findings, the predicate's current count, consumers not yet moved, journal ids and fingerprints per executed step, and recovery limits in force for the current phase.
