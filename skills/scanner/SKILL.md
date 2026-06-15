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

3. **Check imports exhaustively** (JS/TS + Python). Run the bundled checker (needs
   `python3`):
   ```
   python3 import_graph.py
   ```
   It builds the real import graph and resolves every edge, then prints
   `### IMPORT_GRAPH` (per-language tier + edge stats), `### BROKEN_IMPORTS`,
   `### CASE_MISMATCH` (imports that only work on case-insensitive filesystems — they
   break on Linux), `### MISSING_DEPS`, `### UNVERIFIED`, and an `### EDGES_JSON`
   artifact. It prefers the native toolchain (Tier 1, e.g. `tsc`) and falls back to a
   built-in resolver (Tier 2); the `tier=` field says which ran. Each finding carries
   a confidence tag — surface the high-confidence ones first. Save the `### EDGES_JSON`
   block to `<NEXT_REPORT minus .md>.imports.json` (e.g. `scan_03.imports.json`).

4. **Hunt other anomalies.** Use the inventory plus targeted `Grep`/`Read` to check:
   - **Asset placement** — asset folders (`### ASSET_DIRS`) in the conventional spot
     for this project type (e.g. web `public/`/`src/assets`, Android `res/`,
     Unity `Assets/`). Flag stray, duplicated, or deeply-nested asset dirs.
   - **Other-language imports** — for C/C++/Go/Rust/Java/C# (not covered by the
     checker), spot-check `include`/`use`/`import` statements against the filesystem,
     or run that language's native check (`go list ./...`, `cargo check`) if present.
   - **File / naming mismatches** — extension vs content (e.g. JSX in a `.js` under a
     TS project), files outside their conventional dir (tests, components), casing
     inconsistencies.
   - **Config & dependency drift** — multiple lockfiles, manifest referencing missing
     paths, missing entrypoint/README, empty or orphaned directories.
   Only report findings you can substantiate; cite `path:line` where relevant.

5. **Write the report** to the `### NEXT_REPORT` path using the template below. Never
   overwrite an existing `scan_NN.md` — always use the path the script computed.

6. **Summarize to the user**: project type, the top findings by severity, and the
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

## Imports
- Tiers: js_ts=<tier>, python=<tier>
- Edges: N (internal/external/builtin/missing/unresolved)
- Broken imports & case mismatches: <count> (details under Findings)
- Full graph: `scan_NN.imports.json`

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
- `inventory.sh` and `import_graph.py` only read and report — they never modify the
  project.
- `import_graph.py` covers JS/TS + Python today. Tier 1 (native `tsc`) is best-effort:
  it's skipped/labelled honestly when the toolchain is absent or the project's
  tsconfig aborts it, and bare-package `tsc` errors are ignored unless `node_modules`
  is installed (so declared-but-uninstalled deps aren't false-flagged). Tier 2 (the
  built-in resolver) always runs.
