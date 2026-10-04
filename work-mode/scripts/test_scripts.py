"""Behavior tests for the work-mode scripts. Run: python3 -m unittest discover -s <scripts dir>"""

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import check_handoff
import journal

DESTROY = """# Handoff: retire the old reports bucket

Class: destroy
Environment: production
Owner: platform on-call
Revision: r42

## Targets
Count: 2
- s3://reports-2019
- s3://reports-2020

## Inventory
Both buckets have zero reads in 90 days of access logs. No policy references them.

## Reversible first
Deny all access with a bucket policy, observe 7 days, then delete.

## Preconditions
Snapshot copy exists in the archive account.

## Commands
```sh
aws s3 rb s3://reports-2019 --force
aws s3 rb s3://reports-2020 --force
```

## Expected signal
Both bucket names are absent from the bucket list.

## Stop conditions
Any read error reported by a consumer during the deny window.

## Recovery
Restore from the archive copy. Object versions and ACLs are not restored.

## Verification
List buckets and confirm both names are absent.

## Must not change
The bucket count drops by exactly 2. reports-2021 still exists.
"""


def run(module, *argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(list(argv))
    return code, out.getvalue() + err.getvalue()


class HandoffTest(unittest.TestCase):
    def lint(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.md"
            path.write_text(text)
            return run(check_handoff, "check", str(path))

    def test_complete_destroy_handoff_passes(self):
        code, output = self.lint(DESTROY)
        self.assertEqual((code, output.splitlines()[0][:10]), (0, "0 problems"))

    def test_destroy_without_reversible_first_fails(self):
        text = DESTROY.replace("## Reversible first\n", "## Notes\n")
        code, output = self.lint(text)
        self.assertEqual(code, 1)
        self.assertIn("missing section ## Reversible first", output)

    def test_count_mismatch_fails(self):
        code, output = self.lint(DESTROY.replace("Count: 2", "Count: 3"))
        self.assertEqual(code, 1)
        self.assertIn("Count says 3, list has 2", output)

    def test_wildcard_target_fails(self):
        code, output = self.lint(DESTROY.replace("- s3://reports-2020", "- s3://reports-*"))
        self.assertEqual(code, 1)
        self.assertIn("target is a pattern, not an identifier: s3://reports-*", output)

    def test_unfilled_placeholder_in_command_fails(self):
        code, output = self.lint(DESTROY.replace("s3://reports-2019 --force", "<bucket name> --force"))
        self.assertEqual(code, 1)
        self.assertIn("unfilled placeholder", output)

    def test_heredoc_redirect_is_not_a_placeholder(self):
        text = DESTROY.replace("aws s3 rb s3://reports-2019 --force", "cat <<EOF >out.txt")
        code, _ = self.lint(text)
        self.assertEqual(code, 0)

    def test_modify_does_not_need_destroy_sections(self):
        text = DESTROY.replace("Class: destroy", "Class: modify").replace("## Inventory\n", "## Context\n")
        code, _ = self.lint(text.replace("## Reversible first\n", "## Notes\n"))
        self.assertEqual(code, 0)

    def test_unknown_class_fails(self):
        code, output = self.lint(DESTROY.replace("Class: destroy", "Class: cleanup"))
        self.assertEqual(code, 1)
        self.assertIn("Class must be one of", output)

    def test_missing_header_field_fails(self):
        code, output = self.lint(DESTROY.replace("Owner: platform on-call\n", ""))
        self.assertEqual(code, 1)
        self.assertIn("missing header field Owner:", output)

    def test_unknown_environment_fails(self):
        code, output = self.lint(DESTROY.replace("Environment: production", "Environment: prod-ish"))
        self.assertEqual(code, 1)
        self.assertIn("Environment must be one of", output)

    def test_commands_outside_a_fence_fail(self):
        code, output = self.lint(DESTROY.replace("```sh\n", "").replace("--force\n```\n", "--force\n"))
        self.assertEqual(code, 1)
        self.assertIn("Commands needs the exact commands in a non-empty fenced block", output)

    def test_empty_command_fence_fails(self):
        start = DESTROY.index("```sh\n") + len("```sh\n")
        end = DESTROY.index("```\n", start)
        code, output = self.lint(DESTROY[:start] + DESTROY[end:])
        self.assertEqual(code, 1)
        self.assertIn("non-empty fenced block", output)

    def test_empty_section_fails(self):
        text = DESTROY.replace("Both bucket names are absent from the bucket list.\n", "")
        code, output = self.lint(text)
        self.assertEqual(code, 1)
        self.assertIn("empty section ## Expected signal", output)

    def test_fingerprint_changes_when_a_command_changes(self):
        edited = DESTROY.replace("reports-2020 --force", "reports-2021 --force")
        self.assertNotEqual(check_handoff.fingerprint(DESTROY), check_handoff.fingerprint(edited))

    def test_fingerprint_ignores_trailing_whitespace_and_crlf(self):
        noisy = DESTROY.replace("\n", "  \r\n")
        self.assertEqual(check_handoff.fingerprint(DESTROY), check_handoff.fingerprint(noisy))


class JournalTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = str(self.root / ".work-mode" / "journal.jsonl")
        self.snapshot = self.root / "before.yaml"
        self.snapshot.write_text("replicas: 2\n")

    def tearDown(self):
        self.tmp.cleanup()

    def journal(self, *argv):
        return run(journal, "--journal", self.path, *argv)

    def entries(self):
        return [json.loads(line) for line in Path(self.path).read_text().splitlines()]

    def change(self, target="staging/api", env="staging", command="kubectl scale deploy/api --replicas=3",
               revert="kubectl scale deploy/api --replicas=2", *extra):
        return self.journal("record", "change", "--env", env, "--target", target, "--command", command,
                            "--snapshot", str(self.snapshot), "--revert", revert,
                            "--reversibility", "snapshot before.yaml; revert tested on dev; no data; rollout status",
                            "--verification", "kubectl rollout status deploy/api", *extra)

    def result(self, change_id, status, text="rollout status ok"):
        return self.journal("record", "change", "--id", change_id, "--status", status, "--result", text)


class JournalEvidenceTest(JournalTestCase):
    def record(self, revision, claim, status, by, target="prod/api"):
        code, output = self.journal("record", "evidence", "--target", target, "--revision", revision,
                                    "--claim", claim, "--status", status, "--by", by, "--evidence", "probe.txt")
        self.assertEqual(code, 0, output)

    def check(self, revision, claim, *extra, target="prod/api"):
        return self.journal("check", "--target", target, "--revision", revision, "--claim", claim, *extra)

    def test_missing_journal_is_not_verified(self):
        code, output = self.check("r1", "consumer-ok")
        self.assertEqual(code, 2)
        self.assertIn("NOT-VERIFIED", output)

    def test_established_row_for_exact_revision_passes(self):
        self.record("r1", "consumer-ok", "established", "verifier")
        self.assertEqual(self.check("r1", "consumer-ok")[0], 0)

    def test_new_revision_does_not_inherit_evidence(self):
        self.record("r1", "consumer-ok", "established", "verifier")
        self.assertEqual(self.check("r2", "consumer-ok")[0], 2)

    def test_other_target_does_not_inherit_evidence(self):
        self.record("r1", "consumer-ok", "established", "verifier", target="staging/api")
        self.assertEqual(self.check("r1", "consumer-ok")[0], 2)

    def test_agent_row_cannot_override_verifier_failure(self):
        self.record("r1", "consumer-ok", "failed", "verifier")
        self.record("r1", "consumer-ok", "established", "agent")
        code, output = self.check("r1", "consumer-ok")
        self.assertEqual(code, 3)
        self.assertIn("FAILED", output)

    def test_later_verifier_row_supersedes_earlier_verifier_row(self):
        self.record("r1", "consumer-ok", "failed", "verifier")
        self.record("r1", "consumer-ok", "established", "verifier")
        self.assertEqual(self.check("r1", "consumer-ok")[0], 0)

    def test_verifier_row_cannot_override_owner_failure(self):
        self.record("r1", "consumer-ok", "failed", "owner")
        self.record("r1", "consumer-ok", "established", "verifier")
        code, output = self.check("r1", "consumer-ok")
        self.assertEqual(code, 3)
        self.assertIn("by owner", output)

    def test_older_owner_success_does_not_let_agent_clear_verifier_failure(self):
        self.record("r1", "consumer-ok", "established", "owner")
        self.record("r1", "consumer-ok", "failed", "verifier")
        self.record("r1", "consumer-ok", "established", "agent")
        code, output = self.check("r1", "consumer-ok")
        self.assertEqual(code, 3)
        self.assertIn("by verifier", output)

    def test_owner_row_clears_own_earlier_failure(self):
        self.record("r1", "consumer-ok", "failed", "owner")
        self.record("r1", "consumer-ok", "established", "owner")
        self.assertEqual(self.check("r1", "consumer-ok")[0], 0)

    def test_later_agent_failure_overrides_earlier_verifier_success(self):
        self.record("r1", "consumer-ok", "established", "verifier")
        self.record("r1", "consumer-ok", "failed", "agent")
        code, output = self.check("r1", "consumer-ok")
        self.assertEqual(code, 3)
        self.assertIn("by agent", output)

    def test_later_agent_unverified_overrides_earlier_verifier_success(self):
        self.record("r1", "consumer-ok", "established", "verifier")
        self.record("r1", "consumer-ok", "unverified", "agent")
        self.assertEqual(self.check("r1", "consumer-ok")[0], 2)

    def test_max_age_applies_to_the_newest_success(self):
        Path(self.path).parent.mkdir(parents=True)
        old = {"kind": "evidence", "ts": "2000-01-01T00:00:00Z", "target": "prod/api", "revision": "r1",
               "claim": "consumer-ok", "status": "established", "by": "verifier", "evidence": "old.txt"}
        Path(self.path).write_text(json.dumps(old) + "\n")
        self.record("r1", "consumer-ok", "established", "agent")
        self.assertEqual(self.check("r1", "consumer-ok", "--max-age-hours", "1")[0], 0)

    def test_approval_counts_only_owner_entries(self):
        code, output = self.journal("record", "evidence", "--target", "prod/api", "--revision", "abc",
                                    "--claim", "owner-approved", "--status", "established", "--by", "agent",
                                    "--evidence", "chat")
        self.assertEqual(code, 1)
        self.assertIn("record approval", output)
        self.assertEqual(self.check("abc", "owner-approved")[0], 2)
        code, _ = self.journal("record", "approval", "--target", "prod/api", "--fingerprint", "abc",
                               "--by", "owner", "--evidence", "approved in terminal")
        self.assertEqual(code, 0)
        self.assertEqual(self.check("abc", "owner-approved")[0], 0)

    def test_approval_by_agent_is_rejected(self):
        code, output = self.journal("record", "approval", "--target", "prod/api", "--fingerprint", "abc",
                                    "--by", "agent", "--evidence", "user said ok in chat")
        self.assertEqual(code, 1)
        self.assertIn("--by owner", output)
        self.assertEqual(self.check("abc", "owner-approved")[0], 2)

    def test_approval_for_another_fingerprint_does_not_match(self):
        self.journal("record", "approval", "--target", "prod/api", "--fingerprint", "abc",
                     "--by", "owner", "--evidence", "approved")
        self.assertEqual(self.check("abd", "owner-approved")[0], 2)

    def test_unverified_row_is_not_a_pass(self):
        self.record("r1", "consumer-ok", "unverified", "agent")
        self.assertEqual(self.check("r1", "consumer-ok")[0], 2)

    def test_max_age_marks_old_evidence_stale(self):
        self.record("r1", "consumer-ok", "established", "verifier")
        self.assertEqual(self.check("r1", "consumer-ok", "--max-age-hours", "0")[0], 4)

    def test_formula_cells_are_neutralized(self):
        self.journal("record", "evidence", "--target", "=HYPERLINK(x)", "--revision", "r1",
                     "--claim", "c", "--status", "failed", "--by", "agent", "--evidence", "e")
        self.assertEqual(self.entries()[0]["target"], "'=HYPERLINK(x)")

    def test_malformed_journal_fails_loudly(self):
        Path(self.path).parent.mkdir(parents=True)
        Path(self.path).write_text('{"kind": "evidence"\n')
        code, output = self.check("r1", "consumer-ok")
        self.assertEqual(code, 1)
        self.assertIn("not valid JSON", output)

    def test_unknown_kind_in_journal_fails_loudly(self):
        Path(self.path).parent.mkdir(parents=True)
        Path(self.path).write_text('{"kind": "note", "ts": "2026-10-03T00:00:00Z"}\n')
        code, output = self.check("r1", "consumer-ok")
        self.assertEqual(code, 1)
        self.assertIn("unknown kind", output)

    def test_unknown_field_in_journal_fails_loudly(self):
        Path(self.path).parent.mkdir(parents=True)
        Path(self.path).write_text('{"kind": "grant", "colour": "red"}\n')
        code, output = self.check("r1", "consumer-ok")
        self.assertEqual(code, 1)
        self.assertIn("unknown fields", output)

    def test_bad_status_is_a_usage_error(self):
        code, _ = self.journal("record", "evidence", "--target", "t", "--revision", "r", "--claim", "c",
                               "--status", "looks-good", "--by", "agent", "--evidence", "e")
        self.assertEqual(code, 64)

    def test_unknown_record_kind_is_a_usage_error(self):
        code, _ = self.journal("record", "note", "--target", "t")
        self.assertEqual(code, 64)


class JournalChangeTest(JournalTestCase):
    def test_change_is_recorded_pending_then_done(self):
        code, output = self.change()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.result("c1", "done")[0], 0)
        statuses = [(e["id"], e["status"]) for e in self.entries()]
        self.assertEqual(statuses, [("c1", "pending"), ("c1", "done")])
        self.assertEqual(self.entries()[1]["revert"], "kubectl scale deploy/api --replicas=2")

    def test_change_without_revert_is_rejected(self):
        code, output = self.journal("record", "change", "--env", "staging", "--target", "staging/api",
                                    "--command", "kubectl scale deploy/api --replicas=3",
                                    "--snapshot", str(self.snapshot), "--reversibility", "r", "--verification", "v")
        self.assertEqual(code, 1)
        self.assertIn("--revert", output)
        self.assertFalse(Path(self.path).exists())

    def test_change_with_missing_snapshot_is_rejected(self):
        self.snapshot.unlink()
        code, output = self.change()
        self.assertEqual(code, 1)
        self.assertIn("capture the prior state first", output)

    def test_change_with_empty_snapshot_is_rejected(self):
        self.snapshot.write_text("")
        self.assertEqual(self.change()[0], 1)

    def test_result_for_unknown_change_is_rejected(self):
        code, output = self.result("c9", "done")
        self.assertEqual(code, 1)
        self.assertIn("no change c9", output)

    def test_production_change_needs_a_recorded_grant(self):
        code, output = self.change("prod/api", "production")
        self.assertEqual(code, 1)
        self.assertIn("--grant", output)
        self.assertEqual(self.change("prod/api", "production", "kubectl scale deploy/api --replicas=3",
                                     "kubectl scale deploy/api --replicas=2", "--grant", "g1")[0], 1)
        self.journal("record", "grant", "--env", "prod-eu", "--scope", "namespace payments",
                     "--changes", "scale, config values; no deletes",
                     "--words", "prod-eu, namespace payments, scale and config values, no deletes")
        code, output = self.change("prod/api", "production", "kubectl scale deploy/api --replicas=3",
                                   "kubectl scale deploy/api --replicas=2", "--grant", "g1")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.entries()[-1]["grant"], "g1")

    def test_unknown_environment_is_rejected(self):
        self.assertEqual(self.change("x/api", "unknown")[0], 64)

    def test_secret_in_command_is_rejected(self):
        code, output = self.change(command="mysql -u root --password=hunter2secret -e 'select 1'")
        self.assertEqual(code, 1)
        self.assertIn("looks like it contains a secret", output)
        self.assertFalse(Path(self.path).exists())

    def test_secret_in_revert_is_rejected(self):
        code, _ = self.change(revert="curl -H 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz012345' x")
        self.assertEqual(code, 1)

    def test_secret_in_snapshot_is_rejected(self):
        self.snapshot.write_text("aws_access_key_id: AKIAABCDEFGHIJKLMNOP\n")
        code, output = self.change()
        self.assertEqual(code, 1)
        self.assertIn("redact it first", output)

    def test_common_secret_shapes_are_rejected(self):
        for text in ("DB_PASSWORD=hunter2 psql", "export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMIK7MDENG",
                     "PGPASSWORD=hunter2 psql -h db", "GITHUB_TOKEN=abc123 gh api", "client_secret: abcdef123",
                     "api_token: abc123", 'DB_PASSWORD: "hunter2"', '{"password":"hunter2"}',
                     "psql postgres://app:hunter2@db/x", "curl -H 'Authorization: Basic dXNlcjpwYXNz' x",
                     "mysql --db-password hunter2", "MYSQL_PWD=hunter2 mysql",
                     "DB_PASSWORD=12345678", "api_key: 9876543210123"):
            with self.subTest(text=text):
                self.assertTrue(journal.looks_secret(text))

    def test_references_and_placeholders_are_not_secrets(self):
        for text in ("secretName: api-credentials", "password: <redacted>", 'password: "<redacted>"',
                     "max_tokens: 100", "psql --password=$DB_PASSWORD", "psql postgres://app:$PGPASS@db/x",
                     "kubectl get secret api-credentials -n payments", "tokenRef: vault/app", "password_file=/run/pw",
                     "kubectl -n payments patch configmap api-config -p '{\"data\":{\"LOG_LEVEL\":\"debug\"}}'",
                     "automountServiceAccountToken: false", "imagePullSecrets: [{name: regcred}]",
                     "token_bucket_size: 500", "cd /srv && PWD=/srv make"):
            with self.subTest(text=text):
                self.assertFalse(journal.looks_secret(text))

    def test_long_values_scan_quickly(self):
        import time
        started = time.monotonic()
        for blob in ("a" * 200_000, "0123456789abcdef" * 12_500, "QUJD-_xy" * 25_000):
            self.assertFalse(journal.looks_secret("data: " + blob))
        self.assertLess(time.monotonic() - started, 5)

    def test_prefixed_secret_in_snapshot_is_rejected(self):
        self.snapshot.write_text("env:\n  AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMIK7MDENG\n")
        code, output = self.change()
        self.assertEqual(code, 1)
        self.assertIn("redact it first", output)

    def test_redacted_and_variable_values_are_accepted(self):
        self.snapshot.write_text("password: <redacted>\nsecretName: api-credentials\n")
        code, output = self.change(command="psql --password=$DB_PASSWORD -c 'select 1'")
        self.assertEqual(code, 0, output)

    def test_revert_plan_last_returns_newest_open_change(self):
        self.change(target="staging/a")
        self.change(target="staging/b")
        self.result("c2", "reverted", "reverted by hand")
        code, output = self.journal("revert-plan", "last")
        self.assertEqual(code, 0)
        self.assertIn("c1\t", output)
        self.assertNotIn("c2\t", output)

    def test_revert_plan_all_since_is_newest_first_and_skips_reverts(self):
        self.change(target="staging/a")
        self.change(target="staging/b")
        self.change("staging/b", "staging", "kubectl scale deploy/api --replicas=2",
                    "kubectl scale deploy/api --replicas=3", "--reverts", "c2")
        code, output = self.journal("revert-plan", "all-since", "2000-01-01T00:00:00Z")
        self.assertEqual(code, 0)
        ids = [line.split("\t")[0] for line in output.splitlines() if not line.startswith(" ")]
        self.assertEqual(ids, ["c2", "c1"])

    def test_all_since_uses_creation_time_not_result_time(self):
        self.change()
        lines = Path(self.path).read_text().splitlines()
        early = json.loads(lines[0])
        early.update(ts="2026-10-03T08:55:00Z", created="2026-10-03T08:55:00Z")
        done = dict(early, ts="2026-10-03T09:01:00Z", status="done", result="ok")
        Path(self.path).write_text(json.dumps(early) + "\n" + json.dumps(done) + "\n")
        code, output = self.journal("revert-plan", "all-since", "2026-10-03T09:00:00Z")
        self.assertEqual(code, 0)
        self.assertIn("nothing to revert", output)
        self.assertEqual(self.journal("list", "--since", "2026-10-03T09:00:00Z")[1], "")
        self.assertIn("c1\t2026-10-03T08:55:00Z\tdone", self.journal("list")[1])

    def test_revert_plan_for_reverted_change_says_so(self):
        self.change()
        self.result("c1", "reverted", "reverted")
        code, output = self.journal("revert-plan", "c1")
        self.assertEqual(code, 0)
        self.assertIn("already reverted", output)

    def test_reverts_must_name_an_existing_change(self):
        code, output = self.change("staging/api", "staging", "a", "b", "--reverts", "c7")
        self.assertEqual(code, 1)
        self.assertIn("--reverts names no change", output)

    def test_list_shows_latest_status(self):
        self.change()
        self.result("c1", "failed", "pods crashlooping")
        code, output = self.journal("list")
        self.assertEqual(code, 0)
        self.assertIn("c1\t", output)
        self.assertIn("\tfailed\t", output)


class JournalLocationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.cwd = os.getcwd()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def grant(self):
        return run(journal, "record", "grant", "--env", "dev", "--scope", "all", "--changes", "c", "--words", "w")

    def test_default_journal_lives_in_current_directory(self):
        self.assertEqual(self.grant()[0], 0)
        self.assertTrue((self.root / ".work-mode" / "journal.jsonl").exists())

    def test_first_write_excludes_journal_from_git_locally(self):
        subprocess.run(["git", "init", "-q"], check=True)
        self.grant()
        self.grant()
        exclude = (self.root / ".git" / "info" / "exclude").read_text().splitlines()
        self.assertEqual(exclude.count("/.work-mode/"), 1)
        self.assertFalse((self.root / ".gitignore").exists())

    def test_init_excludes_work_dir_before_any_entry(self):
        subprocess.run(["git", "init", "-q"], check=True)
        self.assertEqual(run(journal, "init")[0], 0)
        self.assertTrue((self.root / ".work-mode").is_dir())
        self.assertFalse((self.root / ".work-mode" / "journal.jsonl").exists())
        self.assertIn("/.work-mode/", (self.root / ".git" / "info" / "exclude").read_text().splitlines())

    def test_home_directory_is_refused(self):
        with mock.patch.object(Path, "home", return_value=self.root):
            code, output = self.grant()
        self.assertEqual(code, 1)
        self.assertIn("is not a project directory", output)
        self.assertFalse((self.root / ".work-mode").exists())


if __name__ == "__main__":
    unittest.main()
