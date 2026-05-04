#!/usr/bin/env bash
# Format + lint touched files. Skip silently if tool missing.
set -euo pipefail

input=$(cat)
paths=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty')

[ -z "$paths" ] && exit 0

for p in $paths; do
  [ ! -f "$p" ] && continue

  case "$p" in
    *.py)
      command -v ruff >/dev/null 2>&1 && ruff format "$p" >/dev/null 2>&1 || true
      command -v ruff >/dev/null 2>&1 && ruff check --fix "$p" >/dev/null 2>&1 || true
      ;;
    *.js|*.jsx|*.ts|*.tsx|*.json|*.css|*.md)
      if [ -f frontend/package.json ] && command -v npx >/dev/null 2>&1; then
        (cd frontend && npx --no-install prettier --write "../$p" >/dev/null 2>&1) || true
      fi
      ;;
  esac
done

exit 0