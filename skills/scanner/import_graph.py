#!/usr/bin/env python3
"""Scanner import-graph checker — Tier 1 (native toolchain) + Tier 2 (built-in resolver).

Read-only. Builds the project's import graph for JS/TS and Python, resolves every
edge against the real filesystem, and reports broken imports, case mismatches (which
break on case-sensitive filesystems like Linux), and undeclared dependencies.

Prints ### SECTION blocks for the `scanner` skill to fold into its report, ending
with an ### EDGES_JSON machine-readable artifact. Never modifies the project.

Usage: import_graph.py [root]   (defaults to the git toplevel, else CWD)
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import time

PRUNE = {"node_modules", ".git", "dist", "build", "out", "target", ".venv", "venv",
         "__pycache__", ".next", ".nuxt", ".gradle", "Pods", "DerivedData", ".idea",
         ".vscode", "vendor", "coverage", ".cache"}

JS_SRC_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
JS_RESOLVE_EXTS = [".ts", ".tsx", ".d.ts", ".js", ".jsx", ".mjs", ".cjs", ".json"]

NODE_BUILTINS = {
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console",
    "constants", "crypto", "dgram", "diagnostics_channel", "dns", "domain", "events",
    "fs", "http", "http2", "https", "inspector", "module", "net", "os", "path",
    "perf_hooks", "process", "punycode", "querystring", "readline", "repl", "stream",
    "string_decoder", "sys", "timers", "tls", "trace_events", "tty", "url", "util",
    "v8", "vm", "wasi", "worker_threads", "zlib",
}


def find_root():
    if len(sys.argv) > 1:
        return os.path.abspath(sys.argv[1])
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      stderr=subprocess.DEVNULL).decode().strip()
        if out:
            return out
    except Exception:
        pass
    return os.getcwd()


ROOT = find_root()
os.chdir(ROOT)

ALL_FILES = set()   # relative posix paths, exact case
ALL_DIRS = set()    # relative posix dir paths
LOWER_MAP = {}      # lowercased path -> actual-case path


def index_tree():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in PRUNE]
        rd = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
        if rd != ".":
            ALL_DIRS.add(rd)
        for fn in filenames:
            rel = (fn if rd == "." else f"{rd}/{fn}")
            ALL_FILES.add(rel)
            LOWER_MAP.setdefault(rel.lower(), rel)


def read(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


# ---- manifests -------------------------------------------------------------

def loose_json(text):
    """Parse JSON that may carry // and /* */ comments and trailing commas (tsconfig)."""
    try:
        return json.loads(text)
    except Exception:
        pass
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    try:
        return json.loads(text)
    except Exception:
        return None


def collect_node_deps():
    deps, have_manifest = set(), False
    for f in ALL_FILES:
        if f == "package.json" or f.endswith("/package.json"):
            data = loose_json(read(f))
            if not isinstance(data, dict):
                continue
            have_manifest = True
            for key in ("dependencies", "devDependencies", "peerDependencies",
                        "optionalDependencies"):
                deps.update((data.get(key) or {}).keys())
    return (deps if have_manifest else None)


def collect_tsconfig():
    cfgs = sorted([f for f in ALL_FILES
                   if f == "tsconfig.json" or f.endswith("/tsconfig.json")],
                  key=len)
    if not cfgs:
        return ".", {}, None
    cfg_path = cfgs[0]
    data = loose_json(read(cfg_path)) or {}
    opts = data.get("compilerOptions", {}) if isinstance(data, dict) else {}
    cfg_dir = os.path.dirname(cfg_path)
    base_url = os.path.normpath(os.path.join(cfg_dir, opts.get("baseUrl", "."))).replace(os.sep, "/")
    if base_url == ".":
        base_url = ""
    return base_url, (opts.get("paths") or {}), cfg_path


def collect_py_deps():
    names = set()
    for f in ALL_FILES:
        base = f.rsplit("/", 1)[-1]
        if base == "requirements.txt" or (base.startswith("requirements") and base.endswith(".txt")):
            for line in read(f).splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "-")):
                    pkg = re.split(r"[<>=!~;\[ ]", line, 1)[0]
                    if pkg:
                        names.add(pkg.lower().replace("_", "-"))
        elif base == "pyproject.toml":
            for m in re.finditer(r'["\']([A-Za-z0-9._-]+)\s*(?:[<>=!~\[ ].*)?["\']', read(f)):
                names.add(m.group(1).lower().replace("_", "-"))
    return names


