#!/usr/bin/env bash
# Frontend unit tests (Jest) with coverage threshold ≥75% (package.json jest.coverageThreshold).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

if [[ ! -d node_modules ]]; then
  npm install --no-fund --no-audit
fi

CI=true npm run test:ci
