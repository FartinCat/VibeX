---
name: new-skill
description: Scaffold a new VibeX skill with a correct SKILL.md and folder layout. Use when the user wants to author, add, or create a new skill for the VibeX toolkit (or any Claude Code plugin).
---

# Authoring a new VibeX skill

Use this when adding a capability to the VibeX toolkit. Skills are **model-invoked**:
Claude decides to load one based on its `description`, so the description is the most
important field.

## Steps

1. **Name it.** Lowercase, hyphenated, verb-or-noun describing the capability
   (e.g. `commit-message`, `db-migration`, `api-scaffold`).

2. **Create the folder** under `skills/<name>/` containing `SKILL.md`. Supporting
   files (scripts, templates, references) go in the same folder and are loaded only
   when needed (progressive disclosure).

3. **Write the frontmatter:**
   ```yaml
   ---
   name: <name>
   description: <what it does> + <when to use it — the triggering conditions>
   ---
   ```
   The `description` MUST state *when* to invoke it, in the third person, with
   concrete trigger words. This is what makes the skill discoverable.

4. **Write the body** as concise, imperative instructions — the procedure Claude
   should follow. Keep it focused on one capability. Link to bundled files rather
   than inlining long references.

5. **Keep it lean.** A skill is guidance, not a manual. If it's getting long, split
   reference material into separate files in the skill folder.

## Checklist before finishing

- [ ] `description` clearly says *what* and *when*
- [ ] Body is imperative and scoped to one capability
- [ ] No secrets, no machine-specific absolute paths
- [ ] Folder name matches the `name` field
