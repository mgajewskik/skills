#!/usr/bin/env python3
"""Read-only structural checks for work-mode and the infra-principle leaves.

Run from anywhere: python3 scripts/check_work_mode.py [--root <skills catalog>]
Exit 0 when every check passes, 1 with one line per problem.
"""

import argparse
import re
import sys
from pathlib import Path

CODE_PLAYBOOKS = {
    "investigation", "bug-fix", "perf-issue", "hillclimb", "trace-forensics", "runtime-forensics", "feature",
    "refactoring", "prototype", "authoring-a-skill", "eval", "babysit", "autonomous-run", "session-pickup",
    "pause-safely", "opening-a-pr",
}
INFRA_PLAYBOOKS = {"debug", "change", "deploy", "live-modify", "teardown", "incident", "drift", "migration"}
NOT_INDEXED = {"principle-experience-first"}
REMOVED = ("poteto-mode", "setup-pstack", "make-bot-ui", "automate-me", "infra-mode", "ledger.py", "contracts.md",
           "deslop", "control-ui", "control-cli", "create-skill", "Origin")
LEAF_PARTS = ("## Why", "## Pattern", "## Stop and limit", "The test:", "You skipped this when",
              "../work-mode/references/contract.md")
VENDOR = re.compile(r"agents/vendor|vendor/(cursor-plugins|matt-skills|pstack)")
BOLD_SKILL = re.compile(r"\*\*([a-z][a-z0-9]*(?:-[a-z0-9]+)*)\*\*")


def frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def vendored_names(root):
    script = (root / "scripts/update-skills.sh").read_text()
    return {Path(path).name for path in re.findall(r'"https://github\.com/[^"]+?/tree/[^/]+/([^"]+)"', script)}


def user_only_problems(skill_dir, meta):
    """work-mode and its leaves load only by name or path: both hosts must keep them out of the model's list."""
    problems = []
    if meta.get("disable-model-invocation") != "true":
        problems.append(f"{skill_dir.name}/SKILL.md: missing disable-model-invocation: true")
    yaml = skill_dir / "agents/openai.yaml"
    if not yaml.is_file() or not re.search(r"^policy:\n\s+allow_implicit_invocation: false$", yaml.read_text(), re.M):
        problems.append(f"{skill_dir.name}/agents/openai.yaml: missing policy allow_implicit_invocation: false")
    return problems


def listed_playbooks(router):
    groups, group = {"code": set(), "infra": set()}, None
    for line in router.splitlines():
        heading = re.match(r"\*\*(Code|Infra)\*\* \(`playbooks/(code|infra)/`\)", line)
        if heading:
            group = heading.group(2)
            continue
        item = re.match(r"- \*\*[^*]+\*\* .*`([a-z-]+)\.md`\.$", line)
        if item and group:
            groups[group].add(item.group(1))
    return groups


