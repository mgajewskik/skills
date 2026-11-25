# Review

Adversarial, read-only PASS-gate review in a **fresh context**. Assume the change or plan is wrong until current evidence proves otherwise. Find real defects; spare taste. Leave the worktree unchanged: no creating, editing, deleting, staging, or work-log writes; use the shell only for non-mutating diagnostics, checks, and verification steps or skills.

Only the main session / orchestrator spawns reviewer subagents — a subagent spawned by the orchestrator never spawns a reviewer itself; it finishes its playbook (or pauses at `Deploy` step 6) and returns changed paths, evidence, and its work log so the main orchestrator decides whether to spawn a fresh reviewer subagent under `work/SKILL.md`'s significance gate. Pass `Mode: full | delta | plan`, what was asked, binary criteria, anti-criteria, the review surface, fresh verification outputs already run, optional repo-standards paths and classification hint, and the work log path when one exists — never your conclusion. When invoked directly by the user on an existing diff, branch, PR, or plan you did not author in this session, run this playbook directly in the matching mode.

**Modes (set by the orchestrator; defaults to `full`):**

- **`Mode: full`** — First review of a significant completed change, `Auto` aggregate close, or `Deploy` preparation. Audits the full review surface across Spec, verification steps/skills, repo standards, and applicable smells.
- **`Mode: delta`** — Scoped follow-up re-review after fixing behavioral, contract, logic, or security `BLOCKER`s from a prior `FAIL` (or a bounded substantive post-review edit). Focuses only on prior blockers and the incremental diff since the prior review checkpoint; escalates to `Mode: full` only if the fix unexpectedly widened scope across unrelated modules or redesigned a core contract.
- **`Mode: plan`** — Pre-execution review of a significant plan or design (architecture redesign, multi-unit `Auto` plan, `Migration`, or risky `Deploy`/`Teardown` plan). Requires no diff; audits goal fit, codebase grounding, edge cases, failure/rollback hazards, over-engineering, and binary verification criteria.

**PASS-gate loop (main orchestrator):** Fix behavioral, contract, logic, or security `BLOCKER`s, re-run verification, and re-review in `Mode: delta` until `Decision: PASS` (or an explicit user waiver), capped at 2 follow-up rounds before escalating unresolved disagreements to the user. On re-review, reopen a fixed issue only with new evidence and promote a `NOTE` to `BLOCKER` only when it passes the severity test. Purely mechanical, objectively verifiable fixes (e.g., removing a stray comment, typo, formatting) do not require a follow-up reviewer subagent; substantive edits after `PASS` trigger `Mode: delta`.

**Two-case comment rule (for code diffs):** New or edited code carries no comments except in two cases: (1) the user asked for that comment, or (2) the code is deliberately unusual and a future reader would otherwise "fix" it (vendor/platform bug, protocol quirk, external constraint, or out-of-scope workaround), and the comment states why it is this way, what breaks if it changes, and when it can change (issue, version, or condition). Tool directives (shebangs, lint/type suppressions, build tags, PEP 723 script metadata), license headers, and doc comments required by repo tooling are code, not comments. Existing comments outside the change stay; one made false by the change must be fixed or deleted. A stray violation of this rule is a `NOTE` (not a `BLOCKER`) unless the comment actively misleads/contradicts behavior or violates an explicit user criterion.

Read the brief as prose and extract: `Mode`, what was asked, criteria (`C1`, `C2`, …), anti-criteria (`A1`, `A2`, …), the review surface, prior blockers (for `delta`), fresh checks already run, and any spec, standards, or work-log path. A thin brief still runs: infer the bar from the brief and surface, list each inference, and review against that list.

1. **Pin the review surface (by mode).**
   - `Mode: full`: resolve changed paths, working-tree diff, fixed-point range (`git diff <fixed-point>...HEAD` and `git log <fixed-point>..HEAD --oneline`), prepared rollout artifact revision, preview, and unit plans (for `Deploy` preparation), or completed Ops execution records and artifacts in a named work log (for pure-Ops `Auto` goals), plus direct impact (callers, tests, configs, contracts). Separate **introduced** defects from **pre-existing** ones (`OUT_OF_SCOPE` unless the change worsens or relies on them unsafely). With no changed paths, no diff, no prepared rollout artifact or preview, and no Ops work-log surface, stop before running tools and return `VERDICT: blocked`, `Decision: FAIL`.
   - `Mode: delta`: resolve the prior `BLOCKER` list and the **incremental diff** since the prior review checkpoint (`git diff <checkpoint>` or the named delta files/hunks) plus immediate callers and tests. Do not re-audit untouched files unless the fix widened scope into unrelated modules (in which case escalate to `Mode: full`). With no incremental diff or prior blocker surface, return `VERDICT: blocked`, `Decision: FAIL`.
   - `Mode: plan`: read the plan file or inline proposal and locate the codebase files, interfaces, and configs it references. Requires no diff (never block on an empty working tree).
   Done when the mode's surface is fixed and readable.
