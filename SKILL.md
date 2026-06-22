---
name: nomoreslop
version: 1.0.0
description: >-
  Remove AI slop from source code so it reads clean and human-written. Use when
  the user wants to de-AI code, remove slop, humanize code, or clean an AI-assisted
  diff. Scores with scripts/score.py, calibrates to neighbor files, rewrites by hand.
  Modes: clean, calibrate (default), inject (opt-in). Behavior-preserving. No UI
  framework opinions. Uses lodash/date-fns/zod only when already in package.json.
license: MIT
compatibility: claude-code opencode cursor
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
---

# nomoreslop

Remove AI slop from **source code**. Match the repo's style. Use existing utils and deps — never add npm packages without approval.

Inspired by Rocky **human-readable-code**: read neighbors, reuse project utils, keep diffs focused.

## Install

| Editor | Path |
|--------|------|
| **Cursor** | `~/.cursor/skills/nomoreslop/` |
| Claude Code | `~/.claude/skills/nomoreslop/` |
| OpenCode | `~/.config/opencode/skills/nomoreslop/` |

Clone the repo into that folder (folder name must be `nomoreslop`). See [README.md](README.md).

## Modes

See [MODES.md](MODES.md). Default: **calibrate**.

| Mode | Flag |
|------|------|
| clean | `--clean-only` |
| calibrate | default |
| inject | `--inject-signals` (opt-in) |

## Behavior contract

- Success-path behavior stays identical (inputs, outputs, API).
- FLAG-tier edits are reported, never auto-applied.
- Removing swallow-all `catch`/`except` may change failure paths — say so explicitly.
- Never `yarn add` / `npm install` a new dependency without user approval.

## Workflow

1. **Scope** — `git diff main --name-only` or user paths. Skip generated files (see below).
2. **Config** — read `.nomoresloprc` if present (threshold, ignore, verify).
3. **Score** — run `python scripts/score.py --repo . --base main --json` when Python is available; else audit with [PATTERNS.md](PATTERNS.md) + Grep.
4. **Inventory** — read nearest `package.json`, neighbor imports, `src/utils/` → [LIBRARIES.md](LIBRARIES.md).
5. **Calibrate** — read 2–3 neighbor files: naming length, comment density, import style, idioms.
6. **Rewrite** — remove slop + apply library/native rewrites. Edit by hand; never generate a bulk find-replace script.
7. **SAFE fixes** — remove `# Step N`, debug `console.log`, dead imports inline.
8. **Verify** — run detect verify commands from score output or `.nomoresloprc`.
9. **Rescore** — same as step 3.
10. **Audit** — "What still reads as AI?" Fix or list remaining findings.
11. **Report** — slop score before → after, library swaps, FLAG items, verify result.

## Skip these paths

`node_modules`, `dist`, `build`, `.next`, `vendor`, `__pycache__`, `*.generated.*`, `*.g.ts`, `prisma/`, `__generated__/`

## Rocky (optional)

When Rocky devkit is connected on the **target repo** (not this skill repo):

- Read `human-readable-code` + matching stack agent before editing user code.
- After humanizing user code: `pre_pr_quality_gate` on their repo.

See [docs/rocky-workflow.md](docs/rocky-workflow.md).

## Reference files

- [PATTERNS.md](PATTERNS.md) — 22 slop patterns
- [LIBRARIES.md](LIBRARIES.md) — util reuse, native JS vs lodash
- [MODES.md](MODES.md) — mode details
- [patterns/typescript.md](patterns/typescript.md) / [patterns/javascript.md](patterns/javascript.md)

## Comment voice

Working notes, not tutorials:

```typescript
// was 0.008 — too weak
// todo: confirm with billing team
```

No `# Step 1:`, no emoji logs, no "This function comprehensively...".
