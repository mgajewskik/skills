#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "pyyaml",
# ]
# ///
"""Improve a skill description from trigger-eval failures using a configured JSONL runner."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

try:
    from .utils import (
        extract_text_from_runner_events,
        get_skill_repository_root,
        parse_skill_md,
        replace_description,
        run_runner_json,
    )
except ImportError:
    from utils import (
        extract_text_from_runner_events,
        get_skill_repository_root,
        parse_skill_md,
        replace_description,
        run_runner_json,
    )


def _call_runner(prompt: str, runner_command: str, model: str | None, agent: str | None) -> str:
    events = run_runner_json(
        prompt,
        runner_command,
        agent=agent,
        model=model,
        directory=get_skill_repository_root(),
    )
    text = extract_text_from_runner_events(events)
    if not text:
        raise RuntimeError("Runner returned no text output")
    return text


def improve_description(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    model: str | None = None,
    history: list[dict] | None = None,
    agent: str | None = None,
    runner_command: str = "",
) -> str:
    if not runner_command:
        raise ValueError("A runner command is required")
    failed_positive = [result for result in eval_results["results"] if result["should_trigger"] and not result["pass"]]
    failed_negative = [
        result for result in eval_results["results"] if not result["should_trigger"] and not result["pass"]
    ]

    prompt = [
        f'You are improving the description for an agent skill named "{skill_name}".',
        "The description is the only thing visible before the skill loads.",
        "Write a new description that improves trigger accuracy without becoming a keyword dump.",
        "Stay well below the 1024 character limit.",
        "Respond with only the description wrapped in <new_description> tags.",
        "",
        f'Current description: "{current_description}"',
        "",
        "Failed positives (should have triggered):",
    ]
    if failed_positive:
        prompt.extend(
            f"- {result['query']} (observed {result['triggers']}/{result['runs']})" for result in failed_positive
        )
    else:
        prompt.append("- none")

    prompt.append("")
    prompt.append("Failed negatives (should NOT have triggered):")
    if failed_negative:
        prompt.extend(
            f"- {result['query']} (observed {result['triggers']}/{result['runs']})" for result in failed_negative
        )
    else:
        prompt.append("- none")

    if history:
        prompt.append("")
        prompt.append("Previous attempts to avoid repeating:")
        for item in history:
            prompt.append(f"- {item.get('description', '')}: {item.get('score', '')}".strip())

    prompt.extend(
        [
            "",
            "Skill content for context:",
            skill_content,
        ]
    )

    response = _call_runner("\n".join(prompt), runner_command, model=model, agent=agent)
    match = re.search(r"<new_description>(.*?)</new_description>", response, re.DOTALL)
    description = " ".join((match.group(1) if match else response).strip().strip('"').split())
    if len(description) > 1024:
        raise ValueError("Generated description exceeds 1024 character limit")
    return description


def main() -> int:
    parser = argparse.ArgumentParser(description="Improve a skill description from eval results")
    parser.add_argument("--eval-results", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--agent", default=None)
    parser.add_argument(
        "--runner-command",
        default=os.environ.get("SKILL_EVAL_RUNNER"),
        help="JSONL runner command template; supports {prompt}, {agent}, {model}, and {directory}",
    )
    parser.add_argument("--history", default=None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.runner_command:
        parser.error("--runner-command or SKILL_EVAL_RUNNER is required")

    eval_results = json.loads(Path(args.eval_results).read_text())
    history = json.loads(Path(args.history).read_text()) if args.history else None
    skill_path = Path(args.skill_path)
    name, current_description, content = parse_skill_md(skill_path)
    new_description = improve_description(
        name,
        content,
        current_description,
        eval_results,
        model=args.model,
        history=history,
        agent=args.agent,
        runner_command=args.runner_command,
    )

    if args.apply:
        replace_description(skill_path, new_description)

    print(new_description)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
