# vc-global-dashboard-playground (prototype fixture)

Vibe-coded dashboard prototype. README admits dummy data.

## Expected scores (approx)

| Metric | Before |
|--------|--------|
| Slop | ~90 FAIL |
| Structural | ~90+ FAIL |
| escalateRocky | **true** |

## Key hits

- `UnitPanel.tsx` / `LoadLens.tsx` — 1200+ LOC
- `directory-bloat` — `options/a/` has 4+ mega files
- `duplicate-module-filename` — `SearchOverlay.tsx`, `ProjectPicker*`
- `hooks-rule-disable` — `OperationalKpisPage.tsx`
- `dnd-any-copy-paste` — react-dnd `item: any`
- `stub-not-wired` — config panel features

## nomoreslop can fix

- Tutorial comments, date-fns swaps, index loops
- Dead exports, some reduce → native

## Escalate to Rocky

- Hooks violation, lint/typecheck
- Split 1200 LOC components (deep + scope analyzer)
- Dedupe shell vs options/shared
- `pre_pr_quality_gate` before any PR

Config: [configs/vc-playground.nomoresloprc.json](../../configs/vc-playground.nomoresloprc.json)
