#!/usr/bin/env bash
# update upstream principles from pstack directly into principles directory
# without principles- prefix

set -euo pipefail

REPO="https://github.com/cursor/plugins.git"
BRANCH="main"
UPSTREAM_PATH="pstack/skills"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
DEST="$SKILL_DIR/principles"

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

mkdir -p "$DEST"
for src in "${sources[@]}"; do
    name="$(basename "$src")"
    name="${name#principle-}"
    rm -rf "${DEST:?}/$name"
    cp -R "$src" "$DEST/$name"
    # Follow the rename and the move: the skill name and links to sibling principles drop the
    # prefix, and links to other catalog skills climb out of work/principles/.
    sed -i -E 's/^name: principle-/name: /' "$DEST/$name/SKILL.md"
    find "$DEST/$name" -name '*.md' -exec perl -pi -e \
        's#\.\./(?!principle-)([a-z0-9-]+)/#../../../$1/#g; s#\.\./principle-#../#g' {} +
    echo "Updated: $name"
done
