# Extending work-mode

Most changes are one file plus one line in the router. The checker tells you when the two disagree.

## Add a playbook

1. Write `work-mode/playbooks/code/<name>.md` or `work-mode/playbooks/infra/<name>.md`. Follow the existing shape: a title, one paragraph naming the deliverable and what stays off-limits, numbered steps that each end in something checkable ("Done when ..."), and a `**Reply.**` line.
2. Any step that touches a live system or a git remote points at the contract instead of restating it. Never give a playbook more authority than the contract does.
3. Add one line to the matching list in `work-mode/SKILL.md`: `- **Name.** When it applies. \`<name>.md\`.`
4. Add the name to `CODE_PLAYBOOKS` or `INFRA_PLAYBOOKS` in `scripts/check_work_mode.py`.
5. Run the checks below.

## Add a principle

1. Create `infra-principle-<name>/SKILL.md` with the leaf anatomy from [principles](principles.md): an `Apply when ...` description, `disable-model-invocation: true`, the contract pointer, `## Why` with a linked source, `## Pattern`, `The test:`, `You skipped this when`, and `## Stop and limit`. Add `agents/openai.yaml` with `policy: allow_implicit_invocation: false` so Codex keeps it user-only too.
2. Add one line under **Infra** in the router's Principles index: `- **infra-principle-<name>**. When it applies.`
3. Name it from the playbook steps where it should fire.

A rule you keep restating in prose is a candidate for a check instead (`principle-encode-lessons-in-structure`): a test in `test_scripts.py`, a refusal in `journal.py`, or a rule in `check_work_mode.py`.

## Add a script

Scripts live in `work-mode/scripts/` with a `test_<name>.py` next to them. Use the standard library and existing CLIs (`gh`, `git`) first. When a third-party package earns its place, declare it in the script's inline metadata and run the script through uv, never with a separate install:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["<package>==<version>"]
# ///
```

`watch_pr.py` carries this header with `dependencies = []`, so it also runs with plain `python3`.

## Change the authority rule

Change `work-mode/references/contract.md` first, then the short form in `SKILL.md`'s Authority section, then this repository's docs, then your global `CLAUDE.md` and Codex `AGENTS.md`, so the agent behaves the same with and without the mode. If the change can be enforced, add a refusal to `journal.py` and a test that fails without it.

## Run the checks

```sh
python3 scripts/check_work_mode.py                                # structure, index, links, leaf anatomy
python3 -m unittest discover -s work-mode/scripts                 # journal and handoff linter tests
bash scripts/update-skills.sh && git status --short               # after touching the update script
```

The checker is read-only and exits 1 with one line per problem: a playbook on disk but not in the router (or the reverse), an index entry with no installed skill, an installed principle missing from the index, a leaf missing an anatomy part, a handoff template out of step with the linter, a skill named in bold that is neither vendored nor part of work-mode, a reference to a removed skill or to `~/.agents/vendor`, a broken or out-of-package link, an unbalanced code fence, or a non-ASCII diagram.

The checker only proves structure. Whether the mode makes the agent behave better is an eval question: use the Eval playbook, with a blinded judge and fixtures that include an unsafe and an ambiguous request.
