# Pause safely

**You own a clean stop. Leave a checkpoint a cold-start agent can resume from.** Explicit only: on "keep going", "going to bed, keep going", or "don't stop", do not pause.

1. Stop at a safe boundary. Finish the current atomic step or back out of it. Start nothing new, and cancel any running subagents. A live change in flight gets its journal result line (`done`, `failed`, or still `pending` with what you observed) before you stop.
2. Take no irreversible action to pause. No PR, no push, no live change.
3. Make the work durable. Commit uncommitted edits as one commit on the current branch so nothing is lost, with the message from the **commit** skill and a subject that says the work is unfinished. If the tree is broken, say so in the commit body in one line. If the user asked for no commits, leave the edits uncommitted and list them in the note instead.
4. Write the resume note to `./.work-mode/resume-<slug>.md`: intent, what you were doing, progress and what's verified, current state (including journal ids not yet verified or reverted), next steps, key files, and gotchas. If a show-me-your-work trail exists, point at it instead of duplicating it.

**Reply.** Where you are in the loop, what's on disk versus still in your head (paths, no diff dumps), the commits you made and whether the tree is clean, open journal entries, and the first action on resume. This is a pause, not a final report.
