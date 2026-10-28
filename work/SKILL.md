---
name: work
description: Work discipline for any task that changes or investigates code, config, or infrastructure. Use when the user asks you to do work (build, fix, change, clean up, debug, review, deploy, investigate), or when work lands in front of you mid-task or in a delegated brief. Casual questions do not need it.
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "echo 'work is on for this session. When this prompt asks for work, follow the work skill. If its content is no longer in your context, load the work skill again first. Ignore this on a casual turn.'"
  SubagentStart:
    - matcher: "^(general-purpose|sonnet|claude|Plan)$"
      hooks:
        - type: command
          command: >-
            echo '{"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": "The parent session runs the work skill. Before any work, load the work skill and follow it."}}'
---

# Work

## Non-negotiables

The Principles section below grounds every trigger. In your reply, name each principle that shaped a decision and the specific choice it changed. Cite only principles whose leaf SKILL.md you read this session.

**No comments.** Code you write, and every delegate diff you accept, carries no comments. Make the code say it instead: a precise name, an extracted function, a type, a test. A surprise in our own code that this change can make obvious gets reshaped, not explained. Write a comment only in two cases:

- The user asked for that comment.
- The code is deliberately unusual and a future reader would otherwise "fix" it: a vendor or platform bug, a protocol quirk, an external constraint, or a workaround whose root fix is out of scope. The comment says why it is this way, what breaks if it changes, and when it can change (an issue, a version, a condition).

`# Load config` or `// increment the retry counter` gets deleted. `# The billing API returns 200 with an error body (issue #123); keep the body check until v3.` stays. Tool directives (shebangs, lint or type suppressions, build tags), license headers, and doc comments the repo's tooling requires are code, not comments. Existing comments outside your change stay; one your change makes false is fixed or deleted. Every review brief (PASS-gate or Independent review) lists "no comment outside these two cases" as an anti-criterion.

## Playbooks

Match the task to a playbook, open its file, and copy its steps into the todolist verbatim before any task-specific todos. A step you skip stays in the list with `skip: <reason>`. When a task spans several playbooks, name the current one and its exit evidence before moving on.

Code is everything kept in version-controlled files: application code, tests, scripts, config, and infrastructure as code (manifests, roles, unit files, pipelines). Code playbooks work locally and offline: nothing is applied, initialized against a real backend, installed, or deployed; a code change reaches a live system only through Deploy. Ops are operations run against live systems by executing commands. A question about a live system's current behavior is Debug. A mixed task ("fix the Terraform module and roll it out") starts where the failure is observed and hands over at the boundary, naming the exit evidence.

**Code**

- **Implement.** Build or change code and verify it offline. [`implement.md`](playbooks/implement.md).
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

- **Guided.** The user runs every command and makes every change; you guide from their pasted output. Wraps the matched playbook. Use when the user asks to be guided or walked through, or says not to execute. [`guided.md`](playbooks/guided.md).

## Work log

Every task keeps one log, continued across the playbooks it chains through. It is the audit record the user reads weeks or months later, without running a command, to see what changed, why, on what evidence, how it was verified, and how to undo it; whatever the environment will lose by then must be in it. Write it only through `uv run <this skill's directory>/scripts/log.py`, run from inside the project (`--help` lists every field); each log is a directory `.work/<id>/` holding `log.yml` and its artifacts, excluded from git. Playbook steps say "log" for these calls:

