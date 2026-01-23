#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")/skill"

SKILLS=(
	"https://github.com/anthropics/skills/tree/main/skills/skill-creator"
)

mkdir -p "$SKILL_DIR"

for url in "${SKILLS[@]}"; do
	[[ "$url" =~ github\.com/([^/]+/[^/]+)/tree/([^/]+)/(.+) ]] || continue
	repo="${BASH_REMATCH[1]}" branch="${BASH_REMATCH[2]}" path="${BASH_REMATCH[3]}"
	skill_name="$(basename "$path")"
	tmp_dir="/tmp/skill-$$"

	rm -rf "$tmp_dir"
	git clone --depth=1 --filter=blob:none --sparse -b "$branch" \
		"https://github.com/$repo.git" "$tmp_dir" 2>/dev/null
	git -C "$tmp_dir" sparse-checkout set "$path" 2>/dev/null

	if [[ -d "$tmp_dir/$path" ]]; then
		rm -rf "$SKILL_DIR/$skill_name"
		cp -R "$tmp_dir/$path" "$SKILL_DIR/$skill_name"
		echo "Updated: $skill_name"
	else
		echo "Failed: $url" >&2
	fi
	rm -rf "$tmp_dir"
done
