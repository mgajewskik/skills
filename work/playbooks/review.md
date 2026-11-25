# Review

Adversarial, read-only PASS-gate review in a **fresh context**. Assume the implementation is wrong until current evidence proves otherwise. Find real defects; spare taste. Leave the worktree unchanged: no creating, editing, deleting, staging, or work-log writes; use the shell only for non-mutating diagnostics, tests, and configured checks.

When invoked after your own implementation (`Implement`, `Fix`, `Reduce`, `Deploy` preparation, or `Auto`), spawn a fresh, non-author read-only subagent on this playbook — never self-review in the author's context. Only the main session / orchestrator spawns reviewer subagents — a subagent spawned by the orchestrator never spawns a reviewer itself; it stops before review and returns its review inputs and work log so the main orchestrator spawns the fresh reviewer subagent directly. Pass what was asked, binary criteria, anti-criteria (including the two-case comment rule below for code diffs), the review surface (changed paths, diff fixed-point, prepared rollout artifact revision and preview, or completed Ops work-log surface), parent claims, optional spec path and classification hint, and the work log path when one exists — never your conclusion. When invoked directly by the user on an existing diff, branch, or PR you did not author in this session, run this playbook directly and use the Reply format below (opening with the goal when helpful).

**PASS-gate loop (parent / orchestrator):** Fix every `BLOCKER`, re-run checks, and re-run review until `Decision: PASS` (or an explicit user waiver). On re-review, re-check prior blockers against current files; reopen a fixed issue only with new evidence; promote a `NOTE` to `BLOCKER` only when it passes the severity test. Any edit after `Decision: PASS` voids the verdict.

**Two-case comment rule (for code diffs):** New or edited code carries no comments except in two cases: (1) the user asked for that comment, or (2) the code is deliberately unusual and a future reader would otherwise "fix" it (vendor/platform bug, protocol quirk, external constraint, or out-of-scope workaround), and the comment states why it is this way, what breaks if it changes, and when it can change (issue, version, or condition). Tool directives (shebangs, lint/type suppressions, build tags, PEP 723 script metadata), license headers, and doc comments required by repo tooling are code, not comments. Existing comments outside the change stay; one made false by the change must be fixed or deleted. A comment violating this rule is a failed anti-criterion (`BLOCKER`, not a `NOTE`).

Read the brief as prose and extract: what was asked, criteria (`C1`, `C2`, …), anti-criteria (`A1`, `A2`, …), the review surface (changed paths, diff fixed-point, prepared rollout artifact revision and preview, or completed Ops work-log surface), parent claims, and any spec or work-log path. No prohibition given or inferred → `RECEIVED_A: none` and `A_RESULTS: none`. A thin brief still runs: infer the bar from the brief and surface, list each inference, and review against that list.

1. **Pin the change surface.** Resolve the review surface: changed paths, working-tree diff, fixed-point range (`git diff <fixed-point>...HEAD` and `git log <fixed-point>..HEAD --oneline`), prepared rollout artifact revision, preview, and unit plans (for `Deploy` preparation), or completed Ops execution records and artifacts in a named work log (for pure-Ops `Auto` goals), plus direct impact (callers, tests, configs, contracts). Separate **introduced** defects from **pre-existing** ones (`OUT_OF_SCOPE` unless the change worsens or relies on them unsafely). Done when the change surface is fixed and readable; with no changed paths, no diff, no prepared rollout artifact or preview, and no Ops work-log surface to audit, stop before running tools and return `STATUS: blocked`, `VERDICT: blocked`, `Decision: FAIL`.
2. **Classify the change.** Pick one label: `application` (app, library, or service source and tests → code smells), `ops` (config, IaC, CI/CD, deploy, platform, or env → ops smells), or `mixed` (material amounts of both → both baselines). Done when one label is chosen.
3. **Run configured checks and verify work-log claims.** Inspect current artifacts directly (**[prove-it-works](../principles/prove-it-works.md)**) and verify API, flag, and config claims against the versions pinned in the target runtime rather than memory or latest docs (**[ground-claims-in-the-environment](../principles/ground-claims-in-the-environment.md)**). Run configured checks for the changed paths (tests, linters, type checkers, validators, pre-commit, CI targets) in check-only mode; skip any check that would alter `git status`, install dependencies, need secrets, or contact external systems, naming which and why. A failure caused by the change is a `BLOCKER`; an unrelated failure is pre-existing. When the brief names a **Work log** (`.work/<id>/log.yml`), treat its `evidence` entries and `revert` section as parent claims, not proof: re-run or re-read what each claim rests on; an unheld claim, a reversible change in `revert` without a working undo (or missing referenced artifact), or an irreversible change lacking user handover (`--by user`) and documented recovery limits (`--no-revert` or verified recovery) is a `BLOCKER`. Done when every relevant check and work-log claim is verified or explicitly skipped with a reason.
4. **Gate Spec (requirements).** Check every `C` and `A` item (including listed inferences) without adding unasked requirements: (1) missing or partial criterion (undemonstrated required behavior → `insufficient` and `BLOCKER`), (2) wrong behavior or broken contract, (3) anti-criterion violated or left unchecked when checkable (genuinely uncheckable offline items get `not-checked` with the reason in `Unknowns`), (4) scope creep adding risk or complexity, (5) criteria drift (criteria miss what was asked or were loosened to fit the result). Done when every `C` has `pass | fail | insufficient` and every `A` has `checked | violated | not-checked`, each with `file:line` or command evidence.
5. **Gate Standards (repo + smell baselines).** Discover repo standards relevant to the scope (style and coding docs, ADRs, security baselines, linter/policy intent, domain runbooks) and list them (or `"none — baselines only"`). **Repo wins** over any conflicting smell baseline. Skip formatting or lint already enforced by tooling unless the change breaks or bypasses the gate. Apply the Smell baselines below for the step 2 classification, naming each smell and quoting the hunk. Keep Spec and Standards reported separately so one axis cannot mask the other. Done when sources are listed and applicable baselines are applied to the diff.
6. **Assign severity and verdict.** Walk findings in priority order (`C/A` → correctness, edges, errors → security and data → contracts → tests for required behavior → scope and smells) and assign one severity to each:
   - **BLOCKER:** Real defect passing all three checks: (1) a careful peer would refuse to ship until fixed, (2) concrete evidence in the change (`file:line`, failing check, broken contract), (3) maps to a failed `C`/`A`, security/correctness/contract defect, broken work-log evidence or undo, or standards breach with real operational risk.
   - **NOTE:** Optional improvement leaving Spec intact with no demonstrated defect (clearer names, wording polish on kept comments, extra edge tests beyond criteria, non-critical smells, optional elegance). Never causes `FAIL`. *(Comments that violate the two-case comment rule above are a failed `A` → `BLOCKER`, not a `NOTE`.)*
   - **OUT_OF_SCOPE:** Pre-existing defect not worsened by the change, unrelated code, or pure preference (mention at most once under pre-existing).

   **Verdict:** Any `BLOCKER` → `VERDICT: request-changes`, `Decision: FAIL`. Zero blockers, every criterion `pass`, every checkable anti-criterion `checked` (with any uncheckable offline `not-checked` reason recorded in `Unknowns`) → `VERDICT: approve`, `Decision: PASS` (`NOTE`s allowed). No review surface → `VERDICT: blocked`, `Decision: FAIL`, `STATUS: blocked`.
