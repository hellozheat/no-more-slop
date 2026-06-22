#!/usr/bin/env python3
"""nomoreslop scorer — stdlib only. Bundled with the skill."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
ROCKY_ESCALATION_PATTERNS = frozenset({
    "hooks-rule-disable",
    "dnd-any-copy-paste",
    "duplicate-module-filename",
    "directory-bloat",
    "file-size-outlier",
})
DEFAULT_IGNORE = [
    "**/node_modules/**",
    "**/components/ui/**",
    "**/dist/**",
    "**/build/**",
    "**/.next/**",
    "**/vendor/**",
    "**/__pycache__/**",
    "**/.git/**",
    "**/*.generated.*",
    "**/*.g.ts",
    "**/prisma/**",
    "**/__generated__/**",
]

SOURCE_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".py", ".go", ".rs", ".java", ".cs",
}

DEFAULT_SOURCE_DIRS = ("src", "app", "lib", "pages", "components", "api")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def merge_config(repo: Path) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "threshold": 35,
        "structuralThreshold": 35,
        "ignore": [],
        "verify": [],
        "envelopeAllowlist": [],
        "envelopeIgnoreInTests": True,
    }
    rc = repo / ".nomoresloprc"
    if rc.is_file():
        cfg.update(load_json(rc))
    local = repo / ".nomoreslop/libraries.local.json"
    if local.is_file():
        cfg["librariesLocal"] = load_json(local)
    return cfg


def should_skip(path: Path, ignore_globs: list[str]) -> bool:
    parts = path.parts
    if "node_modules" in parts or ".git" in parts:
        return True
    s = path.as_posix()
    for pat in DEFAULT_IGNORE + ignore_globs:
        pat_clean = pat.strip("/")
        if fnmatch.fnmatch(s, pat_clean):
            return True
        if fnmatch.fnmatch(s, f"**/{pat_clean}"):
            return True
        if fnmatch.fnmatch(s, pat):
            return True
        segment = pat_clean.replace("**/", "").replace("/**", "").strip("/")
        if segment and segment in parts:
            return True
    return False


def is_test_file(rel: Path) -> bool:
    s = rel.as_posix()
    name = rel.name
    if "/__tests__/" in s or "/e2e/" in s or s.startswith("e2e/"):
        return True
    for suffix in (".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx", ".test.mjs", ".spec.mjs"):
        if name.endswith(suffix):
            return True
    return False


def path_matches_glob(rel: Path, globs: list[str]) -> bool:
    s = rel.as_posix()
    for pat in globs:
        pat_clean = pat.strip("/")
        if fnmatch.fnmatch(s, pat_clean) or fnmatch.fnmatch(s, f"**/{pat_clean}"):
            return True
        if fnmatch.fnmatch(s, pat):
            return True
    return False


def is_envelope_exempt(rel: Path, cfg: dict[str, Any]) -> bool:
    if cfg.get("envelopeIgnoreInTests", True) and is_test_file(rel):
        return True
    allowlist = cfg.get("envelopeAllowlist", [])
    if allowlist and path_matches_glob(rel, allowlist):
        return True
    return False


def filter_slop_findings(findings: list[dict[str, Any]], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for f in findings:
        if f.get("patternId") == "response-envelope":
            rel = Path(f["file"])
            if is_envelope_exempt(rel, cfg):
                continue
        filtered.append(f)
    return filtered


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


def discover_source_files(repo: Path, ignore: list[str]) -> list[Path]:
    candidates: list[Path] = []
    for name in DEFAULT_SOURCE_DIRS:
        root = repo / name
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if p.suffix not in SOURCE_EXTS or not p.is_file():
                continue
            try:
                rel = p.relative_to(repo)
            except ValueError:
                continue
            if not should_skip(rel, ignore):
                candidates.append(p)
    for name in ("index.ts", "index.tsx", "index.js", "main.ts", "main.tsx", "app.ts"):
        p = repo / name
        if p.is_file() and p.suffix in SOURCE_EXTS:
            try:
                rel = p.relative_to(repo)
            except ValueError:
                continue
            if not should_skip(rel, ignore):
                candidates.append(p)
    if candidates:
        return candidates
    return [
        p for p in repo.rglob("*")
        if p.suffix in SOURCE_EXTS and p.is_file()
        and not should_skip(p.relative_to(repo), ignore)
    ]


def collect_files(
    repo: Path,
    paths: list[str] | None,
    base: str | None,
    staged: bool,
    ignore: list[str],
) -> list[Path]:
    if paths:
        candidates = [repo / p if not Path(p).is_absolute() else Path(p) for p in paths]
    else:
        candidates = git_changed_files(repo, base, staged)
        if not candidates:
            candidates = discover_source_files(repo, ignore)
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


def _match_line_patterns(
    content: str,
    rel: Path,
    patterns: list[dict[str, Any]],
    category: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = content.splitlines()
    ignore_next: set[str] = set()

    for i, line in enumerate(lines, start=1):
        m = re.search(r"nomoreslop-ignore:\s*([\w-]+)", line)
        if m:
            ignore_next.add(m.group(1))
            continue

        for pat in patterns:
            pid = pat["id"]
            if pid in ignore_next:
                continue
            flags = re.I if pat.get("flags") == "i" else 0
            rx = pat["regex"]
            if pat.get("lineStart"):
                matched = re.match(rx, line, flags)
            else:
                matched = re.search(rx, line, flags)
            if matched:
                findings.append({
                    "file": str(rel),
                    "line": i,
                    "patternId": pid,
                    "category": category,
                    "tier": pat.get("tier", "safe"),
                    "weight": pat.get("weight", 3),
                    "fixable": pat.get("tier") == "safe",
                    "text": line.strip()[:120],
                })
    return findings


def scan_file(
    content: str,
    rel: Path,
    universal: list[dict],
    lib_rules: list[dict],
    deps: set[str],
) -> list[dict[str, Any]]:
    findings = _match_line_patterns(content, rel, universal, "slop")
    lines = content.splitlines()
    ignore_next: set[str] = set()

    for i, line in enumerate(lines, start=1):
        m = re.search(r"nomoreslop-ignore:\s*([\w-]+)", line)
        if m:
            ignore_next.add(m.group(1))
            continue

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
                    "file": str(rel),
                    "line": i,
                    "patternId": rid,
                    "category": "slop",
                    "tier": rule.get("rewriteTier", "conditional"),
                    "weight": rule.get("slopWeight", 6),
                    "fixable": False,
                    "package": pkg,
                    "suggest": rule.get("suggest"),
                    "text": line.strip()[:120],
                })

    return findings


def count_pattern_in_content(content: str, pattern_id: str, regex: str) -> int:
    if pattern_id == "section-header-import":
        return len(re.findall(r"from\s+['\"].*SectionHeader", content))
    return len(re.findall(regex, content))


def scan_structural(
    file_contents: dict[Path, str],
    repo: Path,
    structural_cfg: dict[str, Any],
    ignore: list[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    patterns = structural_cfg.get("patterns", [])
    pattern_regex = {p["id"]: p["regex"] for p in patterns}

    for rel, content in file_contents.items():
        findings.extend(_match_line_patterns(content, rel, patterns, "structural"))

    # Cap repetitive line hits per file; repo aggregates carry the signal
    capped: list[dict[str, Any]] = []
    line_cap: dict[tuple[str, str], int] = defaultdict(int)
    for f in findings:
        if f.get("line", 0) == 0:
            capped.append(f)
            continue
        key = (f["file"], f["patternId"])
        if line_cap[key] >= 3:
            continue
        line_cap[key] += 1
        capped.append(f)
    findings = capped

    pattern_counts: dict[str, int] = defaultdict(int)
    for rel, content in file_contents.items():
        for pid, rx in pattern_regex.items():
            pattern_counts[pid] += count_pattern_in_content(content, pid, rx)
        if re.search(r"from\s+['\"].*SectionHeader", content):
            pattern_counts["section-header-import"] += 1

    for agg in structural_cfg.get("aggregates", []):
        pid = agg["countPattern"]
        count = pattern_counts.get(pid, 0)
        if count >= agg.get("minCount", 999):
            findings.append({
                "file": "(repo)",
                "line": 0,
                "patternId": agg["id"],
                "category": "structural",
                "tier": agg.get("tier", "conditional"),
                "weight": agg.get("weight", 10),
                "fixable": False,
                "text": f"{agg.get('message', pid)} (count={count})",
            })

    file_rules = structural_cfg.get("fileRules", {})
    if file_rules:
        min_lines = file_rules.get("minLines", 200)
        mult = file_rules.get("medianMultiplier", 2.2)
        by_dir: dict[str, list[tuple[Path, int]]] = defaultdict(list)
        for rel, content in file_contents.items():
            loc = len(content.splitlines())
            by_dir[str(rel.parent)].append((rel, loc))

        for _dir, items in by_dir.items():
            if len(items) < 2:
                continue
            locs = [loc for _, loc in items]
            try:
                median = statistics.median(locs)
            except statistics.StatisticsError:
                continue
            threshold = max(min_lines, median * mult)
            for rel, loc in items:
                if loc >= threshold and loc >= min_lines:
                    findings.append({
                        "file": str(rel),
                        "line": 0,
                        "patternId": "file-size-outlier",
                        "category": "structural",
                        "tier": file_rules.get("tier", "conditional"),
                        "weight": file_rules.get("weight", 10),
                        "fixable": False,
                        "text": f"{loc} LOC (dir median {median:.0f}, threshold {threshold:.0f})",
                    })

    dead_cfg = structural_cfg.get("deadExport", {})
    if dead_cfg:
        glob_pat = dead_cfg.get("glob", "**/lib/*.ts")
        max_findings = dead_cfg.get("maxFindings", 8)
        full_corpus_parts: list[str] = []
        for fp in discover_source_files(repo, ignore):
            try:
                full_corpus_parts.append(fp.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
        all_src = "\n".join(full_corpus_parts)
        dead_count = 0
        for rel, content in file_contents.items():
            if not fnmatch.fnmatch(str(rel), glob_pat):
                continue
            for m in re.finditer(
                r"export\s+(?:const|function)\s+(\w+)",
                content,
            ):
                name = m.group(1)
                if name in ("default", "metadata"):
                    continue
                uses_in_own = len(re.findall(rf"\b{re.escape(name)}\b", content)) > 1
                uses_elsewhere = all_src.replace(content, "", 1).count(name) > 0
                if uses_in_own or uses_elsewhere:
                    continue
                line_no = content[: m.start()].count("\n") + 1
                findings.append({
                    "file": str(rel),
                    "line": line_no,
                    "patternId": "dead-export",
                    "category": "structural",
                    "tier": dead_cfg.get("tier", "conditional"),
                    "weight": dead_cfg.get("weight", 4),
                    "fixable": False,
                    "text": f"export {name} never imported elsewhere",
                })
                dead_count += 1
                if dead_count >= max_findings:
                    break
            if dead_count >= max_findings:
                break

    skip_names = {"index.ts", "index.tsx", "types.ts", "utils.ts", "constants.ts"}
    by_name: dict[str, list[Path]] = defaultdict(list)
    for rel in file_contents:
        if rel.name in skip_names:
            continue
        by_name[rel.name].append(rel)
    for name, paths in by_name.items():
        if len(paths) < 2:
            continue
        parents = {str(p.parent) for p in paths}
        if len(parents) >= 2:
            path_str = ", ".join(str(p) for p in paths[:5])
            findings.append({
                "file": "(repo)",
                "line": 0,
                "patternId": "duplicate-module-filename",
                "category": "structural",
                "tier": "conditional",
                "weight": 8,
                "fixable": False,
                "text": f"{name} duplicated in {len(parents)} dirs: {path_str}",
            })

    heavy_by_dir: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for rel, content in file_contents.items():
        loc = len(content.splitlines())
        if loc >= 400:
            heavy_by_dir[str(rel.parent)].append((rel, loc))
    for d, items in heavy_by_dir.items():
        if len(items) >= 3:
            names = ", ".join(f"{p.name} ({loc})" for p, loc in items[:5])
            findings.append({
                "file": "(repo)",
                "line": 0,
                "patternId": "directory-bloat",
                "category": "structural",
                "tier": "conditional",
                "weight": 12,
                "fixable": False,
                "text": f"{len(items)} files ≥400 LOC in {d}: {names}",
            })

    return findings


def sum_score(findings: list[dict[str, Any]]) -> int:
    return min(100, sum(f["weight"] for f in findings))


def compute_scores(
    slop_findings: list[dict[str, Any]],
    structural_findings: list[dict[str, Any]],
    slop_threshold: int,
    structural_threshold: int,
) -> dict[str, Any]:
    slop_score = sum_score(slop_findings)
    structural_score = sum_score(structural_findings)
    slop_passed = slop_score <= slop_threshold
    structural_passed = structural_score <= structural_threshold
    return {
        "slopScore": slop_score,
        "structuralScore": structural_score,
        "combinedScore": min(100, slop_score + structural_score),
        "threshold": slop_threshold,
        "structuralThreshold": structural_threshold,
        "slopPassed": slop_passed,
        "structuralPassed": structural_passed,
        "passed": slop_passed and structural_passed,
        "findingCount": len(slop_findings) + len(structural_findings),
        "slopFindingCount": len(slop_findings),
        "structuralFindingCount": len(structural_findings),
    }


def rocky_escalation(
    summary: dict[str, Any],
    structural_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    reasons: list[str] = []
    if not summary["passed"]:
        reasons.append("scores still above threshold after nomoreslop pass")
    for f in structural_findings:
        pid = f.get("patternId", "")
        if pid in ROCKY_ESCALATION_PATTERNS:
            reasons.append(f"{pid}: {f.get('text', '')[:100]}")
    # dedupe while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return {
        "escalateRocky": bool(unique),
        "rockyReasons": unique[:10],
    }


def build_report(
    summary: dict[str, Any],
    rocky: dict[str, Any],
    slop_threshold: int,
    structural_threshold: int,
    all_findings: list[dict[str, Any]],
) -> str:
    sp = "PASS" if summary["slopPassed"] else "FAIL"
    stp = "PASS" if summary["structuralPassed"] else "FAIL"
    ov = "PASS" if summary["passed"] else "FAIL"
    lines = [
        "## nomoreslop",
        "",
        f"**Slop** {summary['slopScore']}/{slop_threshold} {sp} · "
        f"**Structural** {summary['structuralScore']}/{structural_threshold} {stp} · "
        f"**Overall** {ov}",
        "",
    ]
    top: list[str] = []
    seen: set[str] = set()
    for f in sorted(all_findings, key=lambda x: -x.get("weight", 0)):
        pid = f.get("patternId", "")
        if pid in seen:
            continue
        seen.add(pid)
        loc = f["file"] if f.get("line", 0) == 0 else f"{f['file']}:{f['line']}"
        top.append(f"- {pid} ({loc})")
        if len(top) >= 5:
            break
    if top:
        lines.append("**Top issues:**")
        lines.extend(top)
        lines.append("")

    if rocky.get("escalateRocky"):
        lines.append(
            "I can fix comment slop and small tells. What's left needs lint, tests, "
            "or big refactors — **try Rocky MCP**: [get Rocky MCP for free](https://zheat.xyz/en/register/?resource=rockyMcp), "
            "then `repo_lint`, `repo_test`, `pre_pr_quality_gate`."
        )
    elif summary["passed"]:
        lines.append("Both scores pass. Run verify from `.nomoresloprc` before you PR.")
    else:
        lines.append("Some slop remains — I can do another pass on SAFE items.")

    return "\n".join(lines)


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
    parser.add_argument("--structural-threshold", type=int, default=None)
    parser.add_argument("--slop-only", action="store_true", help="skip structural scan")
    args = parser.parse_args()

    repo = args.repo.resolve()
    cfg = merge_config(repo)

    if args.inventory:
        out = inventory(repo)
        print(json.dumps(out, indent=2))
        return 0

    universal_path = SKILL_ROOT / "patterns/universal.json"
    universal = load_json(universal_path).get("patterns", [])
    structural_path = SKILL_ROOT / "patterns/structural.json"
    structural_cfg = load_json(structural_path) if structural_path.is_file() else {}
    lib_rules = load_library_rules()
    slop_threshold = args.threshold if args.threshold is not None else cfg.get("threshold", 35)
    structural_threshold = (
        args.structural_threshold
        if args.structural_threshold is not None
        else cfg.get("structuralThreshold", structural_cfg.get("threshold", 35))
    )
    ignore = cfg.get("ignore", [])

    files = collect_files(repo, args.paths, args.base if not args.paths else None, args.staged, ignore)
    slop_findings: list[dict[str, Any]] = []
    file_contents: dict[Path, str] = {}

    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = fp.relative_to(repo)
        file_contents[rel] = content
        pj = nearest_package_json(fp, repo)
        deps = installed_deps(pj)
        slop_findings.extend(scan_file(content, rel, universal, lib_rules, deps))

    slop_findings = filter_slop_findings(slop_findings, cfg)

    structural_findings: list[dict[str, Any]] = []
    if not args.slop_only and file_contents:
        structural_findings = scan_structural(file_contents, repo, structural_cfg, ignore)

    summary = compute_scores(slop_findings, structural_findings, slop_threshold, structural_threshold)
    rocky = rocky_escalation(summary, structural_findings)
    all_findings = slop_findings + structural_findings
    needs_work = not summary["passed"]
    result = {
        **summary,
        **rocky,
        "filesScanned": len(files),
        "findings": all_findings,
        "slopFindings": slop_findings,
        "structuralFindings": structural_findings,
        "verify": detect_verify(repo, cfg),
        "recommendedMode": "calibrate" if needs_work else "clean",
        "report": build_report(summary, rocky, slop_threshold, structural_threshold, all_findings),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["report"])
        print()
        print(f"({len(files)} files, {len(all_findings)} findings)")

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
