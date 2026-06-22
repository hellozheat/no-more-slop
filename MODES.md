# Modes

## clean (`--clean-only`)

Subtract AI tells only. No injection.

- Run all SAFE + CONDITIONAL patterns from PATTERNS.md
- Library rewrites when deps exist
- No casual-comment injection

Use before PR when you want a minimal, review-friendly diff.

## calibrate (default)

`clean` + match neighbor style.

- Read 2–3 files in the same directory (or imports graph)
- Match naming length, comment density, import order, idioms
- Prefer project `src/utils/` over new lodash imports

This is the default for `/nomoreslop`.

## inject (`--inject-signals`, opt-in)

`calibrate` + light human signals:

- A few terse *why* comments where neighbors have comments
- No fake typos, no whitespace entropy, no emoji

Only when user explicitly asks. Not for test files (`*.test.*`, `*.spec.*`).

## inject vs full

v1 has no `full` mode (no whitespace entropy script). Deferred.
