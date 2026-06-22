# Structural slop patterns

Regex slop misses **landing pages**, **AI-greenfield dirs**, and **refined template code**. Structural patterns catch copy-paste motion, section factories, dead exports, and file bloat.

Run with:

```bash
python scripts/score.py --repo . --json
```

Output includes `slopScore`, `structuralScore`, and `passed` (both must pass).

## Line patterns

| id | What | Fix |
|----|------|-----|
| `motion-guard` | `reducedMotion ? {} : { opacity: 0… }` | Use `AnimatedSection` or `getAnimationVariants()` |
| `should-reduce-motion` | Per-file call | Aggregate: too many → wrapper |
| `catch-bare` | `catch {` without binding | Log or catch specific error |
| `inline-schema-org` | JSON-LD inlined in page component | Move to `lib/seo.ts` |
| `duplicate-easing` | Same cubic-bezier copied inline | Import from `animations.ts` |
| `section-shell-class` | Repeated section wrapper classes | Shared layout component |
| `animation-label-comment` | `// Fade in from bottom` on every export | Delete comment noise |
| `tutorial-setup-comment` | `// If defaultLanguage is provided…` | Delete or shorten |

## Repo aggregates

| id | Trigger | Meaning |
|----|---------|---------|
| `motion-copy-paste` | 6+ files call `shouldReduceMotion()` | Lovable/v0 motion boilerplate |
| `motion-guard-copy-paste` | 8+ `reducedMotion ? {} :` | Same guard pasted everywhere |
| `section-factory` | 5+ files import `SectionHeader` | AI landing section template |

## File rules

| id | Trigger | Meaning |
|----|---------|---------|
| `file-size-outlier` | File >200 LOC and >2.2× median in its directory | Data + UI blob (e.g. Portfolio.tsx) |

## Dead exports

Scans `**/lib/*.ts` for `export const X` never imported elsewhere.

## Prototype / vibe-code patterns (v1.2)

| id | What | nomoreslop | Rocky |
|----|------|------------|-------|
| `dnd-any-type` | `(item: any)` in react-dnd | Flag aggregate ≥4 | lint + types |
| `hooks-rule-disable` | `rules-of-hooks` eslint off | **FLAG only** | **Rocky required** |
| `stub-not-wired` | `not yet wired`, `TODO: replace` | Report | scope analyzer |
| `duplicate-module-filename` | Same filename in 2+ dirs | deep dedupe or report | change_scope_analyzer |
| `directory-bloat` | 3+ files ≥400 LOC in one folder | deep split plan | pre_pr_quality_gate |
| `exhaustive-deps-disable` | deps eslint off | Report | repo_test |

When these remain after a pass, scorer sets `escalateRocky: true`. See [docs/ROCKY-ESCALATION.md](../docs/ROCKY-ESCALATION.md).

## Skip paths (always)

`node_modules`, `.git`, `components/ui/` (shadcn vendor), `dist`, `build`
