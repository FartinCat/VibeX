# VibeX

A personal, version-controlled **agentic toolkit for Claude Code** — packaged as a
plugin so it can be installed once and reused across every project.

VibeX bundles a consistent "operating system" for Claude: curated skills, workflow
commands, specialized subagents, and a two-layer rule system (soft guidance + hard,
enforced guardrails).

## What's inside

| Path | Primitive | What it is |
|------|-----------|------------|
| `CLAUDE.md` | Memory | Soft operating principles — do's, don'ts, "instincts" (advisory) |
| `commands/` | Slash commands | User-invoked workflows. Type `/ship` to activate one |
| `skills/` | Skills | Model-invoked capabilities, loaded on demand (e.g. `new-skill`) |
| `agents/` | Subagents | Specialized delegates (e.g. `code-reviewer`) |
| `hooks/` | Hooks | **Hard** guardrails that BLOCK violations (e.g. no push to main) |
| `.claude-plugin/` | Manifest | Plugin + marketplace definitions |

### The soft / hard split

- **Soft (advisory):** `CLAUDE.md`. Claude reads it and usually follows it. Best for
  preferences and conventions.
- **Hard (enforced):** `hooks/`. These run code that can *deny* an action outright.
  Use them for rules that must never be violated. A sentence in CLAUDE.md cannot
  guarantee this; a hook can.

## Install

VibeX is a Claude Code plugin. From Claude Code:

```
/plugin marketplace add /path/to/VibeX
/plugin install vibex@vibex
```

This makes the commands, skills, agents, and hooks available globally across your
projects. To also load the `CLAUDE.md` principles globally, add an import to your
user memory (`~/.claude/CLAUDE.md`):

```
@/path/to/VibeX/CLAUDE.md
```

## Extending VibeX

Ask Claude to "create a new skill" — the bundled `new-skill` skill scaffolds it with
the correct layout. Add workflow commands under `commands/`, subagents under
`agents/`, and tighten guardrails in `hooks/guard-bash.sh`.

## Status

`v0.1.0` — scaffold. One working example of each primitive; ready to grow.
