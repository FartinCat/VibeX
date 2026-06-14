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

# 4. Push identity gate (opt-in). If a push-policy.conf exists next to this script,
#    enforce that the git user.email matches the target remote — stops personal/work
#    identities from crossing. No policy file = gate off.
policy="$(dirname "$0")/push-policy.conf"
if [ -f "$policy" ] && printf '%s' "$cmd" | grep -Eq '\bgit\b.*\bpush\b'; then
  # Target remote: first non-flag token after 'push', else the branch upstream,
  # else 'origin'.
  remote="$(printf '%s' "$cmd" | sed -E 's/.*\bpush\b//' \
            | tr ' \t' '\n' | grep -Ev '^(-.*)?$' | head -n1 || true)"
  [ -z "$remote" ] && remote="$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null | cut -d/ -f1 || true)"
  [ -z "$remote" ] && remote="origin"

  url="$(git remote get-url "$remote" 2>/dev/null || true)"
  [ -z "$url" ] && block "push to unknown remote '$remote' — can't verify identity. Confirm the destination first."

  email="$(git config user.email 2>/dev/null || true)"

  expected=""
  while IFS= read -r line; do
    case "$line" in ''|\#*) continue;; esac
    pat="$(printf '%s' "$line" | awk '{print $1}')"
    if printf '%s' "$url" | grep -qF "$pat"; then
      expected="$(printf '%s' "$line" | awk '{print $2}')"
      break
    fi
  done < "$policy"

  [ -z "$expected" ] && block "remote '$remote' ($url) is not listed in hooks/push-policy.conf. Confirm the destination and add it before pushing."
  [ "$email" != "$expected" ] && block "identity mismatch — git user.email is '$email' but '$remote' ($url) requires '$expected'. Fix: git config user.email '$expected'"
fi

exit 0
