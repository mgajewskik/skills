# Trust

An agent's "done" is a report, and a report is the weakest evidence there is. work-mode is built so that you can trust a result without trusting the agent's word for it.

## Four rules

- **The author never verifies its own work.** A significant change gets an independent reviewer that sees criteria, anti-criteria, changed paths, and evidence pointers, not the author's conclusion. It closes only on `Decision: PASS` or your explicit waiver.
- **Verdicts bind to a revision.** Evidence and approvals are keyed to a target and a revision or fingerprint. A new revision starts unverified. An edited handoff has a new fingerprint and needs a new approval.
- **Unknown is never a pass.** A skipped check, a missing tool, or evidence from another host or time window is `unverified`.
- **Every claim carries a label.** `established`, `failed`, or `unverified` for outcomes; measured, inferred, or guess for causes. You can scan a reply for what was actually shown.

## The evidence ladder

```text
rung  evidence                                                   enough for
----  ---------------------------------------------------------  -----------------------------
0     a report: the agent's, a subagent's, an exit code, green   nothing on its own
1     a source pointer: the file or doc that says how it works   explaining intent
2     the agent's own bounded read-only observation, in context  diagnosis, one acceptance claim
3     a rerunnable check, recorded with journal.py               gates between rollout units
4     an independent non-author verdict on the fingerprint       calling significant work ready
5     your approval of that exact fingerprint, recorded by you   handing over an irreversible change
```

## What the scripts enforce

Prose can be skimmed; scripts cannot. Each guard below has a test in `work-mode/scripts/` (`test_scripts.py`, `test_watch_pr.py`), and each guard was mutation-checked: removing it from a copy of the script makes a test fail.

| Guard | Enforced by |
| --- | --- |
| A live change has a snapshot file and a revert command before it runs | `journal.py record change` refuses otherwise |
| A production change cites a recorded grant | `journal.py record change --env production` refuses without `--grant` |
| Approvals come from you | `journal.py record approval` requires `--by owner`; the agent is told never to run it |
| A self-report cannot hide a reviewer's failure, and nobody overrules yours | `journal.py check`: a newer success cannot clear a `failed` from a higher-ranked author (agent < verifier < owner) |
| An old success cannot hide a fresh failure | `journal.py check`: the newest `failed` or `unverified` entry blocks, whoever wrote it |
| Evidence does not travel between revisions or targets | `journal.py check` matches target and revision exactly |
| Secrets stay out of the journal | values and snapshot files that look like keys, tokens, passwords, or URL credentials are refused (a net, not a proof: redact first) |
| "Revert everything since 9:00" means changes made since 9:00 | `revert-plan all-since` filters on each change's creation time, not its last update |
| The working directory never lands in a commit | `journal.py init` adds `.work-mode/` to the local git exclude before anything is written there |
| A malformed journal is noticed | every command fails loudly on bad JSON, unknown kinds, or unknown fields |
| A revert plan never re-applies a revert | `journal.py revert-plan` skips changes that are themselves reverts |
| Babysit's status tool cannot change a PR | `watch_pr.py` runs only `gh pr view/list/checks`, GraphQL queries, and `git remote get-url`; a test records every command it issues |
| `READY` means nothing the agent can fix is left, and shows what GitHub still holds | `watch_pr.py` waits while GitHub's mergeability is `UNKNOWN`, reports a merge refused over a failing head commit even when the check list looks green, reads every page of review threads, and carries `mergeState` and `reviewDecision` in each row (a required review can still be outstanding at `READY`) |
| A handoff is complete and names exact targets | `check_handoff.py check`: required sections, no placeholders, no wildcards, count matches |

## What nothing can enforce

`--by owner` is a plain argument. An agent that types it has forged your approval, and the journal cannot tell. The skill text forbids it, and the reviewer looks for it, but if an approval must hold against a careless or compromised agent, keep the journal where the agent cannot write.

Reversibility is a judgment. The checklist and its evidence are the guard; "unsure" resolves to irreversible. The eval fixtures include an ambiguous case to keep that honest.

A linted handoff is complete, not correct. Whether its commands do what its purpose says is a claim that needs evidence or a reviewer.
