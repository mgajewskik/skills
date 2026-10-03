# Authority and revert

work-mode does not have an autonomy level. It decides, for each action, whether the agent runs it or you do. The rule lives in `work-mode/references/contract.md`; this page explains it and walks through one change, its revert, and a deletion.

## Who runs what

```text
action
  |
  +-- read-only, narrowly scoped --------------------------------> agent
  +-- local file edits the task asked for -----------------------> agent
  +-- local tests and validators, after reading what they do ----> agent
  +-- git: local operations (branch, commit, rebase unpushed) ---> agent
  +-- git: push without force to your working branch ------------> agent
  +-- git: any other push, force-push, remote branch delete,
  |        merge, tag, release, PR open/close/merge/review ------> you
  |
  +-- live change (cloud, cluster, host, service, database)
        |
        +-- production? -- no grant ---------------------------> you
        |               -- session grant covers it ------------> continue below
        |
        +-- reversibility checklist, every item yes with evidence
        |
        +-- all yes ----------> agent: journal entry first, execute, verify, record
        +-- any no / unsure --> you: handoff, you run it, agent verifies
```

"Your working branch" is the one branch you are working on in this task: the one you named, or the non-default branch checked out when the task started. The agent never pushes to the default branch, to another person's branch, or to a branch it created unless you named it.

Some actions are irreversible whatever the checklist says: deleting resources or data, data writes and repairs, secret or key rotation, removing an identity's permissions, and anything that sends a message or notifies people. One message is the agent's: on a PR you asked it to babysit, it replies to review threads and resolves the review-bot threads it fixed or dismissed. The replies go out under your `gh` account. Human reviewers resolve their own threads, and reviews, approvals, top-level comments, and anything on another PR stay yours. A deny or disable stage during a teardown is judged by the checklist instead. Installing or upgrading dependencies always needs your approval first.

## The reversibility checklist

| Item | What counts as yes |
| --- | --- |
| Prior state captured | A redacted snapshot file of exactly what changes, read just before the change. |
| Revert written and executable | The exact restoring command, and evidence the agent's identity may run it. |
| Nothing lost, nothing sent | No data written or deleted, no rotation, no permission removed, no message, payment, or webhook; no in-flight state dropped by a restart. |
| Verification both ways | A read-only signal showing the change took effect, and the same signal showing the revert restored the snapshot. |

"Unsure" counts as no. A reconciler that owns the field (Terraform, Argo CD, a controller) also makes it a no until ownership is settled, because the revert would race the reconciler.

## Production grants

Production changes are yours unless you grant a session-scoped permission in words that name the environment, the scope, and the change types:

> prod-eu, namespace payments, scale and config values, no deletes

The agent records your words as a `grant` entry and cites its id on every production change. Inside the grant, reversible changes go through the same journal path as staging. Irreversible changes are still yours. The grant ends with the session.

## Worked example: a reversible change and its revert

The task: turn on debug logging for the `api` service in staging to chase a bug. Output below is real, from running `journal.py` in a scratch git repository; long JSON lines are trimmed to the fields that matter.

**1. Classify.** The change is a ConfigMap value in `staging-eu`. The agent reads the current value (`LOG_LEVEL: info`) into a snapshot, checks `kubectl auth can-i patch configmaps -n payments`, confirms nothing is written or sent and that the `api` pods are stateless and roll with graceful shutdown, and names the verification signal. Every item is yes, so the change is reversible.

**2. Journal first.**

```text
$ journal.py record change --env staging --target "staging-eu/payments/configmap api-config" \
    --command "kubectl -n payments patch configmap api-config --type merge -p '{\"data\":{\"LOG_LEVEL\":\"debug\"}}'" \
    --snapshot .work-mode/snapshots/c1-api-config.yaml \
    --revert  "kubectl -n payments patch configmap api-config --type merge -p '{\"data\":{\"LOG_LEVEL\":\"info\"}}'" \
    --reversibility "snapshot c1-api-config.yaml; kubectl auth can-i patch configmaps -n payments = yes; ..." \
    --verification "kubectl -n payments get configmap api-config -o jsonpath='{.data.LOG_LEVEL}' ..."
{"id": "c1", "kind": "change", "env": "staging", "status": "pending", "snapshot": ".work-mode/snapshots/c1-api-config.yaml", ...}
```

The first write also adds `/.work-mode/` to `.git/info/exclude`, so the journal never shows up in `git status`.

**3. Run, verify, record.** The agent says in one line that it is running `c1`, runs exactly the recorded command, checks the value and the logs, and records the result:

```text
$ journal.py record change --id c1 --status done --result "LOG_LEVEL=debug at 10:42Z; debug lines in logs of api-7f9c"
{"id": "c1", "status": "done", "result": "LOG_LEVEL=debug at 10:42Z; ...", ...}
```

**4. You say "revert".** The agent asks the journal what to undo:

```text
$ journal.py revert-plan last
c1	done	staging	staging-eu/payments/configmap api-config
  revert:   kubectl -n payments patch configmap api-config --type merge -p '{"data":{"LOG_LEVEL":"info"}}'
  snapshot: .work-mode/snapshots/c1-api-config.yaml
```

**5. The revert is a change too.** It passes the same checklist, so it gets its own entry (`c2`, with `--reverts c1`) before it runs. After verifying the value matches `c1`'s snapshot, the agent marks both:

```text
$ journal.py record change --id c2 --status done --result "LOG_LEVEL=info at 11:05Z, matches c1 snapshot"
$ journal.py record change --id c1 --status reverted --result "restored by c2"
$ journal.py list
c1	2026-10-03T09:07:03Z	reverted	staging	staging-eu/payments/configmap api-config
c2	2026-10-03T09:07:03Z	done	staging	staging-eu/payments/configmap api-config	reverts c1
$ journal.py revert-plan last
nothing to revert
```

`revert-plan` skips `c2` because it is itself a revert; undoing it would re-apply `c1`. For "revert everything since this morning", `revert-plan all-since <TS>` lists every open change newest first, and the agent works down the list, stopping at the first revert that fails verification.

## Worked example: a deletion

The task: "clean up the old reports buckets". The removal wording routes to the Teardown playbook, and deletion is always irreversible.

```text
inventory (read-only query)  -> 2 buckets, owners, no reads in 90 days
recovery                     -> archive copy exists; versions and ACLs not restorable
reversible stage             -> deny-all bucket policy. In non-prod the agent journals and runs it,
                                but only if the deny exempts the identity that must restore the old
                                policy (otherwise the revert is not executable: a handoff for you).
                                In prod, a modify handoff for you
observe the window           -> 7 days, no consumer errors
destroy                      -> handoff .work-mode/handoffs/retire-reports.md, Class: destroy
                                check_handoff.py check -> 0 problems; fingerprint F
you                          -> read it, run: journal.py record approval --fingerprint F --by owner ...
                                then run the commands yourself
agent                        -> journal.py check --claim owner-approved --revision F  (exit 0)
                                verify: both names absent, bucket count dropped by exactly 2
```

The agent never writes the `approval` entry. If the handoff changes after you approve it, the fingerprint changes and the check fails, so a stale approval cannot cover a different command.

## The journal in one paragraph

`./.work-mode/journal.jsonl` in the project directory, one JSON object per line, append-only, written only by `journal.py`. It holds four kinds of entry: `change`, `evidence`, `approval`, `grant`. The script refuses entries that look like they contain secrets, changes without a snapshot and revert, production changes without a grant, and approvals not marked `--by owner`. It refuses to create a journal in your home directory. Full schema: `work-mode/references/journal.md`.
