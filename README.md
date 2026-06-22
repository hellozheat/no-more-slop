# No More Slop

A skill for Claude Code, Cursor, and OpenCode that strips AI slop from source code so it reads like your team wrote it.

Same idea as [blader/humanizer](https://github.com/blader/humanizer), but for code. Humanizer fixes prose. This fixes functions.

## Installation

### Cursor

```bash
mkdir -p ~/.cursor/skills
git clone https://github.com/hellozheat/no-more-slop.git ~/.cursor/skills/nomoreslop
```

Already cloned locally:

```bash
mkdir -p ~/.cursor/skills/nomoreslop
cp -r /path/to/no-more-slop/* ~/.cursor/skills/nomoreslop/
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/hellozheat/no-more-slop.git ~/.claude/skills/nomoreslop
```

Already cloned locally:

```bash
mkdir -p ~/.claude/skills/nomoreslop
cp -r /path/to/no-more-slop/* ~/.claude/skills/nomoreslop/
```

### OpenCode

```bash
mkdir -p ~/.config/opencode/skills
git clone https://github.com/hellozheat/no-more-slop.git ~/.config/opencode/skills/nomoreslop
```

OpenCode also reads `~/.claude/skills/`. If you use Claude Code and OpenCode, one clone under `~/.claude/skills/nomoreslop/` is enough.

## Usage

```
/nomoreslop

Humanize the diff against main
```

Or plain language:

```
Remove slop from src/auth/login.ts
```

### Style calibration

Point at a file that already looks right:

```
/nomoreslop

Match the style in src/users/listUsers.ts

Now humanize:
src/checkout/cart.ts
```

It copies naming, comment density, imports, and idioms from neighbors instead of producing generic "clean" code.

## Overview

AI code usually compiles. It also ships with docstrings on three-line functions, `# Step 1:` comments, names like `processUserDataList`, hand-rolled `groupBy` when lodash is already in the repo, and `catch (e) { return null }`.

nomoreslop finds that stuff, rewrites by hand (not a regex script), rescoring after, then a second pass for anything still obviously AI. Behavior stays the same unless removing a swallow-all catch changes the failure path. That gets called out.

LLMs write toward the average repo. Yours isn't average. Read the file next door and match it.

## 22 Patterns Detected (with Before/After Examples)

Full list: [PATTERNS.md](PATTERNS.md)

### Comments and docs


| #   | Pattern                    | Before                                        | After                            |
| --- | -------------------------- | --------------------------------------------- | -------------------------------- |
| 1   | Trivial docstrings         | `"""Adds two numbers and returns the sum."""` | (remove)                         |
| 2   | Comments that restate code | `// Increment counter` above `counter++`      | (remove)                         |
| 3   | Step banners               | `# Step 1: Fetch users`                       | (remove)                         |
| 4   | Tutorial voice             | `# Here we validate the input`                | `# skip rows from legacy import` |
| 5   | Emoji narration            | `console.log("✅ Success!")`                   | (remove or real logger)          |
| 6   | Placeholder TODOs          | `# TODO: your logic here`                     | (remove or `TODO(PROJ-123): …`)  |
| 7   | Uniform comment density    | Every line commented                          | Few uneven *why* comments        |


### Naming


| #   | Pattern              | Before                         | After                       |
| --- | -------------------- | ------------------------------ | --------------------------- |
| 8   | Verbose names        | `totalUserInputCharacterCount` | `charCount`                 |
| 9   | Generic names        | `processData(data)`            | `parseInvoice(raw)`         |
| 10  | Non-idiomatic locals | `for (let index = 0; …)`       | `for (const item of items)` |


### Structure


| #   | Pattern            | Before                         | After                   |
| --- | ------------------ | ------------------------------ | ----------------------- |
| 11  | Over-engineering   | Factory for one use case       | Plain function          |
| 12  | Single-use helpers | 3-line fn called once          | Inline                  |
| 13  | Status envelopes   | `{ status: 'success', data }`  | Return `data` or throw  |
| 14  | Eerie uniformity   | Same comment style on every fn | Match neighbor variance |


### Error handling


| #   | Pattern               | Before                           | After                                     |
| --- | --------------------- | -------------------------------- | ----------------------------------------- |
| 15  | Swallow-all catch     | `catch (e) { return null }`      | Throw or catch specific (note the change) |
| 16  | Redundant null checks | Guard after typed non-null param | Remove unreachable guard                  |


### Types, idioms, imports


| #   | Pattern              | Before                                | After                   |
| --- | -------------------- | ------------------------------------- | ----------------------- |
| 17  | Useless type hints   | `: string` on `'hello'` in loose repo | Trim; keep in strict TS |
| 18  | Throwaway demo main  | Appended `if __name__ == '__main__'`  | Remove                  |
| 19  | Markdown in comments | `# **Important*`*                     | Plain text              |
| 20  | Non-idiomatic loops  | `range(len(x))`                       | `enumerate` / `for..of` |
| 21  | Dead imports         | Unused imports                        | Remove                  |


### Audit


| #   | Pattern           | Before             | After                      |
| --- | ----------------- | ------------------ | -------------------------- |
| 22  | Hallucinated APIs | Import not in repo | Report; don't invent a fix |


### Library slop (dep already in `package.json`)


| Pattern            | Before                          | After                               |
| ------------------ | ------------------------------- | ----------------------------------- |
| Manual groupBy     | `Object.keys(x).reduce(...)`    | `groupBy(items, 'key')`             |
| JSON clone         | `JSON.parse(JSON.stringify(x))` | `structuredClone(x)` or `cloneDeep` |
| Manual date format | `getFullYear()` string hacks    | `format(date, 'yyyy-MM-dd')`        |


Won't add npm packages without you saying so.

## Full Example

**Before:**

```typescript
function processUserData(userDataList) {
  try {
    // Step 1: Initialize the list to store active users
    const activeUsersList = [];
    // Step 2: Loop through each user
    for (let index = 0; index < userDataList.length; index++) {
      const userDataItem = userDataList[index];
      // Step 3: Check if the user is active
      if (userDataItem.isActive === true) {
        activeUsersList.push(userDataItem);
      }
    }
    console.log("✅ Successfully processed user data!");
    return activeUsersList;
  } catch (error) {
    console.log("❌ An error occurred:", error);
    return null;
  }
}
```

**After:**

```typescript
function activeUsers(users) {
  return users.filter((u) => u.isActive);
}
```

Removing the blanket `catch` means bad input throws instead of returning `null`. Same result on the happy path.

More in [examples/](examples/).

## Scoring

`scripts/score.py` is stdlib Python. Lower is better; 35 or under passes.

```bash
python scripts/score.py --repo /path/to/your/app --base main --json
```

Copy [.nomoresloprc.example](.nomoresloprc.example) to `.nomoresloprc` in the repo you're cleaning up.

## Modes


| Mode      | Flag               | When                          |
| --------- | ------------------ | ----------------------------- |
| calibrate | default            | Match neighbors               |
| clean     | `--clean-only`     | Strip slop, small diff        |
| inject    | `--inject-signals` | Optional terse *why* comments |


## References

- [blader/humanizer](https://github.com/blader/humanizer)
- [PATTERNS.md](PATTERNS.md)
- [LIBRARIES.md](LIBRARIES.md)
- [docs/rocky-workflow.md](docs/rocky-workflow.md)

## Version History

- **1.0.0** - 22 patterns, neighbor calibration, library rewrites, bundled scorer.

## License

MIT