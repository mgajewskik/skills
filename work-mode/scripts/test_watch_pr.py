"""Behavior tests for watch_pr.py. Run: python3 -m unittest discover -s <scripts dir>"""

import io
import json
import subprocess
import unittest
from unittest import mock

import watch_pr


def facts(number, **overrides):
    base = {"number": number, "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN", "reviewDecision": "",
            "headRefOid": f"sha{number}", "state": "OPEN", "mergedAt": None, "isDraft": False}
    return {**base, **overrides}


class FakeReader:
    """Serves PR facts, checks, and threads per PR; a list of values is served one poll at a time."""

    def __init__(self, prs, checks=None, threads=None, rollups=None, open_prs=None, origin=("acme", "app")):
        self.prs, self.checks_by_pr, self.threads_by_pr = prs, checks or {}, threads or {}
        self.rollups, self.open, self.origin = rollups or {}, open_prs or [], origin
        self.polls = {}

    def _next(self, table, number, default):
        value = table.get(number, default)
        if isinstance(value, list) and value and isinstance(value[0], list):
            index = self.polls.get((id(table), number), 0)
            self.polls[(id(table), number)] = index + 1
            return value[min(index, len(value) - 1)]
        return value

    def origin_repo(self):
        return self.origin

    def current_pr(self, number):
        return ("acme", "app", number or 1)

    def pull_request(self, owner, repo, number):
        value = self.prs[number]
        if isinstance(value, Exception):
            raise value
        return value

    def open_prs(self, owner, repo):
        return self.open

    def checks(self, owner, repo, number):
        return self._next(self.checks_by_pr, number, [[watch_pr.Check("build", "passed", "SUCCESS")]])

    def review_threads(self, owner, repo, number):
        return self.threads_by_pr.get(number, [])

    def commit_rollups(self, owner, repo, number):
        return self.rollups.get(number, {})


PASSED = watch_pr.Check("build", "passed", "SUCCESS")
PENDING = watch_pr.Check("build", "pending", "IN_PROGRESS")
FAILED = watch_pr.Check("build", "failed", "FAILURE", "https://ci/1")
THREAD = watch_pr.Thread("T1", "reviewer", "app.py", 3, "please rename")


class Clock:
    def __init__(self):
        self.now = 0.0
        self.slept = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def watch(reader, *argv):
    out, clock = io.StringIO(), Clock()
    code = watch_pr.main(list(argv), reader=reader, out=out, sleep=clock.sleep, clock=clock)
    events = [json.loads(line) for line in out.getvalue().splitlines()]
    return code, events, clock


