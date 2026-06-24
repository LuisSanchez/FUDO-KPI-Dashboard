# Google Auth + Neon Postgres (Stack 3)

## Railway safety

| Env var | Default | Effect if unset |
|---------|---------|-----------------|
| `DATABASE_URL` | (empty) | SQLite `backend/db.sqlite3` — **current Railway behavior** |
| `GOOGLE_OAUTH_ENABLED` | `False` | Auth endpoints return 503; app works anonymously |
| `REQUIRE_AUTH` | `False` | All existing `/api/*` routes remain public |
| `GOOGLE_CLIENT_ID` | (empty) | Required only when OAuth enabled |
| `GOOGLE_CLIENT_SECRET` | (empty) | Reserved for server-side flows; ID token verify uses client id only |

**Dockerfile CMD unchanged:** `migrate && gunicorn`. Migrations are additive only.

## Neon setup (do not delete data)

1. Project: `silent-bar-52888891`, branch: `br-cold-sky-ah5al4jn`
2. Copy connection string from Neon console → set as `DATABASE_URL` on Railway (or local `.env`)
3. Run migrate (happens automatically on container start):
   - Creates `simulator_user_profile` (new)
   - Adds nullable `user_id` on `simulator_user_session` (existing rows untouched)
4. **Never** run `flush`, `DROP TABLE`, or reset Neon branch from this app

## Google OAuth setup

1. [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. OAuth 2.0 Client ID (Web application)
3. Authorized JavaScript origins: your Railway URL + `http://localhost:3000`
4. Set on Railway / local:
   ```
   GOOGLE_OAUTH_ENABLED=True
   GOOGLE_CLIENT_ID=....apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=...   # optional for ID-token-only flow
   REQUIRE_AUTH=False         # set True only after verifying login works
   ```
5. Frontend: optional `REACT_APP_GOOGLE_CLIENT_ID` (backend `/api/auth/config/` is source of truth)

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/config/` | `{ oauth_enabled, require_auth, google_client_id }` |
| GET | `/api/auth/me/` | Current user or anonymous |
| POST | `/api/auth/google/` | Body `{ credential: <GIS id_token> }` → session login |
| POST | `/api/auth/logout/` | Clear session |

## Local test with Neon

```bash
export DATABASE_URL="postgresql://...@ep-....neon.tech/neondb?sslmode=require"
cd backend && python manage.py migrate
python manage.py runserver
```

## Linear issues

LUI-OMP-020 … LUI-OMP-025 (see `docs/linear-issues/`)
