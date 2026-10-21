# Auth & Neon (Railway-safe)

Optional features. Agent overview: [AGENTS.md](../AGENTS.md).

## Defaults (no env = current behavior)

- **SQLite** at `backend/db.sqlite3`
- **Clerk off** until `VITE_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` are set (see `env.sample`). The dashboard stays open on a single machine. With both keys, `/api/` requires a Clerk session JWT. `SUPER_ADMIN_EMAIL` is the only account that can change AI settings; the browser never receives that address.
- **Google OAuth (GIS) off** (`GOOGLE_OAUTH_ENABLED=False`) → `/api/auth/google/` returns **503**. The visible login is Clerk, not this GIS flow.
- Session upload flow works anonymously while Clerk is off

## Enable Neon Postgres

```bash
DATABASE_URL=postgresql://neondb_owner:***@ep-....neon.tech/neondb?sslmode=require
```

Then `python manage.py migrate --noinput` (additive only). Do **not** drop `public.sales_order` or `neon_auth.*`.

Neon branch used for prep: `br-cold-sky-ah5al4jn` (project `silent-bar-52888891`).

## Enable Google Sign-In

```bash
GOOGLE_OAUTH_ENABLED=True
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret   # reserved for server flows; GIS uses ID token verify
# optional hard gate once login is verified:
REQUIRE_AUTH=False
```

Frontend polls `GET /api/auth/config/`; `GoogleSignIn` renders only when `oauth_enabled` is true.

## Endpoints

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/auth/config/` | public |
| GET | `/api/auth/me/` | session user |
| POST | `/api/auth/google/` | body `{ "credential": "<gis id_token>" }` |
| POST | `/api/auth/logout/` | clear session |

## Railway

Leave `DATABASE_URL` and OAuth unset on Railway until ready; Docker CMD (`migrate` + gunicorn) is unchanged.
