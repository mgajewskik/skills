# Session pickup

**You own the resume point. Read the prior trail, don't redo it.**

1. Locate the prior trail: a resume note under `./.work-mode/`, a show-me-your-work decision log, the work-mode journal (`journal.py list`), this project's session transcript ([host notes](../../references/host-notes.md) name the location; never read other projects' transcripts), or a pushed branch. Read the last messages and the note first, then scan back for the decision points. Parse a long transcript in a subagent and keep the reduced timeline in the main thread (**principle-guard-the-context-window**).
2. Reconstruct operational state. The branch and worktree, what already landed (`git log`, `git diff` against the base), journal changes still `pending` or not reverted, open todos, the decisions made. The prior trail is authoritative input for what was decided; resist re-deriving it.
3. Diff done vs pending. Compare what shipped against what was planned, name the resume point, do not redo completed work. Live state is the exception: a journal entry or handoff says what was done, not what holds now. Re-observe any live target before acting on it (**infra-principle-bind-evidence-to-context**).
4. Route the remaining work to the matching playbook and pick the verdict: continue the execution, ship a finished recommendation, ratify or override a prior conclusion, or postmortem a failed run. The pickup playbook ends here. The routed playbook owns the rest.
5. Verify the inherited claims against the original goal on the real artifact (**principle-prove-it-works**). A passing prior self-report is not the proof.

**Reply.** Where the prior session stopped, what you inherited vs redid (ideally nothing redone), the resume point, and the outcome.
