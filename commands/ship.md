---
description: Run the pre-ship workflow — lint, test, review, and prepare a commit.
argument-hint: "[optional scope or message]"
---

# /ship — Pre-ship workflow

Activate the standard "ready to ship" pipeline for the current changes. Work through
these steps in order and report the outcome of each; stop and surface any failure
rather than pushing past it.

1. **Survey the diff.** Run `git status` and `git diff` to see exactly what changed.
2. **Lint & format.** Detect and run the project's linter/formatter. Fix what's safe.
3. **Test.** Detect and run the relevant test suite. Report pass/fail with real output.
4. **Self-review.** Re-read the diff for the don'ts in CLAUDE.md (dead code, stray
   TODOs, restate-the-code comments, unverified claims).
5. **Prepare commit.** Draft a focused commit message (what + why). Do NOT commit or
   push unless the user explicitly asked.

Context for this run: $ARGUMENTS
