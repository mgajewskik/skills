---
name: review
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the change follow this repo's documented standards?) and Spec (does the change match what the originating issue/PRD asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X". Works for application code and for configuration, infrastructure-as-code, CI/CD, and platform/ops changes.
---

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards** — does the change conform to this repo's documented standards (and the applicable smell baselines below)?
- **Spec** — does the change faithfully implement the originating issue / PRD / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`, etc. If they didn't specify one, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here — not inside two parallel sub-agents.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.) — fetch via the workflow in `docs/agents/issue-tracker.md` when that file exists; otherwise use the repo's normal issue/MR tooling.
2. A path the user passed as an argument.
3. A PRD/spec file under common locations (e.g. `docs/`, `specs/`, `.scratch/`) matching the branch name or feature — discover what this repo actually uses; do not assume a fixed tree.
4. If nothing is found, ask the user where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

### 3. Identify the standards sources and which baselines apply

#### 3a. Discover standards in the repo

Search the **repo itself** for anything that documents how work in this change should be done. Do **not** stop at contribution or coding-standards markdown files, and do **not** hardcode a fixed filename list or external skill names.

Look for, by content and role (examples of *kinds*, not required paths):

- Human standards and process docs (contribution guides, coding standards, architecture/decision records, platform/ops runbooks, security baselines, style guides).
- Tooling and policy that encode standards (linters, formatters, policy-as-code, pre-commit or CI quality gates, editor/analyzer config) — treat enforced rules as "tooling already enforces"; treat comments and documented intent in those configs as standards when they express project rules.
- Domain docs that match the diff (infra, config management, CI/CD, deployment, environments) wherever this repo keeps them.

Prefer sources that are clearly authoritative for the paths touched by the diff. List every file you will hand to the Standards sub-agent. If the search finds nothing, say so — the baselines still apply.

#### 3b. Classify the diff (one line)

From the file list and hunks, label the change:

- **application** — mostly app/library/service source and its tests
- **ops** — mostly configuration, infrastructure-as-code, CI/CD, deployment, platform, or environment definition
- **mixed** — material amounts of both

Use that label only to choose which smell baselines the Standards sub-agent must apply:

| Classification | Baselines |
|----------------|-----------|
| application | code smells |
| ops | ops smells |
| mixed | both |

#### 3c. Smell baselines (always judgement calls; repo wins)

On top of whatever the repo documents, the Standards axis carries the applicable **smell baseline(s)** below even when a repo documents nothing. Two rules bind them:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Secret Leak"), never a hard violation — and, like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff.

##### Code smells (application / mixed)

Fowler code smells (_Refactoring_, ch.3):

- **Mysterious Name** — a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code** — the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy** — a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps** — the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession** — a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches** — the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery** — one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change** — one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality** — abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains** — long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man** — a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest** — a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

##### Ops smells (ops / mixed)

Portable heuristics for configuration, infrastructure-as-code, CI/CD, and platform changes. Tool- and product-agnostic — do not invent project conventions; only flag what the diff itself supports.

- **Mysterious Name** — a resource, role, job, var, or env key whose name does not reveal what it configures or for whom. → rename for intent and scope; if no honest name fits, the boundary is murky.
- **Duplicated Config** — the same shape repeated across envs, modules, or pipeline jobs with only incidental differences. → extract the shared shape; parameterize only what truly differs.
- **Shotgun Surgery** — one logical change forces scattered edits across many files/envs in the diff. → gather what changes together so one concern has one place to edit.
- **Divergent Change** — one file/module/stack is edited for several unrelated reasons. → split so each unit changes for one reason.
- **Speculative Generality** — abstraction, indirection, or multi-env machinery for needs the spec does not have. → delete it; keep the concrete form until a real second case exists.
- **Secret Leak** — credentials, tokens, private keys, or secret-bearing material introduced or left in plain config, committed artifacts, logs, or world-readable outputs. → remove from the change; load from the project's secret mechanism; avoid baking secrets into durable state or logs when the diff shows that path.
- **Blast Radius** — a change that can affect many hosts, environments, or resources with weak scope limits or weak review of destructive effect. → narrow targeting; separate environments; require an explicit plan/check/preview path for high-impact applies.
- **Non-Idempotent Change** — a step that is not safe to re-run, or that always reports change / mutates without clear desired-state semantics. → prefer declarative/desired-state forms; make change detection explicit; avoid "run this shell until it works" as the steady path.
- **Unpinned Runtime** — mutable version selectors (`latest`, floating majors, unpinned modules/images/collections) on a path that can deploy or apply. → pin what the apply path resolves; keep upgrades in deliberate, separate changes when possible.
- **Env Bleed** — shared defaults or wiring that couples environments (e.g. prod and non-prod) so a change in one can alter another. → hard boundaries for inventory, state, variables, and credentials per environment.
- **Missing Safety Gate** — a path that applies or mutates real systems without the validation, policy, plan/preview, or approval step this kind of change implies — or no rollback/recovery note for clearly destructive work. → add or restore the gate the change implies; document how to undo when destroy/replace is in play.
- **Privilege Overreach** — wider network, identity, or access scope than the change needs (open ingress, wildcard permissions, standing admin). → least privilege; justify any broad grant in the diff context.
- **Identity Churn** — renames, re-indexing, or address shifts that force destroy/recreate or retarget of existing resources without a migration story. → stable identifiers; explicit migrate/move/import when identity must change.

Shared structure smells (Mysterious Name, Duplication, Shotgun Surgery, Divergent Change, Speculative Generality) appear in both lists so either baseline stays complete when used alone.

### 4. Spawn both sub-agents in parallel

Send a single message with two `Agent` tool calls. Use the `general-purpose` subagent for both.

**Standards sub-agent prompt** — include:

- The full diff command and commit list.
- The diff classification from step 3b (`application` / `ops` / `mixed`).
- The list of standards-source files (or paths) found in step 3a, **plus the applicable smell baseline(s) from step 3c pasted in full** — the sub-agent has no other access to the baseline text unless pasted. For mixed, paste both baselines.
- Explicit note: load any skills relevant to the diff's domain when they would improve the review; discover them from available skills — do not invent filename conventions or project standards that are not in the provided sources, the pasted baseline(s), the diff, or a loaded skill.
- The brief: "Report — per file/hunk where relevant — (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any applicable baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls — documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling already enforces. If no repo standards sources were provided, say so and rely on the baseline(s) plus any relevant skills you load. Under 400 words."

**Spec sub-agent prompt** — include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- Explicit note: load any skills relevant to interpreting the domain or the change when they would improve the review; discover them from available skills — do not invent requirements not in the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

If the spec is missing, skip the Spec sub-agent and note this in the final report.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings — the two axes are deliberately separate (see _Why two axes_).

Mention the diff classification (`application` / `ops` / `mixed`) once near the top of the Standards section so "clean Standards" is not over-read when only baselines applied.

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes — that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- A change that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- A change that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
