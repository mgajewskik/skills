#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Tests for log.py. Run: uv run --script test_log.py"""

import contextlib
import datetime
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import log  # noqa: E402
import yaml  # noqa: E402

TODAY = datetime.date.today().isoformat()


class LogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "project"
        (self.project / "sub").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        subprocess.run(["git", "-C", str(self.project), "config", "core.excludesFile", "/dev/null"], check=True)
        self.old_cwd = os.getcwd()
        os.chdir(self.project)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.tmp.cleanup()

    def run_log(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = log.main(list(argv))
        return code, out.getvalue().strip()

    def ok(self, *argv):
        code, out = self.run_log(*argv)
        self.assertEqual(code, 0, f"{argv} -> {out}")
        return out

    def new(self, slug="fix-api"):
        return self.ok("new", slug, "--task", "api returns 502", "--playbook", "debug")

    def doc(self, log_id):
        return yaml.safe_load(log.locate(log_id).read_text())

    def file(self, name):
        return Path(self.tmp.name) / name

    def test_new_creates_a_log_directory_and_excludes_it_from_git(self):
        log_id = self.new()
        self.assertEqual(log_id, f"{TODAY}-fix-api")
        self.assertEqual(list((self.project / ".work").iterdir()), [self.project / ".work" / log_id])
        self.assertEqual(list((self.project / ".work" / log_id).iterdir()),
                         [self.project / ".work" / log_id / "log.yml"])
        self.assertEqual(self.new(), f"{TODAY}-fix-api-2")
        exclude = (self.project / ".git" / "info" / "exclude").read_text().splitlines()
        self.assertEqual(exclude.count("/.work/"), 1)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        self.assertEqual(status, "")
        self.assertEqual(self.run_log("new", "Bad_Slug", "--task", "x", "--playbook", "debug")[0], 2)

    def test_new_with_parent_nests_the_log_inside_the_parent_log_directory(self):
        parent = self.ok("new", "ship-api", "--task", "ship the api", "--playbook", "auto")
        child = self.ok("new", "fix-api", "--task", "fix the 502", "--playbook", "fix", "--parent", parent)
        self.assertEqual(child, f"{TODAY}-ship-api/{TODAY}-fix-api")
        self.assertEqual(list((self.project / ".work").iterdir()), [self.project / ".work" / f"{TODAY}-ship-api"])
        self.assertTrue((self.project / ".work" / f"{TODAY}-ship-api" / f"{TODAY}-fix-api" / "log.yml").is_file())
        self.assertEqual(self.doc(child)["parent"], f"{TODAY}-ship-api")
        self.assertEqual(self.ok("new", "fix-api", "--task", "fix it again", "--playbook", "fix", "--parent", parent),
                         f"{TODAY}-ship-api/{TODAY}-fix-api-2")
        self.assertEqual(self.ok("add", child, "note", "--text", "child entry"), "1")
        self.assertEqual(self.doc(parent)["timeline"], [])
        self.assertNotIn("parent", self.doc(parent))
        self.assertEqual(self.run_log("new", "fix-api", "--task", "x", "--playbook", "fix", "--parent", "no-such-log")[0], 2)

    def test_run_entries_resolve_project_from_subdirectory(self):
        log_id = self.new()
        os.chdir(self.project / "sub")
        self.assertEqual(self.ok("add", log_id, "run", "--class", "read-only", "--command", "kubectl get pods",
                                 "--target", "ctx=prod ns=api", "--identity", "viewer"), "1")
        self.assertEqual(self.run_log("add", log_id, "run", "--class", "reversible", "--command", "scale 5")[0], 2)
        self.assertEqual(self.run_log("add", log_id, "plan", "--by", "user", "--command", "delete pod")[0], 2)
        delete = ("add", log_id, "plan", "--by", "user", "--class", "irreversible", "--command",
                  "kubectl delete pod api-old")
        self.assertEqual(self.run_log(*delete)[0], 2)
        self.assertEqual(self.ok(*delete, "--no-revert", "the pod's local state is gone"), "2")
        entries = self.doc(log_id)["timeline"]
        self.assertEqual([(e["n"], e["kind"]) for e in entries], [(1, "run"), (2, "plan")])
        self.assertEqual(entries[0]["identity"], "viewer")

    def test_check_gates_on_latest_evidence_per_claim(self):
        log_id = self.new()
        self.assertEqual(self.run_log("check", log_id)[0], 1)
        self.assertEqual(self.run_log("add", log_id, "evidence", "--claim", "200", "--status", "established")[0], 2)
        evidence = ("add", log_id, "evidence", "--claim", "api serves 200", "--command", "curl /health")
        self.ok(*evidence, "--status", "established")
        self.assertEqual(self.run_log("check", log_id)[0], 0)
        self.ok(*evidence, "--status", "failed")
        self.assertEqual(self.run_log("check", log_id)[0], 1)
        self.ok(*evidence, "--status", "established")
        self.assertEqual(self.run_log("check", log_id)[0], 0)
        self.assertEqual(self.run_log("check", log_id, "--max-age-hours", "0")[0], 1)
        self.ok("add", log_id, "evidence", "--claim", "old unit", "--command", "x", "--status", "unverified")
        self.assertEqual(self.run_log("check", log_id)[0], 1)
        self.ok("add", log_id, "evidence", "--claim", "unit 2 healthy", "--command", "x", "--status", "established")
        self.assertEqual(self.run_log("check", log_id, "--since", "4")[0], 0)
        self.assertEqual(self.run_log("check", log_id, "--since", "5")[0], 1)

    def test_secrets_are_refused_and_the_log_is_unchanged(self):
        log_id = self.new()
        path = log.locate(log_id)
        before = path.read_bytes()
        for value in ("token: ghp_abcdefghijklmnopqrstuvwxyz0123456789",
                      "curl -H 'Authorization: Bearer abcdefgh12345678' x",
                      "--password hunter2hunter2"):
            self.assertEqual(self.run_log("add", log_id, "note", "--text", value)[0], 2, value)
        leak = self.file("leak.env")
        leak.write_text("DB_PASSWORD=hunter2hunter2\n")
        self.assertEqual(self.run_log("add", log_id, "note", "--text", "env", "--artifact", str(leak))[0], 2)
        latin1 = self.file("errors.log")
        latin1.write_bytes(b"caf\xe9\nDB_PASSWORD=hunter2hunter2\n")
        self.assertEqual(self.run_log("add", log_id, "note", "--text", "log", "--artifact", str(latin1))[0], 2)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(path.parent.iterdir()), [path], "a refused artifact must not be saved")
        self.ok("add", log_id, "note", "--text", "timeout_seconds=30 and token_ttl: 3600 and DB_PASSWORD=$DB_PASSWORD")

    def test_artifacts_are_named_after_their_entry(self):
        log_id = self.new()
        self.ok("add", log_id, "note", "--text", "no artifact")
        pods = self.file("pods.csv")
        pods.write_text("name,status\napi-1,Running\n")
        self.ok("add", log_id, "evidence", "--claim", "pods up", "--status", "established",
                "--command", "kubectl get pods", "--artifact", str(pods))
        folder = self.project / ".work" / log_id
        self.assertEqual((folder / "002-pods.csv").read_text(), "name,status\napi-1,Running\n")
        self.ok("add", log_id, "note", "--text", "again", "--artifact", str(pods))
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ["002-pods.csv", "003-pods.csv", "log.yml"])
        doc = self.doc(log_id)
        self.assertEqual(doc["artifacts"], ["002-pods.csv", "003-pods.csv"])
        self.assertEqual([e.get("artifact") for e in doc["timeline"]], [None, "002-pods.csv", "003-pods.csv"])

    def test_phases_decisions_and_corrections(self):
        log_id = self.new()
        self.ok("add", log_id, "note", "--text", "before any phase")
        self.assertEqual(self.ok("phase", log_id, "4. Loop one probe at a time"), "2")
        self.ok("add", log_id, "evidence", "--claim", "upstream times out", "--status", "established",
                "--command", "curl -m 5 upstream", "--why", "separates timeout from refusal")
        self.ok("phase", log_id, "6. Conclude")
        self.assertEqual(self.run_log("add", log_id, "decision", "--text", "raise timeout")[0], 2)
        self.assertEqual(self.run_log("add", log_id, "decision", "--text", "raise timeout", "--why", "slow",
                                      "--evidence", "3,9")[0], 2)
        self.ok("add", log_id, "decision", "--text", "raise the upstream timeout to 30s", "--why",
                "p99 upstream latency is 12s", "--evidence", "3", "--rejected", "add retries: doubles load")
        self.assertEqual(self.run_log("add", log_id, "note", "--text", "x", "--supersedes", "9")[0], 2)
        self.ok("add", log_id, "note", "--text", "p99 was 14s, not 12s", "--supersedes", "5")
        timeline = self.doc(log_id)["timeline"]
        self.assertNotIn("phase", timeline[0])
        self.assertEqual(timeline[1], {"n": 2, "at": timeline[1]["at"], "kind": "phase",
                                       "name": "4. Loop one probe at a time"})
        self.assertEqual((timeline[2]["phase"], timeline[2]["why"]),
                         ("4. Loop one probe at a time", "separates timeout from refusal"))
        self.assertEqual({k: v for k, v in timeline[4].items() if k != "at"}, {
            "n": 5, "kind": "decision", "phase": "6. Conclude", "why": "p99 upstream latency is 12s",
            "text": "raise the upstream timeout to 30s", "rejected": "add retries: doubles load", "evidence": [3]})
        self.assertEqual((timeline[5]["supersedes"], timeline[5]["phase"]), (5, "6. Conclude"))

    def test_revert_plan_lists_unreverted_changes_newest_first(self):
        log_id = self.new()
        reversible = ("add", log_id, "run", "--class", "reversible")
        self.ok(*reversible, "--why", "scale up", "--command", "scale 5", "--revert", "scale 3")
        self.ok(*reversible, "--why", "conns", "--command", "patch 4096", "--revert", "patch\n  1024")
        self.ok("add", log_id, "run", "--class", "read-only", "--command", "get cm")
        header = f"# run from {log.project_root()}\n\n"
        scale = "# #1 executed, reversible: scale up\nscale 3"
        self.assertEqual(self.ok("revert-plan", log_id),
                         header + "# #2 executed, reversible: conns\npatch\n  1024\n\n" + scale)
        self.assertEqual(self.run_log(*reversible, "--reverts", "3", "--command", "x", "--revert", "y")[0], 2)
        self.ok(*reversible, "--reverts", "2", "--command", "patch 1024")
        self.assertEqual(self.ok("revert-plan", log_id), header + scale)
        self.assertEqual([r["of"] for r in self.doc(log_id)["revert"]], [1])
        for refused in (("plan", "--by", "user", "--class", "read-only", "--command", "scale 3", "--reverts", "1"),
                        ("note", "--text", "reverted", "--reverts", "1"),
                        ("run", "--class", "read-only", "--command", "patch 4096", "--reverts", "4"),
                        ("run", "--class", "read-only", "--command", "patch 1024", "--reverts", "2")):
            self.assertEqual(self.run_log("add", log_id, *refused)[0], 2, refused)
        self.assertEqual(self.ok("revert-plan", log_id), header + scale)

    def test_handed_over_and_irreversible_changes_carry_their_revert(self):
        log_id = self.new()
        manifest = self.file("cm-nginx-before.yaml")
        manifest.write_text("kind: ConfigMap\ndata:\n  worker_connections: '1024'\n")
        plan = ("add", log_id, "plan", "--by", "user", "--class", "reversible", "--why", "raise conns",
                "--command", "kubectl apply -f cm-new.yaml")
        self.assertEqual(self.run_log(*plan)[0], 2)
        self.assertEqual(self.run_log(*plan, "--revert", "kubectl apply -f {artifact}")[0], 2)
        self.ok(*plan, "--revert", "kubectl apply -f {artifact}", "--artifact", str(manifest))
        self.ok("add", log_id, "run", "--class", "irreversible", "--why", "drop cache", "--command",
                "redis-cli FLUSHDB", "--no-revert", "cache contents are not backed up")
        self.ok("add", log_id, "run", "--class", "irreversible", "--why", "delete pvc", "--command",
                "kubectl delete pvc data", "--revert", "velero restore create --from-backup nightly")
        saved = f".work/{log_id}/001-cm-nginx-before.yaml"
        self.assertEqual((self.project / saved).read_text(), manifest.read_text())
        self.assertEqual(self.doc(log_id)["revert"], [
            {"of": 3, "state": "executed", "class": "irreversible", "why": "delete pvc",
             "command": "velero restore create --from-backup nightly"},
            {"of": 2, "state": "executed", "class": "irreversible", "why": "drop cache",
             "no_revert": "cache contents are not backed up"},
            {"of": 1, "state": "planned for user", "class": "reversible", "why": "raise conns",
             "command": f"kubectl apply -f {saved}"}])
        self.assertEqual(self.ok("revert-plan", log_id), (
            f"# run from {log.project_root()}\n\n"
            "# #3 executed, irreversible: delete pvc\nvelero restore create --from-backup nightly\n\n"
            "# #2 executed, irreversible: drop cache\n# cannot be reverted: cache contents are not backed up\n\n"
            "# --- planned, not known to have run: uncomment only for a change you ran ---\n\n"
            f"# #1 planned for user, reversible: raise conns\n# kubectl apply -f {saved}"))
        self.assertEqual(self.run_log("add", log_id, "run", "--class", "read-only", "--command", "x",
                                      "--reverts", "2")[0], 2)
        self.assertEqual(self.run_log("add", log_id, "note", "--text", "ran", "--from-plan", "1")[0], 2)
        self.assertEqual(self.run_log("add", log_id, "run", "--by", "user", "--from-plan", "2")[0], 2)
        self.assertEqual(self.ok("add", log_id, "run", "--by", "user", "--from-plan", "1"), "4")
        self.assertEqual(self.doc(log_id)["revert"][0], {
            "of": 4, "state": "executed", "class": "reversible", "why": "raise conns",
            "command": f"kubectl apply -f {saved}"})
        self.assertEqual(self.run_log("add", log_id, "run", "--by", "user", "--from-plan", "1")[0], 2)
        self.ok("add", log_id, "run", "--by", "user", "--class", "reversible", "--command",
                f"kubectl apply -f {saved}", "--reverts", "4")
        self.assertEqual([r["of"] for r in self.doc(log_id)["revert"]], [3, 2])

    def test_a_user_run_closes_a_read_only_plan(self):
        log_id = self.new()
        self.ok("add", log_id, "plan", "--by", "user", "--class", "read-only", "--why", "pod state",
                "--command", "kubectl -n api get pods")
        output = self.file("pods.txt")
        output.write_text("api-1   0/1   CrashLoopBackOff\n")
        self.assertEqual(self.ok("add", log_id, "run", "--by", "user", "--from-plan", "1",
                                 "--result", "api-1 CrashLoopBackOff", "--artifact", str(output)), "2")
        run = self.doc(log_id)["timeline"][1]
        self.assertEqual({k: run[k] for k in ("kind", "by", "from_plan", "class", "command", "artifact")},
                         {"kind": "run", "by": "user", "from_plan": 1, "class": "read-only",
                          "command": "kubectl -n api get pods", "artifact": "002-pods.txt"})
        self.assertEqual(self.run_log("add", log_id, "run", "--by", "user", "--from-plan", "1")[0], 2)
        self.assertEqual(self.doc(log_id)["revert"], [])

    def test_home_is_not_a_project(self):
        home = Path(self.tmp.name) / "home"
        home.mkdir()
        old_home = os.environ["HOME"]
        os.environ["HOME"] = str(home)
        try:
            os.chdir(home)
            self.assertEqual(self.run_log("new", "x", "--task", "t", "--playbook", "debug")[0], 2)
            self.assertEqual(list(home.iterdir()), [])
        finally:
            os.environ["HOME"] = old_home

    def test_root_cause_close_and_readable_yaml(self):
        log_id = self.new()
        self.ok("add", log_id, "evidence", "--claim", "conns exhausted", "--status", "established",
                "--command", "nginx -T |\n  grep worker_connections")
        self.assertEqual(self.run_log("root-cause", log_id, "--summary", "x", "--confidence", "established",
                                      "--evidence", "9")[0], 2)
        self.ok("root-cause", log_id, "--summary", "worker_connections too low", "--confidence",
                "leading-hypothesis", "--evidence", "1")
        self.ok("add", log_id, "note", "--text", "pasted output:\n\n- n: 9\n  kind: run")
        self.ok("close", log_id, "--status", "done", "--summary", "raised the limit")
        text = log.locate(log_id).read_text()
        self.assertIn("  command: |-\n    nginx -T |\n      grep worker_connections\n", text)
        self.assertIn("\nsummary: raised the limit\n\nroot_cause:\n", text)
        self.assertIn("\n  - 1\n\nrevert: []\n\ntimeline:\n- n: 1\n", text)
        self.assertIn("      grep worker_connections\n\n- n: 2\n", text)
        doc = yaml.safe_load(text)
        self.assertEqual(list(doc), ["id", "task", "playbook", "status", "created", "updated", "summary",
                                     "root_cause", "revert", "timeline"])
        self.assertEqual(doc["root_cause"], {"summary": "worker_connections too low",
                                             "confidence": "leading-hypothesis", "evidence": [1]})
        self.assertEqual((doc["status"], doc["summary"]), ("done", "raised the limit"))
        self.assertEqual([e["n"] for e in doc["timeline"]], [1, 2])
        self.assertEqual(doc["timeline"][1]["text"], "pasted output:\n\n- n: 9\n  kind: run")

    def test_check_enforces_required_claims_revision_and_supersedes(self):
        log_id = self.new()
        self.ok("add", log_id, "evidence", "--claim", "health 200", "--status", "established",
                "--command", "curl /health", "--revision", "v1")
        self.assertEqual(self.run_log("check", log_id, "--require", "health 200", "--require", "neg space")[0], 1)
        self.assertEqual(self.run_log("check", log_id, "--revision", "v2")[0], 1)
        self.ok("add", log_id, "evidence", "--claim", "health 200", "--status", "established",
                "--command", "curl /health", "--revision", "v2")
        self.ok("add", log_id, "evidence", "--claim", "typo claim", "--status", "failed",
                "--command", "check neg", "--revision", "v2")
        self.assertEqual(self.run_log("check", log_id, "--since", "1", "--revision", "v2",
                                      "--require", "health 200")[0], 1)
        self.ok("add", log_id, "evidence", "--claim", "neg space", "--status", "established",
                "--command", "check neg", "--revision", "v2", "--supersedes", "3")
        self.assertEqual(self.run_log("check", log_id, "--since", "1", "--revision", "v2",
                                      "--require", "health 200", "--require", "neg space")[0], 0)

    def test_failed_and_unknown_reverts_keep_original_recovery_active(self):
        log_id = self.new()
        self.ok("add", log_id, "run", "--class", "reversible", "--why", "scale up",
                "--command", "scale 5", "--revert", "scale 3")
        self.ok("add", log_id, "run", "--class", "reversible", "--reverts", "1",
                "--command", "scale 3", "--outcome", "failed", "--result", "exit 1")
        self.assertEqual([r["of"] for r in self.doc(log_id)["revert"]], [1])
        self.assertIn("scale 3", self.ok("revert-plan", log_id))
        self.ok("add", log_id, "run", "--class", "reversible", "--reverts", "1",
                "--command", "scale 3", "--outcome", "unknown", "--result", "timed out")
        self.assertEqual([r["of"] for r in self.doc(log_id)["revert"]], [1])
        self.ok("add", log_id, "run", "--class", "reversible", "--reverts", "1",
                "--command", "scale 3", "--outcome", "ok", "--result", "replicas=3")
        self.assertEqual(self.doc(log_id)["revert"], [])
        self.assertEqual(self.ok("revert-plan", log_id), "nothing to revert")

    def test_unknown_and_failed_change_outcomes_are_commented_in_revert_plan(self):
        log_id = self.new()
        self.ok("add", log_id, "run", "--class", "reversible", "--why", "timed out patch",
                "--command", "apply x", "--revert", "undo x", "--outcome", "unknown")
        self.ok("add", log_id, "run", "--class", "reversible", "--why", "failed patch",
                "--command", "apply y", "--revert", "undo y", "--outcome", "failed")
        plan_text = self.ok("revert-plan", log_id)
        self.assertIn("# undo x", plan_text)
        self.assertIn("# undo y", plan_text)
        self.assertNotIn("\nundo x\n", plan_text)
        self.assertNotIn("\nundo y\n", plan_text)

    def test_from_plan_rejects_conflicting_fields_and_preserves_recovery(self):
        log_id = self.new()
        self.ok("add", log_id, "plan", "--by", "user", "--class", "reversible", "--why", "scale up",
                "--target", "ctx=prod", "--identity", "ops", "--command", "scale 5", "--revert", "scale 3")
        before = log.locate(log_id).read_bytes()
        for bad in (("--class", "read-only"),
                    ("--command", "scale 6"),
                    ("--target", "ctx=staging"),
                    ("--identity", "admin"),
                    ("--by", "agent"),
                    ("--revert", "scale 1")):
            self.assertEqual(self.run_log("add", log_id, "run", "--from-plan", "1", *bad)[0], 2, bad)
        self.assertEqual(log.locate(log_id).read_bytes(), before)
        self.ok("add", log_id, "run", "--from-plan", "1", "--outcome", "ok", "--result", "scaled")
        self.assertEqual(self.doc(log_id)["timeline"][-1]["by"], "user")
        self.assertEqual(self.doc(log_id)["revert"][0]["command"], "scale 3")

    def test_log_id_path_traversal_and_symlink_escape_are_rejected(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        outside_log = outside / "log.yml"
        outside_log.write_text("id: x\ntimeline: []\n")
        before = outside_log.read_text()
        for bad_id in ("../../outside", "/tmp/outside", "../outside", "a/../../outside", f"{TODAY}-fix-api\n"):
            self.assertEqual(self.run_log("close", bad_id, "--status", "done", "--summary", "pwn")[0], 2, bad_id)
        self.assertEqual(self.run_log("new", "fix-api\n", "--task", "t", "--playbook", "debug")[0], 2)
        (self.project / ".work").mkdir(exist_ok=True)
        (self.project / ".work" / f"{TODAY}-escape").symlink_to(outside)
        self.assertEqual(self.run_log("close", f"{TODAY}-escape", "--status", "done", "--summary", "pwn")[0], 2)
        self.assertEqual(outside_log.read_text(), before)

        (self.project / ".work" / f"{TODAY}-escape").unlink()
        (self.project / ".work").rmdir()
        (self.project / ".work").symlink_to(outside)
        (outside / f"{TODAY}-linked").mkdir()
        (outside / f"{TODAY}-linked" / "log.yml").write_text("id: x\ntimeline: []\n")
        self.assertEqual(self.run_log("close", f"{TODAY}-linked", "--status", "done", "--summary", "pwn")[0], 2)
        self.assertEqual(self.run_log("new", "linked-new", "--task", "t", "--playbook", "debug")[0], 2)
        self.assertEqual((outside / f"{TODAY}-linked" / "log.yml").read_text(), "id: x\ntimeline: []\n")

    def test_artifact_paths_with_spaces_are_shell_quoted_and_executable(self):
        log_id = self.new()
        snap = self.file("before snapshot.txt")
        snap.write_text("saved-state-42\n")
        self.ok("add", log_id, "run", "--class", "reversible", "--why", "update",
                "--command", "write new", "--revert", "cat {artifact}", "--artifact", str(snap))
        plan_lines = [line for line in self.ok("revert-plan", log_id).splitlines()
                      if line and not line.startswith("#")]
        self.assertEqual(len(plan_lines), 1)
        out = subprocess.run(["sh", "-c", plan_lines[0]], cwd=self.project, capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout, "saved-state-42\n")

    def test_exclude_from_git_respects_existing_ignore_and_fails_cleanly_when_unwritable(self):
        (self.project / ".gitignore").write_text("/.work/\n")
        exclude = self.project / ".git" / "info" / "exclude"
        exclude.chmod(0o444)
        try:
            log_id = self.new("ignored-ok")
            self.assertTrue((self.project / ".work" / log_id / "log.yml").is_file())
        finally:
            exclude.chmod(0o644)

        (self.project / ".gitignore").unlink()
        info_dir = self.project / ".git" / "info"
        exclude.chmod(0o444)
        info_dir.chmod(0o555)
        try:
            code, _ = self.run_log("new", "unwritable", "--task", "t", "--playbook", "debug")
            self.assertEqual(code, 2)
            self.assertFalse((self.project / ".work" / f"{TODAY}-unwritable").exists())
        finally:
            info_dir.chmod(0o755)
            exclude.chmod(0o644)

    def test_superseded_plan_and_nested_delegate_reverts(self):
        parent = self.ok("new", "ship-api", "--task", "ship", "--playbook", "auto")
        child = self.ok("new", "patch-cfg", "--task", "patch", "--playbook", "live-modify", "--parent", parent)
        self.ok("add", child, "plan", "--by", "agent", "--class", "reversible", "--why", "typo",
                "--command", "set wrong", "--revert", "unset wrong")
        self.ok("add", child, "plan", "--by", "agent", "--class", "reversible", "--why", "right",
                "--command", "set right", "--revert", "unset right", "--supersedes", "1")
        self.ok("add", child, "run", "--from-plan", "2", "--outcome", "ok")
        child_plan = self.ok("revert-plan", child)
        self.assertIn("unset right", child_plan)
        self.assertNotIn("unset wrong", child_plan)
        parent_plan = self.ok("revert-plan", parent)
        self.assertIn(child, parent_plan)
        self.assertIn("unset right", parent_plan)

    def test_superseding_from_plan_and_revert_entries_and_disallowing_invalid_combos(self):
        log_id = self.new()
        self.ok("add", log_id, "plan", "--by", "agent", "--class", "reversible", "--why", "scale",
                "--command", "scale 5", "--revert", "scale 3")
        self.assertEqual(self.run_log("add", log_id, "run", "--from-plan", "1", "--supersedes", "1")[0], 2)
        self.ok("add", log_id, "run", "--from-plan", "1", "--outcome", "ok")
        self.ok("add", log_id, "run", "--from-plan", "1", "--outcome", "unknown", "--supersedes", "2")
        self.assertIn("# scale 3", self.ok("revert-plan", log_id))

        log_id2 = self.new("revert-fix")
        self.ok("add", log_id2, "run", "--class", "reversible", "--why", "patch",
                "--command", "patch on", "--revert", "patch off")
        self.assertEqual(self.run_log("add", log_id2, "run", "--class", "reversible", "--command", "patch off",
                                      "--reverts", "1", "--supersedes", "1")[0], 2)
        self.ok("add", log_id2, "run", "--class", "reversible", "--command", "patch off",
                "--reverts", "1", "--outcome", "ok")
        self.assertEqual(self.ok("revert-plan", log_id2), "nothing to revert")
        self.ok("add", log_id2, "run", "--class", "reversible", "--command", "patch off",
                "--reverts", "1", "--outcome", "failed", "--supersedes", "2")
        self.assertIn("patch off", self.ok("revert-plan", log_id2))

        self.ok("add", log_id2, "plan", "--by", "agent", "--class", "reversible", "--why", "second",
                "--command", "set b", "--revert", "unset b")
        self.assertEqual(self.run_log("add", log_id2, "run", "--from-plan", "4", "--reverts", "1")[0], 2)
        self.assertEqual(self.run_log("check", log_id2, "--require", "   ")[0], 2)

    def test_delegate_reverts_are_ordered_chronologically_newest_first(self):
        parent = self.ok("new", "rollout", "--task", "rollout", "--playbook", "auto")
        first = self.ok("new", "deploy-db", "--task", "db", "--playbook", "deploy", "--parent", parent)
        second = self.ok("new", "deploy-api", "--task", "api", "--playbook", "deploy", "--parent", parent)
        self.ok("add", first, "run", "--class", "reversible", "--why", "db", "--command", "db up", "--revert", "db down")
        self.ok("add", second, "run", "--class", "reversible", "--why", "api", "--command", "api up", "--revert", "api down")
        first_doc = self.doc(first)
        second_doc = self.doc(second)
        first_doc["timeline"][0]["at"] = "2026-11-23T10:00:00+00:00"
        second_doc["timeline"][0]["at"] = "2026-11-23T11:00:00+00:00"
        log.save(log.locate(first), first_doc)
        log.save(log.locate(second), second_doc)
        output = self.ok("revert-plan", parent)
        self.assertLess(output.index("api down"), output.index("db down"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
