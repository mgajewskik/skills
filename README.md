# Agent skills

Reusable agent skills shared across my local coding tools.

Each skill lives directly at the repository root:

```text
<skill-name>/
└── SKILL.md
```

Clone the repository to `~/.agents/skills`:

```bash
git clone https://github.com/mgajewskik/skills ~/.agents/skills
```

Compatible local agents discover skills from this shared location. External
skills listed in `scripts/update-skills.sh` can be refreshed by running that
script from a trusted checkout; it replaces only the listed skill directories.

## work

`work` is the work discipline for code, config, and infrastructure tasks:
playbooks, engineering principles, and a `.work/` log for live changes and
their reverts. See [work/SKILL.md](work/SKILL.md). Its principles are vendored
from pstack by `work/scripts/update.sh`.

## License

Original content in this repository is covered by the root `LICENSE`.
Vendored or third-party skills remain subject to their upstream licenses or
terms.
