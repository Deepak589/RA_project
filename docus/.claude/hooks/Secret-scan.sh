#!/usr/bin/env bash
# Block writes containing secrets. Hooks receive JSON on stdin.
set -euo pipefail

input=$(cat)
paths=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty')

[ -z "$paths" ] && exit 0

for p in $paths; do
  [ ! -f "$p" ] && continue

  # Skip the .env.example template and docs about secrets
  case "$p" in
    *.env.example|*README*|*.md) continue ;;
  esac

  # Patterns: AWS keys, generic API keys, JWT secrets, postgres URLs with password,
  # USDA FDC api keys (long alphanumeric in DEMO/USDA_API_KEY context), bearer tokens
  if grep -E -n \
    -e 'AKIA[0-9A-Z]{16}' \
    -e '(api[_-]?key|secret|password|token)["'"'"' :=]+["'"'"' ]?[A-Za-z0-9_\-]{24,}' \
    -e 'postgres(ql)?://[^:]+:[^@]{6,}@' \
    -e 'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}' \
    -e 'USDA_API_KEY=[A-Za-z0-9]{20,}' \
    "$p" >&2; then
    echo "blocked: secret-like value in $p" >&2
    exit 2
  fi
done

exit 0