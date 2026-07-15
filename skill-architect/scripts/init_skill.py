#!/usr/bin/env -S uv run --script
"""Create a minimal, portable Agent Skill scaffold."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESOURCE_NAMES = frozenset({"references", "scripts", "assets"})


def valid_name(value: str) -> str:
    if not value:
        raise argparse.ArgumentTypeError("name must not be empty")
    if len(value) > 64:
        raise argparse.ArgumentTypeError("name must be at most 64 characters")
    if not NAME_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "name must be one lowercase kebab-case component with no separators, "
            "leading/trailing hyphens, or consecutive hyphens"
        )
    return value


def valid_description(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("description must not be empty")
    if len(value) > 1024:
        raise argparse.ArgumentTypeError("description must be at most 1024 characters")
    return value


def requested_resources(value: str) -> tuple[str, ...]:
    names = value.split(",")
    if not names or any(not name for name in names):
        raise argparse.ArgumentTypeError("resources must be a comma-separated list")
    unknown = set(names) - RESOURCE_NAMES
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unsupported resource(s): {', '.join(sorted(unknown))}; "
            "choose from references,scripts,assets"
        )
    if len(names) != len(set(names)):
        raise argparse.ArgumentTypeError("resources must not contain duplicates")
    return tuple(names)


def title_for(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split("-"))


def skill_markdown(name: str, description: str) -> str:
    quoted_description = json.dumps(description, ensure_ascii=False)
    return f"""---
name: {name}
description: {quoted_description}
---

# {title_for(name)}

## Instructions

- Define the workflow this skill must follow.
- State material guardrails, safe defaults, and failure behavior.
- Verify the result against concrete success criteria before reporting completion.
"""


def init_skill(name: str, base_path: Path, description: str, resources: tuple[str, ...]) -> Path:
    destination = base_path / name
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")

    destination.mkdir(parents=True)
    try:
        (destination / "SKILL.md").write_text(skill_markdown(name, description), encoding="utf-8")
        for resource in resources:
            (destination / resource).mkdir()
    except BaseException as error:
        try:
            shutil.rmtree(destination)
        except OSError as cleanup_error:
            raise RuntimeError(
                f"initialization failed and partial destination could not be removed: {destination}"
            ) from cleanup_error
        raise error
    return destination


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", type=valid_name)
    parser.add_argument("--path", required=True, type=Path, help="parent directory for the skill")
    parser.add_argument("--description", required=True, type=valid_description)
    parser.add_argument("--resources", type=requested_resources, default=())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        destination = init_skill(args.name, args.path, args.description, args.resources)
    except (FileExistsError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Initialized skill at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
