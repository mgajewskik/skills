# Perf issue

**You own the measurement story. Plan, review, verify the numbers.** Tie every fix to a measurement; don't read source instead of measuring.

1. Capture a baseline on the matching surface (a profiler, a benchmark command, a timed request against a local or non-production target). Vet the baseline, and each later number, with the **benchmark-checklist** skill. Load generation against a shared or production system is a live action under [the contract](../../references/contract.md).
2. `how` to ground hypotheses. Don't claim a perf ceiling without running it first.
   Most fixes come from eight strategy families. Use them as hypothesis generators, not a checklist. A family earns an attempt only when the trace shows the signal it names.
   - **Elimination.** Before optimizing the hot path, ask whether it needs to exist: a computation nobody consumes, a feature gate that's always off for this user, a sync that redundantly mirrors state, a legacy path kept "just in case". The trace shows what's slow, never that it's deletable, so this family needs the `how` pass, not the profiler.
   - **Divide and conquer.** The dominant cost scales with input size. Split the work so each piece touches less (chunk, shard, prune the search space) or so independent pieces run in parallel.
   - **Caching.** The same computation or fetch repeats on identical inputs. Store and reuse the result. Name what invalidates it before claiming the win.
   - **Indirection.** The hot path does expensive work a cheaper intermediate could absorb: an index instead of a scan, a queue that shifts work off the interactive thread, a handle that lets a cheaper implementation swap in. Add the hop only when it removes more from the critical path than it adds.
   - **Batching.** Many small operations each pay a fixed overhead (RPC, query, syscall, draw call). Coalesce them to pay the overhead once per batch.
   - **Redundancy.** The wait hangs on one slow instance or attempt. Duplicate the work (replicas, hedged requests, speculative execution) and take the fastest result. The trace has to show the wait dominates and the system has headroom.
   - **Lazy evaluation.** Cost lands on results that are never used or not needed yet (eager init on the boot path, rendering offscreen items). Defer the work until first use.
   - **Scheduling.** The work must happen, but not during the interactive moment. Move it to where nobody is waiting: idle callbacks, a background warmup after boot, precompute before the user arrives, cleanup after the frame commits. The win is perceived latency, so measure the interactive path, not total work done.
3. Plan the fix from the trace. If it crosses a function boundary, `architect` first. Delegate implementation to a subagent with a tight scope, or own it when small. Review the diff. Capture a post-fix trace. Apply **principle-sequence-verifiable-units**, verifying each attempt before trying the next, and log each attempt (hypothesis, before, after, kept or reverted) with the **show-me-your-work** skill.
4. Parse and compare the artifacts (JSON or CSV into sqlite, diff). "Inconclusive" or wrong-surface is not a pass. Flag it. Apply **principle-explain-the-number** before reporting the delta.
5. Cite the measurement in the PR.
6. Run **Opening a PR** when the fix is meant for review.

For sustained improvement against a metric rather than a one-off fix, use the Hillclimb playbook.

**Reply.** Baseline number, post-fix number, delta, artifact path.