# ---- JS/TS extraction + resolution ----------------------------------------

JS_PATTERNS = [
    re.compile(r"""\bfrom\s+['"`]([^'"`]+)['"`]"""),
    re.compile(r"""\bimport\s+['"`]([^'"`]+)['"`]"""),
    re.compile(r"""\brequire\s*\(\s*['"`]([^'"`]+)['"`]\s*\)"""),
    re.compile(r"""\bimport\s*\(\s*['"`]([^'"`]+)['"`]\s*\)"""),
]


def js_specs(path):
    out = []
    for i, line in enumerate(read(path).splitlines(), 1):
        if "//" in line:
            line = line[:line.index("//")]
        seen = set()
        for pat in JS_PATTERNS:
            for m in pat.finditer(line):
                spec = m.group(1)
                if spec not in seen:
                    seen.add(spec)
                    out.append((i, spec))
    return out


def pkg_name(spec):
    if spec.startswith("@"):
        return "/".join(spec.split("/")[:2])
    return spec.split("/")[0]


def resolve_target(raw):
    raw = raw.lstrip("/")
    if not raw or raw.startswith(".."):
        return ("oob", None)
    cands = [raw] + [raw + e for e in JS_RESOLVE_EXTS] + \
            [f"{raw}/index{e}" for e in JS_RESOLVE_EXTS]
    for c in cands:
        if c in ALL_FILES:
            return ("ok", c)
    if raw in ALL_DIRS and f"{raw}/package.json" in ALL_FILES:
        return ("ok", f"{raw}/package.json")
    for c in cands:
        hit = LOWER_MAP.get(c.lower())
        if hit:
            return ("case", hit)
    return ("broken", None)


def resolve_alias(spec, base_url, paths):
    for pattern, targets in paths.items():
        if "*" in pattern:
            pre, post = pattern.split("*", 1)
            if spec.startswith(pre) and spec.endswith(post) and \
                    len(spec) >= len(pre) + len(post):
                star = spec[len(pre): len(spec) - len(post) or None]
                for t in targets:
                    raw = os.path.normpath(os.path.join(
                        base_url, t.replace("*", star))).replace(os.sep, "/")
                    status, hit = resolve_target(raw)
                    if status in ("ok", "case"):
                        return (status, hit)
                return ("broken", None)
        elif spec == pattern:
            for t in targets:
                raw = os.path.normpath(os.path.join(base_url, t)).replace(os.sep, "/")
                status, hit = resolve_target(raw)
                if status in ("ok", "case"):
                    return (status, hit)
            return ("broken", None)
    return None


# ---- Python extraction + resolution ---------------------------------------

def py_resolve_abs(module, src_roots, stdlib, py_deps):
    modpath = module.replace(".", "/")
    top = module.split(".")[0]
    top_internal = False
    for r in src_roots:
        base = f"{r}/{modpath}" if r else modpath
        if f"{base}.py" in ALL_FILES or f"{base}/__init__.py" in ALL_FILES or base in ALL_DIRS:
            return ("ok", None)
        tbase = f"{r}/{top}" if r else top
        if f"{tbase}.py" in ALL_FILES or f"{tbase}/__init__.py" in ALL_FILES or tbase in ALL_DIRS:
            top_internal = True
    if top_internal:
        return ("broken", None)  # internal package, but this submodule path is missing
    if top in stdlib:
        return ("builtin", None)
    if top.lower().replace("_", "-") in py_deps:
        return ("external", None)
    return ("missing", None)


def py_resolve_rel(file_rel, module, level):
    base = os.path.dirname(file_rel)
    for _ in range(level - 1):
        base = os.path.dirname(base)
        if base == "" and level > 1:
            return ("oob", None)
    if module:
        target = os.path.join(base, module.replace(".", "/")).replace(os.sep, "/").lstrip("/")
        if f"{target}.py" in ALL_FILES or f"{target}/__init__.py" in ALL_FILES or target in ALL_DIRS:
            return ("ok", None)
        return ("broken", None)
    # `from . import x` — verify the referenced package directory exists
    if base == "" or base in ALL_DIRS:
        return ("ok", None)
    return ("broken", None)


# ---- Tier 1: native toolchain ---------------------------------------------

