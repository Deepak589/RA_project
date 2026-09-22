#!/usr/bin/env bash
# Append a lesson to .claude/lessons.md with today's date.
# Auto-rotates to lessons.archive.md when file exceeds 200 lines.
# Usage: ./add-lesson.sh "Don't reuse alembic migration numbers"
set -euo pipefail

if [ $# -eq 0 ]; then
  echo "usage: $0 \"lesson text\"" >&2
  exit 1
fi

lesson="$*"
file=".claude/lessons.md"
archive=".claude/lessons.archive.md"

[ ! -f "$file" ] && touch "$file"

date=$(date +%Y-%m-%d)
echo "${date}: ${lesson}" >> "$file"

# Rotate if needed
lines=$(wc -l < "$file")
if [ "$lines" -gt 200 ]; then
  # Move oldest 100 lessons to archive (skip the header lines)
  head -n 100 "$file" >> "$archive"
  tail -n +101 "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
  echo "rotated 100 old lessons → $archive" >&2
fi

echo "logged: ${lesson}"