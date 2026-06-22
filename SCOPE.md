# Scope and limitations

nomoreslop v1.1 scores **two layers**: regex slop + structural slop. Both must pass for an overall PASS.

## What it covers

| Layer | Strength | How |
|-------|----------|-----|
| Comment/doc slop | Strong | Regex + manual |
| Generic naming | Strong | Regex |
| **Motion copy-paste** | Strong | Structural aggregate |
| **Section factories** | Strong | Structural aggregate |
| **File bloat** | Strong | LOC vs directory median |
| **Dead exports** | Partial | `lib/*.ts` import scan |
| Library rewrites | Partial | When dep installed |
| Framework envelopes (`ok:`) | Partial | Flag; human decides |
| MCP handler repetition | Manual | Often required by SDK |

## Scorer behavior

| Case | Behavior |
|------|----------|
| Git diff has no `.ts` files | Scan `src/`, `app/`, `api/` — **not** `node_modules` |
| shadcn `components/ui/` | Skipped by default |
| Slop PASS + structural FAIL | **Overall FAIL** — report both |
| AI-greenfield (whole dir is AI) | Calibrate to repo median, not one neighbor |

## Out of scope

- Rewriting shadcn vendor components
- Removing framework-required MCP tool boilerplate
- Copy/design of marketing text in locale JSON

## Manual checklist (after score)

1. Duplicate utils across files
2. Shared envelope/types consolidation
3. Regex-chain files (800+ LOC parsers) — split by domain
4. Rescore: `python scripts/score.py --repo . --json`

## Fixture: zheat-landing

See [examples/05-landing/notes.md](../examples/05-landing/notes.md). Regex ~6 PASS; structural ~80+ FAIL. This is the intended behavior for AI landing pages.

## Envelope allowlist

`ok: true` / `makeEnvelope({ ok:` are intentional in MCP tools, health endpoints, and test mocks.

```json
{
  "envelopeIgnoreInTests": true,
  "envelopeAllowlist": [
    "**/register-*-tools.ts",
    "api/health.ts",
    "server/chatbot-proxy/**"
  ]
}
```

Copy-ready: [configs/web-hq.nomoresloprc.json](../configs/web-hq.nomoresloprc.json), [configs/mcp-devkit.nomoresloprc.json](../configs/mcp-devkit.nomoresloprc.json).
