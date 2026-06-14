#!/usr/bin/env bash
# Scanner inventory — gathers raw structural facts for the `scanner` skill to analyze.
# It does the deterministic work (walk, detect markers, compute the next report path);
# the skill does the judgement (classify, find anomalies, write the report).
#
# Output is grouped under ### SECTION headers for the model to parse.
set -uo pipefail

root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$root" || exit 1

reports_dir="logs/scanner_reports"

# Next report number: highest existing scan_NN.md + 1, zero-padded to 2 digits.
last=0
if [ -d "$reports_dir" ]; then
  for f in "$reports_dir"/scan_*.md; do
    [ -e "$f" ] || continue
    n="$(basename "$f" .md | sed -E 's/^scan_0*//')"
    [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -gt "$last" ] && last="$n"
  done
fi
next=$((last + 1))
printf -v padded "%02d" "$next"
next_report="$reports_dir/scan_${padded}.md"

# Heavy/generated directories to keep out of the structure and counts.
PRUNE='node_modules|\.git|dist|build|out|target|\.venv|venv|__pycache__|\.next|\.nuxt|\.gradle|Pods|DerivedData|\.idea|\.vscode|vendor|coverage|\.cache'

echo "### SCANNER_ROOT"
echo "$root"
echo

echo "### NEXT_REPORT"
echo "$next_report"
echo

echo "### MARKERS"  # manifest/build files that hint at the project type
for m in 'package.json' 'pnpm-lock.yaml' 'yarn.lock' 'package-lock.json' 'tsconfig.json' \
         'index.html' 'vite.config.*' 'next.config.*' 'angular.json' 'svelte.config.*' \
         'Cargo.toml' 'go.mod' 'pom.xml' 'build.gradle' 'settings.gradle' \
         'AndroidManifest.xml' 'Info.plist' 'Podfile' 'pubspec.yaml' \
         'requirements.txt' 'pyproject.toml' 'setup.py' 'Gemfile' 'composer.json' \
         'CMakeLists.txt' 'Makefile' 'project.godot' '*.uproject' '*.sln' '*.csproj' \
         '*.xcodeproj' '*.xcworkspace' 'Dockerfile' 'docker-compose.*' 'src-tauri'; do
  found="$(find . -maxdepth 4 -name "$m" 2>/dev/null | grep -Ev "/($PRUNE)(/|$)" | head -n 5)"
  [ -n "$found" ] && { echo "$m:"; echo "$found" | sed 's/^/  /'; }
done
echo

echo "### ASSET_DIRS"  # where asset-like folders live (for placement checks)
find . -type d \( -iname assets -o -iname static -o -iname public -o -iname resources \
   -o -iname images -o -iname img -o -iname media -o -iname fonts \) 2>/dev/null \
   | grep -Ev "/($PRUNE)(/|$)" | head -n 40
echo

echo "### FILE_COUNTS_BY_EXT"  # top extensions by file count
find . -type f 2>/dev/null | grep -Ev "/($PRUNE)(/|$)" | sed 's:.*/::' \
   | awk -F. 'NF>1{print "."$NF}' | sort | uniq -c | sort -rn | head -n 25
echo

echo "### TOTALS"
files="$(find . -type f 2>/dev/null | grep -Evc "/($PRUNE)(/|$)")"
dirs="$(find . -type d 2>/dev/null | grep -Evc "/($PRUNE)(/|$)")"
echo "files: $files"
echo "dirs:  $dirs"
echo

echo "### STRUCTURE"  # the bare tree (pruned), capped to keep it readable
if command -v tree >/dev/null 2>&1; then
  tree -a -F --dirsfirst -L 4 -I "$(echo "$PRUNE" | sed 's/\\//g')" | head -n 400
else
  find . 2>/dev/null | grep -Ev "/($PRUNE)(/|$)" | LC_ALL=C sort \
    | sed -E 's:[^/]*/:  :g' | head -n 400
fi
