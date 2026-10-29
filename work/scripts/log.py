#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Work log: one directory per task, <project>/.work/ID/, holding log.yml and its artifacts, written only
by this script.

new SLUG --task TEXT --playbook NAME [--parent ID]
                                       start a log; prints its id (YYYY-MM-DD-SLUG, or ID/YYYY-MM-DD-SLUG
                                       nested inside log ID's directory)
phase ID NAME                          start a playbook step; later entries carry its name
add ID run|plan|evidence|decision|note ...  append a timeline entry; prints its number
root-cause ID --summary TEXT --confidence LEVEL [--evidence N,N]
close ID --status done|halted|reverted --summary TEXT
check ID [--since N] [--max-age-hours H]  exit 0 only when every claim's latest evidence is established
revert-plan ID                         newest first, how to undo each change not yet reverted

Every reversible change, run or planned, carries --revert; an irreversible one carries --revert or
--no-revert. An --artifact is copied beside log.yml as NNN-NAME, NNN being its entry's number. A wrong
entry is corrected by a new one with --supersedes N; the file is never edited. Values and text artifacts
that look like secrets are refused.
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

WORK_DIR = ".work"
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*$")
CLASSES = ("read-only", "reversible", "irreversible")
CHANGES = ("reversible", "irreversible")
ARTIFACT_PLACEHOLDER = "{artifact}"
EVIDENCE_STATUSES = ("established", "failed", "unverified")
CONFIDENCE = ("established", "leading-hypothesis", "unknown")
LOG_STATUSES = ("open", "done", "halted", "reverted")

# Secret detection, kept identical to work-mode's journal.py.
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
SECRET_ASSIGNMENT = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"([A-Za-z0-9_.-]{0,64}(?:password|passwd|_pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)"
    r"[A-Za-z0-9_.-]{0,64})"
    r"[\"']?[ \t]*[=:][ \t]*[\"']?(?![$<{*\[\"'])([^\s,\"'}\]]+)",
    re.IGNORECASE,
)
REFERENCE_KEY = re.compile(
    r"(name|ref|path|file|id|type|length|ttl|expiry|expires|count|tokens|secrets|limit|size|seconds|timeout"
    r"|version|enabled)$",
    re.IGNORECASE,
)
PLAIN_VALUE = re.compile(r"(true|false|yes|no|null|none|[0-9]{1,5})$", re.IGNORECASE)


class LogError(Exception):
    pass


def looks_secret(text):
    if SECRET_SHAPES.search(text):
        return True
    return any(not REFERENCE_KEY.search(m.group(1)) and not PLAIN_VALUE.match(m.group(2))
               for m in SECRET_ASSIGNMENT.finditer(text))


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def literal_blocks(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.SafeDumper.add_representer(str, literal_blocks)


def project_root():
    cwd = Path.cwd().resolve()
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                             check=True).stdout.strip()
        root = Path(top)
    except (OSError, subprocess.CalledProcessError):
        root = cwd
    if root in (Path.home().resolve(), Path("/")):
        raise LogError(f"{root} is not a project directory; run from inside the project")
    return root


def exclude_from_git(root):
    """Add .work/ to the repository's local exclude file, never to .gitignore."""
    try:
        exclude = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"],
                                 capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return
    exclude = Path(exclude) if Path(exclude).is_absolute() else root / exclude
    pattern = f"/{WORK_DIR}/"
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if pattern not in lines:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a") as handle:
            handle.write(("\n" if lines and lines[-1] else "") + pattern + "\n")


def locate(log_id):
    path = project_root() / WORK_DIR / log_id / "log.yml"
    if not path.exists():
        raise LogError(f"no log {log_id!r} under {path.parent.parent}")
    return path


def load(path):
    doc = yaml.safe_load(path.read_text())
    if not isinstance(doc, dict) or "timeline" not in doc:
        raise LogError(f"{path} is not a work log")
    return doc


def clean(name, value):
    value = value.strip()
    if not value:
        raise LogError(f"--{name} must be non-empty")
    if looks_secret(value):
        raise LogError(f"--{name} looks like it contains a secret; redact it and try again")
    return value


