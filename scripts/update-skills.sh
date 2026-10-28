#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Every skill keeps its upstream invocation setting. A user-only skill (frontmatter
# "disable-model-invocation: true") never enters the model's skill list; the user names it,
# or the agent reads its SKILL.md by path.
SKILLS=(
    # Softaworks skills
    "https://github.com/softaworks/agent-toolkit/tree/main/skills/crafting-effective-readmes"

    # Third-party skills
    "https://github.com/antonbabenko/terraform-skill/tree/master/skills/terraform-skill"

    # Matt Pocock's skills
    "https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents"
    "https://github.com/mattpocock/skills/tree/main/skills/engineering/domain-modeling"
    "https://github.com/mattpocock/skills/tree/main/skills/engineering/research"
    "https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder"
    "https://github.com/mattpocock/skills/tree/main/skills/engineering/pr"

    # pstack skills
    "https://github.com/cursor/plugins/tree/main/pstack/skills/architect"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/arena"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/benchmark-checklist"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/blast-radius"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/bro"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/create-verification-skill"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/figure-it-out"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/how"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/maintain-verification-skill"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/recall"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/reflect"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/sharpen"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/tdd"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/teach"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/technical-writing"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/typescript-best-practices"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/unslop"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/why"

    "https://github.com/cloudflare/security-audit-skill/tree/main/skills/security-audit"
)

# Print the line number of the closing "---" of the SKILL.md frontmatter.
frontmatter_end() {
    awk 'NR == 1 && $0 != "---" { exit } NR > 1 && $0 == "---" { print NR; exit }' "$1"
}

# True when the SKILL.md frontmatter sets "disable-model-invocation: true".
is_user_only() {
    local end
    end="$(frontmatter_end "$1")"
    [[ -n "$end" ]] && head -n "$end" "$1" | grep -qx 'disable-model-invocation: true'
}

# Codex reads agents/openai.yaml, not the frontmatter flag. Give every user-only skill a
# policy that disables implicit invocation. An upstream openai.yaml is kept as it is.
mirror_policy_for_codex() {
    local skill_name="$1" skill_dir="$2" yaml="$2/agents/openai.yaml"
    if [[ ! -f "$yaml" ]]; then
        mkdir -p "$skill_dir/agents"
        printf 'policy:\n  allow_implicit_invocation: false\n' > "$yaml"
        echo "Codex policy: $skill_name: wrote agents/openai.yaml (user-only upstream)"
    elif ! grep -q 'allow_implicit_invocation: false' "$yaml"; then
        echo "Warning: $skill_name: agents/openai.yaml exists without allow_implicit_invocation: false; left unchanged" >&2
    fi
}

VENDORED=()
for url in "${SKILLS[@]}"; do
    VENDORED+=("$(basename "$url")")
done

# A name written as "**name** skill" points nowhere unless it is a catalog skill or a work principle.
warn_unresolved_skills() {
    local skill_name="$1" token
    while read -r token; do
        if [[ ! -f "$SKILL_DIR/$token/SKILL.md" && ! -f "$SKILL_DIR/work/principles/${token#principle-}/SKILL.md" ]]; then
            echo "Warning: $skill_name: names the $token skill, which is not in the catalog" >&2
        fi
    done < <(grep -rhoE '(\*\*|`)[a-z][a-z0-9-]*(\*\*|`)( principle)? skill' "$SKILL_DIR/$skill_name" \
        --include='*.md' | sed -E 's/^[*`]+([a-z0-9-]+).*/\1/' | sort -u)
}

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
        if is_user_only "$SKILL_DIR/$skill_name/SKILL.md"; then
            mirror_policy_for_codex "$skill_name" "$SKILL_DIR/$skill_name"
        fi
    else
        echo "Failed: $url" >&2
        failed=1
    fi
    rm -rf "$tmp_dir"
done

for skill_name in "${VENDORED[@]}"; do
    if [[ -f "$SKILL_DIR/$skill_name/SKILL.md" ]]; then
        warn_unresolved_skills "$skill_name"
    fi
done

exit "$failed"
