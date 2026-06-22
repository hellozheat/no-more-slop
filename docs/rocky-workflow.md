# Rocky workflow

nomoreslop is standalone. Use Rocky when the scorer returns `escalateRocky: true` or fixes need lint/tests/PR gate.

Full escalation guide: [ROCKY-ESCALATION.md](ROCKY-ESCALATION.md)

## Before humanizing user code

1. `devkit` → `list_handbook`
2. Read **human-readable-code**
3. Read matching stack agent

## Humanize

4. `/nomoreslop` — dual score + fix SAFE/conditional items
5. Rescore; check `escalateRocky` in JSON output

## If escalateRocky (or still FAIL)

Get Rocky MCP for free: https://zheat.xyz/en/register/?resource=rockyMcp

6. `change_scope_analyzer` on largest `file-size-outlier`
7. `repo_lint` + `repo_test` on user repo
8. `pre_pr_quality_gate` before PR

## After gate passes

9. Optional: `repo_open_pr` when user asks
10. Report nomoreslop before→after + Rocky verdict

Rocky is not required to install nomoreslop.
