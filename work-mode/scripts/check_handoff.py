#!/usr/bin/env python3
"""Lint a user-executed handoff and print its fingerprint.

check        exit 0 when the handoff is complete, 1 with file:line problems, 64 usage.
fingerprint  print the sha256 that an owner approval binds to. Any edit changes it.

The linter checks completeness, not truth: required header fields and sections,
no unfilled <placeholder>, an explicit finite target list whose length matches Count,
and a fenced command block. Destroy handoffs also need Inventory and Reversible first.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

CLASSES = ("modify", "deploy", "destroy", "contain")
ENVIRONMENTS = ("production", "staging", "development", "unknown")
FIELDS = ("Class", "Environment", "Owner", "Revision")
SECTIONS = (
    "Targets",
    "Preconditions",
    "Commands",
    "Expected signal",
    "Stop conditions",
    "Recovery",
    "Verification",
    "Must not change",
)
DESTROY_SECTIONS = ("Inventory", "Reversible first")
BROAD_TARGET = re.compile(r"[*?]|^(all|everything|any)\b", re.IGNORECASE)
PLACEHOLDER = re.compile(r"<[A-Za-z][\w .:/-]*[\w.]>")


def normalized(text):
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip() + "\n"


def fingerprint(text):
    return hashlib.sha256(normalized(text).encode()).hexdigest()


def parse(lines):
    fields, sections, current, fence = {}, {}, None, False
    for number, line in enumerate(lines, start=1):
        if line.startswith("```"):
            fence = not fence
        elif fence and current and line.strip():
            sections[current]["fenced"] = True
        elif not fence and line.startswith("## "):
            current = line[3:].strip()
            sections[current] = {"line": number, "body": [], "fenced": False}
            continue
        elif not fence and current is None:
            match = re.match(r"^([A-Z][A-Za-z ]+):\s*(.*)$", line)
            if match:
                fields[match.group(1)] = (match.group(2).strip(), number)
        if current:
            sections[current]["body"].append((number, line))
    return fields, sections, fence


def check(path, text):
    lines = text.replace("\r\n", "\n").split("\n")
    fields, sections, open_fence = parse(lines)
    problems = []

    def problem(line, message):
        problems.append(f"{path}:{line}: {message}")

    if open_fence:
        problem(len(lines), "unclosed code fence")
    for number, line in enumerate(lines, start=1):
        if PLACEHOLDER.search(line):
            problem(number, f"unfilled placeholder: {line.strip()}")
    for name in FIELDS:
        if not fields.get(name, ("",))[0]:
            problem(1, f"missing header field {name}:")
    kind = fields.get("Class", ("", 1))
    if kind[0] and kind[0] not in CLASSES:
        problem(kind[1], f"Class must be one of {', '.join(CLASSES)}")
    environment = fields.get("Environment", ("", 1))
    if environment[0] and environment[0] not in ENVIRONMENTS:
        problem(environment[1], f"Environment must be one of {', '.join(ENVIRONMENTS)}")

    required = SECTIONS + (DESTROY_SECTIONS if kind[0] == "destroy" else ())
    for name in required:
        section = sections.get(name)
        if section is None:
            problem(len(lines), f"missing section ## {name}")
        elif not any(line.strip() for _, line in section["body"]):
            problem(section["line"], f"empty section ## {name}")

    targets = sections.get("Targets")
    if targets:
        items = [(n, line[2:].strip()) for n, line in targets["body"] if line.startswith("- ")]
        count = [(n, line) for n, line in targets["body"] if line.startswith("Count:")]
        if not items:
            problem(targets["line"], "Targets needs an explicit list of target identifiers")
        for number, item in items:
            if BROAD_TARGET.search(item):
                problem(number, f"target is a pattern, not an identifier: {item}")
        if not count:
            problem(targets["line"], "Targets needs a Count: line")
        elif count[0][1][6:].strip() != str(len(items)):
            problem(count[0][0], f"Count says {count[0][1][6:].strip()}, list has {len(items)}")
    commands = sections.get("Commands")
    if commands and not commands["fenced"]:
        problem(commands["line"], "Commands needs the exact commands in a non-empty fenced block")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("check", "fingerprint"))
    parser.add_argument("handoff", type=Path)
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return 64 if error.code else 0
    text = args.handoff.read_text()
    if args.command == "fingerprint":
        print(fingerprint(text))
        return 0
    problems = check(args.handoff, text)
    for line in problems:
        print(line, file=sys.stderr)
    print(f"{len(problems)} problems; fingerprint {fingerprint(text)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