def tier1_tsc(tsconfig):
    """Returns (status, hits). status: 'ok' | 'config_error' | 'unavailable'.
    A config error (e.g. deprecated option) can abort tsc before resolution, so we
    distinguish it from a clean run and never claim native coverage we didn't get."""
    if not tsconfig:
        return ("unavailable", [])
    if shutil.which("tsc"):
        base = ["tsc"]
    elif shutil.which("npx"):
        base = ["npx", "--no-install", "tsc"]
    else:
        return ("unavailable", [])

    def run(extra):
        cmd = base + ["--noEmit", "--skipLibCheck"] + extra + ["-p", tsconfig]
        try:
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
        except Exception:
            return None
        return (proc.stdout or "") + (proc.stderr or "")

    out = run(["--ignoreDeprecations", "6.0"])
    if out is None:
        return ("unavailable", [])
    if "TS5023" in out:  # this tsc version rejects --ignoreDeprecations; retry without it
        retry = run([])
        if retry is not None:
            out = retry

    rx = re.compile(r"^(.*?)\((\d+),\d+\):\s*error TS2307:\s*Cannot find module ['\"]([^'\"]+)['\"]")
    hits = []
    for line in out.splitlines():
        m = rx.match(line.strip())
        if m:
            hits.append((m.group(1).replace(os.sep, "/"), int(m.group(2)), m.group(3)))
    if hits:
        return ("ok", hits)
    if re.search(r"error TS(5\d{3}|6053|18002|18003|18004)\b", out):
        return ("config_error", [])
    return ("ok", [])


# ---- main ------------------------------------------------------------------

def main():
    index_tree()
    node_deps = collect_node_deps()
    base_url, ts_paths, tsconfig = collect_tsconfig()
    py_deps = collect_py_deps()
    stdlib = set(getattr(sys, "stdlib_module_names", ()))

    src_roots = [""]
    if "src" in ALL_DIRS:
        src_roots.append("src")

    broken, case_mismatch, missing, unverified, edges = [], [], [], [], []
    counts = {"internal": 0, "external": 0, "builtin": 0, "missing": 0, "unresolved": 0}

    js_files = sorted(f for f in ALL_FILES if f.endswith(JS_SRC_EXTS) and not f.endswith(".d.ts"))
    py_files = sorted(f for f in ALL_FILES if f.endswith(".py"))

    # Tier 1 (native): run tsc, keep only *reliable* TS2307 module-not-found errors.
    nm_present = os.path.isdir(os.path.join(ROOT, "node_modules"))
    tsc_status, tsc_raw = tier1_tsc(tsconfig)

    def tsc_reliable(spec):
        if spec.startswith((".", "/")):
            return True  # relative paths: tsc is authoritative regardless of deps
        if ts_paths and resolve_alias(spec, base_url, ts_paths) is not None:
            return True  # aliases resolve via tsconfig, not node_modules
        return nm_present  # bare specifier: trust tsc only if deps are installed

    tsc_set = {(f, ln, s) for (f, ln, s) in tsc_raw if tsc_reliable(s)}
    if tsc_status == "ok":
        js_tier = "native+builtin"
    elif tsc_status == "config_error":
        js_tier = "builtin (tsc aborted: config error)"
    else:
        js_tier = "builtin (tsc unavailable)"

    # Tier 2 (built-in resolver) for JS/TS.
    cls = {}
    for f in js_files:
        base = os.path.dirname(f)
        for ln, spec in js_specs(f):
            kind = status = resolved = None
            if spec.startswith((".", "/")):
                raw = os.path.normpath(os.path.join(base, spec)).replace(os.sep, "/")
                status, resolved = resolve_target(raw)
                kind = "internal"
            else:
                alias = resolve_alias(spec, base_url, ts_paths) if ts_paths else None
                if alias is not None:
                    status, resolved = alias
                    kind = "internal"
                else:
                    kind = "external"
                    name = pkg_name(spec)
                    if spec.startswith("node:") or name in NODE_BUILTINS:
                        status, kind = "builtin", "builtin"
                    elif node_deps is None:
                        status = "unverified"
                    elif name in node_deps:
                        status = "ok"
                    else:
                        status = "missing"

            cls[(f, ln, spec)] = status
            edges.append({"from": f, "line": ln, "spec": spec, "kind": kind, "status": status})
            if status == "ok":
                counts["internal" if kind == "internal" else "external"] += 1
            elif status == "builtin":
                counts["builtin"] += 1
            elif status == "case":
                counts["unresolved"] += 1
                case_mismatch.append((f, ln, spec, resolved))
            elif status == "broken":
                counts["unresolved"] += 1
                note = "tsc-confirmed" if (f, ln, spec) in tsc_set else "unresolved relative/alias"
                broken.append((f, ln, spec, "js", "high", note))
            elif status == "missing":
                counts["missing"] += 1
                missing.append((f, ln, spec, "js", "medium"))
            elif status in ("unverified", "oob"):
                reason = "no manifest to verify" if status == "unverified" else "resolves outside project root"
                unverified.append((f, ln, spec, reason))

    # Tier 1 catches broken edges Tier 2 couldn't confirm (exports maps, unverified).
    for (f, ln, s) in sorted(tsc_set):
        if cls.get((f, ln, s)) in (None, "unverified", "oob"):
            counts["unresolved"] += 1
            broken.append((f, ln, s, "js", "high", "tsc TS2307"))

    # Tier 2 for Python (ast-based).
    for f in py_files:
        src = read(f)
        try:
            tree = ast.parse(src, filename=f)
        except SyntaxError:
            unverified.append((f, 0, "", "unparseable (syntax error)"))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    st, _ = py_resolve_abs(alias.name, src_roots, stdlib, py_deps)
                    edges.append({"from": f, "line": node.lineno, "spec": alias.name,
                                  "kind": "python", "status": st})
                    _tally_py(st, f, node.lineno, alias.name, counts, broken, missing)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if node.level > 0:
                    st, _ = py_resolve_rel(f, node.module, node.level)
                    spec = "." * node.level + mod
                else:
                    st, _ = py_resolve_abs(mod, src_roots, stdlib, py_deps)
                    spec = mod
                edges.append({"from": f, "line": node.lineno, "spec": spec,
                              "kind": "python", "status": st})
                _tally_py(st, f, node.lineno, spec, counts, broken, missing)

    emit(js_tier, len(js_files), len(py_files), counts,
         broken, case_mismatch, missing, unverified, edges)


