# Score rubric

Slop score **0–100** (lower is better). Default pass threshold: **35**.

| Hit | Weight |
|-----|--------|
| SAFE pattern | +3 each |
| CONDITIONAL pattern | +5 each |
| FLAG pattern | +8 each |
| Library reimplementation (dep installed) | +6 each |
| Uniform comment density (heuristic) | +10 max |

Cap at 100.

## Threshold

Override in `.nomoresloprc`:

```json
{ "threshold": 35 }
```
