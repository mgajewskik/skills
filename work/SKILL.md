---
name: work
description: Work discipline for any task that changes or investigates code, config, or infrastructure. Use when the user asks you to do work (build, fix, change, clean up, debug, review, deploy, investigate), or when work lands in front of you mid-task or in a delegated brief. Casual questions do not need it.
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "echo 'work is on for this session. When this prompt asks for work, follow the work skill. When it steers the work in a new direction, pick the playbook again. If its content is no longer in your context, load the work skill again first. Ignore this on a casual turn.'"
  SubagentStart:
    - matcher: "^(general-purpose|sonnet|claude|Plan)$"
      hooks:
        - type: command
          command: >-
            echo '{"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": "The parent session runs the work skill. If your brief is a read-only lookup, research, or review, follow your brief only. If your brief runs a workstream inside the parent playbook, follow the brief and do not start a separate work log. Otherwise, load the work skill and follow the playbook your brief names, or pick the one your brief matches."}}'
---

# Work

## Non-negotiables

The Principles section below grounds every trigger. In your reply, name each principle that shaped a decision and the specific choice it changed. For any principle that links to a file below, read its file in full before acting on or citing it; entries without a link are complete as written.

**Goal first.** Before the first action, restate the user's goal and the smallest scope (or smallest end state, in Reduce) that meets it, then proceed. Open each delegate brief and the final report with the goal.

**Prototype before asking.** A fork that an allowed local experiment or read-only probe can settle (behavior, output, timing, whether a check tells the cases apart) is not the user's to answer. Run it and decide from what you observe, respecting the active playbook's authority and read-only rules (never run live probes in Guided mode or before Debug fixes target and identity; never run a probe that writes state). Ask only for a product or preference call that no experiment can settle.

**No comments.** Code you write, and every delegate diff you accept, carries no comments. Make the code say it instead: a precise name, an extracted function, a type, a test. A surprise in our own code that this change can make obvious gets reshaped, not explained. Write a comment only in two cases:

- The user asked for that comment.
- The code is deliberately unusual and a future reader would otherwise "fix" it: a vendor or platform bug, a protocol quirk, an external constraint, or a workaround whose root fix is out of scope. The comment says why it is this way, what breaks if it changes, and when it can change (an issue, a version, a condition).

`# Load config` or `// increment the retry counter` gets deleted. `# The billing API returns 200 with an error body (issue #123); keep the body check until v3.` stays. Tool directives (shebangs, lint or type suppressions, build tags), license headers, and doc comments the repo's tooling requires are code, not comments. Existing comments outside your change stay; one your change makes false is fixed or deleted. Every Independent review brief lists "no comment outside these two cases" as an anti-criterion.

## Authority and review

**Precedence:** Explicit user prohibition > `Guided` mode > Active playbook authority > Non-negotiables > Principles.

**Execution authority and grants.** Code playbooks work locally and offline only: nothing is applied, initialized against a real backend, installed, or deployed; a code change reaches a live system only through Deploy. Ops playbooks run against live systems:

- Reversible Ops changes outside production run after logging a `plan --by agent` with a verified revert (and snapshot artifact when needed).
- Reversible Ops changes in production require a **session grant** — an explicit user statement naming environment, target scope, and allowed change types, logged as a `note` or `decision` before use. Without a grant, log a `plan --by user` and hand over.
- Irreversible Ops changes and `Teardown` destroys are **always user-executed**, in every environment.

**Independent review (`Decision: PASS`).** Required after every implementation and wherever a playbook calls for an independent review or verdict. Spawn a fresh, non-author read-only subagent instructed to follow [`playbooks/review.md`](playbooks/review.md) without starting a work log. Give it what was asked, binary criteria, anti-criteria (including "no comment outside the two allowed cases" for code diffs), changed paths or artifact revision and preview, parent claims, and the work log path when one exists — never your own conclusion. Fix every `BLOCKER` and re-review until `Decision: PASS` (or an explicit user waiver); any edit after `PASS` voids the verdict.

## Playbooks

Match the task to a playbook, open its file, and copy its steps into the todolist verbatim before any task-specific todos (when the runtime has no todolist tool, track the steps through work-log phases and the reply instead). A step you skip stays in the list with `skip: <reason>`.

**Pick again** when the user's prompt steers the work in a new direction, when the current playbook reaches its exit evidence or routes onward and the work goes on, and when a delegated brief arrives; a follow-up within the current task keeps its playbook. Name the playbook you leave with its exit evidence or the reason it stopped, then the one you enter, and log the switch as a decision.

**Delegate with the skill.** Delegation has three shapes:

- **Delegated playbook unit** (e.g., an Auto unit or handed-off task): brief tells the agent to load `work`, names the playbook when known (or leaves the agent to pick), passes the parent log id for `new --parent`, and gets back the delegate's log id and evidence.
- **Parallel workstream** (inside Implement): edits only its disjoint file scope, runs scoped checks, keeps no separate work log, and returns changed paths and evidence to the parent.
- **Read-only lookup or independent review:** runs on its own brief (following [`playbooks/review.md`](playbooks/review.md) for reviews); does not load other `work` playbooks or start a work log.

Code is everything kept in version-controlled files: application code, tests, scripts, config, and infrastructure as code (manifests, roles, unit files, pipelines). Ops are operations run against live systems by executing commands. A question about a live system's current behavior is Debug; an adversarial diff/branch/PR review is Review; a general read-only audit or exploration of local code is Investigate. A mixed task ("fix the Terraform module and roll it out") starts where the failure is observed and hands over at the boundary, naming the exit evidence.

**Code**

- **Investigate.** Read-only audit, exploration, or analysis of code, config, or infrastructure as code; changes nothing. [`investigate.md`](playbooks/investigate.md).
- **Review.** Adversarial, read-only PASS-gate review of a diff, implementation, or prepared rollout across configured checks, Spec, Standards, and work-log claims; runs in a fresh context after every implementation. [`review.md`](playbooks/review.md).
- **Implement.** Build or change code and verify it offline. [`implement.md`](playbooks/implement.md).
- **Fix.** A defect in code: make it red with a check, fix the root cause, keep the check as a regression guard. [`fix.md`](playbooks/fix.md).
- **Reduce.** Make code smaller and simpler while keeping current behavior or reaching a target behavior the user states: cleanup, deleting what is no longer needed, cutting complexity. [`reduce.md`](playbooks/reduce.md).

**Ops**

- **Debug.** Find the cause of a failure, regression, or unexpected behavior with read-only evidence. [`debug.md`](playbooks/debug.md).
- **Deploy.** Roll out a reviewed artifact unit by unit, executed or handed over, verified and gated. [`deploy.md`](playbooks/deploy.md).
- **Live modify.** A direct change to a running system outside the normal rollout path. [`live-modify.md`](playbooks/live-modify.md).
- **Teardown.** Remove resources, data, or whole environments. [`teardown.md`](playbooks/teardown.md).
- **Incident.** Active consumer impact: containment first, cause second. [`incident.md`](playbooks/incident.md).
- **Drift.** Desired and live state disagree; decide per field which side wins. [`drift.md`](playbooks/drift.md).
- **Migration.** Change a contract, format, or platform across mixed versions or persisted data. [`migration.md`](playbooks/migration.md).

**Mode**

- **Guided.** The user runs every live command and makes every edit; you guide from their pasted output (offline local reads and checks only, or zero execution if the user forbids running commands). Wraps the matched playbook. [`guided.md`](playbooks/guided.md).
- **TDD.** Build test-first in vertical slices at agreed seams. Wraps Implement. Use only when the user asks for TDD, test-first, or red-green. [`tdd.md`](playbooks/tdd.md).
- **Auto.** Pursue one stated goal to completion as an orchestrator: fresh subagents run its units, each on the playbook it matches, chaining playbooks until the goal is met or only handovers remain. Wraps a sequence of playbooks. Use when the user asks for auto mode, orchestration, or a long run toward a goal. [`auto.md`](playbooks/auto.md).

## Work log