class ParsingTest(unittest.TestCase):
    def test_fast_check_buckets(self):
        cases = [({"name": "a", "state": "SUCCESS", "bucket": "pass"}, "passed"),
                 ({"name": "a", "state": "IN_PROGRESS", "bucket": "pending"}, "pending"),
                 ({"name": "a", "state": "SKIPPED", "bucket": "skipping"}, "skipped"),
                 ({"name": "a", "state": "FAILURE", "bucket": "fail"}, "failed"),
                 ({"name": "a", "state": "ACTION_REQUIRED", "bucket": "pending"}, "failed"),
                 ({"name": "a", "state": "WEIRD", "bucket": "cancel"}, "failed")]
        for item, expected in cases:
            with self.subTest(item=item):
                self.assertEqual(watch_pr.parse_fast_check(item).state, expected)

    def test_rollup_nodes(self):
        cases = [({"__typename": "CheckRun", "name": "a", "status": "IN_PROGRESS"}, "pending"),
                 ({"__typename": "CheckRun", "name": "a", "status": "COMPLETED", "conclusion": "SUCCESS"}, "passed"),
                 ({"__typename": "CheckRun", "name": "a", "status": "COMPLETED", "conclusion": "NEUTRAL"}, "skipped"),
                 ({"__typename": "CheckRun", "name": "a", "status": "COMPLETED", "conclusion": "TIMED_OUT"}, "failed"),
                 ({"__typename": "StatusContext", "context": "ci", "state": "EXPECTED"}, "pending"),
                 ({"__typename": "StatusContext", "context": "ci", "state": "ERROR"}, "failed")]
        for node, expected in cases:
            with self.subTest(node=node):
                self.assertEqual(watch_pr.parse_rollup_node(node).state, expected)
        self.assertIsNone(watch_pr.parse_rollup_node({"__typename": "Other"}))

    def test_remotes(self):
        self.assertEqual(watch_pr.parse_remote("git@github.com:acme/app.git\n"), ("acme", "app"))
        self.assertEqual(watch_pr.parse_remote("https://github.com/acme/app"), ("acme", "app"))
        self.assertEqual(watch_pr.parse_remote("ssh://git@github.com/acme/app.git"), ("acme", "app"))
        self.assertIsNone(watch_pr.parse_remote("https://gitlab.com/acme/app.git"))

    def test_pr_url(self):
        self.assertEqual(watch_pr.parse_pr_url("https://github.com/acme/app/pull/12"), ("acme", "app", 12))
        with self.assertRaises(watch_pr.QueryError) as caught:
            watch_pr.parse_pr_url("https://example.com/acme/app/pull/12")
        self.assertFalse(caught.exception.retryable)

    def test_threads_keep_only_unresolved_and_truncate(self):
        data = {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
            {"id": "A", "isResolved": True, "comments": {"nodes": [{"body": "old"}]}},
            {"id": "B", "isResolved": False, "comments": {"nodes": [
                {"body": "x" * 1000, "path": "a.py", "line": 4, "author": {"login": "rev"}}]}},
        ]}}}}}
        threads = watch_pr.parse_threads(data)
        self.assertEqual([t.id for t in threads], ["B"])
        self.assertEqual(len(threads[0].body), watch_pr.BODY_LIMIT)
        self.assertEqual((threads[0].author, threads[0].path, threads[0].line), ("rev", "a.py", 4))

    def test_bugbot_passes_count_distinct_runs_including_resolved(self):
        def node(id, resolved, author, body):
            return {"id": id, "isResolved": resolved, "comments": {"nodes": [{"body": body, "author": {"login": author}}]}}
        data = {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
            node("A", True, "cursor[bot]-bugbot", "old finding RUN_ID: r1"),
            node("B", False, "cursor-bugbot", "new finding RUN_ID: r2"),
            node("C", False, "cursor", "Severity: high " + "x" * 400 + " CURSOR_AUTOMATION_ID: r2"),
            node("D", False, "human", "please rename"),
        ]}}}}}
        threads = {t.id: t for t in watch_pr.parse_threads(data)}
        self.assertEqual(sorted(threads), ["B", "C", "D"])
        self.assertEqual([threads[i].is_bugbot for i in "BCD"], [True, True, False])
        self.assertEqual({t.bugbot_review_passes for t in threads.values()}, {2})

    def test_bugbot_without_run_id_counts_one_pass(self):
        data = {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
            {"id": "A", "isResolved": False, "comments": {"nodes": [{"body": "bug", "author": {"login": "bugbot"}}]}}]}}}}}
        self.assertEqual(watch_pr.parse_threads(data)[0].bugbot_review_passes, 1)

    def test_order_stack_bottom_to_top(self):
        open_prs = [{"number": 3, "headRefName": "c", "baseRefName": "b"},
                    {"number": 1, "headRefName": "a", "baseRefName": "main"},
                    {"number": 2, "headRefName": "b", "baseRefName": "a"},
                    {"number": 9, "headRefName": "z", "baseRefName": "main"}]
        self.assertEqual(watch_pr.order_stack(2, open_prs), [1, 2, 3])
        self.assertEqual(watch_pr.order_stack(9, open_prs), [9])
        self.assertEqual(watch_pr.order_stack(5, open_prs), [5])

    def test_fork_prs_are_never_stack_members(self):
        open_prs = [{"number": 32, "headRefName": "main", "baseRefName": "main", "isCrossRepository": True},
                    {"number": 485, "headRefName": "fix", "baseRefName": "main", "isCrossRepository": False},
                    {"number": 486, "headRefName": "fix-2", "baseRefName": "fix", "isCrossRepository": False}]
        self.assertEqual(watch_pr.order_stack(485, open_prs), [485, 486])
        self.assertEqual(watch_pr.order_stack(32, open_prs), [32])

    def test_run_id_wins_over_automation_id(self):
        self.assertEqual(watch_pr.bugbot_pass_key("CURSOR_AUTOMATION_ID: a\nRUN_ID: b"), "b")
        self.assertEqual(watch_pr.bugbot_pass_key("CURSOR_AUTOMATION_ID: a"), "a")

    def test_threads_carry_the_rest_comment_id(self):
        data = {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
            {"id": "T", "isResolved": False, "comments": {"nodes": [{"databaseId": 991, "body": "x"}]}}]}}}}}
        self.assertEqual(watch_pr.parse_threads(data)[0].comment_id, 991)

    def test_thread_is_answered_when_the_viewer_wrote_the_latest_reply(self):
        def node(id, count, first, latest):
            return {"id": id, "isResolved": False,
                    "comments": {"totalCount": count, "nodes": [{"body": "x", "author": {"login": first}}]},
                    "latest": {"nodes": [{"author": {"login": latest}}]}}
        data = {"data": {"viewer": {"login": "me"}, "repository": {"pullRequest": {"reviewThreads": {"nodes": [
            node("replied", 2, "rev", "me"),
            node("reviewer-again", 3, "rev", "rev"),
            node("own-note", 1, "me", "me"),
        ]}}}}}
        answered = {t.id: t.answered for t in watch_pr.parse_threads(data)}
        self.assertEqual(answered, {"replied": True, "reviewer-again": False, "own-note": False})

    def test_thread_is_unanswered_when_the_viewer_is_unknown(self):
        data = {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
            {"id": "T", "isResolved": False, "comments": {"totalCount": 2, "nodes": [{"body": "x"}]},
             "latest": {"nodes": [{"author": {"login": "me"}}]}}]}}}}}
        self.assertFalse(watch_pr.parse_threads(data)[0].answered)

    def test_order_stack_survives_a_cycle(self):
        open_prs = [{"number": 1, "headRefName": "a", "baseRefName": "b"},
                    {"number": 2, "headRefName": "b", "baseRefName": "a"}]
        self.assertEqual(sorted(watch_pr.order_stack(1, open_prs)), [1, 2])


