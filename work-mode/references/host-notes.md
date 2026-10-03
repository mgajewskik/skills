# Host notes

`work-mode` is written for any agent harness. This page is the one place that maps its generic words to specific harnesses, and translates the Cursor-specific text that stays inside vendored pstack skills. Checked on 2026-10-03 against Claude Code 2.1.288 and codex-cli 0.160.0; check your installed version's help when something here does not match.

## Generic words used in work-mode

| work-mode says | Claude Code | Codex CLI | Other harnesses |
| --- | --- | --- | --- |
| Spawn a fresh subagent | The Agent tool; pass the full brief, since a fresh agent sees none of your context. | Its multi-agent feature (`codex features list` shows `multi_agent`). | Whatever spawns an isolated worker; without one, do the work in a separate session and paste the brief. |
| `work-agent` (delegates that run in work-mode) | `~/.claude/agents/work-agent.md`, linked from `~/.agents/agents/`; `claude --agent work-agent` keeps a whole session in work-mode. | `~/.codex/agents/work-agent.toml`, linked from `~/.agents/agents/`. | Grok: the same `work-agent.md` in `~/.grok/agents/`; `grok --agent work-agent` for a session, `subagent_type: work-agent` for a delegate. Its sandbox must be able to read the file. Elsewhere: paste the agent's instructions at the top of the brief. |
| The todolist | The built-in task list. | The plan tool. | A checklist in the reply, updated as steps finish. |
| Loop or wake later | `/loop` (fixed or self-paced interval). | No built-in loop: the user reruns the playbook, or schedules `codex exec` themselves. | Manual rerun. |
| The user runs a command in the session | `! <command>` puts its output in the conversation. | The user runs it and pastes the result. | Same. |
| Session transcripts (for `recall`, `reflect`, `show-me-your-work`) | `~/.claude/projects/<project>/*.jsonl` | `~/.codex/sessions/` | Ask the user where they are. |
| Drive a browser (UI repro and verification) | Standard Chrome through the `chrome-devtools` MCP server: navigate, click, fill, read the console and network, take screenshots. | The `chrome-devtools` plugin. | A Chrome DevTools MCP server when configured. Without one, a headless screenshot from an installed tool, and say the check is weaker. |
| Per-turn work-mode reminder | The `UserPromptSubmit` hook in work-mode's frontmatter. Invoking `/work-mode` registers it, and it then adds a one-line reminder to every later prompt in the session. `work-agent.md` declares the same hook, so a `--agent work-agent` session should get it too (untested). | No equivalent; retype `work-mode` when a new task starts. | Paste the reminder line from work-mode's frontmatter when a new task starts. |

## Reading vendored pstack skills here

Vendored pstack skills are installed unchanged apart from an added `agents/openai.yaml`, generated `skill-paths.md` pointers, and `user-invocable: false` on the `principle-*` leaves, so their Cursor-specific text stays. Read it like this:

| Vendored text | Read it as |
| --- | --- |
| Model slugs (`grok-4.7-xhigh-fast`, `claude-opus-5-5-max`, `gpt-5.6-sol-max`, `composer-*`) and role lines in `~/.cursor/rules/pstack-models.mdc` | The model from [Model routing](#model-routing). Its rules replace the skill's defaults and fallbacks. |
| `Task(...)`, `subagent_type: generalPurpose`, `run_in_background` | Spawn a subagent with the host's tool. |
| `environment: "cloud"`, `cloud_base_branch` (in `swarm`) | Ignore. Run every worker locally; work-mode never starts cloud agents. Workers that edit files get disjoint file ownership or separate git worktrees. |
| `Comment Sicko` (in `no-comments`) | A reviewer subagent briefed with that skill's rules. |
| `~/.cursor/projects/...`, `agent-transcripts` (in `recall`, `reflect`, `show-me-your-work`) | The host's transcript location from the table above. |
| `~/.cursor/skills/`, `~/.cursor/plugins/` (in `reflect` references) | This skill catalog. |
| "read the Principles section of `poteto-mode`" (in `figure-it-out`) | Read the Principles section of **work-mode**'s `SKILL.md`. |
| "Use the **how** skill", "run `why`", "read **principle-...**" inside a vendored skill | Do not call a skill tool. Read `<catalog>/<name>/SKILL.md` by path, per the rule at the top of work-mode's `SKILL.md`. |
| `control-ui` | Chrome through the `chrome-devtools` MCP server ([Drive a browser](#generic-words-used-in-work-mode)). |
| `control-cli`, Origin, Graphite, `/setup-pstack` | Not available. Drive the CLI or TUI yourself (run it, or a `tmux` session for a TUI), use HTTP or the test harness, or generate a project verification skill with **create-verification-skill**; use plain git and `gh` for stacks and PRs. |

None of this changes authority: a vendored skill's instruction to commit, push, comment, open a PR, or touch a live system still goes through [the contract](contract.md).

## Model routing

Every delegate takes its model from here, including the role lines and slugs that vendored skills name.

**Claude Code.** Set the Agent tool's `model` per delegate:

- `sonnet`: context-heavy exploration and mapping that needs little judgment. That means searching and locating code, reading files or docs and summarizing them, tracing call paths, and inventories. Role lines: `how explorer`, `why investigators`, the `recall` fan-out, and `swarm workers` on exploration or mapping slices.
- The parent model (omit `model`): everything else. That covers explainers and synthesizers, every reviewer, judge, runner, and lens (`interrogate`, `arena`, `architect`, `reflect`, the `show-me-your-work` reviewer), debugging, design, edits, and any delegate you hesitate over.

Seats a skill spreads across model families (claude, gpt, grok) all run on the parent model, each in a fresh context; say so in the reply. Effort suffixes (`-max`, `xhigh`) have no per-spawn setting here.

**Codex, Grok, and other harnesses.** Every role is `inherit-parent`: omit the model, and the delegate runs on the harness default.