def check(root):
    errors = []
    mode = root / "work-mode"
    router = (mode / "SKILL.md").read_text() if (mode / "SKILL.md").is_file() else ""
    meta = frontmatter(router)

    if meta.get("name") != "work-mode":
        errors.append("work-mode/SKILL.md: missing or malformed frontmatter")
    errors += user_only_problems(mode, meta)

    listed = listed_playbooks(router)
    for group, expected in (("code", CODE_PLAYBOOKS), ("infra", INFRA_PLAYBOOKS)):
        on_disk = {p.stem for p in (mode / "playbooks" / group).glob("*.md")}
        for name in sorted(expected - on_disk):
            errors.append(f"missing playbook playbooks/{group}/{name}.md")
        for name in sorted(on_disk ^ listed[group]):
            errors.append(f"playbook {group}/{name} is on disk or listed in SKILL.md, not both")

    installed = {p.parent.name for p in root.glob("*/SKILL.md")}
    indexed = set(re.findall(r"\*\*((?:infra-)?principle-[a-z-]+)\*\*", router.split("## Principles", 1)[-1].split("## Authority", 1)[0]))
    principles = {name for name in installed if re.match(r"(infra-)?principle-", name)}
    for name in sorted(indexed - installed):
        errors.append(f"index names {name}, which is not installed")
    for name in sorted(principles - indexed - NOT_INDEXED):
        errors.append(f"installed {name} is missing from the work-mode index")

    leaves = sorted(name for name in installed if name.startswith("infra-principle-"))
    if len(leaves) != 11:
        errors.append(f"expected 11 infra-principle leaves, found {len(leaves)}")
    for name in leaves:
        text = (root / name / "SKILL.md").read_text()
        meta = frontmatter(text)
        if meta.get("name") != name:
            errors.append(f"{name}: frontmatter name does not match directory")
        errors += user_only_problems(root / name, meta)
        if not meta.get("description", "").startswith("Apply "):
            errors.append(f"{name}: description should start with 'Apply' (a trigger)")
        for part in LEAF_PARTS:
            if part not in text:
                errors.append(f"{name}: missing '{part}'")
        why = text.split("## Why", 1)[-1].split("\n## ", 1)[0]
        if "](https://" not in why:
            errors.append(f"{name}: ## Why cites no source link")

    sys.path.insert(0, str(mode / "scripts"))
    try:
        import check_handoff
        template = (mode / "references/handoff.md").read_text()
        for section in check_handoff.SECTIONS + check_handoff.DESTROY_SECTIONS:
            if f"## {section}" not in template:
                errors.append(f"handoff.md template lacks '## {section}' that the linter requires")
    except (ImportError, OSError) as error:
        errors.append(f"cannot compare handoff template with linter: {error}")

    allowed = vendored_names(root) | set(leaves) | {"work-mode"}
    for package in [mode] + [root / name for name in leaves]:
        for file in sorted(package.rglob("*.md")):
            content = file.read_text()
            where = file.relative_to(root)
            for name in () if file.name == "host-notes.md" else REMOVED:
                if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", content):
                    errors.append(f"{where}: references removed or unavailable '{name}'")
            for name in sorted(set(BOLD_SKILL.findall(content))):
                if name not in allowed:
                    errors.append(f"{where}: names skill '{name}', which is not vendored or part of work-mode")
                elif name not in installed:
                    errors.append(f"{where}: names skill '{name}', which is not installed")
            if len(re.findall(r"^\s*```", content, re.MULTILINE)) % 2:
                errors.append(f"{where}: unbalanced fences")
            for diagram in re.findall(r"```text\n(.*?)\n```", content, re.DOTALL):
                if not diagram.isascii():
                    errors.append(f"{where}: non-ASCII diagram")
            for target in re.findall(r"\]\(([^)\s]+)\)", content):
                if target.startswith(("https://", "http://", "#")):
                    continue
                actual = (file.parent / target.split("#", 1)[0]).resolve()
                if not actual.is_relative_to(package.resolve()):
                    errors.append(f"{where}: link leaves its package: {target}")
                elif not actual.exists():
                    errors.append(f"{where}: broken link {target}")

    skill_dirs = {root / name for name in installed} | {root / "scripts"}
    for file in sorted(root.rglob("*")):
        if not file.is_file() or file.suffix not in (".md", ".sh", ".py", ".yaml", ".yml"):
            continue
        if not any(file.is_relative_to(directory) for directory in skill_dirs):
            continue
        if file.resolve() == Path(__file__).resolve():
            continue
        if VENDOR.search(file.read_text(errors="replace")):
            errors.append(f"{file.relative_to(root)}: references ~/.agents/vendor")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="skills catalog (default: this script's repository)")
    root = parser.parse_args(argv).root.resolve()
    errors = check(root)
    if errors:
        print("FAIL\n" + "\n".join(errors))
        return 1
    print("PASS: 16 code and 8 infra playbooks, 11 infra leaves, index and links resolve. Structural checks only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
