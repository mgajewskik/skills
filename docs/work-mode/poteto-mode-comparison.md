# Compared with Poteto Mode

work-mode started as a port of Poteto Mode from `github.com/cursor/plugins` at commit `23e4138`. This page records what work-mode does differently, so you can restore any item by name. [Vendoring](vendoring.md) lists the files adapted from upstream.

## What work-mode adds

The [authority contract](../../work-mode/references/contract.md), the journal and revert path, the eight infra playbooks, and the 14 `infra-principle-*` leaves have no upstream equivalent. Every pstack principle in the router carries a "Live:" limit for live systems.

## Dropped on purpose

These cuts follow from one rule: the agent never merges, publishes, or messages people on its own. The one exception is replies on a PR you asked it to babysit.

| Upstream | work-mode | To bring it back |
| --- | --- | --- |
| Team chat, ticket updates, and starting evals proceed without asking. | User-executed. | A contract exception for the message class, like the Babysit replies rule. |
| Opening a PR | The agent prepares the branch and body, and you run `gh pr create`. | A contract exception for PR creation. |
| Shipping playbook: land a verified green stack bottom-up. | Removed. Merges are always yours. | Port `shipping.md` and allow merges under a session grant. |
| Autopilot-full: one owner per PR, build through merge. | Removed. | Needs merges and pushes to many branches. Same as Shipping. |
| Autopilot-stack: build a reviewed stack that you land. | Removed. | The closest fit, since you still land the stack. It needs pushes to every stack branch, which a session grant naming those branches could allow. |
| Orchestrate: a multi-day program with `orch.ts` and a coordinator. | Removed. | Port `orchestrate.md` and its scripts. Large work goes to `figure-it-out` meanwhile. |

## Dropped as not relevant here

- Visual parity, a pixel-exact UI comparison playbook.
- Worktree and simulator cleanup.
- `principle-experience-first`. It stays installed but is not indexed.
- Origin, Graphite, `/setup-pstack`, `control-cli`, and `deslop`, which are not installed. [Host notes](../../work-mode/references/host-notes.md) map what remains.

## Restored on 2026-10-03

- **Per-turn reminder.** Upstream marks Poteto Mode as a mode with a `reminder:` line. work-mode declares a `UserPromptSubmit` hook in its frontmatter instead. Invoking `/work-mode` registers it for the rest of the Claude Code session. `work-agent.md` declares the same hook, so a `claude --agent work-agent` session should get the reminder too (expected from the docs, untested). Keep the two reminder lines identical.
- **Router triggers.** These fire on any task again, not only inside a matched playbook: `how`, `architect`, `swarm` and `arena`, `interrogate`, the throughput checkpoint, driving the real surface for repros, Babysit for any PR-status request, and skeptical triage of review-bot comments.
- **Full-autonomy defaults.** Under "run until done", the agent decides the calls the request covers. For a call only you can make, it applies a default and explains it.
- **figure-it-out override.** Large or cross-cutting work goes to `figure-it-out` even when Feature fits. A request for a plan goes to your `plan` skill.
- **Babysit replies.** On a PR you asked it to babysit, the agent replies to review threads and resolves the review-bot threads it fixed or dismissed. `watch_pr.py` counts a thread whose latest reply is the `gh` user's as awaiting the reviewer, so the loop moves on and never replies twice.
- **Browser driving.** `control-ui` maps to Chrome through the `chrome-devtools` MCP server.

Two changes have no upstream equivalent. Teardown now fires only for removing live resources, data, access, or environments, so "clean up this module" stays a refactor. Every commit message comes from your `commit` skill.

## Still missing

| Gap | Effect | To bring it back |
| --- | --- | --- |
| Model diversity | `interrogate`, `arena`, and the Eval judge run every seat on the parent model, so a judge grades its own model's work. | Route one seat to another model family in [Model routing](../../work-mode/references/host-notes.md#model-routing). |
| Multi-phase plan playbook and `check-plan.mjs` | No audited skeleton for multi-PR programs with unit, live, and perf boxes per PR. Your `plan` skill covers part of it. | Port `multi-phase-plan.md` and the validator, with local swarm lanes and merges left to you. |
| Comments section | Lost rules: no step-narrating comments in test and verify scripts, and the comment rule covers a delegate's diff. Feature step 4 keeps "comments only for a non-obvious why". | Add a short Comments section to `SKILL.md`. |
| `no-comments` before every commit | It runs only in Opening a PR. Skipped by choice. | A trigger row: before any commit, the `no-comments` skill. |
| `deslop` before commit | No stand-in. | Claude Code's built-in `/simplify` does similar cleanup. |
| Reply rules | Lost: "terse is not an excuse to drop content" and "write clean while drafting". `unslop` still bans long dashes and mid-sentence colons. | Two bullets in Writing the reply. |
| Reminder in Codex | Codex sessions get no per-turn reminder. | Codex has no skill or agent hook for it today; retype `work-mode` when a new task starts. |