7. **Output.** Emit the required envelope first, then the structured review below, citing `file:line` for every actionable finding.

## Smell baselines (judgement calls; repo wins)

Apply only the baseline(s) matching `CLASSIFICATION`, and flag only what the diff supports. Each smell reads *what* → *fix direction*.

**Code smells (`application` / `mixed`)**

- **Mysterious Name** — name hides purpose → rename or clarify the murky boundary.
- **Duplicated Code** — same logic shape in multiple hunks → extract the shared shape.
- **Feature Envy** — method uses another object's data more than its own → move it to the data.
- **Data Clumps** — same fields travel together → bundle into one type.
- **Primitive Obsession** — primitive stands in for a domain concept → introduce a small type.
- **Repeated Switches** — same type cascade recurs → replace with polymorphism or a shared map.
- **Shotgun Surgery** — one logical change scatters across many files → gather the concern.
- **Divergent Change** — one module edited for unrelated reasons → split by reason.
- **Speculative Generality** — abstraction for unasked needs → delete until a second real case exists.
- **Message Chains** — long `a.b().c().d()` walk → hide behind one method.
- **Middle Man** — wrapper mostly delegates → call the real target directly.
- **Refused Bequest** — subtype ignores most of its parent → prefer composition.

**Ops smells (`ops` / `mixed`)**

- **Mysterious Name** — resource, role, job, var, or env key hides intent/scope → rename.
- **Duplicated Config** — same shape repeated across envs/modules with incidental diffs → extract and parameterize only real variance.
- **Shotgun Surgery** — one logical change scatters across files/envs → consolidate per concern.
- **Divergent Change** — one stack/file edited for unrelated reasons → split.
- **Speculative Generality** — multi-env machinery for unasked needs → keep concrete.
- **Secret Leak** — credentials, tokens, or keys in plain config, commits, or logs → load from the secret mechanism.
- **Blast Radius** — wide host/env effect with weak scope limits → narrow targeting and add plan/preview gates.
- **Non-Idempotent Change** — unsafe to re-run or always mutates → use declarative desired-state semantics.
- **Unpinned Runtime** — `latest` or floating majors on an apply path → pin versions.
- **Env Bleed** — shared defaults couple prod and non-prod → enforce hard per-env boundaries.
- **Missing Safety Gate** — mutates live systems without the plan, policy, approval, or rollback the change implies → restore the gate.
- **Privilege Overreach** — wider network, identity, or access scope than needed → apply least privilege.
- **Identity Churn** — rename or reindex forces destroy/recreate without migration → keep stable IDs or migrate explicitly.

## Reply format

**Envelope (first):**

```text
STATUS: done | blocked
RECEIVED_C:
RECEIVED_A:
C_RESULTS:
- C1 | pass/fail/insufficient | evidence
A_RESULTS:
- A1 | checked/violated/not-checked | evidence
SCOPE_RESULT:
- actions, checks run or skipped, and files inspected (read-only), or none
BLOCKERS:
```

**Review (after envelope):**

```markdown
VERDICT: approve | request-changes | blocked
Decision: PASS | FAIL
CLASSIFICATION: application | ops | mixed

## Blockers
- [BLOCKER] description; Location file:line; failed C/A or risk class; concrete fix
- or: none

## Notes
- [NOTE] file:line; short suggestion
- or: none

## Spec
- missing/partial/wrong/creep/drift findings, or clean

## Standards
- sources used (or "none — baselines only")
- hard standard breaches and applicable smells, or clean

## Pre-existing vs Introduced
- Pre-existing (OUT_OF_SCOPE unless worsened):
- Introduced:

## Test Coverage
- gaps that affect criteria, or none required beyond current evidence

## Unknowns
- or none

## Fastest Next Probe
- or n/a
```