class VerdictTest(unittest.TestCase):
    def test_clean_pr_is_ready(self):
        code, events, _ = watch(FakeReader({7: facts(7)}), "--pr", "7")
        self.assertEqual((code, events[-1]["kind"]), (0, "READY"))

    def test_merged_pr_is_ready(self):
        code, events, _ = watch(FakeReader({7: facts(7, state="MERGED", mergedAt="2026-10-03T10:00:00Z")}), "--pr", "7")
        self.assertEqual((code, events[-1]["kind"]), (0, "READY"))

    def test_conflict_exits_2(self):
        code, events, _ = watch(FakeReader({7: facts(7, mergeable="CONFLICTING")}), "--pr", "7")
        self.assertEqual((code, events[-1]["blocker"]), (2, "conflicts"))

    def test_unresolved_thread_exits_3_with_thread_data(self):
        code, events, _ = watch(FakeReader({7: facts(7)}, threads={7: [THREAD]}, checks={7: [FAILED]}), "--pr", "7")
        self.assertEqual(code, 3)
        self.assertEqual(events[-1]["threads"][0]["body"], "please rename")
        self.assertEqual((events[-1]["rows"][0]["ci"], events[-1]["rows"][0]["failed"]), ("failing", ["build"]))

    def test_answered_threads_wait_for_the_reviewer_instead_of_blocking(self):
        answered = watch_pr.Thread("T2", "reviewer", "app.py", 9, "why?", answered=True)
        code, events, _ = watch(FakeReader({7: facts(7)}, threads={7: [answered]}), "--pr", "7")
        self.assertEqual((code, events[-1]["kind"]), (0, "READY"))
        self.assertEqual((events[-1]["rows"][0]["threads"], events[-1]["rows"][0]["awaitingReviewer"]), (0, 1))

    def test_only_unanswered_threads_block(self):
        answered = watch_pr.Thread("T2", "reviewer", "app.py", 9, "why?", answered=True)
        code, events, _ = watch(FakeReader({7: facts(7)}, threads={7: [THREAD, answered]}), "--pr", "7")
        self.assertEqual(code, 3)
        self.assertEqual([t["id"] for t in events[-1]["threads"]], ["T1"])

    def test_failing_check_exits_4(self):
        code, events, _ = watch(FakeReader({7: facts(7)}, checks={7: [FAILED, PENDING]}), "--pr", "7")
        self.assertEqual((code, events[-1]["failed"][0]["link"]), (4, "https://ci/1"))

    def test_github_refusal_without_visible_failure_exits_4(self):
        reader = FakeReader({7: facts(7, mergeStateStatus="BLOCKED")}, rollups={7: {"sha7": "FAILURE"}})
        code, events, _ = watch(reader, "--pr", "7")
        self.assertEqual((code, events[-1]["ci"]), (4, "refused"))

    def test_blocked_by_required_review_alone_is_ready(self):
        reader = FakeReader({7: facts(7, mergeStateStatus="BLOCKED", reviewDecision="REVIEW_REQUIRED")},
                            rollups={7: {"sha7": "SUCCESS"}})
        code, events, _ = watch(reader, "--pr", "7")
        self.assertEqual(code, 0)
        self.assertEqual(events[-1]["rows"][0]["reviewDecision"], "REVIEW_REQUIRED")

    def test_changes_requested_exits_6(self):
        code, events, _ = watch(FakeReader({7: facts(7, reviewDecision="CHANGES_REQUESTED")}), "--pr", "7")
        self.assertEqual((code, events[-1]["reason"]), (6, "changes-requested"))

    def test_closed_pr_exits_6(self):
        code, events, _ = watch(FakeReader({7: facts(7, state="CLOSED")}), "--pr", "7")
        self.assertEqual((code, events[-1]["reason"]), (6, "closed-without-merge"))

    def test_draft_is_a_gate_unless_allowed_or_pending(self):
        self.assertEqual(watch(FakeReader({7: facts(7, isDraft=True)}), "--pr", "7")[0], 6)
        self.assertEqual(watch(FakeReader({7: facts(7, isDraft=True)}), "--pr", "7", "--allow-draft")[0], 0)
        reader = FakeReader({7: facts(7, isDraft=True)}, checks={7: [[PENDING], [PASSED]]})
        code, events, _ = watch(reader, "--pr", "7")
        self.assertEqual([e["kind"] for e in events], ["WAITING", "BLOCKER"])
        self.assertEqual(code, 6)

    def test_draft_with_pending_checks_waits_even_with_changes_requested(self):
        reader = FakeReader({7: facts(7, isDraft=True, reviewDecision="CHANGES_REQUESTED")}, checks={7: [[PENDING]]})
        code, events, _ = watch(reader, "--pr", "7", "--interval", "60", "--timeout", "60")
        self.assertEqual((code, events[0]["kind"]), (5, "WAITING"))

    def test_malformed_response_is_a_verdict_not_a_traceback(self):
        reader = FakeReader({7: ["not", "a", "dict"]})
        code, events, _ = watch(reader, "--pr", "7", "--max-query-errors", "1")
        self.assertEqual(code, 7)
        self.assertIn("unexpected gh response shape", events[-1]["detail"])

    def test_owner_and_repo_override_inferred_context(self):
        reader = FakeReader({1: facts(1)}, origin=None)
        code, events, _ = watch(reader, "--owner", "fork", "--repo", "copy")
        self.assertEqual(code, 0)
        self.assertEqual(events[-1]["rows"][0]["url"], "https://github.com/fork/copy/pull/1")

    def test_pending_waits_then_ready(self):
        reader = FakeReader({7: facts(7)}, checks={7: [[PENDING], [PENDING], [PASSED]]})
        code, events, clock = watch(reader, "--pr", "7", "--interval", "30")
        self.assertEqual([e["kind"] for e in events], ["WAITING", "WAITING", "READY"])
        self.assertEqual((code, clock.slept), (0, [30.0, 30.0]))

    def test_unknown_mergeability_waits_instead_of_ready(self):
        reader = FakeReader({7: facts(7, mergeStateStatus="UNKNOWN", mergeable="UNKNOWN")})
        code, events, _ = watch(reader, "--pr", "7", "--interval", "60", "--timeout", "60")
        self.assertEqual([e["kind"] for e in events], ["WAITING", "WAITING", "TIMEOUT"])
        self.assertEqual((code, events[-1]["reason"]), (5, "mergeability-unknown"))

    def test_pending_times_out_with_exit_5(self):
        reader = FakeReader({7: facts(7)}, checks={7: [[PENDING]]})
        code, events, clock = watch(reader, "--pr", "7", "--interval", "60", "--timeout", "120")
        self.assertEqual((code, events[-1]["kind"], events[-1]["reason"]), (5, "TIMEOUT", "pending-checks"))
        self.assertEqual(clock.now, 120)

    def test_default_deadline_is_one_hour(self):
        reader = FakeReader({7: facts(7)}, checks={7: [[PENDING]]})
        code, _, clock = watch(reader, "--pr", "7")
        self.assertEqual((code, clock.now), (5, 3600))

    def test_no_checks_is_unavailable_unless_allowed(self):
        code, events, _ = watch(FakeReader({7: facts(7)}, checks={7: []}), "--pr", "7", "--max-query-errors", "1")
        self.assertEqual((code, events[-1]["blocker"]), (7, "status-unavailable"))
        self.assertIn("--allow-no-checks", events[-1]["detail"])
        code, events, _ = watch(FakeReader({7: facts(7)}, checks={7: []}), "--pr", "7", "--allow-no-checks")
        self.assertEqual((code, events[-1]["rows"][0]["ci"]), (0, "none"))

    def test_query_errors_retry_with_backoff_then_give_up(self):
        reader = FakeReader({7: watch_pr.QueryError("gh: rate limited")})
        code, events, clock = watch(reader, "--pr", "7", "--max-query-errors", "3", "--interval", "10")
        self.assertEqual([e["kind"] for e in events], ["RETRY", "RETRY", "BLOCKER"])
        self.assertEqual((code, clock.slept), (7, [60, 120]))

    def test_non_retryable_error_stops_at_once(self):
        reader = FakeReader({7: watch_pr.QueryError("bad url", retryable=False)})
        code, events, _ = watch(reader, "--pr", "7")
        self.assertEqual((code, len(events)), (7, 1))

    def test_status_only_reports_and_exits_0_even_when_blocked(self):
        code, events, _ = watch(FakeReader({7: facts(7, mergeable="CONFLICTING")}), "--pr", "7", "--status-only")
        self.assertEqual((code, events[-1]["kind"], len(events)), (0, "STATUS", 1))


