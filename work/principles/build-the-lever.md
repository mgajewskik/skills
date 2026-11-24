# Build the Lever

When the work isn't trivial, build the tool that does it or proves it (a codemod, script, generator, or rerunnable check) instead of doing it by hand. The bar is triviality, not repetition. Skip the tool only for a couple of obvious edits.

- Do the first unit by hand, then build the tool and prove it by rerunning it on that unit. Make it safe to rerun.
- A deterministic tool beats fan-out. When you do fan out, give delegates a brief referencing the `work` skill and playbook (with explicit criteria, scope, and fences) instead of inventing ad-hoc delegate skills.
- Keep the tool minimal: the smallest script that does or proves the job, never a framework. Commit it only when the repository benefits from keeping it; otherwise save it under `/tmp` or attach it as a work-log artifact so throwaway files stay out of the diff.
