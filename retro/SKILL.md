---
name: retro
description: "Retrospective on the current or past agent sessions. Finds the mistakes, silent failures, and friction the environment caused, and fixes each class at the highest level that holds. Use for /retro."
disable-model-invocation: true
---

# Retro

Agents in this repo repeat mistakes, waste time, and finish work that only looks done. Change the environment so the next agent can't.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that looks done.

## Read the sessions

Default to the current session; read past ones when the user names them. Claude Code keeps sessions in `~/.claude/projects/<cwd, every non-alphanumeric character as "-">/<session-id>.jsonl`, with subagent runs and full large outputs under `<session-id>/subagents/` and `<session-id>/tool-results/`; Codex keeps them in `~/.codex/sessions/`, and work logs live in the project's `.work/`. Give more than two sessions to subagents that return cited incidents. Read the raw tool results, not the agent's summary of them, then recent commits, reverts, review comments, and comments that explain workarounds.

## Find the mistake classes

Collect every incident: a user correction; a **silent failure** (a claim no command backs, a swallowed error, a test that never exercised the change, a subagent report taken on trust, a skill or hook that didn't fire); a long search for a file or fact; a mistake a check could have caught; a fact the agent couldn't reach; an expensive or repeated tool call; a steering rule broken anyway. An existing check that is unwired or broken is the finding, not a reason to add another.

Group incidents into classes by their cause in the environment. A class counts once it has happened twice; a silent failure that produced a wrong result counts the first time. Rank silent wrong results first, then repeats, then wasted time.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types so the bad state can't be written.** If bad code still compiles, add a lint or CI check whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** Fix or delete any test that still passes when the behavior it checks breaks, or that fails when only the internals change.
4. **Give the agent the tool or access it lacked**: a fast single-test command, a teed log, read-only access to a service.
5. **Write words last, only for judgment calls.** Nothing fails when an agent skips them. Put standards in the reviewer's rules (or, with no reviewer, a standards file the agent instruction file points to); `AGENTS.md` and `CLAUDE.md` get pointers only. Write them through the **writing-for-agents** skill.

## Fix and prove

Present the classes in rank order in the reply format below, then fix the ones the user picks, one commit each. Prove each new check fails on a real past mistake. Run the same command locally and in CI. Exceptions go on the offending line with a reason, an expiry date, and a human's approval.

## Keep the rule table

Keep a table pairing each rule with what enforces it, in the file the reviewer reads. A rule already in the table and broken again is a repeat: move it up the ladder in the same change. Drop a rule once its mistake can't happen.

**Reply:** each class with its evidence, the level you picked, and why a higher level didn't work.
