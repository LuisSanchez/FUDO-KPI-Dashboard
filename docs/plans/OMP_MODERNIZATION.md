# OMP Modernization — historical stack plan

Originally tracked as stacked PRs toward `dev`. **Status: landed on `main`** (fast-forward merge of stack tip `stack/05-frontend-soc`, then quality/pre-commit work).

| Priority | Stack branch | Scope | Status |
|----------|--------------|--------|--------|
| Critical | `stack/01-tests-foundation` | pytest + CI (SQLite) | Merged |
| High | `stack/02-backend-soc` | processing/ + session_store | Merged |
| High | `stack/03-neon-google-auth` | DATABASE_URL + Google OAuth | Merged |
| Medium | `stack/04-e2e-playwright` | Playwright package | Merged |
| Low | `stack/05-frontend-soc` | api client, hooks, DashboardPage | Merged |
| Follow-up | (on `main`) | Unit coverage ≥75%, pre-commit, docs | Done |

## Current working rules

- Prefer **`main`** for integrated work unless the team re-opens a stack.
- GitHub default branch may still be `dev` — keep `dev` in sync when shipping if deploy tracks it.
- Railway: SQLite unless `DATABASE_URL` is set. OAuth remains optional.
- Agent map: [`AGENTS.md`](../../AGENTS.md). Auth/DB: [`docs/AUTH_AND_NEON.md`](../AUTH_AND_NEON.md).
