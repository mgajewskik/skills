---
name: plan
description: Plan new work from scratch as a living markdown file with binary success criteria, anti-criteria, and independent workstreams. Use when the user says "let's create a plan", wants to plan a feature or change before implementing it, or needs a plan file other agents can execute and verify against. Use to-spec instead when the conversation already holds the design.
---

# Plan

Create one **living plan file** for new work and keep it current as the picture sharpens. The file is both the implementation contract and the decision record, and it lands on disk early so a lost context never loses the plan. It scales from a single small feature to multi-lane work.

This skill produces the plan file only and invokes no other skills. Implementation, doc updates, tickets, and loop execution each belong to other skills the user invokes explicitly.

## Process

### 1. Frame

Recover everything the invocation already states — goal, constraints, non-goals. Nothing recovered here gets re-asked later.

### 2. Explore

Answer code-answerable questions from the codebase, not from the user. Collect the paths, symbols, and docs the plan will cite — only what was actually inspected. Done when every remaining question is genuinely user-only.

### 3. Write the skeleton immediately

As soon as the goal can be named, put the file on disk — before any interview. Resolve the location in order:

1. explicit path from the user
2. a plans-location instruction or convention already in the repo
3. an existing `./plans` or `./docs/dev/plans`, when exactly one exists
4. `./plans`

Name it `YYYY-MM-DD-<kebab-slug>.md`, fill the template below with what framing and exploration already settled, set `Status: draft`. Done when the file exists on disk.

### 4. Resolve the unknowns

Ask one question at a time, each with a recommended answer. **Save the file after every answer, before the next question** — the file is the running record and the conversation never runs ahead of it. When the user has explicitly invoked an interview skill (`$grill-me`, `$grill-with-docs`) alongside, let that skill drive the questioning and record its answers the same way. The interview always covers:

- What does done look like, observably? → feeds success criteria
- What must never happen? → feeds anti-criteria — every non-trivial plan needs at least one

Done when no open decision would still change the goal, criteria, or workstreams — or the user defers one, which keeps `Status: draft` with the blocker named.

### 5. Define done

Map every requirement and hard constraint to a **binary** success criterion with a concrete verification method: a command with a pass/fail signal, an observable state, or a measured threshold with units. Anti-criteria name the likely regressions, scope leaks, and forbidden shortcuts, verified by non-occurrence. Replace "works correctly"-style vagueness with observable outcomes. A criterion without a verification method keeps the plan in `draft`.

### 6. Shape the workstreams

Break the work into tracer-bullet workstreams:

- vertical slices, each independently verifiable and sized to fit one fresh context
- blocking edges declared — a workstream with no blockers can start immediately; prefactoring goes first
- small work is exactly one workstream
- every workstream maps to at least one criterion, every criterion to at least one workstream

Independent workstreams are what make a plan loopable: when they exist, flag `Loop candidate: yes` — a later loop skill can execute the plan task-by-task in fresh contexts. This skill only flags candidacy.

### 7. Confirm

Present the summary: goal, criteria, workstreams with blocking edges, validation commands. On approval set `Status: ready` and record the approval in Decisions. Then say the plan is ready and let the user decide when to execute.

## Living file

The plan file is the single source of truth for the work: update it whenever new information lands or the plan changes shape. Status flow: `draft` → `ready` → `in progress` → `done`; `done` requires every validation check executed with evidence.

## Template

```markdown
# <Feature title>

**Status:** draft
**Loop candidate:** no
**Date:** YYYY-MM-DD

## Goal

<What done looks like, observably, from the user's perspective. One or two paragraphs.>

### Success criteria

- [ ] <binary criterion — a command that passes or a concrete observable state>

### Anti-criteria

- <what must never happen — a likely regression, scope leak, or shortcut; verified by non-occurrence>

## Context & References

- <path, symbol, or doc> — <why it matters to this plan>

## Decisions

<Distilled record of the interview, appended newest-last. One entry per decision.>

- **Q:** <the question asked> → **A:** <what was decided> — <why; rejected alternatives>

## Workstreams

<Slices in dependency order. Small work: exactly one.>

### WS-1: <title>

**Delivers:** <the end-to-end behavior this workstream makes work>
**Blocked by:** <WS ids, or "None — can start immediately">
**Suggested skills:** <skills the executor should invoke>

- [ ] <acceptance criterion — machine-checkable>

## Validation

<How we confirm the plan was executed successfully and can be marked done.>

- `<command or observation>` → proves <criterion>

## Out of Scope

<What this plan consciously excludes.>
```
