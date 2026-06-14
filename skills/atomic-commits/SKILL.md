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

2. **Plan the commits.** Read the diff and list the distinct logical groups out loud,
   e.g. "(1) fix off-by-one in pager, (2) rename `cfg`→`config`, (3) add CHANGELOG
   entry". Decide commit order so each one is self-contained — usually
   prerequisites/refactors first, then the feature that uses them.

3. **For each group, in order:**
   - **Stage precisely** (see below) — only the hunks for *this* concern.
   - **Verify the staged set** matches exactly one concern, nothing extra:
     ```
     git diff --staged
     ```
   - **Commit** with a focused message:
     ```
     git commit -m "Subject" -m "Body explaining what + why"
     ```

4. **Repeat** until the tree is clean:
   ```
   git status --porcelain   # empty output = done
   ```

5. **Respect the guardrails.** Branch for non-trivial work — never commit straight to
   `main`/`master`. Do NOT `git push` unless the user explicitly asked.

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