class StackTest(unittest.TestCase):
    OPEN = [{"number": 1, "headRefName": "a", "baseRefName": "main"},
            {"number": 2, "headRefName": "b", "baseRefName": "a"},
            {"number": 3, "headRefName": "c", "baseRefName": "b"}]

    def reader(self, **kwargs):
        return FakeReader({1: facts(1), 2: facts(2), 3: facts(3)}, open_prs=self.OPEN, **kwargs)

    def test_whole_clean_stack_is_ready(self):
        code, events, _ = watch(self.reader(), "--pr", "2", "--stack")
        self.assertEqual([r["pr"] for r in events[-1]["rows"]], [1, 2, 3])
        self.assertEqual((code, events[0]["kind"]), (0, "STATUS"))

    def test_conflict_upstack_outranks_a_thread_on_the_frontier(self):
        reader = FakeReader({1: facts(1), 2: facts(2), 3: facts(3, mergeable="CONFLICTING")},
                            threads={1: [THREAD]}, open_prs=self.OPEN)
        code, events, _ = watch(reader, "--pr", "1", "--stack")
        self.assertEqual((code, events[-1]["pr"]["pr"]), (2, 3))

    def test_waiting_names_the_lowest_pending_pr(self):
        code, events, _ = watch(self.reader(checks={2: [[PENDING]], 3: [[PENDING]]}), "--pr", "1", "--stack",
                                "--timeout", "60")
        waiting = [e for e in events if e["kind"] == "WAITING"]
        self.assertEqual((code, waiting[0]["pr"]["pr"]), (5, 2))


