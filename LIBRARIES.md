# Library-aware rewrites

Only suggest packages **already in the nearest `package.json`**. Never add deps without approval (FLAG).

## Priority

1. **Project util** — `src/utils/`, `@/lib/`, etc.
2. **Native JS** — when neighbors use it (`Object.groupBy`, `structuredClone`, `?.`)
3. **Installed npm util** — lodash, date-fns, zod, dayjs, etc.

## Native vs lodash

| Task | Native (prefer if neighbors use it) | lodash (if installed + neighbors use it) |
|------|-------------------------------------|------------------------------------------|
| Group | `Object.groupBy(arr, fn)` | `groupBy` / `_.groupBy` |
| Deep clone | `structuredClone(x)` | `cloneDeep` |
| Null safe | `obj?.a?.b` | `get(obj, 'a.b')` |
| Unique | `[...new Set(arr)]` | `uniq` |
| Debounce | — | `debounce` |

Match neighbor import style: `import { groupBy } from 'lodash-es'` vs `import _ from 'lodash'`.

## Catalog

Rule files: [patterns/libraries/](patterns/libraries/). Loaded by `score.py` when `--inventory` or scoring.

Tier 1 (v1): lodash, date-fns, dayjs, zod.

## Per-repo overrides

`.nomoreslop/libraries.local.json`:

```json
{
  "prefer": ["src/utils/array.ts:groupBy"],
  "ignorePackages": ["lodash"],
  "extraRules": []
}
```

## Out of scope

No UI/CSS framework suggestions (antd, tailwind, MUI, etc.).
