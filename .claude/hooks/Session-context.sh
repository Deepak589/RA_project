#!/usr/bin/env bash
# Token-minimal session context.
# Reads: graphify (state) + todo.md (top 5 open) + lessons.md (last 10 lines).
set -euo pipefail

branch=$(git branch --show-current 2>/dev/null || echo "?")

# Graphify — current project state (caps verbose output)
graph=""
if command -v graphify >/dev/null 2>&1; then
  graph=$(graphify status 2>/dev/null \
    || graphify summary 2>/dev/null \
    || graphify query --recent 2>/dev/null \
    || echo "")
fi
graph="${graph:0:1000}"

# Active todos — top 5 unchecked
todo=""
[ -f .claude/tasks/todo.md ] && todo=$(grep -m 5 -E '^\s*[-*]\s*\[ \]' .claude/tasks/todo.md 2>/dev/null || head -n 5 .claude/tasks/todo.md 2>/dev/null || echo "")

# Lessons — last 10 lines only, skip if file empty
lessons=""
if [ -f .claude/lessons.md ] && [ -s .claude/lessons.md ]; then
  lessons=$(tail -n 10 .claude/lessons.md 2>/dev/null || echo "")
fi

# Build context, skip empty sections
ctx="branch:${branch}"
[ -n "$graph" ] && ctx="${ctx}

graphify:
${graph}"
[ -n "$todo" ] && ctx="${ctx}

todo:
${todo}"
[ -n "$lessons" ] && ctx="${ctx}

lessons (avoid repeating):
${lessons}"

# Hard cap
ctx="${ctx:0:1800}"

if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$ctx" '{additionalContext: $c}'
else
  esc=$(printf '%s' "$ctx" | python3 -c 'import sys,json;print(json.dumps(sys.stdin.read()))')
  printf '{"additionalContext": %s}\n' "$esc"
fi