def _tally_py(st, f, ln, spec, counts, broken, missing):
    if st == "ok":
        counts["internal"] += 1
    elif st == "external":
        counts["external"] += 1
    elif st == "builtin":
        counts["builtin"] += 1
    elif st == "broken":
        counts["unresolved"] += 1
        broken.append((f, ln, spec, "py", "high", "unresolved internal import"))
    elif st == "missing":
        counts["missing"] += 1
        missing.append((f, ln, spec, "py", "low"))
    elif st == "oob":
        pass


def emit(js_tier, n_js, n_py, counts, broken, case_mismatch, missing, unverified, edges):
    p = print
    p("### IMPORT_GRAPH")
    p(f"js_ts: tier={js_tier} (files={n_js})")
    p(f"python: tier=builtin (files={n_py})")
    total = len(edges)
    p(f"edges={total} internal={counts['internal']} external={counts['external']} "
      f"builtin={counts['builtin']} missing={counts['missing']} unresolved={counts['unresolved']}")
    p("")
    p("### BROKEN_IMPORTS")
    for f, ln, spec, lang, conf, note in broken:
        p(f"{f}:{ln}  '{spec}'  [{lang}, {conf}]  {note}")
    p("")
    p("### CASE_MISMATCH")
    for f, ln, spec, actual in case_mismatch:
        p(f"{f}:{ln}  '{spec}'  -> actual: {actual}  [js, high]")
    p("")
    p("### MISSING_DEPS")
    for f, ln, spec, lang, conf in missing:
        p(f"{f}:{ln}  '{spec}'  [{lang}, {conf}]")
    p("")
    p("### UNVERIFIED")
    for f, ln, spec, reason in unverified:
        loc = f"{f}:{ln}" if ln else f
        p(f"{loc}  '{spec}'  {reason}")
    p("")
    artifact = {
        "root": ROOT,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "stats": {"edges": total, **counts, "files_js_ts": n_js, "files_python": n_py},
        "findings": {
            "broken": [{"file": f, "line": ln, "spec": s, "lang": l, "confidence": c, "note": n}
                       for f, ln, s, l, c, n in broken],
            "case_mismatch": [{"file": f, "line": ln, "spec": s, "actual": a}
                              for f, ln, s, a in case_mismatch],
            "missing_deps": [{"file": f, "line": ln, "spec": s, "lang": l, "confidence": c}
                             for f, ln, s, l, c in missing],
            "unverified": [{"file": f, "line": ln, "spec": s, "reason": r}
                           for f, ln, s, r in unverified],
        },
        "edges": edges[:5000],
    }
    p("### EDGES_JSON")
    p(json.dumps(artifact, indent=2))


if __name__ == "__main__":
    main()
