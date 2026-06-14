---
name: atomic-commits
description: Split working-tree changes into atomic commits — one logical change per commit, each with a clear what+why message. Use when the user asks to commit, wants atomic/granular/clean commits, or the working tree mixes several unrelated changes.
---

# Atomic commits

Turn the current changes into a series of **atomic commits**: each commit captures
exactly one logical change, stands on its own, and reads clearly in `git log`. The
hard part is not committing — it's *separating* unrelated changes that happen to sit
in the working tree together.

## What "atomic" means

- **One concern per commit.** A bug fix, a rename, a new helper, a formatting pass —
  each is its own commit, never blended.
- **Self-contained.** Each commit should leave the repo in a working state (builds /
  tests pass). Never split a change so that an intermediate commit is broken.
- **Don't mix:** behavior changes with refactors, logic with reformatting, unrelated
  features, or "drive-by" edits with the main change.
- **Message = what + why.** The diff shows *how*; the message explains *what* changed
  and *why* it was needed.

## Procedure

1. **Survey everything.** See the full picture before touching the index:
   ```
   git status
   git diff            # unstaged
   git diff --staged   # already staged
   ```

2. **Plan the commits.** Read the diff and group it into distinct logical changes,
   e.g. "(1) fix off-by-one in pager, (2) rename `cfg`→`config`, (3) add CHANGELOG
   entry". Decide commit order so each one is self-contained — usually
   prerequisites/refactors first, then the feature that uses them.

3. **Present the plan as a copyable block** (see [Output format](#output-format-copyable-plan)).
   Each commit lists its related files and a ready-to-run `git add` + `git commit`
   block the user can copy with one click, plus a single "copy-all" block.

4. **Then either** run the commands yourself (only if the user asked you to commit)
   **or** let the user copy and run them. When you run them, do it group by group and
   **verify the staged set** before each commit — exactly one concern, nothing extra:
   ```
   git diff --staged
   ```

5. **Repeat** until the tree is clean:
   ```
   git status --porcelain   # empty output = done
   ```

6. **Respect the guardrails.** Branch for non-trivial work — never commit straight to
   `main`/`master`. **Never `git push` on your own.** Before any push, confirm with
   the user **which remote and branch**, and surface the current
   `git config user.email` plus the target remote's URL so they can confirm the
   identity is correct — when a machine has multiple remotes or SSH keys (e.g.
   personal vs work), never assume the destination or identity.

## Output format (copyable plan)

Always present the result so the commands are **copy-paste runnable**. Put every
command in a fenced `bash` block (IDEs render these with a one-click copy button).
Do not interleave prose inside the block — keep it pure shell so it runs as-is.

For each atomic commit, show its **related files** and its block:

> **Commit 1 — Fix pager off-by-one**
> Files: `src/pager.py`
> ```bash
> git add src/pager.py
> git commit -m "Fix pager off-by-one" \
>   -m "Page boundary was inclusive and dropped the last row; make it exclusive."
> ```
>
> **Commit 2 — Rename cfg to config**
> Files: `src/config.py`, `src/main.py`
> ```bash
> git add src/config.py src/main.py
> git commit -m "Rename cfg to config for clarity"
> ```

Then end with one **copy-all** block that runs the whole plan in order:

```bash
git add src/pager.py
git commit -m "Fix pager off-by-one" \
  -m "Page boundary was inclusive and dropped the last row; make it exclusive."

git add src/config.py src/main.py
git commit -m "Rename cfg to config for clarity"
```

When a commit needs a sub-file split, put its staging steps in the same block:
```bash
git diff -- src/big.py > /tmp/commit3.patch   # then trim to this concern's hunks
git apply --cached /tmp/commit3.patch
git commit -m "Extract retry helper"
```

## Staging precisely

**Whole files** (the common case — each file belongs to a single concern):
```
git add path/to/a path/to/b
```

**Part of a file** (one file holds several concerns — stage only some hunks). Claude
runs git non-interactively, so do NOT rely on `git add -p`'s prompts. Instead, split
via a patch:
```
git diff -- path/to/file > /tmp/change.patch   # capture the unstaged diff
# Edit /tmp/change.patch down to only the hunks for THIS concern
#   (keep the diff/---/+++/@@ headers intact; delete the other hunks)
git apply --cached /tmp/change.patch           # stage just those hunks
```
The remaining hunks stay unstaged for the next commit. (`git add -p` is the
interactive equivalent for a human at a terminal.)

**New/untracked files:** `git add path/to/new_file`.
**Deletions & renames:** `git add -A path/...` stages them; verify with `git status`.

## Commit messages

- **Subject:** imperative mood, ~50 chars, no trailing period. "Fix pager off-by-one",
  not "Fixed" / "Fixes". An optional type prefix (`fix:`, `feat:`, `refactor:`,
  `docs:`, `test:`, `chore:`) is fine if the project already uses one — match the repo.
- **Body** (when the change isn't self-evident): blank line, then *what* and *why*,
  wrapped ~72 cols. Skip the body for trivial commits.
- Match the surrounding `git log` style before imposing a new convention.

## Checklist before each commit

- [ ] `git diff --staged` shows exactly one concern — nothing unrelated rode along
- [ ] The change is complete on its own (no half-staged function that won't build)
- [ ] Subject is imperative and specific; body explains *why* if non-obvious
- [ ] Not on `main`/`master`; not pushing unless asked
