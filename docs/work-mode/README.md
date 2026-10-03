# work-mode

`work-mode` is one operating mode for code and infrastructure work. It sends each task to a playbook, loads a principle only when its trigger fires, and decides for each action who runs it: the agent or you.

It never turns on by itself. Type `work-mode` (or `/work-mode`) at the start of a task you want done with this discipline. Casual questions don't need it. To keep it on for a whole session, start Claude Code as the work agent: `claude --agent work-agent`.

## The loop at runtime

```text
you type work-mode + a task
        |
        v
SKILL.md (router)  -- triggers table, principles index, authority, reply rules
        |
        v
match a playbook  -- code/ or infra/; steps copied into the todolist verbatim
        |
        +--> a trigger fires ------> read ../<leaf>/SKILL.md by path, in full, then cite it
        |
        +--> a live action --------> references/contract.md classifies it
        |                               |
        |                               +-- reversible: snapshot -> journal -> run -> verify
        |                               +-- irreversible / prod without grant:
        |                                     handoff -> you approve and run -> agent verifies
        v
reply: consumer-first, every claim labeled, one status line, one next action
```

## Reading order

1. [How it works](how-it-works.md). The layers and the rules that tie them together.
2. [Authority and revert](authority-and-revert.md). Who runs what, the journal, and a worked example end to end.
3. [Principles](principles.md). Where each principle comes from and when it fires.
4. [Trust](trust.md). Why the agent's own "done" is not enough, and what the scripts enforce.
5. [Vendoring](vendoring.md). How upstream skills reach this catalog.
6. [Extending](extending.md). Adding a playbook or a principle, and running the checks.

## Where things live

```text
work-mode/
  SKILL.md                  router (user-triggered only)
  agents/openai.yaml        tells Codex not to invoke it implicitly
  playbooks/code/*.md       16 playbooks for application code
  playbooks/infra/*.md      8 playbooks for live systems and infrastructure source
  references/               contract, handoff, journal, host notes, and lookup pages
  scripts/                  journal.py, check_handoff.py, watch_pr.py, and their tests
infra-principle-*/          11 production principles, user-only, read by path
principle-*/ and others     pstack skills (user-only upstream), fetched by scripts/update-skills.sh
scripts/check_work_mode.py  structural checker for all of the above
```
