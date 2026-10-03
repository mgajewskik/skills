#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Every skill keeps its upstream invocation setting; principle-* leaves also get hidden from the
# slash menu (see hide_from_slash_menu). A user-only skill (frontmatter
# "disable-model-invocation: true") never enters the model's skill list; the user names it,
# or the agent reads its SKILL.md by path. A downloaded skill that names other user-only
# skills gets a generated skill-paths.md with those paths (see write_skill_paths).
SKILLS=(
    # Softaworks skills
    "https://github.com/softaworks/agent-toolkit/tree/main/skills/crafting-effective-readmes"
    "https://github.com/softaworks/agent-toolkit/tree/main/skills/reducing-entropy"
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

    # pstack skills (all except poteto-mode, setup-pstack, make-bot-ui, automate-me)
    "https://github.com/cursor/plugins/tree/main/pstack/skills/architect"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/arena"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/benchmark-checklist"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/blast-radius"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/bro"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/create-verification-skill"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/figure-it-out"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/how"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/interrogate"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/maintain-verification-skill"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/no-comments"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-attack-the-premise"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-boundary-discipline"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-build-the-lever"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-encode-lessons-in-structure"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-exhaust-the-design-space"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-experience-first"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-explain-the-number"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-fix-root-causes"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-foundational-thinking"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-guard-the-context-window"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-laziness-protocol"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-make-operations-idempotent"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-migrate-callers-then-delete-legacy-apis"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-minimize-reader-load"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-model-the-domain"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-never-block-on-the-human"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-outcome-oriented-execution"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-prove-it-works"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-redesign-from-first-principles"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-separate-before-serializing-shared-state"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-sequence-verifiable-units"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-subtract-before-you-add"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-test-behavior-not-implementation"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/principle-type-system-discipline"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/recall"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/reflect"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/show-me-your-work"
    "https://github.com/cursor/plugins/tree/main/pstack/skills/swarm"
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

# Add "user-invocable: false" to a principle-* leaf so the slash menu does not list it. Upstream's
# "disable-model-invocation: true" stays, so the leaf is loaded only by path.
hide_from_slash_menu() {
    local file="$1" end
    end="$(frontmatter_end "$file")"
    [[ -n "$end" ]] || return 0
    awk -v end="$end" '
        NR > 1 && NR < end && /^user-invocable:/ { next }
        NR == end { print "user-invocable: false" }
        { print }
    ' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
}

VENDORED=()
for url in "${SKILLS[@]}"; do
    VENDORED+=("$(basename "$url")")
done

# True when $1 is a downloaded skill that is user-only.
is_vendored_user_only() {
    local name="$1" vendored
    for vendored in "${VENDORED[@]}"; do
        if [[ "$vendored" == "$name" && -f "$SKILL_DIR/$name/SKILL.md" ]]; then
            is_user_only "$SKILL_DIR/$name/SKILL.md"
            return
        fi
    done
    return 1
}

POINTER_START="Skills named in this skill are user-only."

# Add the skill-paths.md pointer to $1 (below its frontmatter, if any) unless it is there.
# $2 is the relative path from $1's directory to skill-paths.md.
add_pointer() {
    local file="$1" link="$2" end
    grep -qF "$POINTER_START" "$file" && return 0
    end="$(frontmatter_end "$file")"
    awk -v end="${end:-0}" -v pointer="$POINTER_START Load them by reading the paths in [skill-paths.md]($link), never through a skill tool, and give a subagent the path of any skill it needs." '
        end == 0 && NR == 1 { print pointer; print "" }
        { print }
        NR == end { print ""; print pointer }
    ' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
}

# User-only skills are hidden from the model's skill list and a skill tool refuses them, so a
# downloaded skill that names one needs its path. Write skill-paths.md with the user-only
# downloaded skills this skill names (in **bold**, `code` or `/code`, as <name> or principle-<name>),
# and point to it from SKILL.md and from every other file that names one of them, since a
# subagent may be handed a reference file without SKILL.md.
write_skill_paths() {
    local skill_name="$1" skill_dir="$SKILL_DIR/$1"
    local token target rows="" count=0 mapped=() names file rel
    while read -r token; do
        target=""
        if is_vendored_user_only "$token"; then
            target="$token"
        elif is_vendored_user_only "principle-$token"; then
            target="principle-$token"
        fi
        if [[ -n "$target" && "$target" != "$skill_name" ]]; then
            rows+="| $token | [../$target/SKILL.md](../$target/SKILL.md) |"$'\n'
            mapped+=("$token")
            count=$((count + 1))
        fi
    done < <(grep -rhoE '\*\*[a-z][a-z0-9-]*\*\*|`/?[a-z][a-z0-9-]*`' "$skill_dir" \
        --include='*.md' --exclude=skill-paths.md | tr -d '*`/' | sort -u)
    [[ "$count" -eq 0 ]] && return 0

    {
        echo "# Skill paths"
        echo
        echo "Written by scripts/update-skills.sh on every update. Edit the script, not this file."
        echo
        echo "This skill names the skills below. They are user-only: they are not in your skill list, and a skill tool refuses them. Load each one by reading its SKILL.md at the path given, relative to this file's directory. When a subagent needs one, put the absolute path in its brief and tell it to read the file."
        echo
        echo "| Named as | Path |"
        echo "| --- | --- |"
        printf '%s' "$rows"
    } > "$skill_dir/skill-paths.md"
    echo "Skill paths: $skill_name: wrote skill-paths.md ($count skills)"

    add_pointer "$skill_dir/SKILL.md" "skill-paths.md"
    names="$(IFS='|'; echo "${mapped[*]}")"
    while read -r file; do
        rel="$(dirname "${file#"$skill_dir"/}")"
        if [[ "$rel" == "." ]]; then
            add_pointer "$file" "skill-paths.md"
        else
            add_pointer "$file" "$(echo "$rel" | sed -E 's#[^/]+#..#g')/skill-paths.md"
        fi
    done < <(grep -rlE "(\*\*|\`/?)($names)(\*\*|\`)" "$skill_dir" --include='*.md' --exclude=skill-paths.md)

    # A name written as "**name** skill" that is not in the catalog points nowhere.
    while read -r token; do
        if [[ ! -f "$SKILL_DIR/$token/SKILL.md" && ! -f "$SKILL_DIR/principle-$token/SKILL.md" ]]; then
            echo "Warning: $skill_name: names the $token skill, which is not in the catalog" >&2
        fi
    done < <(grep -rhoE '(\*\*|`)[a-z][a-z0-9-]*(\*\*|`)( principle)? skill' "$skill_dir" \
        --include='*.md' --exclude=skill-paths.md | sed -E 's/^[*`]+([a-z0-9-]+).*/\1/' | sort -u)
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
        if [[ "$skill_name" == principle-* ]]; then
            hide_from_slash_menu "$SKILL_DIR/$skill_name/SKILL.md"
        fi
        if is_user_only "$SKILL_DIR/$skill_name/SKILL.md"; then
            mirror_policy_for_codex "$skill_name" "$SKILL_DIR/$skill_name"
        fi
    else
        echo "Failed: $url" >&2
        failed=1
    fi
    rm -rf "$tmp_dir"
done

# After all downloads, so every named skill's user-only flag is known.
for skill_name in "${VENDORED[@]}"; do
    if [[ -f "$SKILL_DIR/$skill_name/SKILL.md" ]]; then
        write_skill_paths "$skill_name"
    fi
done

exit "$failed"
