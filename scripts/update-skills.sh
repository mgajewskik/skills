#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

SKILLS=(
    # Softaworks skills
    "https://github.com/softaworks/agent-toolkit/tree/main/skills/agent-md-refactor"
    "https://github.com/softaworks/agent-toolkit/tree/main/skills/crafting-effective-readmes"
    "https://github.com/softaworks/agent-toolkit/tree/main/skills/reducing-entropy"
    "https://github.com/softaworks/agent-toolkit/tree/main/skills/requirements-clarity"
    "https://github.com/softaworks/agent-toolkit/tree/main/skills/skill-judge"

    # Third-party skills
    "https://github.com/antonbabenko/terraform-skill/tree/master/skills/terraform-skill"

    # Matt Pocock's skills
    "https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents"
    "https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me"
    "https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling"
    "https://github.com/mattpocock/skills/tree/main/skills/engineering/domain-modeling"
    "https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs"
    "https://github.com/mattpocock/skills/tree/main/skills/engineering/research"
    "https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder"
    "https://github.com/mattpocock/skills/tree/main/skills/productivity/to-questionnaire"

    "https://github.com/UditAkhourii/adhd/tree/main/skills/adhd"
)

mkdir -p "$SKILL_DIR"

failed=0

for url in "${SKILLS[@]}"; do
    [[ "$url" =~ github\.com/([^/]+/[^/]+)/tree/([^/]+)/(.+) ]] || continue
    repo="${BASH_REMATCH[1]}" branch="${BASH_REMATCH[2]}" path="${BASH_REMATCH[3]}"
    skill_name="$(basename "$path")"
    tmp_dir="/tmp/skill-$$"

    rm -rf "$tmp_dir"
    if ! git clone --depth=1 --filter=blob:none --sparse -b "$branch" \
        "https://github.com/$repo.git" "$tmp_dir" 2>/dev/null; then
        echo "Failed (clone): $url" >&2
        failed=1
        continue
    fi
    if ! git -C "$tmp_dir" sparse-checkout set "$path" 2>/dev/null; then
        echo "Failed (sparse-checkout): $url" >&2
        failed=1
        rm -rf "$tmp_dir"
        continue
    fi

    if [[ -d "$tmp_dir/$path" ]]; then
        rm -rf "$SKILL_DIR/$skill_name"
        cp -R "$tmp_dir/$path" "$SKILL_DIR/$skill_name"
        echo "Updated: $skill_name"
    else
        echo "Failed: $url" >&2
        failed=1
    fi
    rm -rf "$tmp_dir"
done

exit "$failed"
