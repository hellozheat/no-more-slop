# Modes

## clean (`--clean-only`)

Subtract AI tells only. No injection.

- Run SAFE + CONDITIONAL patterns from [PATTERNS.md](PATTERNS.md)
- Run structural scan; report findings but only auto-fix SAFE slop items
- Library rewrites when deps exist

Use before PR when you want a minimal diff.

## calibrate (default)

`clean` + match neighbor style + fix structural slop where safe.

- Read 2–3 files in the same directory (or repo median if AI-greenfield)
- Match naming, comment density, imports, idioms
- Fix motion boilerplate (wrapper component), dead exports, duplicate easing
- Split data blobs from UI when user approves scope

Default for `/nomoreslop`.

## deep (`--deep`, opt-in)

`calibrate` + behavior-preserving refactors. **Default for vibe-coded prototypes.**

- Split 400+ LOC components (data → `lib/`, UI → thin component)
- Consolidate duplicate modules (`SearchOverlay.tsx` in two trees)
- Extract inline SEO/schema to `lib/seo.ts`
- Deduplicate copied helpers across files
- If still `escalateRocky` → follow [docs/ROCKY-ESCALATION.md](../docs/ROCKY-ESCALATION.md)

Only when user asks, prototype README says "vibe-coded", or structural score > threshold. Larger diffs — call out in report.

## inject (`--inject-signals`, opt-in)

`calibrate` + light human signals:

- A few terse *why* comments where neighbors have comments
- No fake typos, no whitespace entropy, no emoji

Only when user explicitly asks. Not for test files (`*.test.*`, `*.spec.*`).

## inject vs full

v1 has no `full` mode (no whitespace entropy script). Deferred.
