# OMP Modernization — Stacked PRs to `dev`

See Linear document: OMP Modernization Plan (v2 fresh start).

| Priority | Stack branch | Scope |
|----------|--------------|--------|
| Critical | `stack/01-tests-foundation` | pytest + CI (SQLite) |
| High | `stack/02-backend-soc` | SOLID split processing/services |
| High | `stack/03-neon-google-auth` | Neon DATABASE_URL + Google OAuth |
| Medium | `stack/04-e2e-playwright` | Playwright e2e package |
| Low | `stack/05-frontend-soc` | api client, hooks, DashboardPage |

Never touch `main`. No direct commits to `dev`. Railway uses SQLite unless `DATABASE_URL` set.
