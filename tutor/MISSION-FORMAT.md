# MISSION.md Format

`MISSION.md` lives at the current directory root. It is the only compass: why the user is learning, what success looks like, and what is out of bounds. Every tutoring decision (what to teach next, hands-on vs teach-back, what counts as evidence) traces back to this file.

## Template

```md
# Mission: {Topic}

## Why
{1-3 sentences. The concrete real-world goal the user is chasing. What changes in their life or work when they have this skill? Avoid abstract framings like "to understand X"; push for the underlying outcome.}

## Success looks like
- {A specific, observable thing the user will be able to do}
- {Another specific thing}
- {…}

## Constraints
- {Time, budget, prior commitments, learning preferences, environment, anything that bounds the approach}

## Out of scope
- {Adjacent topics the user explicitly does not want to chase right now}
```

## Rules

- **One mission per workspace.** Related topics in this directory are units under this mission, not additional missions. An unrelated goal is a different directory.
- **Concrete over abstract.** "Ship a Rust CLI to my team" beats "learn Rust." "Run a half marathon by October" beats "get fitter."
- **Push back on vagueness.** If the user cannot articulate why, finish intake before writing this file. A bad mission is worse than no mission.
- **Revise when reality shifts.** When the user's goal moves, update this file; do not leave a stale mission steering future sessions.
- **Keep it short.** If `MISSION.md` runs past a screen, it has stopped being a compass and started being a plan.