def revert_view(timeline):
    """Every change not yet reverted, run or planned, newest first: the command that undoes it, or why
    nothing can. A revert run is never listed itself."""
    reverted = {e["reverts"] for e in timeline if "reverts" in e}
    executed_plans = {e["from_plan"] for e in timeline if "from_plan" in e}
    view = []
    for e in reversed(timeline):
        if e["kind"] not in ("run", "plan") or e.get("class") not in CHANGES:
            continue
        if "reverts" in e or e["n"] in reverted or e["n"] in executed_plans:
            continue
        item = {"of": e["n"], "state": "executed" if e["kind"] == "run" else f"planned for {e['by']}",
                "class": e["class"], "why": e.get("why", "")}
        if "revert" in e:
            item["command"] = e["revert"]
        else:
            item["no_revert"] = e["no_revert"]
        view.append(item)
    return view


def dump(value):
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100)


def render(doc):
    """The log as YAML with a blank line after the header, each section, and each timeline entry. Each part
    is dumped on its own and joined, so the blank lines never touch a value."""
    header = {key: doc[key] for key in ("id", "task", "playbook", "parent", "status", "created", "updated", "summary")
              if key in doc}
    parts = [dump(header)]
    parts += [dump({key: doc[key]}) for key in ("root_cause", "revert", "artifacts") if key in doc]
    if doc["timeline"]:
        parts.append("timeline:\n" + "\n".join(dump([entry]) for entry in doc["timeline"]))
    else:
        parts.append(dump({"timeline": []}))
    return "\n".join(parts)


def save(path, doc):
    doc["updated"] = now()
    doc["revert"] = revert_view(doc["timeline"])
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(render(doc))
    os.replace(tmp, path)


def save_artifact(path, source, n):
    """Copy an artifact beside the log as NNN-NAME, NNN being the number of the entry it belongs to."""
    source = Path(source)
    if not source.is_file():
        raise LogError(f"artifact {source} is not a file")
    if looks_secret(source.read_text(errors="replace")):
        raise LogError(f"artifact {source} looks like it contains a secret; redact it and try again")
    name = f"{n:03d}-{source.name}"
    shutil.copy2(source, path.parent / name)
    return name


def entry_numbers(text, timeline):
    """Parse comma-separated entry numbers, each of which must exist."""
    try:
        numbers = [int(n) for n in text.split(",")]
    except ValueError:
        raise LogError("entry numbers are comma-separated, such as 3,7") from None
    unknown = set(numbers) - {e["n"] for e in timeline}
    if unknown:
        raise LogError(f"unknown entries: {sorted(unknown)}")
    return numbers


def cmd_new(args):
    if not SLUG.match(args.slug):
        raise LogError("slug must be kebab-case, such as fix-nginx-502")
    root = project_root()
    work = root / WORK_DIR
    base = f"{datetime.date.today().isoformat()}-{args.slug}"
    if args.parent:
        locate(args.parent)
        base = f"{args.parent}/{base}"
    log_id, number = base, 2
    while (work / log_id).exists():
        log_id = f"{base}-{number}"
        number += 1
    doc = {"id": log_id, "task": clean("task", args.task), "playbook": clean("playbook", args.playbook),
           "status": "open", "created": now(), "root_cause": None, "timeline": []}
    if args.parent:
        doc["parent"] = args.parent
    (work / log_id).mkdir(parents=True)
    exclude_from_git(root)
    save(work / log_id / "log.yml", doc)
    print(log_id)


def cmd_phase(args):
    path = locate(args.id)
    doc = load(path)
    doc["timeline"].append({"n": len(doc["timeline"]) + 1, "at": now(), "kind": "phase",
                            "name": clean("name", args.name)})
    save(path, doc)
    print(len(doc["timeline"]))


