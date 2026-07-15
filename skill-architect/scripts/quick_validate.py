#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML>=6.0"]
# ///
"""Validate the portable core of an Agent Skill package."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)


def fail(message: str) -> tuple[bool, str]:
    return False, message


def validate_optional_fields(data: dict[str, Any]) -> tuple[bool, str] | None:
    if "license" in data and not isinstance(data["license"], str):
        return fail("'license' must be a string")

    if "compatibility" in data:
        compatibility = data["compatibility"]
        if not isinstance(compatibility, str):
            return fail("'compatibility' must be a string")
        if not 1 <= len(compatibility) <= 500:
            return fail("'compatibility' must contain 1 to 500 characters")

    if "metadata" in data:
        metadata = data["metadata"]
        if not isinstance(metadata, dict):
            return fail("'metadata' must be a mapping")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in metadata.items()):
            return fail("'metadata' keys and values must be strings")

    if "allowed-tools" in data and not isinstance(data["allowed-tools"], str):
        return fail("'allowed-tools' must be a string")
    return None


def validate_skill(skill_path: str | Path) -> tuple[bool, str]:
    path = Path(skill_path)
    if not path.is_dir():
        return fail(f"skill directory not found: {path}")

    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        return fail("SKILL.md not found")

    try:
        content = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return fail(f"cannot read SKILL.md: {exc}")

    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return fail("SKILL.md must start with YAML frontmatter delimited by '---'")
    if not content[match.end():].strip():
        return fail("SKILL.md must contain a non-empty Markdown body after frontmatter")
    if yaml is None:
        return fail("PyYAML is required for validation; run this script with uv or validate with the target runtime")

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return fail(f"invalid YAML frontmatter: {exc}")
    if not isinstance(data, dict):
        return fail("frontmatter must be a YAML mapping")

    unknown = set(data) - ALLOWED_FIELDS
    if unknown:
        return fail(
            f"unknown portable frontmatter field(s): {', '.join(sorted(map(str, unknown)))}; "
            "validate runtime-specific fields with the target runtime"
        )

    for field in ("name", "description"):
        if field not in data:
            return fail(f"missing required field: '{field}'")
        if not isinstance(data[field], str):
            return fail(f"'{field}' must be a string")

    name = data["name"]
    if not 1 <= len(name) <= 64:
        return fail("'name' must contain 1 to 64 characters")
    if not NAME_PATTERN.fullmatch(name):
        return fail("'name' must be lowercase kebab-case without leading, trailing, or consecutive hyphens")
    if path.name != name:
        return fail(f"directory name '{path.name}' must exactly match skill name '{name}'")

    description = data["description"]
    if not 1 <= len(description) <= 1024 or not description.strip():
        return fail("'description' must contain 1 to 1024 non-whitespace characters")

    optional_error = validate_optional_fields(data)
    if optional_error:
        return optional_error
    return True, "Skill is valid"


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: uv run skill-architect/scripts/quick_validate.py <skill-directory>", file=sys.stderr)
        return 2
    valid, message = validate_skill(argv[0])
    print(message, file=sys.stdout if valid else sys.stderr)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
