# Slop patterns (22)

Each pattern has an **id** used in `patterns/universal.json` and `scripts/score.py`.

**Tiers:** SAFE (auto-fix ok) | CONDITIONAL (rewrite by hand) | FLAG (report only)

---

## Comments and docs (1–7)

### 1. `docstring-trivial` (SAFE)

Docblock on a trivial function.

```python
# Before
def add(a, b):
    """Adds two numbers and returns the sum."""
    return a + b

# After
def add(a, b):
    return a + b
```

### 2. `comment-restates` (SAFE)

Comment repeats the next line.

```typescript
// Before
// Increment the counter by one
counter += 1;

// After
counter += 1;
```

### 3. `banner-step` (SAFE)

Section banners or step comments.

```typescript
// Before
// Step 1: Fetch users
// ===== Handler =====

// After
(delete both)
```

### 4. `tutorial-voice` (SAFE)

Tutorial phrasing.

```typescript
// Before
// Here we validate the input before processing

// After
// skip invalid rows from legacy import
```

### 5. `emoji-narration` / `narration-log` (SAFE / CONDITIONAL)

Emoji or tutorial narration in logs. Plain startup logs (`console.log('listening on 3000')`) are fine.

```typescript
// Before
console.log("✅ Successfully processed!");

// After
(remove or use real logger at appropriate level)
```

### 6. `placeholder-todo` (SAFE)

Placeholder TODOs.

```typescript
// Before
// TODO: your logic here

// After
(delete or // TODO(PROJ-123): handle refunds)
```

### 7. `uniform-comments` (CONDITIONAL)

Every block line commented. Reduce to a few uneven *why* comments.

---

## Naming (8–10)

### 8. `verbose-names` (CONDITIONAL)

Dictionary-style names.

```typescript
// Before
const totalUserInputCharacterCount = text.length;

// After
const charCount = text.length;
```

### 9. `generic-names` (CONDITIONAL)

```typescript
// Before
function processData(data) { ... }

// After
function parseInvoice(raw) { ... }
```

### 10. `no-idiomatic-locals` (CONDITIONAL)

Use `i`, `n`, `for..of`, `enumerate` per language pack.

---

## Structure (11–14)

### 11. `over-engineering` (CONDITIONAL)

Factory/ABC for one use → plain function.

### 12. `single-use-helper` (CONDITIONAL)

Three-line helper called once → inline.

### 13. `response-envelope` (CONDITIONAL)

`status: "success"` or `ok: true/false` wrappers when the repo usually returns data or throws.

```typescript
// Before
return { status: "success", data: user };
return makeEnvelope({ ok: true, data: user });

// After (when neighbors don't use envelopes)
return user;
```

Keep the envelope if the API contract or MCP tool schema requires it. Score only; don't auto-strip.

### 14. `eerie-uniformity` (CONDITIONAL)

Same comment/docstring on every function → match neighbor variance.

---

## Error handling (15–16)

### 15. `swallow-except` (FLAG)

```typescript
// Before
try { return parse(x); } catch (e) { return null; }

// After
return parse(x); // or catch specific error — note behavior change
```

### 16. `redundant-null-check` (CONDITIONAL)

Guard after typed non-null parameter → remove if unreachable.

---

## Types, idioms, imports (17–21)

### 17. `useless-types` (CONDITIONAL)

Obvious annotations in untyped repos → trim; keep in strict TS.

### 18. `throwaway-main` (SAFE)

Remove appended demo `if __name__ == "__main__"` blocks.

### 19. `markdown-in-comments` (SAFE)

No `**bold**` or `# headings` inside comments.

### 20. `non-idiomatic-loop` (CONDITIONAL)

```python
# Before
for i in range(len(items)):
    x = items[i]

# After
for item in items:
    ...
```

### 21. `dead-imports` (SAFE)

Remove unused imports.

---

## Audit (22)

### 22. `hallucinated-api` (FLAG)

Import or call not in `package.json` or codebase → report; never invent a fix.

---

## Library slop (see LIBRARIES.md)

Scored via `patterns/libraries/*.json` when matching dep is installed:

- `manual-groupby`, `json-clone`, `manual-debounce`, etc.

---

## nomoreslop-ignore

```typescript
// nomoreslop-ignore: manual-groupby — stable key order required
```