class CliTest(unittest.TestCase):
    def test_usage_errors_exit_64(self):
        for argv in (["--interval", "0"], ["--timeout", "-1"], ["--pr", "x"], ["--bogus"]):
            with self.subTest(argv=argv), mock.patch("sys.stderr"):
                self.assertEqual(watch_pr.main(argv, reader=FakeReader({}), out=io.StringIO()), 64)

    def test_status_table_has_the_four_columns(self):
        out = io.StringIO()
        reader = FakeReader({7: facts(7, isDraft=True)}, checks={7: [FAILED, watch_pr.Check("Bugbot", "pending", "IN_PROGRESS")]},
                            threads={7: [THREAD]})
        watch_pr.main(["--pr", "7", "--status-only", "--pretty"], reader=reader, out=out)
        self.assertIn("| PR | CI | Review | Merge |", out.getvalue())
        self.assertIn("| [#7](https://github.com/acme/app/pull/7) | 1 failed, 1 pending | 1 open, review automation running"
                      " | draft |", out.getvalue())

    def test_pretty_output_is_readable(self):
        out = io.StringIO()
        watch_pr.main(["--pr", "7", "--pretty"], reader=FakeReader({7: facts(7)}, threads={7: [THREAD]}), out=out)
        self.assertIn("BLOCKER review-threads on #7 (exit 3)", out.getvalue())
        self.assertIn("thread T1 comment None app.py:3 by reviewer", out.getvalue())
        self.assertIn("| PR | CI | Review | Merge |", out.getvalue())


