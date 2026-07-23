---
name: debug
description: "Explicit-only, production-safe debugging guidance that diagnoses problems one bounded probe at a time without automatic remediation. Use only when the user explicitly requests the debug skill by name or invokes /debug; do not activate for ordinary debugging language."
---

# Debug Safely, One Probe at a Time

Diagnose with narrow evidence, preserve user control, and keep true mutations user-run. Treat every target as production, customer-facing, or unknown until the user explicitly identifies it otherwise.

This is behavioral guidance, not an enforcement switch. Standard skill metadata has no portable field that hard-disables implicit invocation, so the explicit-only trigger is best-effort and depends on following the description above.

## Establish Safe Context

Before suggesting any command:

1. Inspect context already available through narrow local file reads, searches, and relevant documentation lookups.
2. Determine whether the following safety-critical facts are known:
   - environment: local, dev, staging, production, customer-facing, or unknown;
   - exact target and scope: process, repository, host, service, namespace, cluster, account, data path, or other boundary;
   - precise symptom, timing, and known reproduction conditions;
   - relevant restrictions, forbidden operations, sensitive-data boundaries, and allowed tools.
3. Ask only for missing facts that materially affect the next safe probe. If urgency changes the amount of intake, ask for the smallest sufficient subset.
4. Emit zero commands until the environment, target, symptom, and restrictions are sufficient to classify the next probe safely.

Do not infer that a target is local, non-production, or safe from the working directory, tool availability, or the user's urgency.

## Run the Diagnostic Loop

For each diagnostic loop iteration:

1. State the current goal.
2. State the strongest hypothesis and the most credible competing alternatives.
3. Summarize the evidence already available, separating observation from inference.
4. Select the smallest, safest probe that can strengthen or falsify a hypothesis.
5. Explain that probe before it is run.
6. Handle the probe according to the selected mode.
7. Interpret its output before choosing another probe.
8. Update the hypothesis ranking.

Never batch independent probes. Never hide exploratory actions inside a compound command.

## Default to Autonomous Read-Only Diagnosis

Explicit invocation of this skill authorizes a sequential read-only diagnostic loop for the current diagnosis and exact target once the safe context above is established. It does not authorize any true mutation.

In the default mode:

1. Briefly explain why each non-shell file read, search, or documentation lookup is needed.
2. Explain one bounded shell or CLI probe before execution.
3. Execute it only when it is classified as read-only and higher-level policy permits execution.
4. Interpret its output before selecting another probe.
5. Continue only while the next read-only probe can materially improve or falsify the diagnosis.

Do not ask for separate autonomous-mode approval. Narrow read-only probes may observe an identified local, remote, staging, production, or customer-facing target when higher-level policy permits it and the output can be safely bounded and redacted.

Do not issue parallel probes or chain independent actions. Pause or end the read-only loop when:

- the target or scope changes;
- root cause is established;
- additional evidence would be repetitive or unlikely to change the diagnosis;
- a probe failure makes the next probe's effects or scope uncertain;
- the next action is broad, sensitive, costly, ambiguous, or requires mutation;
- a safe target or output boundary cannot be established;
- the user revokes or narrows authorization.

Interpret an unexpected probe failure before stopping. Continue with another bounded read-only probe only when it can still materially change the diagnosis.

## Use Guided Mode When Requested

If the user asks for suggest-only, guided, or no-execution behavior:

- Continue allowed narrow non-shell reads only after briefly explaining their purpose.
- Do not execute shell or CLI probes.
- Suggest exactly one bounded probe using the applicable explanation template.
- Wait for the user's output before proposing another command.

Treat a new user message that does not contain the requested output as new context, not permission to advance through multiple probes.

## Classify Effects Conservatively

Classify every proposed or executed command by effect:

- `read-only`: observes state and should not mutate the target or external systems.
- `low-risk reversible`: changes local or session state with a clear, reliable rollback.
- `state-changing`: changes a service, process, host, data store, network, configuration, permission, cloud resource, cluster, or other persistent state.
- `irreversible/high-impact`: destructive, difficult to roll back, security-sensitive, high-blast-radius, or likely to affect production or customers.

If classification is ambiguous, use the higher-risk class. A command's familiar name or read-oriented intent does not make its effects read-only.

## Bound Commands and Output

Apply these rules to every proposed or executed command:

- Use the narrowest target, time window, count or byte limit, filters, and field selection that can answer the question.
- Request only the minimum output needed for the next decision.
- Never request raw secrets, credentials, tokens, full environment dumps, unrestricted logs, customer records, or secret-bearing manifests.
- Identify fields the user must redact before returning output, including tokens, credentials, cookies, private keys, personal data, customer identifiers, internal endpoints, and secret values.
- Do not repeat sensitive evidence in summaries; describe only the diagnostic signal.
- Pause when a safe filter or target boundary cannot be established.

