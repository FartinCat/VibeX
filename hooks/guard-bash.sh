#!/usr/bin/env bash
# VibeX hard guardrail. Runs before every Bash tool call.
# Exit 2 = BLOCK the command (stderr is fed back to Claude). Exit 0 = allow.
#
# This is the "hard rules" layer. Unlike CLAUDE.md (advisory), these cannot be
# talked around — the command is denied before it runs.

set -euo pipefail

# The hook receives a JSON payload on stdin; the command is at .tool_input.command
input="$(cat)"
cmd="$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p')"

# Fallback: if extraction failed, allow (don't break the session on a parse miss).
[ -z "$cmd" ] && exit 0

block() {
  echo "VibeX guardrail blocked this command: $1" >&2
  exit 2
}

# 1. Never push directly to main/master.
if printf '%s' "$cmd" | grep -Eq 'git[[:space:]]+push.*(origin[[:space:]]+)?(main|master)\b'; then
  block "direct push to main/master. Open a branch and PR instead."
fi

# 2. Never force-push to main/master.
if printf '%s' "$cmd" | grep -Eq 'git[[:space:]]+push.*(--force|-f)\b.*(main|master)\b'; then
  block "force-push to a protected branch."
fi

# 3. Obvious filesystem-destroying commands.
if printf '%s' "$cmd" | grep -Eq 'rm[[:space:]]+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)[[:space:]]+(/|~|\$HOME)([[:space:]]|$)'; then
  block "recursive force-delete of a root/home path."
fi

exit 0
