# Formats and Professional Communication

Use this reference for reader/task/channel fit in professional messages and owned formats. Keep the artifact self-contained for an asynchronous reader: state the purpose, necessary context, required response or decision, owner, and timing when relevant. Put the key message first unless the reader benefits from a different sequence.

## Email

Use a specific subject that names the topic and purpose. Open with the request, decision, or status in one or two sentences. Add only context needed to act. End with the needed response, owner, deadline, and next step.

- Request: state the ask, why it matters, and the deadline.
- Status: state current state, concrete progress, blockers or risks, and next step.
- Escalation: state the issue, impact, what has been tried, and the decision or help needed.

Keep one primary topic per email. Prefer short paragraphs or bullets when they improve scanning.

## Chat

Write so the recipient can respond without a follow-up for missing context. Do not send a greeting and wait. Open with the actual question, update, or request; include the relevant link, identifier, error, or deadline. Use a thread for follow-up detail when the channel needs to remain scannable. Avoid over-structuring ordinary social conversation.

## Meetings

In an invite, state the objective, expected outcome or decision, concise agenda, required pre-read, and preparation needed. Do not schedule a meeting when a short asynchronous request would resolve the issue.

Afterward, send a brief summary with decisions, actions, owners, and dates. Separate decisions from discussion and commitments from suggestions. Record uncertainty rather than implying consensus.

## Status and technical communication

For a status update, make the current state easy to find. Then list concrete completed work, next work, risks or blockers, and the ask if one exists. Name owners and dates when available. Replace vague progress language with observable state such as shipped, blocked, due, or at risk.

When translating technical material for a nontechnical reader, lead with outcome, impact, and decision relevance. Preserve supplied terms of art verbatim unless the user authorizes replacement, then explain them in plain language. Do not silently paraphrase identifiers, error labels, control names, or domain concepts merely to sound simpler. Use an analogy only when it preserves the boundary of the concept; label it as an analogy and stop before it implies behavior the system does not have. Do not erase uncertainty, tradeoffs, limits, or required technical detail.

For a technical error message, use: what happened; why, if useful and known; next action. Preserve exact diagnostic text unless a safe redaction is needed.

## Decisions and executive summaries

Lead with the decision, request, or recommendation. Follow with the few reasons that determine the choice, their evidence, and material tradeoffs. State impact, risk, owner, and next step when relevant. Move history and supporting detail after the answer.

## Technical procedures

When no dedicated documentation framework is requested, use: goal or done-when; prerequisites; ordered actions; verification; common failure and next action. Keep one action per step when that reduces mistakes. Preserve exact commands, identifiers, conditions, and diagnostic text.

## Incidents and postmortems

For an incident update, separate timestamped status, impact, mitigation, hypothesis or confirmed cause, owner, and next update. Never promote a hypothesis to root cause.

For a postmortem, separate summary, measured impact, factual timeline, confirmed cause and contributing factors, what helped or hindered response, and actions with owner, due date, and verification. Be blameless but specific; describe system and process conditions rather than assigning motive.

## Issue and review prose

For an issue, state the problem, expected and actual behavior, reproduction, environment, impact, and safe evidence. For PR or MR prose, state why the change exists, what changed at a high level, risk, validation, rollout or backout, and reviewer focus. A dedicated repository-host skill still owns platform operations and project policy.

## Design documents

Start with the problem, context, constraints, goals, and explicit non-goals. Describe the proposed design, interfaces or data flow, and the decisions it requires. Cover alternatives and tradeoffs; failure modes; security, reliability, and operational concerns; rollout and rollback; risks; and owned open questions. Preserve the rationale future readers need to challenge or reverse the design. Use a diagram when several components, trust boundaries, or non-obvious flows make prose insufficient. A dedicated ADR still owns the final durable decision record.

## Public posts

For a blog or professional social post, open with a concrete claim, problem, or useful tension. Support it with evidence, experience, or an example; state the boundary or caveat; end with a specific takeaway. Preserve the writer's natural voice and avoid generic inspiration, promotional filler, and engagement bait.

## Format boundary

This reference supplies communication patterns, not specialist templates or policy. Commit messages, ADRs, Diátaxis documentation, and READMEs retain their dedicated skill's structure and policy. Use this reference only to improve supplied prose, reader fit, or a professional communication layer after specialist constraints are applied.

Do not import workplace notification etiquette, Scrum or meeting facilitation, response-time or time-zone policy, recording or working-out-loud rules, static jargon/analogy tables, or unsupported business-impact substitutions.
