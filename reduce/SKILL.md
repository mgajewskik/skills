---
name: reduce
description: Manual-only framework for reducing structural complexity and entropy in existing or proposed engineering code and configuration while preserving behavior and authoritative content. Use only when the user explicitly invokes $reduce or names the reduce skill for source code, tests, scripts, or application/build/CI/deploy/infrastructure configuration. Do not activate for generic reduce/improve/refactor requests, $reducing-entropy, prose, Agent Skills or agent-instruction files, general review/debugging, performance/security audits, or behavior-changing redesigns.
---

# Reduce

Reduce total structural complexity while preserving observable behavior, public contracts, effective configuration, and authoritative content. Seek the smallest final result, not merely the smallest diff. A sound result may be: **no worthwhile reduction found**.

## Boundaries

Use this skill for existing codebases, working-tree changes, proposed designs, and proposed diffs involving source code, tests, scripts, or machine-consumed application, build, CI, deploy, or infrastructure configuration.

Do not use it for prose, READMEs, Agent Skills, or AGENTS/CLAUDE-style instructions. Leave generic branch or spec review, debugging, security auditing, performance analysis, and behavior-changing redesign to their dedicated workflows.

Unless the user explicitly authorizes it, do not:

- remove product behavior or suspected obsolete behavior;
- change public contracts, dependencies, or external systems;
- create or modify ADRs, `CONTEXT.md`, glossaries, or other design records;
- treat formatting, minification, merged statements, generated or vendor changes, or lockfile churn as reduction.

Read repository instructions, domain glossaries, and ADRs as constraints. Consult installed specialist skills only when useful; never require them.

## 1. Scope the reduction

Honor the named file, subsystem, configuration area, diff, or proposal. With no target, perform a bounded hot-spot scan using repository instructions, manifests, architecture records, and recent change history when available. Do not turn an unscoped invocation into an exhaustive audit or widen a scan merely to manufacture work.

Before version-sensitive advice, inspect exact local language, framework, runtime, CLI, and configuration versions.

## 2. Define what must survive

Record the relevant:

- inputs, outputs, invariants, ordering, errors, and side effects;
- public interfaces, schemas, configuration behavior, and authoritative decisions;
- performance expectations, security properties, concurrency behavior, and meaningful comments.

List suspected dead or obsolete behavior separately; require explicit approval before removing it. For a proposal without an editable implementation, return a concrete reduced proposal or patch and leave unrelated repository state unchanged.

## 3. Establish a preservation baseline

Before editing, run the smallest targeted existing test, build, schema check, rendered-config comparison, or deterministic probe. Add a minimal characterization test or configuration probe only when preservation risk is material and existing evidence is insufficient.

Stop if a materially risky change lacks a credible baseline. Proceed with a low-risk unknown only after disclosing the unknown and the smallest next verification.

## 4. Scan through the entropy lens

Look for obsolete support code, duplicated behavior, unused indirection, unnecessary configuration layers, and the maximum safe deletion within scope. Prefer simple over familiar and generic data or operations over needless custom abstractions.

Challenge flexibility, separation, type-safety, or readability claims when they add concepts without demonstrated value. Apply the PAGNI (Probably Are Gonna Need It) exception only when the need is evidence-based, later retrofitting is plausibly at least ten times more expensive, and retaining it now is cheap.

Always preserve security fundamentals, auditability, unrecoverable data, compliance obligations, and public compatibility.

## 5. Scan through the architecture lens

Look for shallow modules, wide interfaces, scattered caller knowledge, poor locality, leaking seams, and pure-function extraction that conceals orchestration bugs.

- Judge depth by leverage through the interface, never by implementation-to-interface line ratios.
- Apply the deletion test: if removing a module makes complexity disappear, it was pass-through; if complexity spreads into callers, the module was earning its place.
- Treat the interface as the behavioral test surface and keep internal testing seams private.
- Treat one adapter as a hypothetical seam and two justified adapters as evidence of a real seam. Never create an adapter to satisfy the heuristic.
- Classify dependencies as in-process, locally substitutable, remote-owned, or truly external before recommending merging, ports/adapters, or mocks.
- Delete obsolete shallow-module tests only after equivalent or stronger interface-level behavioral coverage exists.

## 6. Scan configuration semantically

Trace effective values, precedence, overrides, defaults, duplicated keys, layers, ordering constraints, and meaningful comments. Preserve effective behavior, public keys, ordering, and explanatory intent.

Consolidate or normalize only when a tool-native validator, schema, or rendered/effective-output comparison proves equivalence. Never inspect or expose secrets, credentials, tokens, protected environment values, or raw sensitive output.

## 7. Measure without a fake score

Record only relevant axes, independently:

- hand-authored source, configuration, and test lines;
- duplication, concepts, and custom types;
- public interfaces and caller knowledge;
- dependencies, seams, coupling, locality, and affected call sites;
- file count and behavioral test surface.

Require at least one material reduction. Explain every growing axis and why the larger structural reduction justifies it. Reject code golf, removed safeguards, deleted meaningful comments, hidden complexity, test-count gaming, or semantic loss used to improve a metric.

## 8. Present candidates

Present zero to three concise Markdown candidates. For each, include:

- target files, modules, or configuration;
- observed evidence and proposed reduction;
- expected before/after structural change;
- preservation risk and verification method;
- recommendation strength: `Strong` or `Worth exploring`.

Name one top recommendation when candidates exist. Do not design detailed replacement interfaces until the user selects a candidate.

## 9. Resolve and implement one candidate

After selection, ask one question at a time, with a recommended answer, only when unresolved scope, behavior, interface, risk, or tradeoffs would materially change implementation.

When interface design is genuinely uncertain, generate materially different alternatives locally or with optional helpers, then compare depth, locality, dependency strategy, and entropy.

Implement one coherent candidate per cycle under current runtime authorization. Remove only code, tests, configuration, or documentation made demonstrably obsolete by that change. Do not batch adjacent candidates.

## 10. Verify and report

Rerun the exact preservation evidence captured before editing. Inspect the complete selected-candidate diff and remeasure the relevant axes. Report:

- files changed and preserved contracts or authoritative content;
- before/after evidence and the material structural reduction;
- tests, builds, schemas, renders, or probes executed;
- anti-gaming checks, growing axes, unknowns, and skipped validation.

Refresh remaining candidates only after the selected change passes verification.

## Provenance

Original synthesis informed by Matt Pocock's MIT-licensed [`improve-codebase-architecture`](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md), [`codebase-design`](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md), [`grilling`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md), and [`domain-modeling`](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md), plus the MIT-licensed ancestry of [`reducing-entropy`](https://github.com/joshuadavidthomas/agent-skills). No external skill is required at runtime.
