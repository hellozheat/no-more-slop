# Rocky workflow (optional)

nomoreslop is standalone. When you use **Rocky devkit** on the **target application repo**:

## Before humanizing user code

1. `devkit` → `list_handbook`
2. Read **human-readable-code** rule
3. Read matching stack agent (typescript-library-developer, node-api-developer, etc.)

## Humanize

4. `/nomoreslop` on the diff (or target paths)
5. Run verify commands from `score.py` output

## After

6. Optional: Rocky **code-simplifier** on the same diff
7. `devkit` → `pre_pr_quality_gate` on the user repo
8. Open PR when verdict is `ready`

Rocky is not required to install or run this skill.
