#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Watch a GitHub pull request, or the stack it belongs to, until it is merge-ready or blocked.

Read-only: it runs `gh pr view`, `gh pr list`, `gh pr checks`, `gh api graphql` queries, and
`git remote get-url`. It never merges, comments, edits, or reruns anything.

Blockers are reported in this order across the whole stack, lowest PR first:
merge conflicts, unresolved review threads, failing checks, then the merge gate
(closed, draft, changes requested). A thread whose latest reply is the gh user's own is awaiting the
reviewer: it is counted, not a blocker, until someone else replies. With no blocker, pending checks or a mergeability GitHub has not
computed yet (UNKNOWN) mean wait; otherwise READY.
READY means everything the agent can fix is clear; a required review may still be outstanding.

Output is one JSON object per line (NDJSON); --pretty prints a table instead.
Exit codes: 0 READY (or STATUS with --status-only), 2 merge conflicts, 3 unresolved review threads,
4 failing checks, 5 timeout, 6 merge gate, 7 GitHub status unavailable, 64 usage.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field

REVIEW_THREADS_QUERY = """
query($owner: String!, $repo: String!, $pr: Int!) {
  viewer { login }
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id isResolved
          comments(first: 1) { totalCount nodes { databaseId body path line author { login } } }
          latest: comments(last: 1) { nodes { author { login } } }
        }
      }
    }
  }
}"""
COMMIT_ROLLUPS_QUERY = """
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      commits(last: 50) { nodes { commit { oid statusCheckRollup { state } } } }
    }
  }
}"""
CHECK_ROLLUP_QUERY = """
query($owner: String!, $repo: String!, $pr: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      commits(last: 1) {
        nodes {
          commit {
            statusCheckRollup {
              contexts(first: 100, after: $after) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  __typename
                  ... on CheckRun { name status conclusion detailsUrl }
                  ... on StatusContext { context state targetUrl }
                }
              }
            }
          }
        }
      }
    }
  }
}"""
PR_FIELDS = "number,mergeable,mergeStateStatus,reviewDecision,headRefOid,state,mergedAt,isDraft"
EXIT = {"conflicts": 2, "review-threads": 3, "failing-checks": 4, "merge-gate": 6, "status-unavailable": 7}
BODY_LIMIT = 300


class QueryError(Exception):
    def __init__(self, detail, retryable=True):
        super().__init__(detail)
        self.detail = detail
        self.retryable = retryable


@dataclass
class Check:
    name: str
    state: str  # passed, skipped, failed, pending
    reported: str
    link: str = ""


@dataclass
class Thread:
    id: str
    author: str | None
    path: str | None
    line: int | None
    body: str  # untrusted text from a reviewer, truncated
    comment_id: int | None = None  # REST id of the first comment, for the replies endpoint
    is_bugbot: bool = False
    bugbot_review_passes: int = 0  # Bugbot review runs seen on this PR, resolved threads included
    answered: bool = False  # the gh user wrote the latest reply, so it is the reviewer's turn


@dataclass
class Row:
    pr: int
    url: str
    state: str  # OPEN, MERGED, CLOSED
    mergeable: str = "UNKNOWN"
    merge_state: str = "UNKNOWN"
    review_decision: str | None = None
    draft: bool = False
    ci: str = "none"  # clean, pending, failing, refused, none
    checks: list[Check] = field(default_factory=list)
    threads: list[Thread] = field(default_factory=list)
    review_automation_running: bool = False

    @property
    def open_threads(self):
        return [t for t in self.threads if not t.answered]

    @property
    def answered_threads(self):
        return [t for t in self.threads if t.answered]

    @property
    def failed(self):
        return [c for c in self.checks if c.state == "failed"]

    @property
    def pending(self):
        return [c for c in self.checks if c.state == "pending"]


# Parsing ---------------------------------------------------------------------------------------

