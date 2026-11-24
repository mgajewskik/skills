#!/usr/bin/env bash

set -euo pipefail

REPO="${REPO:-https://github.com/cursor/plugins.git}"
BRANCH="${BRANCH:-main}"
UPSTREAM_PATH="${UPSTREAM_PATH:-pstack/skills}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
DEST="${DEST:-$SKILL_DIR/principles}"

LOCAL_OWNED=(
    act-through-the-narrowest-identity
    bound-change-exposure
    build-the-lever
    design-recovery-first
    explain-the-number
    ground-claims-in-the-environment
    inventory-before-destroy
    leave-no-residue
    never-block-on-the-human
    outcome-oriented-execution
    preserve-compatible-transitions
    prove-it-works
    type-system-discipline
    verify-the-negative-space
)

INLINED=(
    encode-lessons-in-structure
    exhaust-the-design-space
    guard-the-context-window
    laziness-protocol
    migrate-callers-then-delete-legacy-apis
)

in_list() {
    local needle="$1"
    shift
    local item
    for item in "$@"; do
        if [[ "$item" == "$needle" ]]; then
            return 0
        fi
    done
    return 1
}

strip_frontmatter() {
    awk '
        NR == 1 && $0 == "---" { in_fm = 1; next }
        in_fm && $0 == "---" { in_fm = 0; after_fm = 1; next }
        in_fm { next }
        after_fm && $0 == "" { next }
        { after_fm = 0; print }
    ' "$1"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

git clone --quiet --depth=1 --filter=blob:none --sparse -b "$BRANCH" "$REPO" "$tmp_dir"
git -C "$tmp_dir" sparse-checkout set "$UPSTREAM_PATH"

shopt -s nullglob
sources=("$tmp_dir/$UPSTREAM_PATH"/principle-*/)
if [[ ${#sources[@]} -eq 0 ]]; then
    echo "No principle-* skills found in $UPSTREAM_PATH" >&2
    exit 1
fi

backup_dir="${BACKUP_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/update-principles-backup.XXXXXX")}"
mkdir -p "$DEST" "$backup_dir"

for src in "${sources[@]}"; do
    name="$(basename "$src")"
    name="${name#principle-}"
    src_file="$src/SKILL.md"
    if [[ ! -f "$src_file" ]]; then
        continue
    fi

    if in_list "$name" "${INLINED[@]}"; then
        echo "Skipped (inlined): $name"
        continue
    fi

    if in_list "$name" "${LOCAL_OWNED[@]}"; then
        mkdir -p "$backup_dir/upstream-local"
        strip_frontmatter "$src_file" > "$backup_dir/upstream-local/$name.md"
        echo "Skipped (local): $name"
        continue
    fi

    if [[ -e "$DEST/$name.md" ]]; then
        mv "$DEST/$name.md" "$backup_dir/$name.md"
    fi
    if [[ -e "$DEST/$name" ]]; then
        mv "$DEST/$name" "$backup_dir/$name"
    fi

    strip_frontmatter "$src_file" > "$DEST/$name.md"
    perl -pi -e 's#\.\./principle-([a-z0-9-]+)/SKILL\.md#$1.md#g' "$DEST/$name.md"
    if grep -qE '\]\(\.\./' "$DEST/$name.md"; then
        echo "Warning: $name.md contains an external relative link; review manually" >&2
    fi
    echo "Updated: $name"
done

if [[ -n "$(ls -A "$backup_dir")" ]]; then
    echo "Backups and skipped upstream copies saved in $backup_dir"
else
    rmdir "$backup_dir"
fi

if [[ "$DEST" == "$SKILL_DIR/principles" ]]; then
    uv run --script "$SCRIPT_DIR/test_work.py"
fi