def cmd_add(args):
    path = locate(args.id)
    doc = load(path)
    timeline = doc["timeline"]
    entry = {"n": len(timeline) + 1, "at": now(), "kind": args.kind}
    phase = next((e["name"] for e in reversed(timeline) if e["kind"] == "phase"), None)
    if phase:
        entry["phase"] = phase
    for field in ("text", "why", "target", "identity", "class", "by", "claim", "status", "revision",
                  "command", "revert", "no_revert", "result", "rejected"):
        value = getattr(args, field, None)
        if value is not None:
            entry[field] = clean(field.replace("_", "-"), value)
    if args.evidence is not None:
        entry["evidence"] = entry_numbers(args.evidence, timeline)
    if args.supersedes is not None:
        if args.supersedes not in {e["n"] for e in timeline}:
            raise LogError(f"entry {args.supersedes} does not exist")
        entry["supersedes"] = args.supersedes
    if args.from_plan is not None:
        if args.kind != "run":
            raise LogError("--from-plan goes on the run that executed the plan")
        plan = next((e for e in timeline if e["n"] == args.from_plan and e["kind"] == "plan"), None)
        settled = {e.get("from_plan") for e in timeline} | {e.get("reverts") for e in timeline}
        if plan is None or args.from_plan in settled:
            raise LogError(f"entry {args.from_plan} is not a plan still waiting to run")
        for field in ("why", "target", "identity", "class", "command", "revert", "no_revert"):
            if field in plan:
                entry.setdefault(field, plan[field])
        entry["from_plan"] = args.from_plan
    required = {"run": ("command", "class"), "plan": ("command", "class", "by"),
                "evidence": ("claim", "status", "command"), "decision": ("text", "why"),
                "note": ("text",)}[args.kind]
    missing = [f"--{f}" for f in required if f not in entry]
    if missing:
        raise LogError(f"{args.kind} needs {', '.join(missing)}")
    if args.reverts is not None:
        if args.kind != "run":
            raise LogError("--reverts goes on the run that executed the revert")
        if args.reverts not in {item["of"] for item in revert_view(timeline) if "command" in item}:
            raise LogError(f"entry {args.reverts} is not in the revert list")
        entry["reverts"] = args.reverts
    elif entry.get("class") == "reversible" and "revert" not in entry:
        raise LogError("a reversible change needs --revert")
    elif entry.get("class") == "irreversible" and "revert" not in entry and "no_revert" not in entry:
        raise LogError("an irreversible change needs --revert (best-known recovery) or --no-revert REASON")
    uses_artifact = any(ARTIFACT_PLACEHOLDER in entry.get(f, "") for f in ("command", "revert"))
    if uses_artifact and not args.artifact:
        raise LogError(f"{ARTIFACT_PLACEHOLDER} needs --artifact")
    if args.artifact:
        name = save_artifact(path, args.artifact, entry["n"])
        entry["artifact"] = name
        doc.setdefault("artifacts", []).append(name)
        relative = os.path.relpath(path.parent / name, project_root())
        for field in ("command", "revert"):
            if field in entry:
                entry[field] = entry[field].replace(ARTIFACT_PLACEHOLDER, relative)
    timeline.append(entry)
    save(path, doc)
    print(entry["n"])


def cmd_root_cause(args):
    path = locate(args.id)
    doc = load(path)
    evidence = entry_numbers(args.evidence, doc["timeline"]) if args.evidence else []
    doc["root_cause"] = {"summary": clean("summary", args.summary), "confidence": args.confidence,
                         "evidence": evidence}
    save(path, doc)


def cmd_close(args):
    path = locate(args.id)
    doc = load(path)
    doc["status"] = args.status
    doc["summary"] = clean("summary", args.summary)
    save(path, doc)


def cmd_check(args):
    doc = load(locate(args.id))
    latest = {}
    for entry in doc["timeline"]:
        if entry["kind"] == "evidence" and entry["n"] > args.since:
            latest[entry["claim"]] = entry
    if not latest:
        print("no claims recorded")
        return 1
    cutoff = None
    if args.max_age_hours is not None:
        cutoff = datetime.datetime.now().astimezone() - datetime.timedelta(hours=args.max_age_hours)
    passed = True
    for claim, entry in latest.items():
        status = entry["status"]
        if cutoff and datetime.datetime.fromisoformat(entry["at"]) < cutoff:
            status = "stale"
        passed = passed and status == "established"
        print(f"{status:12} #{entry['n']:<4} {claim}")
    return 0 if passed else 1


def cmd_revert_plan(args):
    plan = revert_view(load(locate(args.id))["timeline"])
    if not plan:
        print("nothing to revert")
        return
    print(f"# run from {project_root()}\n")
    executed = [item for item in plan if item["state"] == "executed"]
    planned = [item for item in plan if item["state"] != "executed"]
    for item in executed:
        print_revert(item, live=True)
    if planned:
        print("# --- planned, not known to have run: uncomment only for a change you ran ---\n")
    for item in planned:
        print_revert(item, live=False)


