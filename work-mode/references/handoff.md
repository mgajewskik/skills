# Irreversible handoff

Every irreversible change, and every production change outside a grant, leaves the agent as a handoff file that the user reads, approves, and executes. The agent prepares it and verifies the result; the user runs it. Reversible changes do not use this file; they follow the journal path in [the contract](contract.md).

Write handoffs to `./.work-mode/handoffs/`, lint them, and give the user the fingerprint.

```text
agent drafts handoff --> check_handoff.py check --> fingerprint F
                                                        |
user reads, approves F --> journal: approval @ F (by owner, typed by the user)
        |
user executes exactly F --> reports result
        |
agent: journal check owner-approved @ F  (handoff edited since? fingerprint differs -> NOT-VERIFIED, re-approve)
agent: bounded read-only verification --> journal evidence entries per claim @ revision
```

## Format

Header fields come before the first section. Every section is required and non-empty. `destroy` adds `## Inventory` and `## Reversible first`.

```markdown
# Handoff: <one-line purpose>

Class: modify | deploy | destroy | contain
Environment: production | staging | development | unknown
Owner: <who executes and accepts>
Revision: <artifact revision, plan file digest, or change id this handoff executes>

## Targets
Count: <N>
- <exact identifier 1>
- <exact identifier N>

## Inventory            (destroy only: dependents, consumers, retention or backup status, owner per target)
## Reversible first     (destroy only: the disable / detach / scale-to-zero / retain step, its observation window, and the point after which the next step is irreversible)
## Preconditions        (state that must hold right before execution, with the read-only check that shows it)
## Commands             (fenced block; exact commands in order; no placeholders)
## Expected signal      (normal output and the suspicious output that means stop)
## Stop conditions      (observable thresholds chosen for this workload, not copied numbers)
## Recovery             (what restores what, and what cannot be restored)
## Verification         (consumer-level checks the agent will run read-only afterwards)
## Must not change      (the negative space: neighbours, counts, and paths that must be identical afterwards)
```

Git and forge actions that are user-executed (any push other than to the user's working branch, force-push, remote branch delete, merge, tag, release, opening or changing a PR) do not need this file. Hand over the exact command, what it changes, and how to undo it, in the reply.

## What the linter enforces and what it cannot

`python3 <work-mode>/scripts/check_handoff.py check <file>` fails on a missing field or section, an unknown class or environment, an unfilled `<placeholder>` anywhere (including inside commands), a target written as a pattern (`*`, `?`, `all`), a `Count:` that differs from the list, or commands outside a fenced block. It prints `file:line` problems and the fingerprint.

It cannot tell whether the commands do what the purpose says, whether the targets are the right ones, or whether recovery works. Those claims need journal evidence or an independent reviewer. A clean lint is a completeness check, not approval.

## Binding approval to the exact action

`python3 <work-mode>/scripts/check_handoff.py fingerprint <file>` prints a sha256 over the normalized file. The user records approval themselves, by running this command after reading the handoff. Hand it over with the fingerprint and the journal path filled in:

```sh
python3 <work-mode>/scripts/journal.py record approval --target <environment/scope> \
  --fingerprint <fingerprint> --by owner --evidence "<where the user approved>"
```

`--by owner` is a plain argument, so the journal is only as honest as whoever writes it. The agent never records an `approval`; an agent that records one for the user has forged it, whatever the chat said. Where approval must hold against a careless or compromised agent, keep the journal where the agent cannot write.

Before interpreting the user's execution report, recompute the fingerprint and run `journal.py check --target <environment/scope> --revision <fingerprint> --claim owner-approved`. Any edit after approval, including a changed target or command, produces a new fingerprint and `NOT-VERIFIED`. Re-approval is the user's decision.

## Recording verification

After execution, record each acceptance criterion and each `Must not change` item as its own `evidence` entry against the revision that is now running: `--by agent` for your observations, `--by verifier` for an independent reviewer. `journal.py check` exits 0 only for `established`. The rollout or teardown is accepted only when every claim checks 0 for the current revision.
