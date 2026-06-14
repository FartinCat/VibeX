# VibeX Operating Principles

> Soft guidance layer. These are defaults and preferences, applied with judgment.
> Hard, non-negotiable rules live in `hooks/` (they BLOCK actions) — not here.

## Philosophy

- **Do the task, not a demo of the task.** Finish the thing; don't stop at a sketch.
- **Match the surrounding code.** Mirror existing naming, structure, and idioms before introducing new patterns.
- **Smallest change that fully solves it.** No speculative abstractions, no scope creep.
- **Read before you write.** Understand the existing file/module before editing it.

## Do's

- Prefer editing an existing file over creating a new one.
- Run the relevant tests/linters after a change and report the real result.
- State assumptions explicitly when a request is ambiguous, then proceed with the most reasonable one.
- Keep commits focused and messages descriptive (what + why).

## Don'ts

- Don't add comments that merely restate the code.
- Don't leave dead code, TODOs, or commented-out blocks behind.
- Don't claim something works unless it was actually run/verified.
- Don't introduce a dependency for something the stdlib/existing deps already do.

## Workflow conventions

- Branch for non-trivial work; never commit directly to `main`/`master`.
- Commit and push only when explicitly asked.
- When a workflow command (`/...`) is invoked, follow its documented steps in order.

---
*This file is the "instincts/rules" layer. Edit it freely — it ships with the VibeX plugin
and is meant to evolve as your preferences sharpen.*
