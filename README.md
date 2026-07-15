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

OpenCode discovers compatible skills from this location automatically. External
skills listed in `scripts/update-skills.sh` can be refreshed by running that
script from a trusted checkout; it replaces only the listed skill directories.

The portable skill history was migrated from
[mgajewskik/opencode-config](https://github.com/mgajewskik/opencode-config),
with its original authorship, dates, messages, and file evolution preserved in
rewritten commits.

## License

Original content in this repository is covered by the root `LICENSE`.
Vendored or third-party skills remain subject to their upstream licenses or
terms.
