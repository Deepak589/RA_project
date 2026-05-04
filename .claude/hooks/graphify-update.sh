#!/usr/bin/env bash
# Refresh graphify after Claude edits. Print reminder to your terminal.
# Reminder goes to stderr — visible to YOU, not fed to Claude (zero tokens).
set -euo pipefail

# Only fire if Claude edited something
if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
  exit 0
fi

# Refresh graph in background, non-blocking
# with:
GRAPHIFY="$(pwd)/node_modules/.bin/graphify"
if [ -x "$GRAPHIFY" ]; then
  ("$GRAPHIFY" update . >/dev/null 2>&1 &) || true
fi

# Nudge — your terminal only, not Claude's context
files_changed=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "$files_changed" -gt 0 ]; then
  echo "" >&2
  echo "  reminder: ${files_changed} file(s) changed" >&2
  echo "  → check off done items in .claude/tasks/todo.md" >&2
  echo "  → log lessons:  bash .claude/hooks/add-lesson.sh \"<takeaway>\"" >&2
  echo "" >&2
fi

exit 0  