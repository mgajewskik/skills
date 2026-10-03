# Vendoring

Two places hold upstream skills, and they never reference each other.

```text
~/.agents/vendor/                  read-only reference, full upstream clones
  cursor-plugins/                  github.com/cursor/plugins (pstack, Poteto Mode)
  matt-skills/                     github.com/mattpocock/skills
  pstack/                          frozen older copy, not a git repo
  README.md
        |
        |   (nothing in the catalog reads from here)
        |
~/.agents/skills/                  the catalog every harness reads
  scripts/update-skills.sh  ---->  fetches listed skills from GitHub into the catalog
```

`vendor/` is for reading: browsing Poteto Mode's playbooks, diffing an upstream change, borrowing an idea. Update it with `git -C ~/.agents/vendor/<name> pull` when you want. `scripts/check_work_mode.py` fails if any skill or catalog script mentions it; only these docs may.

## update-skills.sh

The script keeps a list of GitHub tree URLs. For each one it sparse-clones the repository and replaces the skill's directory in the catalog with the fresh copy. Each skill keeps the invocation setting its upstream chose: there is no per-entry override.

Claude Code reads the frontmatter flag `disable-model-invocation: true`; Codex reads `agents/openai.yaml`. So for every skill whose upstream frontmatter is user-only and that ships no `openai.yaml`, the script writes one with `allow_implicit_invocation: false`, and prints a line:

```text
Updated: unslop
Codex policy: unslop: wrote agents/openai.yaml (user-only upstream)
```

An upstream `openai.yaml` is never overwritten. When a vendored skill names other user-only vendored skills, the script also writes a `skill-paths.md` with their paths and adds a one-line pointer to it in `SKILL.md` and in every other file that names one. Both are regenerated identically on every run. Nothing else in a vendored skill is edited. Its Cursor-specific text (model slugs, cloud workers, transcript paths) stays, and `work-mode/references/host-notes.md` says how to read it.

The run is idempotent: a second run against the same upstream leaves every file byte-identical.

## Common tasks

- **Add a skill.** Append its tree URL to `SKILLS`, run the script, read the printed lines, and review the new directory with `git diff` and `git status`.
- **Update everything.** Run the script, then review `git diff`. Upstream changes show up as ordinary diffs, including a change to a skill's invocation setting.
- **Change a vendored skill's content or invocation setting.** Don't edit the catalog copy; the next run overwrites it. Change it upstream, or fork it into a skill of your own with a different name.

## Files adapted from upstream

Some work-mode files start from upstream text and carry local edits, so `update-skills.sh` does not refresh them. They were taken from `github.com/cursor/plugins` at commit `23e4138` (2026-10-03).

| work-mode file | Upstream source | Local edits |
| --- | --- | --- |
| `work-mode/playbooks/code/babysit.md` | `pstack/skills/poteto-mode/playbooks/babysit.md` | Verbatim base. Edited only where the contract or missing tooling forces it: no Origin, queued stacks, Autopilot, or Shipping (step 1 says a GitHub MCP server works too, and falls back to plain git for other remotes); merges, replies, thread resolution, PR opening, and other-branch pushes are the user's; the watcher is `watch_pr.py` with its exit codes; CI reruns follow the contract; threads waiting on a drafted reply do not stop CI work. |
| `work-mode/references/bugbot-triage.md` | `pstack/skills/poteto-mode/references/bugbot-triage.md` | Verbatim except the playbook path and "draft a reply for the user" instead of replying. |
| `work-mode/scripts/watch_pr.py` | `pstack/skills/poteto-mode/scripts/watch-pr/` (TypeScript) | Python port of single and stack modes; no queued mode or Origin; default one-hour deadline; waits while mergeability is UNKNOWN; fork PRs are never stack members (the TS version can adopt a fork's `main` as a parent). |
| the other 15 `work-mode/playbooks/code/*.md` | `pstack/skills/poteto-mode/playbooks/<same name>.md` | Adapted more freely; see each file. |

To pick up an upstream change, update the reference clone and read what changed since the recorded commit, then apply the parts that still fit:

```sh
git -C ~/.agents/vendor/cursor-plugins pull
git -C ~/.agents/vendor/cursor-plugins diff 23e4138..HEAD -- pstack/skills/poteto-mode/playbooks pstack/skills/poteto-mode/references pstack/skills/poteto-mode/scripts/watch-pr
```

Then record the new commit here.

## User-only skills

- `work-mode` and the 14 `infra-principle-*` leaves: written here, user-only, read by path from work-mode.
- Every pstack skill, because upstream ships them that way; work-mode reads the ones it needs by path.
- Matt Pocock's `grill-me`, `grill-with-docs`, `wayfinder`, and `to-questionnaire`, because upstream ships them that way (with their own `openai.yaml`).
