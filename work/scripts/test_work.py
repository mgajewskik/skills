#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Structural tests for the work skill. Run: uv run --script test_work.py"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

import yaml  # noqa: E402

WORK_DIR = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]+)?\)")


def frontmatter(path):
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end])


def relative_links(path):
    links = []
    for target in LINK_RE.findall(path.read_text()):
        if "://" in target or target.startswith("#"):
            continue
        links.append(target)
    return links


class WorkSkillTest(unittest.TestCase):
    def test_all_markdown_links_resolve_inside_work(self):
        md_files = sorted(WORK_DIR.rglob("*.md"))
        self.assertTrue(md_files)
        for md in md_files:
            for target in relative_links(md):
                resolved = (md.parent / target).resolve()
                self.assertTrue(
                    resolved.is_relative_to(WORK_DIR.resolve()),
                    f"{md.relative_to(WORK_DIR)} links outside work/: {target}",
                )
                self.assertTrue(
                    resolved.is_file(),
                    f"{md.relative_to(WORK_DIR)} has broken link: {target}",
                )

    def test_principles_are_plain_markdown_with_no_nested_skill_files(self):
        principles_dir = WORK_DIR / "principles"
        nested_skills = list(principles_dir.rglob("SKILL.md"))
        self.assertEqual(nested_skills, [])
        nested_dirs = [p for p in principles_dir.iterdir() if p.is_dir()]
        self.assertEqual(nested_dirs, [])
        principle_files = sorted(principles_dir.glob("*.md"))
        self.assertGreaterEqual(len(principle_files), 20)
        for pf in principle_files:
            text = pf.read_text()
            self.assertFalse(text.startswith("---\n"), f"{pf.name} still carries YAML frontmatter")
            self.assertTrue(text.startswith("# "), f"{pf.name} should start with an H1 heading")

    def test_every_playbook_and_principle_is_linked_from_skill_md(self):
        skill_md = WORK_DIR / "SKILL.md"
        linked = {(skill_md.parent / t).resolve() for t in relative_links(skill_md)}
        for folder in ("playbooks", "principles"):
            for md in sorted((WORK_DIR / folder).glob("*.md")):
                self.assertIn(md.resolve(), linked, f"unlinked file in {folder}/: {md.name}")

    def test_claude_code_hooks_present_and_subagent_hook_exempts_readonly_reviews(self):
        fm = frontmatter(WORK_DIR / "SKILL.md")
        hooks = fm.get("hooks", {})
        self.assertIn("UserPromptSubmit", hooks)
        self.assertIn("SubagentStart", hooks)
        subagent_cmd = hooks["SubagentStart"][0]["hooks"][0]["command"].lower()
        self.assertIn("read-only", subagent_cmd)
        self.assertIn("review", subagent_cmd)
        self.assertIn("workstream", subagent_cmd)

    def test_investigate_playbook_exists_and_auto_does_not_override_teardown(self):
        self.assertTrue((WORK_DIR / "playbooks" / "investigate.md").is_file())
        auto_text = (WORK_DIR / "playbooks" / "auto.md").read_text()
        self.assertNotIn("replaces Teardown step 8", auto_text)
        self.assertNotIn("replaces Teardown's destroy handover", auto_text)

    def test_review_playbook_exists_and_is_wired_across_playbooks(self):
        review_path = WORK_DIR / "playbooks" / "review.md"
        self.assertTrue(review_path.is_file())
        review_text = review_path.read_text()
        self.assertIn("adversarial", review_text.lower())
        for required in (
            "read-only",
            "Decision: PASS",
            "BLOCKER",
            "NOTE",
            "OUT_OF_SCOPE",
            "Code smells",
            "Ops smells",
            "Work log",
            "artifact revision",
            "--no-revert",
        ):
            self.assertIn(required, review_text)
        for caller in ("implement.md", "fix.md", "reduce.md", "deploy.md", "auto.md", "investigate.md"):
            self.assertIn("(review.md)", (WORK_DIR / "playbooks" / caller).read_text(), caller)
        self.assertNotIn("significant behavior", (WORK_DIR / "playbooks" / "implement.md").read_text())
        self.assertNotIn("significant behavior", (WORK_DIR / "playbooks" / "fix.md").read_text())

    def test_update_script_syntax_is_valid(self):
        proc = subprocess.run(["bash", "-n", str(WORK_DIR / "scripts" / "update.sh")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_update_script_flattens_upstream_and_protects_local_and_inlined(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            upstream = tmp_path / "upstream"
            skills = upstream / "pstack" / "skills"
            (skills / "principle-attack-the-premise").mkdir(parents=True)
            (skills / "principle-attack-the-premise" / "SKILL.md").write_text(
                "---\nname: principle-attack-the-premise\ndescription: x\n---\n\n"
                "# Attack the Premise\n\nSee [fix](../principle-fix-root-causes/SKILL.md).\n"
            )
            (skills / "principle-prove-it-works").mkdir(parents=True)
            (skills / "principle-prove-it-works" / "SKILL.md").write_text(
                "---\nname: principle-prove-it-works\ndescription: x\n---\n\n# Upstream Prove\n"
            )
            (skills / "principle-laziness-protocol").mkdir(parents=True)
            (skills / "principle-laziness-protocol" / "SKILL.md").write_text(
                "---\nname: principle-laziness-protocol\ndescription: x\n---\n\n# Upstream Laziness\n"
            )
            subprocess.run(["git", "init", "-q", "-b", "main", str(upstream)], check=True)
            subprocess.run(["git", "-C", str(upstream), "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", str(upstream), "config", "user.name", "T"], check=True)
            subprocess.run(["git", "-C", str(upstream), "add", "."], check=True)
            subprocess.run(["git", "-C", str(upstream), "commit", "-q", "-m", "init"], check=True)

            dest = tmp_path / "dest"
            dest.mkdir()
            (dest / "prove-it-works.md").write_text("# Local Prove\n")
            backup = tmp_path / "backup"
            env = {
                **os.environ,
                "REPO": f"file://{upstream}",
                "BRANCH": "main",
                "DEST": str(dest),
                "BACKUP_DIR": str(backup),
            }
            for _ in range(2):
                proc = subprocess.run(
                    ["bash", str(WORK_DIR / "scripts" / "update.sh")],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertIn("Updated: attack-the-premise", proc.stdout)
                self.assertIn("Skipped (local): prove-it-works", proc.stdout)
                self.assertIn("Skipped (inlined): laziness-protocol", proc.stdout)

            self.assertEqual((dest / "prove-it-works.md").read_text(), "# Local Prove\n")
            self.assertFalse((dest / "laziness-protocol.md").exists())
            self.assertEqual(
                (dest / "attack-the-premise.md").read_text(),
                "# Attack the Premise\n\nSee [fix](fix-root-causes.md).\n",
            )
            self.assertEqual((backup / "upstream-local" / "prove-it-works.md").read_text(), "# Upstream Prove\n")

    def test_every_file_backed_principle_is_referenced_by_at_least_one_playbook(self):
        principle_files = {p.stem for p in (WORK_DIR / "principles").glob("*.md")}
        referenced = set()
        for pb in (WORK_DIR / "playbooks").glob("*.md"):
            for target in relative_links(pb):
                resolved = (pb.parent / target).resolve()
                if resolved.parent == (WORK_DIR / "principles").resolve():
                    referenced.add(resolved.stem)
        self.assertEqual(sorted(principle_files - referenced), [])

    def test_implement_requires_redesign_from_first_principles(self):
        implement_text = (WORK_DIR / "playbooks" / "implement.md").read_text()
        self.assertIn("../principles/redesign-from-first-principles.md", implement_text)

    def test_update_script_ownership_lists_match_principles_and_skill_md(self):
        update_text = (WORK_DIR / "scripts" / "update.sh").read_text()
        local_owned = set(re.findall(r"(?m)^    ([a-z0-9-]+)$", update_text.split("LOCAL_OWNED=(")[1].split(")")[0]))
        inlined = set(re.findall(r"(?m)^    ([a-z0-9-]+)$", update_text.split("INLINED=(")[1].split(")")[0]))
        actual = {p.stem for p in (WORK_DIR / "principles").glob("*.md")}
        self.assertEqual(sorted(local_owned - actual), [])
        self.assertEqual(sorted(inlined & actual), [])
        skill_principles = (WORK_DIR / "SKILL.md").read_text().split("## Principles", 1)[1]
        for slug in sorted(inlined):
            title_pattern = rf"(?im)^- \*\*{re.escape(slug.replace('-', ' '))}\.\*\*"
            self.assertRegex(skill_principles, title_pattern)

    def test_hooks_emit_valid_payloads_and_yield_to_other_skills(self):
        fm = frontmatter(WORK_DIR / "SKILL.md")
        hooks = fm["hooks"]
        prompt_cmd = hooks["UserPromptSubmit"][0]["hooks"][0]["command"]
        prompt_out = subprocess.run(["sh", "-c", prompt_cmd], capture_output=True, text=True, check=True).stdout
        self.assertIn("another skill", prompt_out.lower())

        sub_entry = hooks["SubagentStart"][0]
        matcher = re.compile(sub_entry["matcher"])
        for agent_type in ("general-purpose", "Explore", "Plan", "sonnet", "opus", "haiku", "claude"):
            self.assertRegex(agent_type, matcher)
        sub_cmd = sub_entry["hooks"][0]["command"]
        sub_out = subprocess.run(["sh", "-c", sub_cmd], capture_output=True, text=True, check=True).stdout
        payload = json.loads(sub_out)
        ctx = payload["hookSpecificOutput"]["additionalContext"].lower()
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SubagentStart")
        self.assertIn("another skill", ctx)
        self.assertIn("never spawn a reviewer", ctx)
        self.assertNotIn("under auto, return review inputs", ctx)

    def test_review_playbook_is_self_contained_and_free_of_orphan_envelope_fields(self):
        review_text = (WORK_DIR / "playbooks" / "review.md").read_text()
        self.assertNotIn("TASK_NAME:", review_text)
        self.assertNotIn("PARENT_HANDOFF:", review_text)
        self.assertIn("tool directives", review_text.lower())
        self.assertIn("workaround", review_text.lower())

    def test_auto_routes_review_through_orchestrator_not_nested_subagents(self):
        skill_text = (WORK_DIR / "SKILL.md").read_text().lower()
        self.assertIn("orchestrator-only reviewer spawning", skill_text)
        self.assertNotIn("**under `auto`:** unit subagents", skill_text)
        review_text = (WORK_DIR / "playbooks" / "review.md").read_text().lower()
        self.assertIn("only the main", review_text)
        self.assertIn("never spawns a reviewer", review_text)
        auto_text = (WORK_DIR / "playbooks" / "auto.md").read_text().lower()
        self.assertIn("orchestrator", auto_text)
        self.assertIn("reviewer", auto_text)
        self.assertIn("same reviewed delegate log", auto_text)
        deploy_text = (WORK_DIR / "playbooks" / "deploy.md").read_text().lower()
        self.assertIn("same reviewed delegate log", deploy_text)
        for caller in ("implement.md", "fix.md", "reduce.md", "deploy.md"):
            text = (WORK_DIR / "playbooks" / caller).read_text().lower()
            self.assertIn("orchestrator", text, caller)
            self.assertIn("never spawn a reviewer", text, caller)
            self.assertNotIn("when running as an `auto` unit", text, caller)

    def test_debug_playbook_and_skill_document_artifacts_suggest_closing_and_reopen(self):
        debug_text = (WORK_DIR / "playbooks" / "debug.md").read_text().lower()
        self.assertIn("--artifact", debug_text)
        self.assertIn("--from-plan", debug_text)
        skill_text = (WORK_DIR / "SKILL.md").read_text().lower()
        self.assertIn("reopen <id>", skill_text)
        self.assertIn("--artifact-name", skill_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
