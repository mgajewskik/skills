#!/usr/bin/env python3
"""Append-only work-mode journal: live changes, evidence, owner approvals, and grants.

The journal is ./.work-mode/journal.jsonl in the current directory, one JSON object per line.

record change    before a reversible live change: prints the change id. Needs a snapshot file
                 of the prior state and a revert command. Production needs --grant.
record change --id ID --status done|failed|reverted --result TEXT
                 after executing (or reverting) that change.
record evidence  a claim about a target at a revision: established, failed, or unverified.
record approval  the user's approval of a handoff fingerprint. Written by the user only.
record grant     a production grant, quoting the user's words. Valid for this session only.
check            is a claim established for this exact target and revision?
                 Exit 0 ESTABLISHED, 2 NOT-VERIFIED, 3 FAILED, 4 STALE, 64 usage.
revert-plan      newest first, the revert command and snapshot of each change not yet
                 reverted: `last`, a change id, or `all-since TS` (by creation time). Prints; never executes.
list             changes and their latest status.
init             create ./.work-mode/ and exclude it from git, before writing anything there.

A failed or unverified entry blocks until a later success from an author of equal or higher rank
(agent < verifier < owner) clears it. The claim owner-approved is answered
only by approval entries. Values that look like secrets are rejected.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

JOURNAL_DIR = ".work-mode"
ENVIRONMENTS = ("production", "staging", "development")
CHANGE_STATUSES = ("pending", "done", "failed", "reverted")
EVIDENCE_STATUSES = ("established", "failed", "unverified")
SOURCES = ("agent", "verifier", "owner")
RANK = {"agent": 0, "verifier": 1, "owner": 2}
EXIT = {"established": 0, "unverified": 2, "failed": 3}
FIELDS = {
    "change": {"kind", "id", "ts", "created", "cwd", "env", "grant", "target", "command", "snapshot", "revert",
               "reversibility", "verification", "reverts", "status", "result"},
    "evidence": {"kind", "ts", "target", "revision", "claim", "status", "by", "evidence"},
    "approval": {"kind", "ts", "target", "fingerprint", "by", "evidence"},
    "grant": {"kind", "id", "ts", "env", "scope", "changes", "words", "expires"},
}
SECRET_SHAPES = re.compile(
    r"AKIA[0-9A-Z]{16}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|\bgh[pousr]_[A-Za-z0-9]{20,}"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
    r"|\bglpat-[A-Za-z0-9_-]{20,}"
    r"|\bxox[abposr]-[A-Za-z0-9-]{10,}"
    r"|\bsk-[A-Za-z0-9_-]{20,}"
    r"|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    r"|\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}"
    r"|://[^/\s:@]+:(?![$<{*])[^@\s/]+@"
    r"|--[a-z-]*(password|passwd|token|secret|api-key)[= ]+[\"']?(?![$<{*\"'])\S",
    re.IGNORECASE,
)
# key=value or key: value where the key names a secret (DB_PASSWORD=, client_secret:, api_token:).
# Keys start at a token boundary and are length-bounded, so long values scan in linear time.
SECRET_ASSIGNMENT = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"([A-Za-z0-9_.-]{0,64}(?:password|passwd|_pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)"
    r"[A-Za-z0-9_.-]{0,64})"
    r"[\"']?[ \t]*[=:][ \t]*[\"']?(?![$<{*\[\"'])([^\s,\"'}\]]+)",
    re.IGNORECASE,
)
# Keys that name or point to a secret rather than hold one (secretName:, tokenRef:, imagePullSecrets:).
REFERENCE_KEY = re.compile(
    r"(name|ref|path|file|id|type|length|ttl|expiry|expires|count|tokens|secrets|limit|size|seconds|timeout"
    r"|version|enabled)$",
    re.IGNORECASE,
)
# Values that cannot be a secret: booleans, null, short numbers (a long digit run can be a PIN or key).
PLAIN_VALUE = re.compile(r"(true|false|yes|no|null|none|[0-9]{1,5})$", re.IGNORECASE)


def looks_secret(text):
    if SECRET_SHAPES.search(text):
        return True
    return any(not REFERENCE_KEY.search(m.group(1)) and not PLAIN_VALUE.match(m.group(2))
               for m in SECRET_ASSIGNMENT.finditer(text))


class JournalError(Exception):
    pass


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(text):
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        raise JournalError(f"timestamp must look like 2026-10-03T12:00:00Z, got {text!r}") from None


def clean(name, value):
    value = value.strip()
    if not value:
        raise JournalError(f"{name} must be non-empty")
    if looks_secret(value):
        raise JournalError(f"{name} looks like it contains a secret; redact it and record again")
    if value[:1] in ("=", "+", "-", "@"):
        value = "'" + value
    return value


def journal_path(args):
    if args.journal:
        return Path(args.journal)
    cwd = Path.cwd().resolve()
    if cwd in (Path.home().resolve(), Path("/")):
        raise JournalError(f"{cwd} is not a project directory; ask the user where to journal and pass --journal")
    return cwd / JOURNAL_DIR / "journal.jsonl"


def read(path):
    if not path.exists():
        return []
    entries = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            raise JournalError(f"{path}:{number}: not valid JSON") from None
        kind = entry.get("kind") if isinstance(entry, dict) else None
        if kind not in FIELDS:
            raise JournalError(f"{path}:{number}: unknown kind {kind!r}")
        unknown = set(entry) - FIELDS[kind]
        if unknown:
            raise JournalError(f"{path}:{number}: unknown fields {sorted(unknown)}")
        if kind == "change" and not {"id", "created", "status"} <= set(entry):
            raise JournalError(f"{path}:{number}: a change needs id, created, and status")
        entries.append(entry)
    return entries


def exclude_from_git(journal):
    """Add the journal directory to the repository's local exclude file, never to .gitignore."""
    work = journal.parent.parent
    try:
        exclude = subprocess.run(["git", "-C", str(work), "rev-parse", "--git-path", "info/exclude"],
                                 capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return
    exclude = Path(exclude) if Path(exclude).is_absolute() else work / exclude
    pattern = f"/{journal.parent.name}/"
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if pattern not in lines:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a") as handle:
            handle.write(("\n" if lines and lines[-1] else "") + pattern + "\n")


def append(path, entry):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        exclude_from_git(path)
    with path.open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    print(json.dumps(entry, sort_keys=True))
    return 0


def changes_by_id(entries):
    """Latest line per change id, in order of first appearance."""
    latest = {}
    for entry in entries:
        if entry["kind"] == "change":
            latest[entry["id"]] = entry
    return latest


def record_change(args, path, entries):
    latest = changes_by_id(entries)
    if args.id:
        if args.id not in latest:
            raise JournalError(f"no change {args.id} in {path}")
        if args.status in (None, "pending") or not args.result:
            raise JournalError("a result line needs --status done|failed|reverted and --result")
        entry = dict(latest[args.id], ts=now(), status=args.status, result=clean("result", args.result))
        return append(path, entry)
    missing = [name for name in ("env", "target", "command", "snapshot", "revert", "reversibility", "verification")
               if not getattr(args, name)]
    if missing:
        raise JournalError(f"a new change needs --{' --'.join(missing)}")
    snapshot = Path(args.snapshot)
    if not snapshot.is_file() or snapshot.stat().st_size == 0:
        raise JournalError(f"snapshot {snapshot} does not exist or is empty; capture the prior state first")
    if looks_secret(snapshot.read_text(errors="replace")):
        raise JournalError(f"snapshot {snapshot} looks like it contains a secret; redact it first")
    if args.env == "production":
        grants = {e["id"] for e in entries if e["kind"] == "grant"}
        if args.grant not in grants:
            raise JournalError("a production change needs --grant with the id of a recorded grant. The script cannot "
                               "tell sessions or scopes apart: cite only a grant the user gave in this session "
                               "that covers this target and change type")
    if args.reverts and args.reverts not in latest:
        raise JournalError(f"--reverts names no change: {args.reverts}")
    created = now()
    entry = {
        "kind": "change", "id": f"c{len(latest) + 1}", "ts": created, "created": created, "cwd": os.getcwd(),
        "env": args.env,
        "target": clean("target", args.target), "command": clean("command", args.command),
        "snapshot": str(snapshot), "revert": clean("revert", args.revert),
        "reversibility": clean("reversibility", args.reversibility),
        "verification": clean("verification", args.verification), "status": "pending",
    }
    if args.grant:
        entry["grant"] = args.grant
    if args.reverts:
        entry["reverts"] = args.reverts
    return append(path, entry)


def record(args):
    path = journal_path(args)
    entries = read(path)
    if args.kind == "change":
        return record_change(args, path, entries)
    if args.kind == "evidence":
        if args.claim == "owner-approved":
            raise JournalError("owner-approved is recorded with `record approval`, by the user")
        entry = {"kind": "evidence", "ts": now(), "target": clean("target", args.target),
                 "revision": clean("revision", args.revision), "claim": clean("claim", args.claim),
                 "status": args.status, "by": args.by, "evidence": clean("evidence", args.evidence)}
    elif args.kind == "approval":
        if args.by != "owner":
            raise JournalError("an approval is recorded by the owner: --by owner, from the user's own hands")
        entry = {"kind": "approval", "ts": now(), "target": clean("target", args.target),
                 "fingerprint": clean("fingerprint", args.fingerprint), "by": "owner",
                 "evidence": clean("evidence", args.evidence)}
    else:
        grants = sum(1 for e in entries if e["kind"] == "grant")
        entry = {"kind": "grant", "id": f"g{grants + 1}", "ts": now(), "env": clean("env", args.env),
                 "scope": clean("scope", args.scope), "changes": clean("changes", args.changes),
                 "words": clean("words", args.words), "expires": "session"}
    return append(path, entry)


def check(args):
    target = clean("target", args.target)
    revision = clean("revision", args.revision)
    entries = read(journal_path(args))
    if args.claim == "owner-approved":
        rows = [{"status": "established", "by": "owner", "ts": e["ts"], "evidence": e["evidence"]}
                for e in entries if e["kind"] == "approval" and (e["target"], e["fingerprint"]) == (target, revision)]
    else:
        claim = clean("claim", args.claim)
        rows = [e for e in entries
                if e["kind"] == "evidence" and (e["target"], e["revision"], e["claim"]) == (target, revision, claim)]
    if not rows:
        print("NOT-VERIFIED: no entry for this target, revision, and claim")
        return 2
    # A failed or unverified entry blocks until a later success from an author of equal or higher
    # rank clears it. With nothing blocking, the newest entry (a success) decides.
    blocking = [r for i, r in enumerate(rows) if r["status"] != "established"
                and not any(s["status"] == "established" and RANK[s["by"]] >= RANK[r["by"]] for s in rows[i + 1:])]
    decisive = blocking[-1] if blocking else rows[-1]
    if args.max_age_hours is not None:
        age = datetime.datetime.now(datetime.timezone.utc) - parse_ts(decisive["ts"])
        if age > datetime.timedelta(hours=args.max_age_hours):
            print(f"STALE: {decisive['status']} at {decisive['ts']} by {decisive['by']}")
            return 4
    print(f"{decisive['status'].upper()}: {decisive['ts']} by {decisive['by']}: {decisive['evidence']}")
    return EXIT[decisive["status"]]


def revert_plan(args):
    latest = changes_by_id(read(journal_path(args)))
    open_changes = [c for c in latest.values() if c["status"] != "reverted" and "reverts" not in c]
    open_changes.reverse()
    which = args.which
    if which == ["last"]:
        selected = open_changes[:1]
    elif len(which) == 2 and which[0] == "all-since":
        since = parse_ts(which[1])
        selected = [c for c in open_changes if parse_ts(c["created"]) >= since]
    elif len(which) == 1:
        if which[0] not in latest:
            raise JournalError(f"no change {which[0]}")
        selected = [c for c in open_changes if c["id"] == which[0]]
        if not selected:
            print(f"{which[0]} is already reverted or is itself a revert")
            return 0
    else:
        raise JournalError("revert-plan takes `last`, a change id, or `all-since TS`")
    if not selected:
        print("nothing to revert")
    for change in selected:
        print(f"{change['id']}\t{change['status']}\t{change['env']}\t{change['target']}")
        print(f"  revert:   {change['revert']}")
        print(f"  snapshot: {change['snapshot']}")
    return 0


def init(args):
    path = journal_path(args)
    path.parent.mkdir(parents=True, exist_ok=True)
    exclude_from_git(path)
    print(path.parent)
    return 0


def list_changes(args):
    since = parse_ts(args.since) if args.since else None
    for change in changes_by_id(read(journal_path(args))).values():
        if since and parse_ts(change["created"]) < since:
            continue
        reverts = f"\treverts {change['reverts']}" if "reverts" in change else ""
        print(f"{change['id']}\t{change['created']}\t{change['status']}\t{change['env']}\t{change['target']}{reverts}")
    return 0


def parser():
    top = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    top.add_argument("--journal", help="journal file (default ./.work-mode/journal.jsonl)")
    commands = top.add_subparsers(dest="action", required=True)

    rec = commands.add_parser("record").add_subparsers(dest="kind", required=True)
    change = rec.add_parser("change")
    change.add_argument("--id", help="existing change id, to record its result")
    change.add_argument("--status", choices=CHANGE_STATUSES[1:])
    change.add_argument("--result")
    change.add_argument("--env", choices=ENVIRONMENTS)
    change.add_argument("--grant", help="grant id, required for production")
    change.add_argument("--target")
    change.add_argument("--command")
    change.add_argument("--snapshot", help="file holding the redacted prior state")
    change.add_argument("--revert", help="command that restores the snapshot")
    change.add_argument("--reversibility", help="evidence for each reversibility checklist item")
    change.add_argument("--verification", help="signal that shows the change, and the revert, worked")
    change.add_argument("--reverts", help="id of the change this one reverts")
    evidence = rec.add_parser("evidence")
    for name in ("--target", "--revision", "--claim", "--evidence"):
        evidence.add_argument(name, required=True)
    evidence.add_argument("--status", required=True, choices=EVIDENCE_STATUSES)
    evidence.add_argument("--by", required=True, choices=SOURCES)
    approval = rec.add_parser("approval")
    for name in ("--target", "--fingerprint", "--by", "--evidence"):
        approval.add_argument(name, required=True)
    grant = rec.add_parser("grant")
    for name in ("--env", "--scope", "--changes", "--words"):
        grant.add_argument(name, required=True)

    chk = commands.add_parser("check")
    for name in ("--target", "--revision", "--claim"):
        chk.add_argument(name, required=True)
    chk.add_argument("--max-age-hours", type=float)
    plan = commands.add_parser("revert-plan")
    plan.add_argument("which", nargs="+", help="last | <id> | all-since <TS>")
    lst = commands.add_parser("list")
    lst.add_argument("--since")
    commands.add_parser("init")
    return top


def main(argv=None):
    try:
        args = parser().parse_args(argv)
    except SystemExit as error:
        return 64 if error.code else 0
    handlers = {"record": record, "check": check, "revert-plan": revert_plan, "list": list_changes, "init": init}
    try:
        return handlers[args.action](args)
    except JournalError as error:
        print(f"journal: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
