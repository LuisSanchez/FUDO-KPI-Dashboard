# E2E (Playwright)

Optional end-to-end suite. Not part of the Railway/Docker image and **not** required by pre-commit (unit tests + coverage are). Project map: [AGENTS.md](../AGENTS.md).

Run locally with services up:

```bash
# terminal 1: backend + frontend (or make run)
# terminal 2:
cd e2e && npm i && npx playwright install chromium && npm test
```

Env:

- `E2E_BASE_URL` (default `http://localhost:3000`)
- `E2E_API_URL` (default `http://localhost:8000`)