def print_revert(item, live):
    print(f"# #{item['of']} {item['state']}, {item['class']}: {item['why']}")
    if "no_revert" in item:
        print(f"# cannot be reverted: {item['no_revert']}\n")
    elif live:
        print(f"{item['command']}\n")
    else:
        print("\n".join(f"# {line}" for line in item["command"].splitlines()) + "\n")


def parser():
    top = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = top.add_subparsers(dest="action", required=True)

    new = sub.add_parser("new", help="start a log")
    new.add_argument("slug")
    new.add_argument("--task", required=True)
    new.add_argument("--playbook", required=True)
    new.add_argument("--parent", metavar="ID", help="nest this log inside log ID's directory, as a delegate's log "
                                                    "inside its orchestrator's")

    phase = sub.add_parser("phase", help="start a playbook step")
    phase.add_argument("id")
    phase.add_argument("name", help="the step's number and name, such as '3. Classify each difference'")

    add = sub.add_parser("add", help="append a timeline entry")
    add.add_argument("id")
    add.add_argument("kind", choices=("run", "plan", "evidence", "decision", "note"))
    add.add_argument("--command", help="the exact command (run, plan) or the one that collected the evidence")
    add.add_argument("--why", help="why this was done or chosen; required on a decision")
    add.add_argument("--target", help="resolved target: account, context, host, resource")
    add.add_argument("--identity", help="the identity the command runs as")
    add.add_argument("--class", choices=CLASSES, help="run and plan: read-only, reversible, or irreversible")
    add.add_argument("--revert", help="run and plan: the command that undoes this change; write {artifact} "
                                      "where the path of --artifact goes, such as a manifest to re-apply")
    add.add_argument("--no-revert", metavar="REASON", help="irreversible: why nothing can undo it")
    add.add_argument("--reverts", type=int, help="this run reverts entry N")
    add.add_argument("--from-plan", type=int, metavar="N", help="this run executed plan N (by the user or agent); "
                                                                 "fields it omits are copied from the plan")
    add.add_argument("--by", choices=("agent", "user"), help="plan: who will run it")
    add.add_argument("--claim", help="evidence: the claim this evidence supports or fails")
    add.add_argument("--status", choices=EVIDENCE_STATUSES)
    add.add_argument("--revision", help="evidence: the running revision it is bound to")
    add.add_argument("--result", help="short output, exit code, or observed value")
    add.add_argument("--text", help="decision: what was chosen; note: a criterion, hypothesis, option, or "
                                    "resume note")
    add.add_argument("--evidence", metavar="N,N", help="decision: the entries it rests on")
    add.add_argument("--rejected", help="decision: the alternatives not chosen and why")
    add.add_argument("--supersedes", type=int, metavar="N", help="this entry corrects entry N")
    add.add_argument("--artifact", help="a file to save beside the log as NNN-NAME")

    cause = sub.add_parser("root-cause", help="set the root cause")
    cause.add_argument("id")
    cause.add_argument("--summary", required=True)
    cause.add_argument("--confidence", choices=CONFIDENCE, required=True)
    cause.add_argument("--evidence", help="comma-separated entry numbers")

    close = sub.add_parser("close", help="close the log")
    close.add_argument("id")
    close.add_argument("--status", choices=LOG_STATUSES[1:], required=True)
    close.add_argument("--summary", required=True)

    check = sub.add_parser("check", help="gate on every claim's latest evidence")
    check.add_argument("id")
    check.add_argument("--since", type=int, default=0, help="only evidence logged after entry N, such as the unit's run")
    check.add_argument("--max-age-hours", type=float)

    revert = sub.add_parser("revert-plan", help="print reverts newest first; never executes")
    revert.add_argument("id")
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    handlers = {"new": cmd_new, "phase": cmd_phase, "add": cmd_add, "root-cause": cmd_root_cause, "close": cmd_close,
                "check": cmd_check, "revert-plan": cmd_revert_plan}
    try:
        return handlers[args.action](args) or 0
    except LogError as error:
        print(f"log: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
