# Drift

For desired state (source) and live state disagreeing. The deliverable is a per-field decision about which side wins, carried out as source changes, reversible live changes logged with their revert and executed, or user-executed handoffs, and a re-check showing the drift gone without new drift. Reverting live state to source is a live change and can undo a deliberate emergency fix.

1. **Scope the comparison.** Source revision, target, and the bounded set of fields compared, with the tool and version that produced the comparison. Read what the comparison tool writes: some refresh operations update stored state. Save the drift list as an artifact. Done when the drift list is reproducible by rerunning one read-only command.
2. **Find every writer.** For each drifted field: declared owner, reconcilers, automation, and recent human changes, including your own earlier changes. Name which writer wins the next reconcile (**[verify-the-negative-space](../principles/verify-the-negative-space/SKILL.md)**).
3. **Classify each difference.** Undocumented live fix, platform default or server-side mutation, out-of-band manual change, partial or failed earlier apply, or an upstream provider change. Log evidence for each; unknown stays unknown.
4. **Decide direction with the user.** Adopt into source, revert live to source, transfer ownership, or ignore a field the source should never have managed. The user chooses per field; you recommend with the evidence.
5. **Carry it out.** Adopt-into-source goes through Implement. Revert-live goes through Live modify: reversible fields outside production (or inside a grant) are logged with their revert and executed, the rest handed over. Any removal goes through Teardown.
6. **Re-check.** Rerun the step 1 comparison: decided fields show no difference, no new fields drifted, consumers unaffected. Log the result as evidence.

**Reply.** Drift found (fields and classification), decision and owner per field, what was changed or handed over, and the re-check result.
