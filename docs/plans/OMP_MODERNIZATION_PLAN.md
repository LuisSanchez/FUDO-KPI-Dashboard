# OMP Modernization Plan — Stacked PRs (dev base, never main/dev direct)

**Base branch:** `origin/dev`  
**Never commit to:** `main`, `dev` directly  
**Deploy constraint:** Railway single-image Docker (`Dockerfile` → gunicorn + migrate). All changes must keep CMD compatible.

---

## Blocker: Linear MCP

Linear MCP (`composio`) requires re-auth. Issues below are mirrored in `docs/linear-issues/LUI-OMP-*.md` for import into [LUI project](https://linear.app/luis-sanchez/team/LUI/projects/all). Re-run issue creation once MCP is connected.

---

## SOLID / Architecture issues (current state)

| Issue | Principle violated | Location |
|-------|-------------------|----------|
| God module `data_processing.py` (~1388 LOC) | SRP | backend/simulator/data_processing.py |
| Views do I/O + orchestration + response shaping | SRP / DIP | backend/simulator/views.py |
| Session pickle storage only (no user model) | OCP / extensibility | models.py |
| No tests | regression risk | tests/ empty |
| SQLite only; Neon unused | deploy/prod mismatch | settings.py |
| No auth | security | entire app |
| App.js owns all state | SRP frontend | frontend/src/App.js |
| Business constants scattered | DRY | UBER_COMMISSION_RATE ok; patch magic elsewhere |

---

## Stack priority (each stack = Graphite PR chain → merge to `dev`)

### 🔴 STACK 1 — CRITICAL: Test foundation + Railway-safe CI
**Branch:** `stack/01-tests-foundation`  
**Linear:** LUI-OMP-001 … 004  
**Goal:** Lock current behavior before refactors. CI runs unit tests without changing Railway deploy path.

| PR | Branch | Scope |
|----|--------|-------|
| 1.1 | `stack/01-tests-foundation` | pytest config, conftest fixtures, unit tests for validators/cleanup/KPI/Uber constants |
| 1.2 | (same or child) | GitHub Actions `test.yml` (SQLite only; optional, does not block Railway) |
| 1.3 | | Makefile `test` target; requirements-dev.txt |

**Railway safety:** No Dockerfile/CMD changes. Tests are opt-in in CI; production image unchanged.

---

### 🟠 STACK 2 — HIGH: Backend separation of concerns
**Branch:** `stack/02-backend-soc` (depends on stack/01)  
**Linear:** LUI-OMP-010 … 015  

| PR | Scope |
|----|-------|
| 2.1 | Extract `processing/constants.py`, `processing/validators.py`, `processing/sales_cleanup.py` |
| 2.2 | Extract `processing/kpi.py`, `processing/charts.py`, `processing/tables.py` |
| 2.3 | Extract `processing/uber_eats.py`, `processing/advisor.py`, `processing/sunday.py` |
| 2.4 | `data_processing.py` becomes thin re-export facade (zero behavior change) |
| 2.5 | `services/session_store.py` — isolate pickle session I/O from views |

**Railway safety:** Import paths preserved via facade; no API contract changes.

---

### 🟠 STACK 3 — HIGH: Neon Postgres + Google Auth
**Branch:** `stack/03-neon-google-auth` (depends on stack/02)  
**Linear:** LUI-OMP-020 … 028  

| PR | Scope |
|----|-------|
| 3.1 | `DATABASE_URL` support (Neon/Postgres when set; SQLite fallback for local/Railway without URL) |
| 3.2 | Additive models: `UserProfile` (google_id, email); extend session store with optional `user` FK — **no data deletion** |
| 3.3 | Google OAuth backend (`django-allauth` or custom ID token verify) |
| 3.4 | Auth endpoints: `/api/auth/google/`, `/api/auth/me/`, `/api/auth/logout/` |
| 3.5 | Frontend `GoogleSignIn` + optional gate (env `REACT_APP_REQUIRE_AUTH`) |
| 3.6 | Railway/Neon env docs; migrations additive only |

**Neon branch:** `br-cold-sky-ah5al4jn` — only ADD columns/tables; never DROP/TRUNCATE.

**Railway safety:** If `DATABASE_URL` unset, behavior identical to today (SQLite). Google auth optional via env flags.

---

### 🟡 STACK 4 — MEDIUM: E2E testing
**Branch:** `stack/04-e2e-playwright` (depends on stack/01)  
**Linear:** LUI-OMP-030 … 034  

| PR | Scope |
|----|-------|
| 4.1 | Playwright config in `e2e/` |
| 4.2 | Smoke: app loads, upload zones visible |
| 4.3 | API contract tests via Playwright request (optional with fixture xlsx) |
| 4.4 | CI job `e2e` (manual/nightly; not required for Railway deploy) |

---

### 🟢 STACK 5 — LOW: Frontend SoC + regression guards
**Branch:** `stack/05-frontend-soc` (depends on stack/03 for auth UI)  
**Linear:** LUI-OMP-040 … 045  

| PR | Scope |
|----|-------|
| 5.1 | `hooks/useSimulatorData.js` — extract upload/calculate from App.js |
| 5.2 | `api/client.js` — central axios instance |
| 5.3 | `pages/DashboardPage.js` — thin App shell |
| 5.4 | Component smoke tests (RTL) for formatters/KPI bar |

---

## Execution order (Graphite)

```
origin/dev
  └─ stack/01-tests-foundation          ──► PR → dev
       ├─ stack/02-backend-soc          ──► PR → dev (after 01)
       │    └─ stack/03-neon-google-auth ──► PR → dev (after 02)
       ├─ stack/04-e2e-playwright       ──► PR → dev (after 01, parallel with 02)
       └─ stack/05-frontend-soc         ──► PR → dev (after 03)
```

---

## Env vars (document in README; set in Railway/Neon)

```
# Existing
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=*

# Stack 3 — optional, safe defaults
DATABASE_URL=postgresql://...@ep-....neon.tech/neondb?sslmode=require
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_OAUTH_ENABLED=False   # True only when keys configured
REACT_APP_GOOGLE_CLIENT_ID=
REACT_APP_REQUIRE_AUTH=False  # keep False on Railway until auth verified
```

---

## Acceptance criteria (all stacks)

1. `docker build` + `CMD migrate && gunicorn` still works without new env vars.
2. Existing `/api/*` routes unchanged unless auth explicitly enabled.
3. Neon: migrations additive; no destructive SQL.
4. Tests pass locally: `make test`.
5. No commits on `main` or `dev`; all via stacked PRs.
