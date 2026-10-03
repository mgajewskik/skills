# How work-mode works

work-mode keeps the always-loaded part small and loads detail only when it is needed. Most of what makes it work is a handful of rules about when to read what, and what has to be true before a claim counts.

## Layers

```text
layer             loaded when                    holds
---------------   ----------------------------   ------------------------------------------
router            you type work-mode             triggers, principle index, authority,
                                                 subagent and reply rules, playbook list
playbook          a task matches it              numbered steps, each ending in a check
principle leaf    its trigger fires              one rule: why, pattern, test, skip sign
reference         a step points at it            contract, handoff, journal, host notes,
                                                 diagnostic lenses, stack examples
script            a step runs it                 journal.py, check_handoff.py
```

The router is a table of contents with teeth. Each line in its index names the principle and when it applies, then adds the limit that holds on live systems (pstack principles) or the rule itself (infra principles). The full reasoning stays in the leaf, so a simple task does not pay for fourteen infra rules it never touches.

## The todolist rule

When a task matches a playbook, the agent copies that playbook's steps into its todolist verbatim, before any task-specific items. A step it decides to skip stays in the list as `skip: <reason>`.

This makes skipping visible. You can read the list and see which steps ran, which did not, and why. Silent skipping is the most common way an agent drifts from a procedure, and a list that keeps the skipped item is the cheapest fix.

## The citation rule

The reply names each principle that shaped a decision and what it changed. The agent may cite only principles whose leaf it read in full this session. A citation from memory is a guess dressed as a reference, so it does not count.

## Routing

```text
task
  |
  +-- application code ---------------------> playbooks/code/
  +-- live system or infrastructure source --> playbooks/infra/
  +-- mixed ("fix the module, roll it out") -> start where the failure is observed,
  |                                            hand over at the boundary with exit evidence
  +-- large or cross-cutting, even if Feature
  |   fits; stepped-away work; nothing fits --> the figure-it-out skill
  +-- "plan this before we build it" --------> the plan skill (the plan file is the deliverable)
  +-- a concept question with no target -----> answer with cited sources, no playbook
```

Removal wording ("clean up", "prune", "tear down") sends live resources, data, access, and environments to Teardown. Cleaning up code is Refactoring.

Some triggers fire on any task, whichever playbook matched: `how` before a nontrivial change or judgment, `architect` for code that crosses a function boundary, `swarm` or `arena` for parallel fan-out, `interrogate` for a contested design, the throughput checkpoint for multi-step work, driving the real surface for repros, Babysit for any PR-status request, skeptical triage for review-bot comments, and the `commit` skill for every commit message. The trigger table in `SKILL.md` lists them all.

## Staying on

Invoking `/work-mode` in Claude Code registers a `UserPromptSubmit` hook from the skill's frontmatter. For the rest of the session, every prompt gets a one-line reminder to match a playbook and apply the triggers on a new task, and to skip that on a casual turn. A new `claude` session starts without it. Codex has no equivalent, so retype `work-mode` when a new task starts there.

Code and infra playbooks stay separate on purpose. Infra Debug is strictly read-only and never turns into a fix; code Bug fix reproduces and fixes in one flow. Merging them would blur that line.

## Subagents

- Delegates run as `work-agent` (`~/.agents/agents/work-agent.md` for Claude Code, `work-agent.toml` for Codex). Its only job is to read work-mode's `SKILL.md` first and route the brief to a playbook, so a delegate works under the same rules as the lead. It is the port of Poteto's `poteto-agent`.
- Fresh by default, with the full brief and every later directive, so nothing is lost between rounds.
- The lead owns the output: it reviews the diff and writes its own summary.
- A reviewer is never the author, gets criteria and evidence rather than the author's conclusion, and runs on a different model when the host offers one.
- Live actions, live probes, and secret-bearing content are never delegated.
- Everything runs locally. Cloud parameters in vendored pstack skills are ignored; `references/host-notes.md` says how to read them.

## The reply

- Lead with what changed for the consumer, then for the next maintainer.
- Every claim carries a label in the same sentence: `established`, `failed`, or `unverified` for outcomes; measured, inferred, or guess for causes.
- Consequential claims point at their evidence: target, revision, time.
- One closing status line: playbook, state, leading risk, one next action.

The labels are there so you can scan for what was actually shown, not because the prose looks rigorous.
