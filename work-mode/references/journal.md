# Journal

One append-only file records every live change the agent makes, the evidence behind claims, the user's approvals of handoffs, and production grants. `scripts/journal.py` is the only writer; never edit the file by hand. Run the script by its full path from the project directory.

```text
./.work-mode/
  journal.jsonl     one JSON object per line, append-only
  snapshots/        redacted prior state, one file per change
  handoffs/         irreversible handoffs for the user (see handoff.md)
  replies/          review-reply payloads posted by Babysit
  pr-<slug>.md      a PR body for the user to open (Opening a PR)
  resume-<slug>.md  a resume note (Pause safely)
```

`journal.py init` (and the first journal write) adds `/.work-mode/` to the repository's local `.git/info/exclude`, never to a committed `.gitignore`. Run `init` before writing any other file into `.work-mode/`. It refuses to create a journal in the home directory or `/`; ask the user where to journal and pass `--journal <file>`.

## Entries

| Kind | Fields | Written by |
| --- | --- | --- |
| `change` | `id`, `ts` (time of this line), `created` (time of the pending line), `cwd`, `env`, `grant` (production only), `target`, `command`, `snapshot`, `revert`, `reversibility`, `verification`, `reverts` (a revert only), `status`, `result` | Agent: once before executing (`pending`), once after (`done`, `failed`, or `reverted`). The result line repeats the change's fields. |
| `evidence` | `ts`, `target`, `revision`, `claim`, `status` (`established`, `failed`, `unverified`), `by` (`agent`, `verifier`, `owner`), `evidence` | Agent, independent reviewer, or user, each with their own `--by`. |
| `approval` | `ts`, `target`, `fingerprint`, `by` (always `owner`), `evidence` | The user, by running the command themselves. |
| `grant` | `id`, `ts`, `env`, `scope`, `changes`, `words`, `expires` (always `session`) | Agent, quoting the user's words. |

The script rejects unknown kinds and fields, values that look like secrets (in every field and in the snapshot file), a change without a revert command or a non-empty snapshot file, a production change without `--grant`, and an approval not marked `--by owner`. Secret detection covers known token shapes, URL and Basic credentials, and `key=value` or `key: value` pairs whose key names a password, secret, token, or API, access, or private key (`DB_PASSWORD=`, `client_secret:`); keys that point at a secret (`secretName`, `password_file`) and values that are variables or placeholders (`$DB_PASSWORD`, `<redacted>`) pass. It is a net, not a proof: redact before recording.

The script checks that `--grant` names a recorded grant; it cannot tell sessions apart or compare scopes. Cite only a grant the user gave in this session that covers the target and change type. A leading `=`, `+`, `-`, or `@` in a value gets a `'` prefix so a spreadsheet cannot run it. A malformed journal makes every command fail loudly.

## Commands

```sh
J="python3 <work-mode>/scripts/journal.py"

$J record change --env staging --target T --command C --snapshot S --revert R \
   --reversibility "..." --verification "..."          # prints {"id": "c1", ...}
$J record change --id c1 --status done --result "rollout status ok at 12:04Z"
$J record evidence --target T --revision REV --claim consumer-ok --status established --by agent --evidence E
$J record grant --env prod-eu --scope "namespace payments" --changes "scale, config" --words "..."
$J check --target T --revision REV --claim consumer-ok [--max-age-hours N]
$J revert-plan last | <id> | all-since 2026-10-03T12:00:00Z
$J list [--since TS]
$J init                                                 # before writing any file under .work-mode/
```

`--env` is `production`, `staging`, or `development`. An environment you cannot name is production.

`check` exits 0 established, 2 not verified (no entry, or `unverified`), 3 failed, 4 stale. Verifier and owner entries outrank agent entries, so a self-report cannot hide a reviewer's `failed`. A different target or revision never matches. The claim `owner-approved` is answered only by `approval` entries for that exact fingerprint.

`revert-plan` lists changes whose latest status is not `reverted`, newest first by creation time (`all-since` and `list --since` filter on `created`, so a late result line does not pull an earlier change in), skipping changes that are themselves reverts. It prints the revert command and snapshot; it never executes anything.

## Revert procedure

```text
revert-plan last
   |
   v
revert passes the reversibility checklist?
   |-- yes --> record change --reverts c3 (revert of c3 = new change c4, journal first)
   |           execute c4's command, verify state matches c3's snapshot
   |           record change --id c4 --status done
   |           record change --id c3 --status reverted --result "restored by c4"
   |-- no ---> handoff: the user executes the revert; verify; mark c3 reverted with the evidence
```

Revert newest first. Stop at the first revert that fails verification and report. A `pending` change with no result line may or may not have run: observe the target before reverting it.

## What not to put in it

Secrets, tokens, customer records, whole environments, or full state and plan dumps. Snapshot only the fields the change touches, with secret values replaced by `<redacted>`. The journal is local working state, excluded from git; it is not a backup.
