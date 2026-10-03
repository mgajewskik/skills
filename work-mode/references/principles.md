# Pstack skills in work-mode

The router's Principles section indexes every `principle-*` and `infra-principle-*` leaf with its trigger and, for pstack leaves, the limit that applies on live systems. This page covers what the index does not: the non-principle pstack skills that work-mode leans on, and the one pstack leaf left out of the index. All of them are user-only skills in this catalog, loaded by path per the rule at the top of work-mode's `SKILL.md`. [The contract](contract.md) governs every one of them, and [host notes](host-notes.md) translate their Cursor-specific text.

## Pstack skills used by playbooks

| Skills | What work-mode uses them for | Limit |
| --- | --- | --- |
| `how`, `why`, `teach`, `bro` | Cite the actual flow, separate recorded rationale from inference, explain with state diagrams and simpler models. | Explanation authorizes no observation or repair. Missing history stays unknown. |
| `architect`, `figure-it-out`, `arena`, `blast-radius` | Fix the contract and shape before code, compare real alternatives when it matters, trace what a change can break beyond the diff. | Choose by evidence and constraints. No fixed model names or fixed number of lanes. |
| `swarm`, `interrogate` | Disjoint offline questions or outputs; independent adversarial review of consequential work. | Local subagents only. No live probes delegated. Agreement between agents is a reason to look, not proof. |
| `recall`, `reflect`, `show-me-your-work` | Resume state, rejected hypotheses, decision trails; turn repeated errors into checks. | Revalidate evidence after resuming. No automatic tickets, commits, or personal memory writes. |
| `create-verification-skill`, `maintain-verification-skill`, `tdd`, `benchmark-checklist` | Drive real entrypoints with independently expected outcomes; reproduce a defect and rerun its check; vet a measurement before reporting it. | Startup and cleanup can mutate; read effects first. A skip or missing prerequisite never counts as a pass. |
| `technical-writing`, `unslop`, `no-comments` | Precise action, target, effect, expected signal, and uncertainty in prose; cut AI tells; prefer enforceable constraints over comments. | Keep non-obvious operational rationale and recovery limits; do not carry a blanket deletion bias into live systems. |

## Installed but not indexed

`principle-experience-first` (choose user delight over implementation convenience) is about product and UX scope. It stays installed for product work; work-mode does not cite it. On live systems, operator convenience and urgency never override authority or erase uncertainty.

## Infra leaf anatomy

Every `infra-principle-*` leaf has the same parts, so a reader can find the checkable bits fast. Pstack leaves keep their upstream structure.

```text
description      trigger-phrased: "Apply when ..."
# Title          one-paragraph rule
## Why           the source that justifies it, linked
## Pattern       numbered steps
The test:        one question that shows whether you applied it
You skipped this when ...   an observable sign it was skipped
## Stop and limit            where the rule stops applying
```

The catalog's `scripts/check_work_mode.py` checks the infra leaves for these parts.
