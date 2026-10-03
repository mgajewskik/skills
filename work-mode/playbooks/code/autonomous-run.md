# Autonomous run

**You own the exit condition. Define done, then drive to it without stopping.**

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, benchmark under N ms, every review thread triaged with a fix pushed or a reply drafted for the user).
2. Pick the wake mechanism. Use the harness's loop feature when it has one ([host notes](../../references/host-notes.md)): an event to watch (CI, a ref advancing) gets a watch that wakes you on the event, with a long time-based heartbeat as fallback; no event gets a fixed interval sized to when the result is worth re-checking. Without a loop feature, run until the predicate or a blocker, then leave a resume note per Pause safely so the user can rerun.
3. Each iteration makes the smallest change the evidence justifies, verifies it against the predicate, commits if it advanced, discards changes that didn't help. Belt-and-suspenders that "might help" gets reverted, not left to ride. Sequence the work via **principle-sequence-verifiable-units**, verifying each unit before the next instead of batching checks at the end.
4. Mid-run discoveries are yours. Address related bugs, flaky verifiers, tooling failures, and fixable drift yourself, in their own commits, then return to the predicate. Do not park reversible work for the user. Autonomy never widens authority: anything [the contract](../../references/contract.md) makes user-executed (irreversible actions, production changes without a grant, pushes beyond the user's working branch, messages) goes into a list for the user while you keep working on the rest. Surface genuine product or preference calls no experiment can settle, and real dead ends.
5. Checkpoint every iteration with the **show-me-your-work** skill: a row for what changed and whether the predicate moved. Live changes also go in the work-mode journal.
6. Stop when the predicate is met. A plateau is not a stop, so keep going and pivot your approach to push past it. Surface a genuine dead end rather than spinning, and never relax the predicate to declare victory.

**Reply.** The exit condition, iterations run, what landed, what was discarded, journal entries made, actions waiting for the user, final predicate state.
