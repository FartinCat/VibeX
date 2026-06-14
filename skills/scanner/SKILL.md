---
name: scanner
description: Scan a project's whole directory tree, classify what kind of project it is, flag structural anomalies (misplaced asset folders, broken imports, file/naming mismatches), and write a timestamped report to logs/scanner_reports/scan_NN.md. Use when the user asks to scan, audit, or map the project structure, identify the project type, or check the repo for layout problems.
---

# Scanner

Produce a complete picture of a project's structure, identify what it is, surface
anomalies, and persist a numbered report. The deterministic walk is done by the
bundled `inventory.sh`; your job is the analysis and the write-up.

## Procedure

1. **Gather facts.** Run the bundled script (it lives in this skill's folder):
   ```
   bash inventory.sh
   ```
   It prints `### SCANNER_ROOT`, `### NEXT_REPORT` (the exact path to write — already
   incremented, e.g. `logs/scanner_reports/scan_03.md`), `### MARKERS`,
   `### ASSET_DIRS`, `### FILE_COUNTS_BY_EXT`, `### TOTALS`, and `### STRUCTURE`.

2. **Classify the project type.** Map the `### MARKERS` to a type using
   [project-types.md](project-types.md). State a confidence level and the evidence.
   If it's a monorepo, classify each workspace.

3. **Hunt anomalies.** Use the inventory plus targeted `Grep`/`Read` to check:
   - **Asset placement** — asset folders (`### ASSET_DIRS`) in the conventional spot
     for this project type (e.g. web `public/`/`src/assets`, Android `res/`,
     Unity `Assets/`). Flag stray, duplicated, or deeply-nested asset dirs.
   - **Broken/wrong imports** — spot-check `import`/`require`/`include`/`#include`
     statements that point at relative paths or modules that don't exist on disk.
   - **File / naming mismatches** — extension vs content (e.g. JSX in a `.js` under a
     TS project), files outside their conventional dir (tests, components), casing
     inconsistencies.
   - **Config & dependency drift** — multiple lockfiles, manifest referencing missing
     paths, missing entrypoint/README, empty or orphaned directories.
   Only report findings you can substantiate; cite `path:line` where relevant.

4. **Write the report** to the `### NEXT_REPORT` path using the template below. Never
   overwrite an existing `scan_NN.md` — always use the path the script computed.

5. **Summarize to the user**: project type, the top findings by severity, and the
   report path.

## Report template

```markdown
# Scan NN — <project name>

- **Scanned:** <ISO date>
- **Root:** <SCANNER_ROOT>
- **Project type:** <type> (confidence: high/medium/low)

## Evidence
<markers that drove the classification>

## Structure
<the pruned tree from ### STRUCTURE>

## Findings
### Critical
- ...
### Warnings
- ...
### Notes
- ...

## Stats
- Files: N, Dirs: N
- Top extensions: ...

## Recommendations
- <actionable next steps, most impactful first>
```

## Notes

- The script prunes heavy/generated dirs (`node_modules`, `.git`, `dist`, `target`,
  `Pods`, …) so the tree stays about the source, not dependencies.
- Reports accumulate under `logs/scanner_reports/`. Suggest gitignoring that folder
  if the user doesn't want scan history committed.
- `inventory.sh` only reads and reports — it never modifies the project.
