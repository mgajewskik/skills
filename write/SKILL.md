---
name: write
description: "Draft, rewrite, copyedit, critique, or coach English-first general, technical, and professional prose. Use when the user asks for writing, editing, feedback, clearer or more concise prose, anti-AI cleanup, or writing coaching, unless the user explicitly selects the `writing` skill. Preserve meaning, evidence, uncertainty, constraints, and voice. Do not use as the format or policy authority for commits, ADRs, Diátaxis documentation, or READMEs when a dedicated skill is available."
---

# Writing

Improve the reader's ability to understand, decide, or act without changing the user's meaning, evidence, stance, or recognizable voice.

## Boundaries

Use this skill for prose transformation, line editing, feedback, and general professional communication. Do not invent facts, sources, metrics, causes, commitments, or confidence. Do not treat legal, medical, HR, compliance, or security-sensitive text as advice beyond writing quality.

Dedicated skills own the structure and policy of commit messages, ADRs, Diátaxis documentation, and READMEs. When one is in scope, apply its constraints first; this skill may line-edit supplied prose after those constraints are known.

## Router

Choose one primary route. The most specific applicable intent wins over general drafting or rewriting:

- Feedback or coaching: [feedback and coaching](references/feedback-and-coaching.md). Add [rewrite and safety](references/rewrite-and-safety.md) when transformation is requested or the material-stakes definition and reader-test guidance apply; for transformation, add any other reference selected by that transformation's primary route.
- Copyedit, anti-AI cleanup, grammar, or line polish: [rewrite and safety](references/rewrite-and-safety.md) and [line editing and anti-patterns](references/line-editing-and-anti-patterns.md), even when the prose has a named format.
- Draft or rewrite a named professional or owned format, such as email, chat, meeting communication, status update, technical explanation, incident, postmortem, issue or review prose, design document, or public post: [rewrite and safety](references/rewrite-and-safety.md) and [formats and professional communication](references/formats-and-professional-communication.md). Add line editing only when requested or repeated line-level problems are evident.
- Other draft or rewrite: [rewrite and safety](references/rewrite-and-safety.md) and [line editing and anti-patterns](references/line-editing-and-anti-patterns.md).

Material stakes strengthen the rewrite-and-safety checks but do not create a second route. Load all four only for a genuine combined transformation, named format, line-level problem, and coaching request.

## Working default

Identify the reader, their task, channel, stakes, and any hard constraints. Fix purpose and structure before sentences. Preserve fixed material, distinctions in certainty, and security-sensitive boundaries. Return the requested artifact directly. Add a disclosure only for changed certainty, unresolved factual ambiguity, fixed-language risk, or a major structure or genre change.