- **Start** at the playbook's first step: `new <kebab-slug> --task "<one sentence>" --playbook <name>`. It prints the log id.
- **Phase** at each playbook step: `phase <id> "<step number and name>"`. Later entries carry it.
- **Run** for every command you execute: `add <id> run --class read-only|reversible|irreversible --command ... --target ... --identity ... --why ... --result ...`, logged before you execute a change. A revert you execute carries `--reverts <n>`. Commands that use `{artifact}` run from the project root.
- **Plan** for a command handed to the user or proposed for later: `add <id> plan --by user|agent --class ... --command ... --why ...`. When a plan is executed, by you or by the user's report, log `add <id> run --by user|agent --from-plan <n>`; a revert the user ran is `run --by user --class ... --command ... --reverts <n>`.
- **Revert** on every change, run or plan, so the user can undo it alone: `--revert` with the exact command; an irreversible change gives its best-known recovery or `--no-revert "<reason>"`. When the revert needs a manifest or prior state, save it to a file, pass `--artifact <file>`, and write `{artifact}` in `--revert` where its path goes (`kubectl apply -f {artifact}`).
- **Evidence** for each claim and the command that observed it: `add <id> evidence --claim ... --status established|failed|unverified --command ...`.
- **Decision** for each choice that shaped the work (a fork, a pivot, an abandoned approach): `add <id> decision --text "<what was chosen>" --why ... --evidence <n,n> --rejected "<alternatives and why not>"`.
- **Note** for criteria, hypotheses, options, and resume notes: `add <id> note --text ...`.
- **Artifact** for anything the reader needs that the environment will lose: output that informed a decision or verified a claim (unless it fits verbatim in `--result`), snapshots, previews, manifests, inventories, scraped logs. Write the file under `/tmp`, then pass `--artifact <file>` on the entry it belongs to; it is saved as `<entry number>-<name>`.
- **Correct** a wrong entry with a new one carrying `--supersedes <n>`; never edit the log by hand.
- **Root cause**, gate, revert, close: `root-cause <id> ...`, `check <id> ...`, `revert-plan <id>` (prints only; each revert still follows the playbook's authority rule), and `close <id> --status done|halted|reverted --summary ...` at the end. Before closing, walk the timeline against what you actually did: log any missing decision, pivot, or abandoned approach, and supersede any entry that is wrong.

Write entries the way you would tell a teammate what you did: plain words and concrete actions. A refused value looks like a secret: redact it and log again. Name the log path in the reply.

## Principles

Each principle names when it applies. When one fires, read its `SKILL.md` in full before acting on it. Paths are relative to this skill's directory.

**Core**

- **Laziness Protocol** ([`principles/laziness-protocol`](principles/laziness-protocol/SKILL.md)). Refactoring, sizing a diff, or tempted to add abstractions, layers, or signal threading. Bias to deletion and the smallest change that solves the problem.
- **Foundational Thinking** ([`principles/foundational-thinking`](principles/foundational-thinking/SKILL.md)). Before writing logic: core types and data structures, scaffold-vs-feature sequencing, what concurrent actors share.
- **Redesign from First Principles** ([`principles/redesign-from-first-principles`](principles/redesign-from-first-principles/SKILL.md)). Integrating a new requirement into an existing design. Redesign as if it had been foundational from day one.
- **Attack the Premise** ([`principles/attack-the-premise`](principles/attack-the-premise/SKILL.md)). Two or more fixes that share one premise have failed the same gate. Take a census of which actors hold the imbalance before the next fix, then question the premise instead of writing another fix that assumes it.
- **Subtract Before You Add** ([`principles/subtract-before-you-add`](principles/subtract-before-you-add/SKILL.md)). Sequencing an addition, refactor, or rewrite. Remove dead weight first, then build on the simpler base.
- **Minimize Reader Load** ([`principles/minimize-reader-load`](principles/minimize-reader-load/SKILL.md)). Reviewing or shaping code that's hard to trace. Count layers and hidden state, collapse one-caller wrappers, shrink mutable scope.
- **Outcome-Oriented Execution** ([`principles/outcome-oriented-execution`](principles/outcome-oriented-execution/SKILL.md)). Planned rewrites and migrations with explicit phase boundaries. Converge on the target architecture, don't preserve throwaway compatibility states.
- **Experience First** ([`principles/experience-first`](principles/experience-first/SKILL.md)). Product, UX, or feature-scope tradeoffs. Choose user delight over implementation convenience.
- **Exhaust the Design Space** ([`principles/exhaust-the-design-space`](principles/exhaust-the-design-space/SKILL.md)). A novel interaction or architectural decision with no precedent. Build 2-3 competing prototypes and compare before committing.
- **Build the Lever** ([`principles/build-the-lever`](principles/build-the-lever/SKILL.md)). Any non-trivial work. Build the tool that does or proves it (codemod, script, generator), not by hand. The tool is the artifact a reviewer reruns.

**Architecture**

- **Model the Domain** ([`principles/model-the-domain`](principles/model-the-domain/SKILL.md)). Writing stateful logic, or code that branches a lot or repeats a shape assumption across files. Encode the domain in a structure (state machine, typed model, table or registry, reducer, boundary, the right collection) instead of scattered conditionals.
- **Boundary Discipline** ([`principles/boundary-discipline`](principles/boundary-discipline/SKILL.md)). Wiring validation, error handling, or framework adapters. Guards at system boundaries, trust internal types, keep business logic pure.
- **Type System Discipline** ([`principles/type-system-discipline`](principles/type-system-discipline/SKILL.md)). Designing types or a signature in any typed language. Make illegal states unrepresentable, brand primitives, parse external data at boundaries.
- **Make Operations Idempotent** ([`principles/make-operations-idempotent`](principles/make-operations-idempotent/SKILL.md)). Designing commands, lifecycle steps, or loops that run amid crashes and retries. Converge to the same end state.
- **Migrate Callers Then Delete Legacy APIs** ([`principles/migrate-callers-then-delete-legacy-apis`](principles/migrate-callers-then-delete-legacy-apis/SKILL.md)). Introducing a new internal API while old callers exist. Migrate and delete in one wave.
- **Separate Before Serializing Shared State** ([`principles/separate-before-serializing-shared-state`](principles/separate-before-serializing-shared-state/SKILL.md)). Concurrent actors might write the same file, branch, key, or object. Eliminate the sharing first.

**Verification**

- **Prove It Works** ([`principles/prove-it-works`](principles/prove-it-works/SKILL.md)). After a task, before declaring done. Verify against the real artifact, not a proxy or "it compiles".
- **Fix Root Causes** ([`principles/fix-root-causes`](principles/fix-root-causes/SKILL.md)). Debugging. Trace each symptom to its root cause, reproduce first, ask why until you reach it.
- **Sequence Work into Verifiable Units** ([`principles/sequence-verifiable-units`](principles/sequence-verifiable-units/SKILL.md)). Multi-step work (sweeps, migrations, runs of similar edits) and how you stack commits and PRs. Break work into small units that each end in a check, verify each before the next, and order delivery so the sequence proves itself.
- **Test Behavior, Not Implementation** ([`principles/test-behavior-not-implementation`](principles/test-behavior-not-implementation/SKILL.md)). Writing, changing, or keeping a test. Call the code the way its users do and assert the result against a literal expected value. If the test would still pass when every imported function returns `undefined`, rewrite the assertion or delete the test.
- **Ground Claims in the Environment** ([`principles/ground-claims-in-the-environment`](principles/ground-claims-in-the-environment/SKILL.md)). Before acting on a claim about how code, a tool, an API, or a system behaves, and before any docs lookup. Verify it in the code and the versions where the work runs; read docs only for those versions.
- **Explain the Number** ([`principles/explain-the-number`](principles/explain-the-number/SKILL.md)). Before you measure, and before you trust, report, or act on a number you measured (a speedup, a regression, a throughput, a latency, or an eval result). Find what limits it, and rule out that it measured something other than the work you think.

**Delegation**

- **Guard the Context Window** ([`principles/guard-the-context-window`](principles/guard-the-context-window/SKILL.md)). Context fills up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents, keep summaries in the main thread.
- **Never Block on the Human** ([`principles/never-block-on-the-human`](principles/never-block-on-the-human/SKILL.md)). Tempted to ask "should I do X?" on reversible work. Proceed, present the result, let the human course-correct.

**Meta**

- **Encode Lessons in Structure** ([`principles/encode-lessons-in-structure`](principles/encode-lessons-in-structure/SKILL.md)). You catch yourself writing the same instruction a second time. Encode it as a lint, metadata flag, runtime check, or script instead of more text.

**Infrastructure**

- **Act Through the Narrowest Identity** ([`principles/act-through-the-narrowest-identity`](principles/act-through-the-narrowest-identity/SKILL.md)). Before the first live command, and again before any apply, destroy, or bulk change. Name the identity and resolved target from the tool itself, act with least privilege, lean on platform guards.
- **Bound Change Exposure** ([`principles/bound-change-exposure`](principles/bound-change-exposure/SKILL.md)). Rolling out a change, pushing config or a flag, running a bulk change, or re-running a step that timed out. Representative unit first, stop signals set in advance, widen only after it bakes; a timeout is an unknown outcome, not a failure.
- **Design Recovery First** ([`principles/design-recovery-first`](principles/design-recovery-first/SKILL.md)). A change touching availability, storage, data, access, or external side effects. Name what recovery restores, what it cannot, and the evidence it works; never cut off your own way back.
- **Inventory Before Destroy** ([`principles/inventory-before-destroy`](principles/inventory-before-destroy/SKILL.md)). Any delete, destroy, decommission, prune, or cleanup of a live resource. Resolve selectors to a counted list of exact identifiers, then a reversible stage before the irreversible one.
- **Leave No Residue** ([`principles/leave-no-residue`](principles/leave-no-residue/SKILL.md)). Before a diagnostic that can write, and before closing any repair, rollout, or incident. Preserve what the probe could destroy; remove or name everything the work left behind.
- **Preserve Compatible Transitions** ([`principles/preserve-compatible-transitions`](principles/preserve-compatible-transitions/SKILL.md)). Protocol, schema, serialization, or config changes across mixed versions or persisted data. Expand, migrate, then contract; every stage keeps a version you can roll back to.
- **Verify the Negative Space** ([`principles/verify-the-negative-space`](principles/verify-the-negative-space/SKILL.md)). Accepting any live change, rollout, or destruction. Diff a bounded neighbour set before and after; only the approved targets may differ, and the change must survive the owner's next reconcile.