def parse_remote(url):
    """owner/repo from a github.com remote URL, or None."""
    match = re.fullmatch(r"(?:git@github\.com:|ssh://git@github\.com/|https://github\.com/)"
                         r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", url.strip())
    return (match.group(1), match.group(2)) if match else None


def parse_pr_url(url):
    match = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([0-9]+)", url.strip())
    if not match:
        raise QueryError(f"not a GitHub pull request URL: {url}", retryable=False)
    return match.group(1), match.group(2), int(match.group(3))


def parse_fast_check(item):
    """One entry of `gh pr checks --json name,state,link,bucket`."""
    state = str(item.get("state", "")).upper()
    bucket = item.get("bucket", "")
    kind = {"pass": "passed", "skipping": "skipped", "pending": "pending"}.get(bucket, "failed")
    if bucket == "fail" or state in ("FAILURE", "ERROR", "ACTION_REQUIRED"):
        kind = "failed"
    return Check(name=str(item.get("name", "")), state=kind, reported=state, link=str(item.get("link") or ""))


def parse_rollup_node(node):
    """One status-check-rollup context from GraphQL, or None for unknown node types."""
    if node.get("__typename") == "CheckRun":
        status = str(node.get("status") or "").upper()
        conclusion = str(node.get("conclusion") or "").upper()
        if status != "COMPLETED":
            kind, reported = "pending", status or "PENDING"
        elif conclusion == "SUCCESS":
            kind, reported = "passed", conclusion
        elif conclusion in ("NEUTRAL", "SKIPPED"):
            kind, reported = "skipped", conclusion
        else:
            kind, reported = "failed", conclusion or "FAILURE"
        return Check(name=str(node.get("name", "")), state=kind, reported=reported, link=str(node.get("detailsUrl") or ""))
    if node.get("__typename") == "StatusContext":
        state = str(node.get("state") or "").upper()
        kind = {"SUCCESS": "passed", "PENDING": "pending", "EXPECTED": "pending"}.get(state, "failed")
        return Check(name=str(node.get("context", "")), state=kind, reported=state or "FAILURE",
                     link=str(node.get("targetUrl") or ""))
    return None


def is_bugbot(author, body):
    author, body = (author or "").lower(), body.lower()
    tokens = ("bugbot", "cursor_automation_id", "agentic security review", "description start", "severity")
    return "bugbot" in author or (author == "cursor" and any(token in body for token in tokens))


def bugbot_pass_key(body):
    for label in ("RUN_ID", "CURSOR_AUTOMATION_ID"):
        match = re.search(label + r":\s*([a-zA-Z0-9_.:-]+)", body)
        if match:
            return match.group(1)
    return None


def parse_threads(data):
    """Unresolved review threads, with the first comment's text truncated, and the Bugbot pass count."""
    try:
        nodes = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    except (KeyError, TypeError):
        raise QueryError("review threads: unexpected response shape") from None
    viewer = (data["data"].get("viewer") or {}).get("login")
    parsed, pass_keys, keyless = [], set(), False
    for node in nodes:
        comments = (node.get("comments") or {}).get("nodes") or []
        first = comments[0] if comments else {}
        author, body = (first.get("author") or {}).get("login"), str(first.get("body") or "")
        bugbot = is_bugbot(author, body)
        if bugbot:
            key = bugbot_pass_key(body)
            if key:
                pass_keys.add(key)
            else:
                keyless = True
        latest = ((node.get("latest") or {}).get("nodes") or [{}])[-1]
        replied = (node.get("comments") or {}).get("totalCount", len(comments)) > 1
        answered = bool(viewer) and replied and (latest.get("author") or {}).get("login") == viewer
        parsed.append((node, first, author, body, bugbot, answered))
    passes = len(pass_keys) or (1 if keyless else 0)
    return [Thread(id=node["id"], author=author, path=first.get("path"), line=first.get("line"),
                   body=body[:BODY_LIMIT], comment_id=first.get("databaseId"), is_bugbot=bugbot,
                   bugbot_review_passes=passes, answered=answered)
            for node, first, author, body, bugbot, answered in parsed if not node.get("isResolved")]


def order_stack(number, open_prs):
    """PR numbers of the connected stack containing `number`, bottom to top.

    `open_prs` holds dicts with number, headRefName, baseRefName, isCrossRepository. Parents are
    found by base branch; children are visited depth-first in PR-number order. PRs from forks are
    left out: a fork's `main` is not this repository's `main`.
    """
    open_prs = [pr for pr in open_prs if not pr.get("isCrossRepository")]
    by_number = {pr["number"]: pr for pr in open_prs}
    by_head = {pr["headRefName"]: pr for pr in open_prs}
    if number not in by_number:
        return [number]
    start = by_number[number]
    below, seen, current = [], {number}, start
    while current["baseRefName"] in by_head:
        parent = by_head[current["baseRefName"]]
        if parent["number"] in seen:
            break
        below.append(parent)
        seen.add(parent["number"])
        current = parent
    above = []

    def visit(parent):
        for child in sorted((p for p in open_prs if p["baseRefName"] == parent["headRefName"]), key=lambda p: p["number"]):
            if child["number"] not in seen:
                seen.add(child["number"])
                above.append(child["number"])
                visit(child)

    visit(start)
    return [pr["number"] for pr in reversed(below)] + [number] + above


# GitHub reader (read-only) ---------------------------------------------------------------------

class GhReader:
    """Every GitHub read goes through `gh`, which owns authentication."""

    def run(self, argv):
        try:
            return subprocess.run(argv, capture_output=True, text=True, timeout=120)
        except FileNotFoundError:
            raise QueryError(f"{argv[0]} is not installed", retryable=False) from None
        except subprocess.TimeoutExpired:
            raise QueryError(f"{' '.join(argv[:3])} timed out") from None

    def json(self, argv, ok_codes=(0,)):
        result = self.run(argv)
        if result.returncode not in ok_codes:
            first = (result.stderr.strip().splitlines() or [f"exit {result.returncode}"])[0][:240]
            raise QueryError(f"{' '.join(argv[:3])}: {first}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            raise QueryError(f"{' '.join(argv[:3])}: output is not JSON") from None

    def graphql(self, query, owner, repo, pr, **extra):
        argv = ["gh", "api", "graphql", "-f", f"query={query}", "-f", f"owner={owner}", "-f", f"repo={repo}",
                "-F", f"pr={pr}"]
        for key, value in extra.items():
            argv += ["-f", f"{key}={value}"]
        return self.json(argv)

    def origin_repo(self):
        result = self.run(["git", "remote", "get-url", "origin"])
        return parse_remote(result.stdout) if result.returncode == 0 else None

    def current_pr(self, number):
        argv = ["gh", "pr", "view"] + ([str(number)] if number else []) + ["--json", "number,url"]
        return parse_pr_url(self.json(argv)["url"])

    def pull_request(self, owner, repo, number):
        return self.json(["gh", "pr", "view", str(number), "--repo", f"{owner}/{repo}", "--json", PR_FIELDS])

    def open_prs(self, owner, repo):
        return self.json(["gh", "pr", "list", "--repo", f"{owner}/{repo}", "--state", "open", "--limit", "300",
                          "--json", "number,headRefName,baseRefName,isCrossRepository"])

    def checks(self, owner, repo, number):
        result = self.run(["gh", "pr", "checks", str(number), "--repo", f"{owner}/{repo}",
                           "--json", "name,state,link,bucket"])
        # gh exits 1 when a check failed and 8 when checks are pending; both still print JSON.
        if result.returncode in (0, 1, 8) and result.stdout.strip():
            try:
                checks = [parse_fast_check(item) for item in json.loads(result.stdout)]
            except (json.JSONDecodeError, AttributeError, TypeError):
                checks = []
            if checks:
                return checks
        checks, after = [], None
        while True:
            extra = {"after": after} if after else {}
            data = self.graphql(CHECK_ROLLUP_QUERY, owner, repo, number, **extra)
            try:
                nodes = data["data"]["repository"]["pullRequest"]["commits"]["nodes"]
                rollup = nodes[-1]["commit"]["statusCheckRollup"] if nodes else None
            except (KeyError, TypeError, IndexError):
                raise QueryError("check rollup: unexpected response shape") from None
            if not rollup:
                return checks
            contexts = rollup["contexts"]
            checks += [c for c in map(parse_rollup_node, contexts["nodes"]) if c]
            page = contexts["pageInfo"]
            if not page.get("hasNextPage") or not page.get("endCursor"):
                return checks
            after = page["endCursor"]

    def review_threads(self, owner, repo, number):
        return parse_threads(self.graphql(REVIEW_THREADS_QUERY, owner, repo, number))

    def commit_rollups(self, owner, repo, number):
        data = self.graphql(COMMIT_ROLLUPS_QUERY, owner, repo, number)
        try:
            nodes = data["data"]["repository"]["pullRequest"]["commits"]["nodes"]
            return {n["commit"]["oid"]: (n["commit"]["statusCheckRollup"] or {}).get("state") for n in nodes}
        except (KeyError, TypeError):
            raise QueryError("commit rollups: unexpected response shape") from None


# Policy ----------------------------------------------------------------------------------------

def read_row(reader, owner, repo, number, allow_no_checks):
    facts = reader.pull_request(owner, repo, number)
    row = Row(pr=number, url=f"https://github.com/{owner}/{repo}/pull/{number}", state=facts.get("state", "OPEN"),
              mergeable=facts.get("mergeable") or "UNKNOWN", merge_state=facts.get("mergeStateStatus") or "UNKNOWN",
              review_decision=facts.get("reviewDecision") or None, draft=bool(facts.get("isDraft")))
    if facts.get("mergedAt"):
        row.state = "MERGED"
    if row.state != "OPEN":
        return row
    row.threads = reader.review_threads(owner, repo, number)
    row.checks = reader.checks(owner, repo, number)
    if not row.checks and not allow_no_checks:
        raise QueryError(f"#{number}: no checks reported yet; pass --allow-no-checks if this repository has no CI")
    automation = ("bugbot", "security review", "pr review automation", "review automation")
    row.review_automation_running = any(any(t in c.name.lower() for t in automation) for c in row.pending)
    head_rollup = reader.commit_rollups(owner, repo, number).get(facts.get("headRefOid"))
    if row.failed:
        row.ci = "failing"
    elif row.merge_state == "BLOCKED" and head_rollup in ("FAILURE", "ERROR"):
        row.ci = "refused"  # GitHub counts a failing check that the check list did not show
    elif row.pending:
        row.ci = "pending"
    else:
        row.ci = "clean" if row.checks else "none"
    return row


def conflicted(row):
    return row.state == "OPEN" and (row.mergeable == "CONFLICTING" or row.merge_state in ("DIRTY", "CONFLICTING"))


def gate_reason(row, allow_draft):
    if row.state == "CLOSED":
        return "closed-without-merge"
    if row.state != "OPEN":
        return None
    if row.draft and not allow_draft:
        return None if row.ci == "pending" else "draft"
    if row.review_decision == "CHANGES_REQUESTED":
        return "changes-requested"
    return None


def decide(rows, allow_draft):
    """The stack's decision: ("blocker", kind, row, detail), ("waiting", row, reason), or ("ready",)."""
    for row in rows:
        if conflicted(row):
            return ("blocker", "conflicts", row, {"mergeable": row.mergeable, "mergeState": row.merge_state})
    for row in rows:
        if row.state == "OPEN" and row.open_threads:
            return ("blocker", "review-threads", row, {"threads": [asdict(t) for t in row.open_threads]})
    for row in rows:
        if row.state == "OPEN" and row.ci in ("failing", "refused"):
            failed = [asdict(c) for c in row.failed]
            return ("blocker", "failing-checks", row, {"ci": row.ci, "failed": failed})
    for row in rows:
        reason = gate_reason(row, allow_draft)
        if reason:
            return ("blocker", "merge-gate", row, {"reason": reason})
    for row in rows:
        if row.state == "OPEN" and row.ci == "pending":
            return ("waiting", row, "pending-checks")
    for row in rows:
        # GitHub computes mergeability lazily; UNKNOWN means it has not decided yet.
        if row.state == "OPEN" and (row.merge_state == "UNKNOWN" or row.mergeable == "UNKNOWN"):
            return ("waiting", row, "mergeability-unknown")
    return ("ready",)


# Running ---------------------------------------------------------------------------------------

def backoff(interval, failures):
    return min(max(interval, 60) * 2 ** (failures - 1), 300)


def summarize(row):
    return {"pr": row.pr, "url": row.url, "state": row.state, "ci": row.ci, "mergeState": row.merge_state,
            "reviewDecision": row.review_decision, "draft": row.draft, "mergeable": row.mergeable,
            "threads": len(row.open_threads), "awaitingReviewer": len(row.answered_threads),
            "reviewAutomationRunning": row.review_automation_running,
            "failed": [c.name for c in row.failed], "pending": [c.name for c in row.pending]}


def status_table(rows):
    """The four-column table Babysit's reply carries: PR, CI, Review, Merge."""
    lines = ["| PR | CI | Review | Merge |", "| --- | --- | --- | --- |"]
    for row in rows:
        if row["state"] != "OPEN":
            ci = review = "-"
            merge = "merged" if row["state"] == "MERGED" else "closed"
        else:
            ci = {"clean": "passing", "none": "no checks", "refused": "GitHub reports failing checks",
                  "pending": f"{len(row['pending'])} pending",
                  "failing": f"{len(row['failed'])} failed" + (f", {len(row['pending'])} pending" if row["pending"] else "")
                  }[row["ci"]]
            review = (f"{row['threads']} open" if row["threads"] else "clear") + (
                f", {row['awaitingReviewer']} awaiting reviewer" if row.get("awaitingReviewer") else "") + (
                ", review automation running" if row["reviewAutomationRunning"] else "")
            if row["draft"]:
                merge = "draft"
            elif row["reviewDecision"] == "CHANGES_REQUESTED":
                merge = "changes requested"
            elif row["mergeable"] == "CONFLICTING" or row["mergeState"] in ("DIRTY", "CONFLICTING"):
                merge = "conflict"
            else:
                merge = row["mergeState"].lower()
        lines.append(f"| [#{row['pr']}]({row['url']}) | {ci} | {review} | {merge} |")
    return "\n".join(lines) + "\n"


class Watcher:
    def __init__(self, reader, emit, sleep=time.sleep, clock=time.monotonic):
        self.reader, self.emit, self.sleep, self.clock = reader, emit, sleep, clock
        self.sequence = 0

    def event(self, kind, terminal=False, exit_code=None, **payload):
        self.sequence += 1
        event = {"kind": kind, "sequence": self.sequence, "terminal": terminal,
                 "observedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **payload}
        if terminal:
            event["exitCode"] = exit_code
        self.emit(event)
        return exit_code

    def run(self, owner, repo, numbers, args):
        started, failures = self.clock(), 0
        while True:
            try:
                try:
                    rows = [read_row(self.reader, owner, repo, n, args.allow_no_checks) for n in numbers]
                except (KeyError, TypeError, AttributeError, IndexError) as error:
                    raise QueryError(f"unexpected gh response shape: {error!r}") from None
                failures = 0
            except QueryError as error:
                failures += 1
                if not error.retryable or failures >= args.max_query_errors:
                    return self.event("BLOCKER", True, EXIT["status-unavailable"], blocker="status-unavailable",
                                      detail=error.detail, failures=failures)
                wait = backoff(args.interval, failures)
                self.event("RETRY", detail=error.detail, failures=failures, retryInSeconds=wait)
                if args.timeout and self.clock() - started >= args.timeout:
                    return self.event("TIMEOUT", True, 5, reason="status-unavailable", detail=error.detail)
                self.sleep(wait)
                continue
            if args.status_only:
                return self.event("STATUS", True, 0, rows=[summarize(r) for r in rows])
            if len(rows) > 1:
                self.event("STATUS", rows=[summarize(r) for r in rows])
            decision = decide(rows, args.allow_draft)
            if decision[0] == "blocker":
                _, kind, row, detail = decision
                return self.event("BLOCKER", True, EXIT[kind], blocker=kind, pr=summarize(row), **detail,
                                  rows=[summarize(r) for r in rows])
            if decision[0] == "ready":
                return self.event("READY", True, 0, rows=[summarize(r) for r in rows])
            _, frontier, reason = decision
            self.event("WAITING", reason=reason, pr=summarize(frontier))
            if args.timeout and self.clock() - started >= args.timeout:
                return self.event("TIMEOUT", True, 5, reason=reason, pr=summarize(frontier),
                                  rows=[summarize(r) for r in rows])
            self.sleep(args.interval)


def render_pretty(event):
    kind = event["kind"]
    if "rows" in event and kind in ("STATUS", "READY"):
        head = f"{kind}" + (f" exit {event['exitCode']}" if event["terminal"] else "")
        return head + "\n" + status_table(event["rows"])
    if kind == "BLOCKER":
        where = f" on #{event['pr']['pr']}" if "pr" in event else ""
        text = f"BLOCKER {event['blocker']}{where} (exit {event['exitCode']})"
        for thread in event.get("threads", []):
            text += (f"\n  thread {thread['id']} comment {thread['comment_id']} {thread['path']}:{thread['line']}"
                     f" by {thread['author']}"
                     f" isBugbot={thread['is_bugbot']} bugbotReviewPasses={thread['bugbot_review_passes']}")
        for check in event.get("failed", []):
            text += f"\n  failed {check['name']} {check['link']}"
        if "reason" in event:
            text += f"\n  reason {event['reason']}"
        if "detail" in event:
            text += f"\n  {event['detail']}"
        return text + "\n" + (status_table(event["rows"]) if "rows" in event else "")
    if kind == "WAITING":
        pending = f": {', '.join(event['pr']['pending'])}" if event["pr"]["pending"] else ""
        return f"WAITING on #{event['pr']['pr']} ({event['reason']}){pending}\n"
    if kind == "RETRY":
        return f"RETRY in {event['retryInSeconds']}s after {event['failures']} failure(s): {event['detail']}\n"
    text = f"{kind} exit {event.get('exitCode')}: {event.get('reason', '')}\n"
    return text + (status_table(event["rows"]) if "rows" in event else "")


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pr", type=lambda v: int(v.lstrip("#")), help="PR number (default: the current branch's PR)")
    parser.add_argument("--owner")
    parser.add_argument("--repo")
    parser.add_argument("--stack", action="store_true", help="watch the connected open stack, bottom to top")
    parser.add_argument("--status-only", action="store_true", help="print one status and exit 0")
    parser.add_argument("--interval", type=float, default=60, help="seconds between polls (default 60)")
    parser.add_argument("--timeout", type=float, default=3600, help="deadline in seconds, 0 disables (default 3600)")
    parser.add_argument("--max-query-errors", type=int, default=5, help="consecutive query errors allowed (default 5)")
    parser.add_argument("--allow-draft", action="store_true", help="do not treat a draft as a merge gate")
    parser.add_argument("--allow-no-checks", action="store_true", help="treat a PR with no checks as clean")
    parser.add_argument("--pretty", action="store_true", help="human-readable output instead of NDJSON")
    args = parser.parse_args(argv)
    if args.interval <= 0 or args.timeout < 0 or args.max_query_errors < 1 or (args.pr is not None and args.pr < 1):
        parser.error("--interval and --max-query-errors must be positive, --timeout zero or more, --pr positive")
    return args


def main(argv=None, reader=None, out=sys.stdout, sleep=time.sleep, clock=time.monotonic):
    try:
        args = parse_args(argv)
    except SystemExit as error:
        return 64 if error.code else 0
    reader = reader or GhReader()

    def emit(event):
        out.write(render_pretty(event) if args.pretty else json.dumps(event) + "\n")
        out.flush()

    watcher = Watcher(reader, emit, sleep, clock)
    try:
        if args.pr and args.owner and args.repo:
            owner, repo, number = args.owner, args.repo, args.pr
        elif args.pr and (origin := reader.origin_repo()):
            owner, repo, number = args.owner or origin[0], args.repo or origin[1], args.pr
        else:
            owner, repo, number = reader.current_pr(args.pr)
            owner, repo = args.owner or owner, args.repo or repo
        numbers = order_stack(number, reader.open_prs(owner, repo)) if args.stack else [number]
    except (KeyError, TypeError, AttributeError) as error:
        return watcher.event("BLOCKER", True, EXIT["status-unavailable"], blocker="status-unavailable",
                             detail=f"unexpected gh response shape: {error!r}", failures=1)
    except QueryError as error:
        return watcher.event("BLOCKER", True, EXIT["status-unavailable"], blocker="status-unavailable",
                             detail=error.detail, failures=1)
    return watcher.run(owner, repo, numbers, args)


if __name__ == "__main__":
    sys.exit(main())
