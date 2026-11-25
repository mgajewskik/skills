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
reopen ID --why TEXT                   reopen a closed log (e.g., to record a later revert)
check ID [--since N] [--max-age-hours H] [--revision REV] [--require CLAIM ...]
                                       exit 0 only when every required and recorded claim is established
revert-plan ID                         newest first, how to undo each change not yet reverted (includes
                                       nested delegate logs)

Every reversible change, run or planned, carries --revert; an irreversible one is user-executed
(--by user) and carries --revert or --no-revert. Log an Ops change as a plan before execution, then
as a run with --from-plan N and --outcome ok|failed|unknown after execution. An --artifact (or piped
stdin via --artifact-name NAME) is saved beside log.yml as NNN-NAME and substituted for {artifact}
as a shell-quoted relative path. A wrong entry is corrected by a new one with --supersedes N; the
file is never edited. Values and text artifacts that look like secrets are refused.
"""

import argparse
import datetime
import io
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

WORK_DIR = ".work"
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*\Z")
CLASSES = ("read-only", "reversible", "irreversible")
CHANGES = ("reversible", "irreversible")
OUTCOMES = ("ok", "failed", "unknown")
PLAN_IMMUTABLE_FIELDS = ("by", "command", "class", "target", "identity", "revert", "no_revert")
ARTIFACT_PLACEHOLDER = "{artifact}"
EVIDENCE_STATUSES = ("established", "failed", "unverified")
CONFIDENCE = ("established", "leading-hypothesis", "unknown")
LOG_STATUSES = ("open", "done", "halted", "reverted")

ALLOWED_FIELDS = {
    "run": frozenset({
        "command", "class", "by", "why", "target", "identity", "outcome",
        "revert", "no_revert", "result", "from_plan", "reverts", "supersedes", "artifact", "artifact_name",
    }),
    "plan": frozenset({
        "command", "class", "by", "why", "target", "identity",
        "revert", "no_revert", "supersedes", "artifact", "artifact_name",
    }),
    "evidence": frozenset({
        "claim", "status", "command", "why", "target", "identity",
        "revision", "result", "supersedes", "artifact", "artifact_name",
    }),
    "decision": frozenset({"text", "why", "evidence", "rejected", "supersedes", "artifact", "artifact_name"}),
    "note": frozenset({"text", "why", "supersedes", "artifact", "artifact_name"}),
}
ALL_OPTIONAL_FIELDS = tuple(sorted(frozenset().union(*ALLOWED_FIELDS.values())))

REDACTED_VALUE = re.compile(
    r"^(?:"
    r"\[?REDACTED\]?"
    r"|<[^>\s]+>"
    r"|\*{3,}"
    r"|\.{3,}"
    r"|x{4,}"
    r"|changeme|placeholder|example|dummy|sample|redacted|omitted|masked|hidden|scrubbed|removed"
    r")$",
    re.IGNORECASE,
)

PLAIN_VALUE = re.compile(
    r"^(?:true|false|yes|no|null|none|empty|unset|missing|expired|invalid|revoked|rotated"
    r"|required|optional|strict|enabled|disabled|interactive|default|[0-9]{1,5})$",
    re.IGNORECASE,
)

SECRET_SHAPES_SENSITIVE = re.compile(
    r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"
    r"|-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----"
    r"|\bgh[pousr]_[A-Za-z0-9]{20,}"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
    r"|\bglpat-[A-Za-z0-9_-]{20,}"
    r"|\bxox[abposr]-[A-Za-z0-9-]{10,}"
    r"|\bsk-[A-Za-z0-9_-]{20,}"
    r"|\bAIza[0-9A-Za-z_-]{35}\b"
    r"|\bnpm_[A-Za-z0-9]{20,}\b"
    r"|\bpypi-[A-Za-z0-9_-]{20,}\b"
    r"|\bAGE-SECRET-KEY-1[0-9A-Z]{20,}\b"
    r"|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
)

BEARER_OR_BASIC_SECRET = re.compile(
    r"\bBearer[ \t]+((?=[A-Za-z0-9._~+/=-]*(?:[0-9._~+/=-]|[a-z][A-Z]))[A-Za-z0-9._~+/=-]{8,})"
    r"|\bBasic[ \t]+((?=[A-Za-z0-9+/=]*(?:[0-9+/=]|[a-z][A-Z]))[A-Za-z0-9+/=]{12,})"
)

AUTH_HEADER_SECRET = re.compile(
    r"\bAuthorization[ \t]*:[ \t]*(?:Bearer|Basic|Token|ApiKey)[ \t]+([^\s'\",;]{8,})",
    re.IGNORECASE,
)

URL_CREDENTIAL_SECRET = re.compile(r"://[^/\s:@]+:(?![$<{*])([^@\s/]+)@")

CLI_FLAG_SECRET = re.compile(
    r"(?:^|[\s'\"])--[a-z-]*(?:password|passwd|token|secret|api-key)[= ]+(?:[\"']([^\"'\n]+)[\"']|([^\s\"']+))"
    r"|\b(?:curl|wget)\b[^\n;|&]*?\s(?:-u|--user)[= ]+[\"']?[^:\s\"']+:([^@\s\"']+)",
    re.IGNORECASE,
)

SECRET_ASSIGNMENT = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"([A-Za-z0-9_.-]{0,64}(?:password|passwd|_pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key"
    r"|(?:tls|ssl|ssh|signing|client|server|host|ca|gpg|pgp|age)\.key)[A-Za-z0-9_.-]{0,64})"
    r"[\"']?[ \t]*[=:][ \t]*(?:[\"']([^\"'\n]+)[\"']|(?![$<{*\[\"'])([^\s,\"'}\]]+))",
    re.IGNORECASE,
)

REFERENCE_KEY = re.compile(
    r"(?:name|ref|path|file|id|type|length|ttl|expiry|expires|count|tokens|secrets|limit|size|seconds|timeout"
    r"|version|enabled|policy|store|header|prompt|env|var|endpoint|url|uri|host|domain|issuer|audience"
    r"|scope|scopes|alg|algorithm|format|mode|provider|source|backend|scheme|status|state|error|message"
    r"|hint|label|field|param|arg|flag|option|rotation|lifetime|window|cache|dir|folder|prefix|suffix"
    r"|pattern|regex|check|rule|metric|quota|budget)$",
    re.IGNORECASE,
)


class LogError(Exception):
    pass


def is_placeholder_value(value):
    stripped = value.strip()
    if not stripped or stripped[0] in "$<{*":
        return True
    return bool(REDACTED_VALUE.match(stripped))


def looks_secret(text):
    if SECRET_SHAPES_SENSITIVE.search(text):
        return True
    if any(not is_placeholder_value(m.group(1) or m.group(2) or "") for m in BEARER_OR_BASIC_SECRET.finditer(text)):
        return True
    if any(not is_placeholder_value(m.group(1)) for m in AUTH_HEADER_SECRET.finditer(text)):
        return True
    if any(not is_placeholder_value(m.group(1)) for m in URL_CREDENTIAL_SECRET.finditer(text)):
        return True
    for match in CLI_FLAG_SECRET.finditer(text):
        value = match.group(1) or match.group(2) or match.group(3) or ""
        if not is_placeholder_value(value):
            return True
    for match in SECRET_ASSIGNMENT.finditer(text):
        key = match.group(1)
        value = (match.group(2) or match.group(3) or "").strip()
        if REFERENCE_KEY.search(key) or is_placeholder_value(value) or PLAIN_VALUE.match(value):
            continue
        return True
    return False


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def parse_timestamp(value):
    try:
        dt = datetime.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise LogError(f"invalid timestamp in log: {value!r}") from None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
    return dt.astimezone(datetime.timezone.utc)


def literal_blocks(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.SafeDumper.add_representer(str, literal_blocks)


def project_root(for_locate=False):
    cwd = Path.cwd().resolve()
    home = Path.home().resolve()
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                             check=True).stdout.strip()
        root = Path(top).resolve()
    except (OSError, subprocess.CalledProcessError):
        root = cwd
        if for_locate:
            for candidate in (cwd, *cwd.parents):
                if candidate in (home, Path("/")):
                    break
                work_dir = candidate / WORK_DIR
                if work_dir.exists() and not work_dir.is_symlink() and work_dir.is_dir():
                    root = candidate
                    break
    if root in (home, Path("/")):
        raise LogError(f"{root} is not a project directory; run from inside the project")
    return root


def exclude_from_git(root):
    try:
        ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", f"{WORK_DIR}/"],
                                 capture_output=True)
    except OSError:
        return
    if ignored.returncode == 0:
        return
    try:
        exclude = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"],
                                 capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return
    exclude = Path(exclude) if Path(exclude).is_absolute() else root / exclude
    pattern = f"/{WORK_DIR}/"
    try:
        text = exclude.read_text() if exclude.exists() else ""
        if pattern not in text.splitlines():
            exclude.parent.mkdir(parents=True, exist_ok=True)
            prefix = "\n" if text and not text.endswith("\n") else ""
            with exclude.open("a") as handle:
                handle.write(f"{prefix}{pattern}\n")
    except OSError as error:
        raise LogError(f"cannot exclude {WORK_DIR}/ from git ({exclude}): {error}") from None


def validate_log_id(log_id):
    segments = log_id.split("/")
    if not log_id or any(not SLUG.match(segment) for segment in segments):
        raise LogError(f"invalid log id {log_id!r}")
    return log_id


def work_root_dir(root=None, for_locate=False):
    base = (root or project_root(for_locate=for_locate)).resolve()
    work_root = base / WORK_DIR
    if work_root.is_symlink():
        raise LogError(f"{work_root} must not be a symlink")
    return work_root


def locate(log_id):
    validate_log_id(log_id)
    work_root = work_root_dir(for_locate=True)
    path = (work_root / log_id / "log.yml").resolve()
    if not path.is_relative_to(work_root) or not path.is_file():
        raise LogError(f"no log {log_id!r} under {work_root}")
    return path


def load(path):
    try:
        doc = yaml.safe_load(path.read_text())
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise LogError(f"cannot read {path}: {error}") from None
    if not isinstance(doc, dict) or not isinstance(doc.get("timeline"), list):
        raise LogError(f"{path} is not a work log")
    return doc


def ensure_open(doc, log_id):
    status = doc.get("status", "open")
    if status != "open":
        raise LogError(f"log {log_id!r} is closed ({status}); start a new log instead")


def clean(name, value):
    value = value.strip()
    if not value:
        raise LogError(f"--{name} must be non-empty")
    if looks_secret(value):
        raise LogError(f"--{name} looks like it contains a secret; redact it and try again")
    return value


def superseded_numbers(timeline, extra=None):
    numbers = {e["supersedes"] for e in timeline if "supersedes" in e}
    if extra is not None:
        numbers.add(extra)
    return numbers


def revert_view(timeline, extra_superseded=None):
    """Every change not yet reverted, run or planned, newest first: the command that undoes it, or why
    nothing can. A revert run is never listed itself, and only an ok revert settles its target."""
    superseded = superseded_numbers(timeline, extra_superseded)
    reverted = {e["reverts"] for e in timeline
                if "reverts" in e and e["n"] not in superseded and e.get("outcome", "ok") == "ok"}
    executed_plans = {e["from_plan"] for e in timeline if "from_plan" in e and e["n"] not in superseded}
    view = []
    for e in reversed(timeline):
        if e["n"] in superseded or e["kind"] not in ("run", "plan") or e.get("class") not in CHANGES:
            continue
        if "reverts" in e or e["n"] in reverted or e["n"] in executed_plans:
            continue
        if e["kind"] == "plan":
            state = f"planned for {e['by']}"
        else:
            outcome = e.get("outcome", "ok")
            state = "executed" if outcome == "ok" else ("outcome unknown" if outcome == "unknown" else "failed")
        item = {"of": e["n"], "state": state, "class": e["class"], "why": e.get("why", "")}
        for meta in ("target", "identity"):
            if meta in e:
                item[meta] = e[meta]
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
    rendered = render(doc)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(rendered)
        os.replace(tmp_path, path)
    except OSError as error:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise LogError(f"cannot write {path}: {error}") from None


def stream_looks_secret(handle):
    chunk_size = 1024 * 1024
    overlap = 4096
    tail = ""
    while True:
        raw = handle.read(chunk_size)
        if not raw:
            break
        text = tail + raw.decode("utf-8", errors="replace")
        if looks_secret(text):
            return True
        tail = text[-overlap:]
    return False


def file_looks_secret(source):
    try:
        with source.open("rb") as handle:
            return stream_looks_secret(handle)
    except OSError as error:
        raise LogError(f"cannot read artifact {source}: {error}") from None


def validate_artifact_name(raw):
    if "\x00" in raw or "\n" in raw or "\r" in raw:
        raise LogError(f"invalid artifact name {raw!r}")
    name = raw.strip()
    if not name or name in (".", "..") or "/" in name or "\\" in name or Path(name).name != name:
        raise LogError(f"invalid artifact name {raw!r}")
    if looks_secret(name):
        raise LogError("--artifact-name looks like it contains a secret; redact it and try again")
    return name


def save_artifact(path, source, n):
    source = Path(source)
    if not source.is_file():
        raise LogError(f"artifact {source} is not a file")
    clean_name = validate_artifact_name(source.name)
    if file_looks_secret(source):
        raise LogError(f"artifact {source} looks like it contains a secret; redact it and try again")
    name = f"{n:03d}-{clean_name}"
    try:
        shutil.copy2(source, path.parent / name)
    except (OSError, shutil.SameFileError) as error:
        raise LogError(f"cannot save artifact {source}: {error}") from None
    return name


def save_stdin_artifact(path, raw_name, n):
    clean_name = validate_artifact_name(raw_name)
    if sys.stdin.isatty():
        raise LogError("--artifact-name reads from stdin; pipe input or use --artifact PATH")
    try:
        raw = sys.stdin.buffer.read()
    except OSError as error:
        raise LogError(f"cannot read artifact from stdin: {error}") from None
    if stream_looks_secret(io.BytesIO(raw)):
        raise LogError(f"stdin artifact {clean_name!r} looks like it contains a secret; redact it and try again")
    name = f"{n:03d}-{clean_name}"
    target = path.parent / name
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{name}.", suffix=".tmp", delete=False
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(raw)
        os.replace(tmp_path, target)
    except OSError as error:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise LogError(f"cannot save artifact {name}: {error}") from None
    return name


def entry_numbers(text, timeline):
    try:
        numbers = [int(n) for n in text.split(",")]
    except ValueError:
        raise LogError("entry numbers are comma-separated, such as 3,7") from None
    unknown = set(numbers) - {e["n"] for e in timeline}
    if unknown:
        raise LogError(f"unknown entries: {sorted(unknown)}")
    return numbers


def replace_artifact_placeholder(text, quoted_path):
    for token in (f'"{ARTIFACT_PLACEHOLDER}"', f"'{ARTIFACT_PLACEHOLDER}'", ARTIFACT_PLACEHOLDER):
        text = text.replace(token, quoted_path)
    return text


def cmd_new(args):
    if not SLUG.match(args.slug):
        raise LogError("slug must be kebab-case, such as fix-nginx-502")
    if looks_secret(args.slug):
        raise LogError("slug looks like it contains a secret; redact it and try again")
    root = project_root(for_locate=bool(args.parent))
    work = work_root_dir(root)
    base = f"{datetime.date.today().isoformat()}-{args.slug}"
    if args.parent:
        parent_path = locate(args.parent)
        ensure_open(load(parent_path), args.parent)
        base = f"{args.parent}/{base}"
    doc = {"id": base, "task": clean("task", args.task), "playbook": clean("playbook", args.playbook),
           "status": "open", "created": now(), "root_cause": None, "timeline": []}
    if args.parent:
        doc["parent"] = args.parent
    exclude_from_git(root)
    log_id, number = base, 2
    while True:
        target_dir = work / log_id
        try:
            target_dir.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            log_id = f"{base}-{number}"
            number += 1
        except OSError as error:
            raise LogError(f"cannot create {target_dir}: {error}") from None
    doc["id"] = log_id
    try:
        save(target_dir / "log.yml", doc)
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise
    print(log_id)


def cmd_phase(args):
    path = locate(args.id)
    doc = load(path)
    ensure_open(doc, args.id)
    doc["timeline"].append({"n": len(doc["timeline"]) + 1, "at": now(), "kind": "phase",
                            "name": clean("name", args.name)})
    save(path, doc)
    print(len(doc["timeline"]))


def cmd_add(args):
    path = locate(args.id)
    doc = load(path)
    ensure_open(doc, args.id)
    timeline = doc["timeline"]
    if args.outcome is not None and args.kind != "run":
        raise LogError("--outcome goes on run entries")
    if args.from_plan is not None and args.kind != "run":
        raise LogError("--from-plan goes on the run that executed the plan")
    if args.reverts is not None and args.kind != "run":
        raise LogError("--reverts goes on the run that executed the revert")
    if args.from_plan is not None and args.reverts is not None:
        raise LogError("--from-plan and --reverts cannot be combined on one entry")

    allowed = ALLOWED_FIELDS[args.kind]
    for field in ALL_OPTIONAL_FIELDS:
        if getattr(args, field, None) is not None and field not in allowed:
            raise LogError(f"--{field.replace('_', '-')} is not allowed on {args.kind} entries")

    entry = {"n": len(timeline) + 1, "at": now(), "kind": args.kind}
    if args.supersedes is not None:
        if args.supersedes not in {e["n"] for e in timeline}:
            raise LogError(f"entry {args.supersedes} does not exist")
        entry["supersedes"] = args.supersedes
    effective_superseded = superseded_numbers(timeline, args.supersedes)
    phase = None
    for existing in reversed(timeline):
        if existing["n"] in effective_superseded:
            continue
        if existing["kind"] == "reopen":
            break
        if existing["kind"] == "phase":
            phase = existing["name"]
            break
    if phase:
        entry["phase"] = phase
    for field in ("text", "why", "target", "identity", "class", "by", "outcome", "claim", "status", "revision",
                  "command", "revert", "no_revert", "result", "rejected"):
        value = getattr(args, field, None)
        if value is not None:
            entry[field] = clean(field.replace("_", "-"), value)
    if args.evidence is not None:
        entry["evidence"] = entry_numbers(args.evidence, timeline)
    if args.from_plan is not None:
        plan = next((e for e in timeline if e["n"] == args.from_plan and e["kind"] == "plan"), None)
        settled = {e.get("from_plan") for e in timeline if e["n"] not in effective_superseded} | {
            e.get("reverts") for e in timeline
            if e["n"] not in effective_superseded and e.get("outcome", "ok") == "ok"
        }
        if plan is None or args.from_plan in settled or args.from_plan in effective_superseded:
            raise LogError(f"entry {args.from_plan} is not a plan still waiting to run")
        for field in PLAN_IMMUTABLE_FIELDS:
            if field in plan and field in entry and entry[field] != plan[field]:
                raise LogError(f"--{field.replace('_', '-')} conflicts with plan {args.from_plan}")
        if ("revert" in plan and "no_revert" in entry) or ("no_revert" in plan and "revert" in entry):
            raise LogError(f"recovery option conflicts with plan {args.from_plan}")
        for field in ("why", *PLAN_IMMUTABLE_FIELDS):
            if field in plan:
                entry.setdefault(field, plan[field])
        entry["from_plan"] = args.from_plan
    required = {"run": ("command", "class"), "plan": ("command", "class", "by"),
                "evidence": ("claim", "status", "command"), "decision": ("text", "why"),
                "note": ("text",)}[args.kind]
    missing = [f"--{f}" for f in required if f not in entry]
    if missing:
        raise LogError(f"{args.kind} needs {', '.join(missing)}")
    if "revert" in entry and "no_revert" in entry:
        raise LogError("--revert and --no-revert cannot be combined")
    if entry.get("class") == "read-only" and ("revert" in entry or "no_revert" in entry):
        raise LogError("read-only entries cannot carry --revert or --no-revert")
    if entry.get("class") == "irreversible" and entry.get("by") != "user":
        raise LogError("irreversible changes are always user-executed; pass --by user")
    if args.reverts is not None:
        if "revert" in entry or "no_revert" in entry:
            raise LogError("--reverts cannot be combined with --revert or --no-revert")
        if entry.get("class") == "read-only":
            raise LogError("a revert run must use --class reversible or irreversible")
        active_reverts = revert_view(timeline, extra_superseded=args.supersedes)
        revertable = {
            item["of"] for item in active_reverts
            if "command" in item and not item["state"].startswith("planned")
        }
        if args.reverts not in revertable:
            raise LogError(f"entry {args.reverts} is not an executed change in the revert list")
        entry["reverts"] = args.reverts
    elif entry.get("class") == "reversible" and "revert" not in entry:
        raise LogError("a reversible change needs --revert")
    elif entry.get("class") == "irreversible" and "revert" not in entry and "no_revert" not in entry:
        raise LogError("an irreversible change needs --revert (best-known recovery) or --no-revert REASON")
    if args.artifact is not None and args.artifact_name is not None:
        raise LogError("--artifact and --artifact-name cannot be combined")
    uses_artifact = any(ARTIFACT_PLACEHOLDER in entry.get(f, "") for f in ("command", "revert"))
    if uses_artifact and args.artifact is None and args.artifact_name is None:
        raise LogError(f"{ARTIFACT_PLACEHOLDER} needs --artifact or --artifact-name")
    if args.artifact is not None or args.artifact_name is not None:
        root = project_root(for_locate=True)
        if args.artifact is not None:
            name = save_artifact(path, args.artifact, entry["n"])
        else:
            name = save_stdin_artifact(path, args.artifact_name, entry["n"])
        entry["artifact"] = name
        doc.setdefault("artifacts", []).append(name)
        relative = shlex.quote(os.path.relpath(path.parent / name, root))
        for field in ("command", "revert"):
            if field in entry:
                entry[field] = replace_artifact_placeholder(entry[field], relative)
    timeline.append(entry)
    save(path, doc)
    print(entry["n"])


def cmd_root_cause(args):
    path = locate(args.id)
    doc = load(path)
    ensure_open(doc, args.id)
    evidence = entry_numbers(args.evidence, doc["timeline"]) if args.evidence else []
    doc["root_cause"] = {"summary": clean("summary", args.summary), "confidence": args.confidence,
                         "evidence": evidence}
    save(path, doc)


def cmd_close(args):
    path = locate(args.id)
    doc = load(path)
    ensure_open(doc, args.id)
    doc["status"] = args.status
    doc["summary"] = clean("summary", args.summary)
    save(path, doc)


def cmd_reopen(args):
    path = locate(args.id)
    doc = load(path)
    prev_status = doc.get("status", "open")
    if prev_status == "open":
        raise LogError(f"log {args.id!r} is already open")
    why = clean("why", args.why)
    entry = {"n": len(doc["timeline"]) + 1, "at": now(), "kind": "reopen", "from_status": prev_status, "why": why}
    if "summary" in doc:
        entry["previous_summary"] = doc.pop("summary")
    doc["status"] = "open"
    doc["timeline"].append(entry)
    save(path, doc)
    print(entry["n"])


def cmd_check(args):
    doc = load(locate(args.id))
    superseded = superseded_numbers(doc["timeline"])
    latest = {}
    for entry in doc["timeline"]:
        if entry["kind"] == "evidence" and entry["n"] > args.since and entry["n"] not in superseded:
            latest[entry["claim"]] = entry
    required_claims = [clean("require", claim) for claim in (args.require or [])]
    expected_revision = clean("revision", args.revision) if args.revision is not None else None
    if args.max_age_hours is not None and (not math.isfinite(args.max_age_hours) or args.max_age_hours < 0):
        raise LogError("--max-age-hours must be a finite number >= 0")
    if not latest and not required_claims:
        print("no claims recorded")
        return 1
    cutoff = None
    if args.max_age_hours is not None:
        try:
            cutoff = datetime.datetime.now().astimezone(datetime.timezone.utc) - datetime.timedelta(
                hours=args.max_age_hours
            )
        except OverflowError:
            raise LogError("--max-age-hours is out of range") from None
    passed = True
    for claim, entry in latest.items():
        status = entry["status"]
        detail = ""
        if expected_revision is not None and entry.get("revision") != expected_revision:
            status = "wrong-rev"
            detail = f" (got {entry.get('revision', 'none')}, want {expected_revision})"
        elif cutoff is not None:
            entry_at = parse_timestamp(entry.get("at"))
            stale = entry_at <= cutoff if args.max_age_hours == 0 else entry_at < cutoff
            if stale:
                status = "stale"
        passed = passed and status == "established"
        print(f"{status:12} #{entry['n']:<4} {claim}{detail}")
    for claim in required_claims:
        if claim not in latest:
            passed = False
            print(f"{'missing':12} {'-':<5} {claim}")
    return 0 if passed else 1


def collect_revert_records(doc, source_id):
    plan = revert_view(doc["timeline"])
    by_n = {e["n"]: e for e in doc["timeline"]}
    fallback = doc.get("updated") or doc.get("created") or ""
    records = []
    for item in plan:
        raw_ts = by_n.get(item["of"], {}).get("at") or fallback
        ts = parse_timestamp(raw_ts) if raw_ts else datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        records.append((ts, item["of"], source_id, item))
    return records


def print_comment_lines(prefix, text):
    lines = text.splitlines() or [""]
    print(f"{prefix}{lines[0]}")
    for extra in lines[1:]:
        print(f"# {extra}")


def print_revert(item, live):
    print_comment_lines(f"# #{item['of']} {item['state']}, {item['class']}: ", item["why"])
    if "target" in item:
        print_comment_lines("# target: ", item["target"])
    if "identity" in item:
        print_comment_lines("# identity: ", item["identity"])
    if "no_revert" in item:
        print_comment_lines("# cannot be reverted: ", item["no_revert"])
        print()
    elif live:
        print(f"{item['command']}\n")
    else:
        print("\n".join(f"# {line}" for line in item["command"].splitlines()) + "\n")


def print_revert_records(records, show_sources):
    executed = [r for r in records if r[3]["state"] == "executed"]
    uncertain = [r for r in records if r[3]["state"] in ("outcome unknown", "failed")]
    planned = [r for r in records if r[3]["state"].startswith("planned")]

    def emit_tier(tier_records, banner, live):
        if not tier_records:
            return
        if banner:
            print(f"{banner}\n")
        current_source = object()
        for _, _, source_id, item in tier_records:
            if show_sources and source_id != current_source:
                if source_id is not None:
                    print_comment_lines("# === delegate ", f"{source_id} ===")
                else:
                    print("# === parent ===")
                print()
                current_source = source_id
            print_revert(item, live=live)

    emit_tier(executed, None, live=True)
    emit_tier(uncertain, "# --- failed or outcome unknown: check live state before reverting ---", live=False)
    emit_tier(planned, "# --- planned, not known to have run: uncomment only for a change you ran ---", live=False)


def cmd_revert_plan(args):
    parent_path = locate(args.id)
    root = project_root(for_locate=True)
    work_root = work_root_dir(root)
    records = collect_revert_records(load(parent_path), None)
    seen = {parent_path}
    has_delegates = False
    for child_path in sorted(parent_path.parent.rglob("log.yml")):
        resolved = child_path.resolve()
        if resolved in seen or not resolved.is_relative_to(work_root):
            continue
        seen.add(resolved)
        child_id = resolved.parent.relative_to(work_root).as_posix()
        child_records = collect_revert_records(load(resolved), child_id)
        if child_records:
            has_delegates = True
            records.extend(child_records)
    if not records:
        print("nothing to revert")
        return
    records.sort(key=lambda r: (r[0], r[1], r[2] or ""), reverse=True)
    print_comment_lines("# run from ", str(root))
    print()
    print_revert_records(records, show_sources=has_delegates)


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
    add.add_argument("--by", choices=("agent", "user"), help="plan or run: who runs or ran it")
    add.add_argument("--outcome", choices=OUTCOMES, help="run: ok (default), failed, or unknown")
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
    add.add_argument("--artifact-name", metavar="NAME", help="read an artifact from stdin and save beside the log as NNN-NAME")

    cause = sub.add_parser("root-cause", help="set the root cause")
    cause.add_argument("id")
    cause.add_argument("--summary", required=True)
    cause.add_argument("--confidence", choices=CONFIDENCE, required=True)
    cause.add_argument("--evidence", help="comma-separated entry numbers")

    close = sub.add_parser("close", help="close the log")
    close.add_argument("id")
    close.add_argument("--status", choices=LOG_STATUSES[1:], required=True)
    close.add_argument("--summary", required=True)

    reopen = sub.add_parser("reopen", help="reopen a closed log")
    reopen.add_argument("id")
    reopen.add_argument("--why", required=True, help="why the closed log is being reopened")

    check = sub.add_parser("check", help="gate on every required and recorded claim's latest evidence")
    check.add_argument("id")
    check.add_argument("--since", type=int, default=0, help="only evidence logged after entry N, such as the unit's run")
    check.add_argument("--max-age-hours", type=float)
    check.add_argument("--revision", help="require every checked evidence entry to match this revision")
    check.add_argument("--require", action="append", metavar="CLAIM", help="claim that must be established (repeatable)")

    revert = sub.add_parser("revert-plan", help="print reverts newest first, including nested delegate logs; never executes")
    revert.add_argument("id")
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    handlers = {"new": cmd_new, "phase": cmd_phase, "add": cmd_add, "root-cause": cmd_root_cause, "close": cmd_close,
                "reopen": cmd_reopen, "check": cmd_check, "revert-plan": cmd_revert_plan}
    try:
        return handlers[args.action](args) or 0
    except LogError as error:
        print(f"log: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