class ReadOnlyTest(unittest.TestCase):
    """Every command the real reader runs must be a read: no merge, edit, comment, rerun, or mutation."""

    ALLOWED = {("gh", "pr", "view"), ("gh", "pr", "list"), ("gh", "pr", "checks"), ("gh", "api", "graphql"),
               ("git", "remote", "get-url")}

    def test_reader_only_issues_read_commands(self):
        calls = []

        def fake_run(argv, **kwargs):
            calls.append(argv)
            if argv[:3] == ["gh", "pr", "checks"]:
                return subprocess.CompletedProcess(argv, 8, "[]", "")
            if argv[:3] == ["gh", "api", "graphql"]:
                data = {"data": {"repository": {"pullRequest": {
                    "commits": {"nodes": [{"commit": {"oid": "sha7", "statusCheckRollup": {"state": "SUCCESS",
                        "contexts": {"pageInfo": {"hasNextPage": False, "endCursor": None},
                                     "nodes": [{"__typename": "CheckRun", "name": "b", "status": "COMPLETED",
                                                "conclusion": "SUCCESS"}]}}}}]},
                    "reviewThreads": {"nodes": []}}}}}
                return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")
            if argv[:3] == ["gh", "pr", "list"]:
                return subprocess.CompletedProcess(argv, 0, "[]", "")
            if argv[:3] == ["git", "remote", "get-url"]:
                return subprocess.CompletedProcess(argv, 0, "git@github.com:acme/app.git\n", "")
            return subprocess.CompletedProcess(argv, 0, json.dumps(facts(7)), "")

        with mock.patch.object(watch_pr.subprocess, "run", side_effect=fake_run):
            code = watch_pr.main(["--pr", "7", "--stack"], out=io.StringIO())
        self.assertEqual(code, 0)
        self.assertTrue(calls)
        for argv in calls:
            self.assertIn(tuple(argv[:3]), self.ALLOWED, argv)
            self.assertNotIn("--method", argv)
            self.assertNotIn("-X", argv)
        for query in (watch_pr.REVIEW_THREADS_QUERY, watch_pr.COMMIT_ROLLUPS_QUERY, watch_pr.CHECK_ROLLUP_QUERY):
            self.assertTrue(query.lstrip().startswith("query"))
            self.assertNotIn("mutation", query)

    def test_review_threads_follow_every_page(self):
        def page(ids, resolved, next_cursor):
            return {"data": {"viewer": {"login": "me"}, "repository": {"pullRequest": {"reviewThreads": {
                "pageInfo": {"hasNextPage": bool(next_cursor), "endCursor": next_cursor},
                "nodes": [{"id": i, "isResolved": resolved, "comments": {"totalCount": 1, "nodes": [
                    {"databaseId": 1, "body": "fix this", "path": "a.py", "line": 1,
                     "author": {"login": "rev"}}]}} for i in ids]}}}}}
        pages = [page([str(n) for n in range(100)], True, "c1"), page(["late"], False, None)]
        calls = []

        def fake_run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, json.dumps(pages[len(calls) - 1]), "")

        with mock.patch.object(watch_pr.subprocess, "run", side_effect=fake_run):
            threads = watch_pr.GhReader().review_threads("acme", "app", 7)
        self.assertEqual([t.id for t in threads], ["late"])
        self.assertIn("after=c1", calls[1])


if __name__ == "__main__":
    unittest.main()