2. **Classify the change.** Pick one label: `application` (app, library, or service source and tests → code smells), `ops` (config, IaC, CI/CD, deploy, platform, or env → ops smells), `mixed` (material amounts of both → both baselines), or `plan` (plan/design review → skip smell baselines). Done when one label is chosen.
3. **Run verification steps or skills and check work-log claims.** Inspect current artifacts directly (**[prove-it-works](../principles/prove-it-works.md)**) and ground every API, flag, symbol, and config claim in the codebase and versions pinned in the target runtime (**[ground-claims-in-the-environment](../principles/ground-claims-in-the-environment.md)**).
   - **Verification steps or skills (not tests only):** Discover and run whatever non-mutating verification steps or verification skills are declared in the repo, available skills, or environment to confirm the implementation actually works — tests, linters, type checkers, schema/skill validators, builds, deterministic renders, CLI smoke probes, browser/UI verification skills, or repo verification scripts. Skip any check that would alter `git status`, install dependencies, need secrets, or mutate live/external systems, naming which and why. A failure caused by the change is a `BLOCKER`; an unrelated failure is pre-existing.
   - **Avoid redundant re-runs:** When the orchestrator supplies fresh passing check outputs bound to the exact current tree/revision, inspect those commands and outputs first rather than blindly re-running identical slow suites — **do** execute any declared verification step or verification skill that was missing, stale, incomplete, or suspect, plus targeted probes for risky paths.
   - **By mode:** In `Mode: delta`, run only targeted verification steps or skills for the fixed blockers and changed paths. In `Mode: plan`, skip code/test execution and instead spot-check referenced codebase files, symbols, APIs, and constraints so plan assumptions are verified against real code.
   - **Work log (`Deploy`, Ops, or passed log):** When the brief names a **Work log** (`.work/<id>/log.yml`) for `Deploy` or Ops (or explicitly requests a log audit), treat its `evidence` entries and `revert` section as parent claims, not proof: re-run or re-read what each claim rests on directly; an unheld claim, a reversible change in `revert` without a working undo (or missing referenced artifact), or an irreversible change lacking user handover (`--by user`) and documented recovery limits (`--no-revert` or verified recovery) is a `BLOCKER`.
   Done when applicable verification steps/skills and work-log claims are verified or explicitly skipped with a reason.
4. **Gate Spec (or Plan quality).**
   - In `Mode: full` and `Mode: delta`: check every `C` and `A` item (in `delta`, focus on prior blockers and affected `C`/`A` items) without adding unasked requirements: (1) missing or partial criterion (undemonstrated required behavior → `insufficient` and `BLOCKER`), (2) wrong behavior or broken contract, (3) anti-criterion violated or left unchecked when checkable (genuinely uncheckable offline items get `not-checked` with the reason in `Unknowns`), (4) scope creep adding risk or complexity, (5) criteria drift.
   - In `Mode: plan`: check (1) goal and constraint alignment without scope creep, (2) codebase grounding (cited files, symbols, APIs, and invariants match reality), (3) missing edge cases, failure modes, compatibility/migration or rollback hazards, (4) unnecessary complexity or bolted-on patches, (5) realistic binary verification criteria naming which verification steps or skills will prove the work.
   Done when every evaluated `C` has `pass | fail | insufficient` and every `A` has `checked | violated | not-checked` (each with `file:line` or command evidence).
5. **Gate Standards (repo + smell baselines).** Skip in `Mode: plan`. In `Mode: delta`, inspect only the incremental delta hunks for newly introduced hard standard breaches or severe smells (do not re-discover repo standards or re-sweep untouched files). In `Mode: full`, use repo-standards paths supplied in the brief (discovering only when omitted, or `"none — baselines only"`). **Repo wins** over any conflicting smell baseline. Skip formatting or lint already enforced by tooling unless the change breaks or bypasses the gate. Apply the Smell baselines below for the step 2 classification, naming each smell and quoting the hunk. Keep Spec and Standards reported separately so one axis cannot mask the other. Done when applicable standards and baselines are checked.
6. **Assign severity and verdict.** Walk findings in priority order (`C/A` → correctness, edges, errors → security and data → contracts → verification coverage for required behavior → scope and smells) and assign one severity to each:
   - **BLOCKER:** Real defect passing all three checks: (1) a careful peer would refuse to ship or proceed until fixed, (2) concrete evidence (`file:line`, failing verification step/skill, broken contract, or false plan assumption), (3) maps to a failed `C`/`A`, correctness/security/contract defect, broken `Deploy`/Ops work-log evidence or undo, or hard standards breach with real operational risk.
   - **NOTE:** Optional improvement leaving Spec intact with no demonstrated defect (clearer names, stray comments violating the two-case comment rule — `NOTE`, not a `BLOCKER`, unless misleading or explicitly prohibited — extra edge tests beyond criteria, non-critical smells, optional elegance). Never causes `FAIL`.
   - **OUT_OF_SCOPE:** Pre-existing defect not worsened by the change, unrelated code, or pure preference (mention at most once under pre-existing).

   **Verdict:** Any `BLOCKER` → `VERDICT: request-changes`, `Decision: FAIL`. Zero blockers, every evaluated criterion `pass`, every checkable anti-criterion `checked` (with any uncheckable offline `not-checked` reason recorded in `Unknowns`) → `VERDICT: approve`, `Decision: PASS` (`NOTE`s allowed). Missing review surface in `full` or `delta` → `VERDICT: blocked`, `Decision: FAIL`.
7. **Output.** Emit the compact structured review below, citing `file:line` for every actionable finding (cap `Notes` at 3; keep clean sections to one line).

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

```markdown
VERDICT: approve | request-changes | blocked
Decision: PASS | FAIL
MODE: full | delta | plan
CLASSIFICATION: application | ops | mixed | plan

## Criteria & Anti-Criteria
- C1: pass | fail | insufficient — evidence
- A1: checked | violated | not-checked — evidence (or: none)

## Blockers
- [BLOCKER] description; Location file:line; failed C/A or risk class; concrete fix
- or: none

## Verification
- verification steps, checks, or skills run (and fresh orchestrator checks accepted or skipped with reason)

## Spec & Standards
- Spec: clean | findings
- Standards (sources used, "none — baselines only", or "n/a (plan)"): clean | breaches & applicable smells
- Pre-existing (OUT_OF_SCOPE unless worsened): none | items

## Notes
- [NOTE] file:line; short suggestion (max 3; or: none)

## Unknowns
- none | items
```