Every mutating or Ops task keeps one log, continued across the playbooks it chains through. Skip creating a `.work/` log on strictly read-only `Investigate` tasks when the user asks for no workspace writes; `Review` never creates a `.work/` log. A delegate running its own playbook keeps its own log (`--parent <id>` when in the same project, so it nests inside the parent's directory) and hands back its id and path; a workstream inside the parent's playbook hands its evidence back for the parent's log. Each log has one writer. It is the audit record the user reads weeks later, without running a command, to see what changed, why, on what evidence, how it was verified, and how to undo it; whatever the environment will lose by then must be in it.

Write logs only through `uv run <this skill's directory>/scripts/log.py` from inside the project (`--help` lists every subcommand and flag); each log is `.work/<id>/log.yml` plus entry-numbered artifacts, excluded from git. Calls to `log.py` itself and bounded bootstrap reads before `new` are not logged.

- **Start / phase:** `new <kebab-slug> --task "<one sentence>" --playbook <name> [--parent <id>]`, then `phase <id> "<step>"` at each step.
- **Changes (plan before, run after):** Before executing any change (agent or user), log `add <id> plan --by agent|user --class reversible|irreversible --command ... --why ... --revert ...` (or `--no-revert "<reason>"` for irreversible; attach prior state via `--artifact /tmp/<file>` and write `{artifact}` in `--revert`). After execution, log `add <id> run --from-plan <n> --outcome ok|failed|unknown --result ...`. A revert you or the user ran is `add <id> run --class ... --command ... --reverts <n> --outcome ok|failed|unknown`; only `--outcome ok` clears the original entry from `revert-plan`.
- **Read-only commands:** Log `add <id> run --class read-only --command ... --target ... --identity ... --why ... --result ...` after execution.
- **Evidence, decisions, notes, corrections:** Log `add <id> evidence --claim ... --status established|failed|unverified --command ... [--revision ...]`, `decision --text ... --why ... [--evidence <n,n>] [--rejected ...]`, `note --text ...`. Attach large outputs or snapshots via `--artifact /tmp/<file>`. Fix mistakes append-only with `--supersedes <n>`; never edit `log.yml` by hand.
- **Root cause, gate, revert, close:** `root-cause <id> ...`, `check <id> --since <n> --max-age-hours <h> --revision <rev> --require <claim> ...`, `revert-plan <id>` (prints newest first including nested delegate logs; never executes), and `close <id> --status done|halted|reverted --summary ...` after walking the timeline for missing decisions or wrong entries.

Write entries in plain words and concrete actions. A refused value looks like a secret: redact it and log again. Name the log path in the reply when a log was used.

## Principles

Each principle names when it applies. Read a linked file in full before acting on or citing it; entries without a link are complete as written. Paths are relative to this skill's directory.

**Core**

- **Laziness Protocol.** Refactoring, sizing a diff, or tempted to add abstractions, layers, or signal threading. Bias to deletion and the smallest change that solves the problem; consolidate each repeated decision into one source of truth.
- **Foundational Thinking** ([`foundational-thinking.md`](principles/foundational-thinking.md)). Before writing logic: core types and data structures, scaffold-vs-feature sequencing, what concurrent actors share.
- **Redesign from First Principles** ([`redesign-from-first-principles.md`](principles/redesign-from-first-principles.md)). Integrating a new requirement into an existing design. Redesign as if it had been foundational from day one.
- **Attack the Premise** ([`attack-the-premise.md`](principles/attack-the-premise.md)). Two or more fixes that share one premise have failed the same gate. Write the premise down and test it directly before you write another fix that assumes it.
- **Subtract Before You Add** ([`subtract-before-you-add.md`](principles/subtract-before-you-add.md)). Sequencing an addition, refactor, or rewrite. Remove dead weight first, then build on the simpler base.
- **Minimize Reader Load** ([`minimize-reader-load.md`](principles/minimize-reader-load.md)). Reviewing or shaping code that's hard to trace. Count layers and hidden state, collapse one-caller wrappers, shrink mutable scope.
- **Outcome-Oriented Execution** ([`outcome-oriented-execution.md`](principles/outcome-oriented-execution.md)). Owned, offline rewrites with explicit phase boundaries and no live mixed-version or persisted state. Converge on the target architecture instead of keeping throwaway compatibility code.
- **Experience First** ([`experience-first.md`](principles/experience-first.md)). Product, UX, API, or maintenance tradeoffs (the user includes library callers and future maintainers). Choose consumer clarity and delight over implementation convenience.
- **Exhaust the Design Space.** A novel UI interaction, product-feel choice, or architectural decision with no precedent in the codebase. Build 2-3 competing prototypes or sketches and compare side by side before committing.
- **Build the Lever** ([`build-the-lever.md`](principles/build-the-lever.md)). Any non-trivial work. Build the smallest rerunnable script, codemod, generator, or check instead of working by hand; keep throwaway scripts out of the diff.
- **Encode Lessons in Structure.** You catch yourself writing the same instruction a second time or fixing a recurring mistake. Encode it as a lint, type, runtime check, or script instead of more text; write prose only when judgment is needed, with a concrete failure example.

**Architecture**

- **Model the Domain** ([`model-the-domain.md`](principles/model-the-domain.md)). Writing stateful logic, or code that branches a lot or repeats a shape assumption across files. Encode the domain in a structure (state machine, typed model, map, registry, discriminated union, reducer, or the right collection) instead of scattered conditionals.
- **Boundary Discipline** ([`boundary-discipline.md`](principles/boundary-discipline.md)). Wiring validation, error handling, or framework adapters. Guards at system boundaries, trust internal types, keep business logic pure.
- **Type System Discipline** ([`type-system-discipline.md`](principles/type-system-discipline.md)). Designing types or reviewing a function signature in any statically typed language. Make illegal states unrepresentable, brand primitives, parse external data at boundaries, exhaust variants, derive from authoritative schemas.
- **Make Operations Idempotent** ([`make-operations-idempotent.md`](principles/make-operations-idempotent.md)). Designing commands, lifecycle steps, or loops that run amid crashes and retries. Converge to the same end state.
- **Migrate Callers Then Delete Legacy APIs.** Introducing a new internal API when all callers are owned and no external compatibility is required. Migrate callers, update tests to the new contract, and delete the old API in one wave; use Preserve Compatible Transitions when external or independently deployed consumers exist.
- **Separate Before Serializing Shared State** ([`separate-before-serializing-shared-state.md`](principles/separate-before-serializing-shared-state.md)). Concurrent actors might write the same file, branch, key, or object. Eliminate the sharing first; serialize structurally only when one shared writer is a real invariant.

**Verification**

- **Prove It Works** ([`prove-it-works.md`](principles/prove-it-works.md)). After a task, before declaring done. Verify against the real artifact, not a proxy or "it compiles".
- **Fix Root Causes** ([`fix-root-causes.md`](principles/fix-root-causes.md)). Debugging. Trace each symptom back to the first place the system went wrong and fix it there. A guard is a fix only when the state it handles is legitimate.
- **Sequence Work into Verifiable Units** ([`sequence-verifiable-units.md`](principles/sequence-verifiable-units.md)). Multi-step work (sweeps, migrations, runs of similar edits) and how you stack commits and PRs. Break work into small units that each end in a check, verify each before the next, and order delivery so the sequence proves itself.
- **Test Behavior, Not Implementation** ([`test-behavior-not-implementation.md`](principles/test-behavior-not-implementation.md)). Writing, changing, or keeping a test. Assert what the code's users can observe, so the test fails when that behavior breaks and keeps passing when only the internals change.
- **Ground Claims in the Environment** ([`ground-claims-in-the-environment.md`](principles/ground-claims-in-the-environment.md)). Before acting on a claim about how code, a tool, an API, or a system behaves, and before any docs lookup. Verify it in the code and the versions where the work runs; read docs only for those versions.
- **Explain the Number** ([`explain-the-number.md`](principles/explain-the-number.md)). Before you measure, and before you trust, report, or act on a number you measured (a speedup, a regression, a throughput, a latency, or an eval result). Find what limits it, and rule out that it measured something other than the work you think.

**Delegation**

- **Guard the Context Window.** Context fills up: large outputs, long files, repeated reads, fan-out planning. Size phases, cap scope, route bulk discovery to subagents, and keep summaries rather than raw payloads in the main thread.
- **Never Block on the Human** ([`never-block-on-the-human.md`](principles/never-block-on-the-human.md)). Tempted to ask "should I do X?" on reversible in-scope work within the active playbook's authority. Proceed, present the result, let the human course-correct.

**Infrastructure**

- **Act Through the Narrowest Identity** ([`act-through-the-narrowest-identity.md`](principles/act-through-the-narrowest-identity.md)). Before the first live command, and again before any apply, destroy, or bulk change. Name the identity and resolved target from the tool itself, act with least privilege, lean on platform guards.
- **Bound Change Exposure** ([`bound-change-exposure.md`](principles/bound-change-exposure.md)). Rolling out an infrastructure change, pushing config or a flag, running a bulk change, or re-running a step that timed out. Representative unit first, stop signals set in advance, widen only after it bakes; a timeout is an unknown outcome, not a failure.
- **Design Recovery First** ([`design-recovery-first.md`](principles/design-recovery-first.md)). A change touching availability, storage, data, access, or external side effects. Name what recovery restores, what it cannot, and the evidence it works; never cut off your own way back.
- **Inventory Before Destroy** ([`inventory-before-destroy.md`](principles/inventory-before-destroy.md)). Any delete, destroy, decommission, prune, or cleanup of a live resource. Resolve selectors to a counted list of exact identifiers, then a reversible stage before the irreversible one.
- **Leave No Residue** ([`leave-no-residue.md`](principles/leave-no-residue.md)). Before a diagnostic that can write, and before closing any diagnosis, repair, rollout, or incident. Preserve what the probe could destroy; remove or name everything the work left behind.
- **Preserve Compatible Transitions** ([`preserve-compatible-transitions.md`](principles/preserve-compatible-transitions.md)). Protocol, endpoint, schema, serialization, or config changes across mixed versions or persisted data. Expand, migrate, then contract, readers before writers; every stage keeps a version you can roll back to.
- **Verify the Negative Space** ([`verify-the-negative-space.md`](principles/verify-the-negative-space.md)). Accepting any live change, rollout, or destruction. Diff a bounded neighbour set before and after; only the approved targets may differ, and the change must survive the owner's next reconcile.
