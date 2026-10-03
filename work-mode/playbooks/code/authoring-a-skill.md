# Authoring or modifying a skill

**You own the skill's voice.**

1. Use the **writing-for-agents** skill.
2. Validate the skill: frontmatter has `name` (matching the directory) and `description`; every referenced file exists; every cross-skill name resolves in the catalog. A user-only skill has both settings: `disable-model-invocation: true` in the frontmatter and `agents/openai.yaml` with `policy: allow_implicit_invocation: false`. A vendored skill is changed upstream, or forked into a skill with another name, never by hand in the catalog.
3. Test cases if structural: a checker or script that fails when the structure breaks. Skip if subjective. For behavior changes, use the Eval playbook.
4. Run **Opening a PR** when the skill lives in a reviewed repository.

When in doubt, delete. Keep only prose that changes a decision. Tell it to do the thing and skip the reason. Explain only when the rule is confusing without one. Match tone to scope. Point at structural sources (types, READMEs, config) per **principle-encode-lessons-in-structure**. Delegate to other skills by name. Don't restate. A workflow you keep hitting but isn't captured: propose a new skill.

**Reply.** Summary of the skill, key design decisions, validation notes.