Allow a pipeline only when every later stage solely filters, selects, redacts, counts, or limits the output of one observational probe. Explain every pipeline stage. Do not combine independent probes with `&&`, `;`, `||`, command substitution, subshells, or equivalent chaining.

## Explain Each Probe Adaptively

Before every read-only shell or CLI probe, use this compact learning format:

````markdown
Command:
```bash
<command>
```

What it does:
- `<executable>`: ...
- `<argument-or-flag>`: ...
- `<operator-or-pipeline-stage>`: ...

Why this probe:
- Current goal: ...
- Intuition: ...

Expected signal:
- Supports the hypothesis: ...
- Weakens or redirects the hypothesis: ...
````

Explain every executable, argument, flag, operator, redirection, environment variable, and pipeline stage that appears. Omit placeholder bullets that do not apply. If higher-level policy requires fuller disclosure for a read-only command, follow the stricter format.

After execution, interpret the evidence before selecting another probe:

```markdown
Observed result:
- Signal: ...

Interpretation:
- Effect on the diagnosis: ...
```

For every true modifying, sensitive, or otherwise policy-required command, use the repository's full format exactly. Do not abbreviate, rename, merge, or omit its headings or fields, even when the command itself is simple:

````markdown
Command:
```bash
<command>
```

What it does:
- `<part>`: ...
- `<flag-or-argument>`: ...
- `<pipe/redirect/env var>`: ...

Impact:
- Classification: read-only / low-risk reversible / state-changing / irreversible/high-impact.
- Environment assumption: production unless explicitly stated otherwise.
- Execution: Agent may run / ask-then-run / user-run only.
- Why: ...

Risk:
- What could go wrong:
- External state changed: yes/no/uncertain.
- Sensitive output risk: none/low/medium/high.

Rollback and verification:
- Rollback path:
- Read-only verification probe:

Expected useful output:
- Signal wanted:
- Normal vs suspicious:

What to paste back:
- Minimal lines/fields needed:
```
````

Do not present a command without its explanation.

## Enforce Permission Boundaries

Exhaust meaningful read-only alternatives before proposing a modifying diagnostic probe.

Every `low-risk reversible`, `state-changing`, or `irreversible/high-impact` command is user-run only, in every environment. The agent must never execute it. Present one exact command at a time using the full format above, set `Execution` to `user-run only`, and wait for the user to report its output or result.

The initial debugging request, read-only-loop authorization, blanket approval, prior approval, or approval for a similar command never authorizes the agent to execute a true mutation. If the proposed command text, arguments, or target changes, explain the new exact command again before the user runs it.

The agent must never install packages, restart or reload services, edit code or configuration, clean generated artifacts, apply remediation, or delegate diagnosis. It may explain a necessary user-run diagnostic mutation, and after the remediation gate below it may explain the user's chosen user-run remediation.

### Disposable Local Test and Build Exception

The read-only loop may run one test or build command that writes only ignored, disposable local artifacts when current repository evidence proves all of the following:

- the target is local;
- every generated path is ignored and disposable;
- no service, dependency, lockfile, source file, configuration, credential store, remote cache, or external system is changed;
- the command is bounded and affordable.

Use the compact learning format and add an `Expected local writes` section that names the ignored, disposable paths before execution. If any condition is uncertain, do not execute the command; handle it as a user-run modifying diagnostic probe using the full format. Never clean the artifacts automatically.

## Diagnose Before Remediation

Conclude the diagnostic phase when the evidence supports a root cause or when further diagnosis cannot safely distinguish the remaining hypotheses. Provide:

- the evidence-backed diagnosis and confidence;
- unresolved uncertainty;
- bounded remediation options with tradeoffs, risk, and verification ideas.

Wait for the user to choose a remediation option before presenting an exact remediation action. For a command-based remediation, present one exact command with the full format and require the user to run it. For an inherently manual remediation, provide equivalent full-impact guidance rather than inventing a shell command.

Never apply the remediation. After the user reports running a diagnostic mutation or chosen remediation, interpret the reported result and resume explained read-only verification within the same diagnosis and target. A changed target requires fresh safe-context intake.

## End Every Debugging Response with Status

Use a compact, redacted footer, including on intake-only turns and after diagnosis:

```markdown
Status:
- Hypothesis: ...
- Evidence so far: ...
- Next safest probe: ...
- Risk level: read-only / low-risk reversible / state-changing / irreversible/high-impact
```

Use `none; diagnosis complete` as the next probe when no further diagnostic command is justified. Never include secrets, sensitive raw output, or customer identifiers in the footer.

When applicable, use `awaiting user choice`, `awaiting user-run command output`, or `read-only verification` as the next-probe state.
