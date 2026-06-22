# TypeScript / JavaScript readability

Framework-agnostic. No UI library opinions.

## Naming

- Match neighbor length: `cfg` vs `configuration`
- Domain verbs: `parseInvoice`, not `processData`
- Locals: `i`, `n`, `item` in short loops

## Imports

Match neighbor order: third-party → internal → relative.

## Idioms

- `for..of` / `.map` over index loops
- `?.` over lodash `get` when neighbors use optional chaining
- `Object.groupBy` over manual reduce when neighbors use it
- Early return over deep nesting

## Types

- Strict repo: keep useful types
- Loose repo: don't add annotations on obvious literals

## Tests

`*.test.*` / `*.spec.*`: use `--clean-only`; keep arrange-act-assert.
