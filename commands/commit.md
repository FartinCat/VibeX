---
description: Plan atomic commits for the current changes and output copy-paste-ready git commands.
argument-hint: "[optional scope, path, or guidance]"
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
4. **Do not commit or push automatically.** Let me copy and run the commands myself.
   Only run them if I explicitly say so — and never push, and never commit to
   `main`/`master`.

Scope / guidance for this run: $ARGUMENTS
