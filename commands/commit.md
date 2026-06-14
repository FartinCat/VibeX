---
description: Plan atomic commits for the current changes and output copy-paste-ready git commands.
argument-hint: "[--run] [optional scope, path, or guidance]"
---

# /commit — Atomic commit plan

Group the current working-tree changes into **atomic commits** (one logical change
each) and produce a **copyable plan**. Follow the `atomic-commits` skill.

1. **Survey** the changes: `git status`, `git diff`, `git diff --staged`.
2. **Group** them into distinct logical changes; order so each commit is
   self-contained (prereqs/refactors first).
3. **Output the plan in copy-paste-ready form.** For every commit show its **related
   files** and a fenced `bash` block containing its `git add` + `git commit`
   commands (these render with a one-click copy button). Keep each block pure shell —
   no prose inside it. End with a single **copy-all** block that runs the whole plan
   in order. See the skill's "Output format (copyable plan)" section.

## Modes

- **Default (copy-only):** output the plan and stop. I copy and run the commands.
- **`--run` (when present in the arguments):** after showing the plan, execute the
  `git add` + `git commit` commands yourself, group by group, verifying
  `git diff --staged` before each commit. Never commit to `main`/`master`.

## Pushing — always on a tight leash

**Never `git push` on your own, in either mode.** If a push is wanted, STOP and ask
me first with `AskUserQuestion`, confirming **both**:

- **Which remote and branch** to push to.
- **Which identity** — show the current `git config user.email` and the target
  remote's URL so I can confirm the personal-vs-work context. I keep separate SSH
  keys (personal / work) and switch between Linux and Windows on the same machine, so
  the wrong identity or remote must never be assumed.

Only push after I explicitly confirm.

Scope / guidance for this run: $ARGUMENTS

