#!/usr/bin/env python3
"""nomoreslop scorer — stdlib only. Bundled with the skill."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IGNORE = [
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "**/.next/**",
    "**/vendor/**",
    "**/__pycache__/**",
    "**/*.generated.*",
    "**/*.g.ts",
    "**/prisma/**",
    "**/__generated__/**",
]

SOURCE_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".py", ".go", ".rs", ".java", ".cs",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def merge_config(repo: Path) -> dict[str, Any]:
    cfg: dict[str, Any] = {"threshold": 35, "ignore": [], "verify": []}
    rc = repo / ".nomoresloprc"
    if rc.is_file():
        cfg.update(load_json(rc))
    local = repo / ".nomoreslop/libraries.local.json"
    if local.is_file():
        cfg["librariesLocal"] = load_json(local)
    return cfg


def should_skip(path: Path, ignore_globs: list[str]) -> bool:
    s = path.as_posix()
    for pat in DEFAULT_IGNORE + ignore_globs:
        if fnmatch.fnmatch(s, pat.strip("/")) or fnmatch.fnmatch(s, "**/" + pat.strip("/")):
            return True
    return False


def git_changed_files(repo: Path, base: str | None, staged: bool) -> list[Path]:
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    elif base:
        cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", base]
    else:
        cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"]
    try:
        out = subprocess.check_output(cmd, cwd=repo, text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    files = []
    for line in out.splitlines():
        p = repo / line.strip()
        if p.suffix in SOURCE_EXTS and p.is_file():
            files.append(p)
    return files


def collect_files(repo: Path, paths: list[str] | None, base: str | None, staged: bool, ignore: list[str]) -> list[Path]:
    if paths:
        candidates = [repo / p if not Path(p).is_absolute() else Path(p) for p in paths]
    else:
        candidates = git_changed_files(repo, base, staged)
        if not candidates:
            candidates = [p for p in repo.rglob("*") if p.suffix in SOURCE_EXTS and p.is_file()]
    result = []
    for p in candidates:
        try:
            rel = p.relative_to(repo)
        except ValueError:
            continue
        if not should_skip(rel, ignore):
            result.append(p)
    return result


def nearest_package_json(file_path: Path, repo: Path) -> Path | None:
    d = file_path.parent
    while d == repo or repo in d.parents or d == file_path.anchor:
        pj = d / "package.json"
        if pj.is_file():
            return pj
        if d == repo:
            break
        d = d.parent
    return repo / "package.json" if (repo / "package.json").is_file() else None


def installed_deps(package_json: Path | None) -> set[str]:
    if not package_json or not package_json.is_file():
        return set()
    data = load_json(package_json)
    deps: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        deps.update(data.get(key, {}).keys())
    return deps


def load_library_rules() -> list[dict[str, Any]]:
    index_path = SKILL_ROOT / "patterns/libraries/_index.json"
    if not index_path.is_file():
        return []
    index = load_json(index_path)
    rules: list[dict[str, Any]] = []
    for pkg in index.get("packages", []):
        fp = SKILL_ROOT / "patterns/libraries" / pkg["file"]
        if fp.is_file():
            data = load_json(fp)
            for rule in data.get("rules", []):
                rule["_package"] = data.get("package")
                rule["_aliases"] = data.get("aliases", [])
                rules.append(rule)
    return rules


def detect_verify(repo: Path, cfg: dict[str, Any]) -> list[str]:
    if cfg.get("verify"):
        return list(cfg["verify"])
    pj = repo / "package.json"
    if not pj.is_file():
        return []
    scripts = load_json(pj).get("scripts", {})
    pm = "yarn"
    if (repo / "pnpm-lock.yaml").is_file():
        pm = "pnpm"
    elif not (repo / "yarn.lock").is_file() and (repo / "package-lock.json").is_file():
        pm = "npm"
    run = f"{pm} run"
    cmds = []
    for name in ("lint:fix", "lint", "test:run", "test"):
        if name in scripts:
            cmds.append(f"{run} {name}")
    return cmds


def scan_file(content: str, path: Path, universal: list[dict], lib_rules: list[dict], deps: set[str]) -> list[dict]:
    findings: list[dict] = []
    lines = content.splitlines()
    ignore_next: set[str] = set()

    for i, line in enumerate(lines, start=1):
        m = re.search(r"nomoreslop-ignore:\s*([\w-]+)", line)
        if m:
            ignore_next.add(m.group(1))
            continue

        for pat in universal:
            pid = pat["id"]
            if pid in ignore_next:
                continue
            flags = re.I if pat.get("flags") == "i" else 0
            if re.search(pat["regex"], line, flags):
                findings.append({
                    "file": str(path),
                    "line": i,
                    "patternId": pid,
                    "tier": pat.get("tier", "safe"),
                    "weight": pat.get("weight", 3),
                    "fixable": pat.get("tier") == "safe",
                    "text": line.strip()[:120],
                })

        for rule in lib_rules:
            pkg = rule.get("_package", "")
            aliases = rule.get("_aliases", [])
            if pkg not in deps and not any(a in deps for a in aliases):
                continue
            rid = rule["id"]
            if rid in ignore_next:
                continue
            detect = rule.get("detect", {})
            if re.search(detect.get("regex", "$^"), line):
                findings.append({
                    "file": str(path),
                    "line": i,
                    "patternId": rid,
                    "tier": rule.get("rewriteTier", "conditional"),
                    "weight": rule.get("slopWeight", 6),
                    "fixable": False,
                    "package": pkg,
                    "suggest": rule.get("suggest"),
                    "text": line.strip()[:120],
                })

    return findings


def compute_score(findings: list[dict], threshold: int) -> dict[str, Any]:
    score = min(100, sum(f["weight"] for f in findings))
    return {
        "slopScore": score,
        "threshold": threshold,
        "passed": score <= threshold,
        "findingCount": len(findings),
    }


def inventory(repo: Path) -> dict[str, Any]:
    pj = repo / "package.json"
    deps = installed_deps(pj)
    lib_rules = load_library_rules()
    applicable = []
    for rule in lib_rules:
        pkg = rule.get("_package", "")
        aliases = rule.get("_aliases", [])
        if pkg in deps or any(a in deps for a in aliases):
            applicable.append(rule["id"])
    return {
        "installed": sorted(deps),
        "applicableRules": len(applicable),
        "ruleIds": applicable,
        "verify": detect_verify(repo, merge_config(repo)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="nomoreslop score")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="main", help="git base ref for diff")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--paths", nargs="*", help="specific files")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--threshold", type=int, default=None)
    args = parser.parse_args()

    repo = args.repo.resolve()
    cfg = merge_config(repo)

    if args.inventory:
        out = inventory(repo)
        print(json.dumps(out, indent=2) if args.json else json.dumps(out, indent=2))
        return 0

    universal_path = SKILL_ROOT / "patterns/universal.json"
    universal = load_json(universal_path).get("patterns", [])
    lib_rules = load_library_rules()
    threshold = args.threshold if args.threshold is not None else cfg.get("threshold", 35)
    ignore = cfg.get("ignore", [])

    files = collect_files(repo, args.paths, args.base if not args.paths else None, args.staged, ignore)
    all_findings: list[dict] = []

    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        pj = nearest_package_json(fp, repo)
        deps = installed_deps(pj)
        all_findings.extend(scan_file(content, fp.relative_to(repo), universal, lib_rules, deps))

    summary = compute_score(all_findings, threshold)
    result = {
        **summary,
        "filesScanned": len(files),
        "findings": all_findings,
        "verify": detect_verify(repo, cfg),
        "recommendedMode": "calibrate" if summary["slopScore"] > threshold else "clean",
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Slop score: {summary['slopScore']}/{threshold} {'PASS' if summary['passed'] else 'FAIL'}")
        print(f"Files: {len(files)}  Findings: {len(all_findings)}")
        for f in all_findings[:20]:
            print(f"  {f['file']}:{f['line']} [{f['patternId']}] ({f['tier']})")
        if len(all_findings) > 20:
            print(f"  ... and {len(all_findings) - 20} more")

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
