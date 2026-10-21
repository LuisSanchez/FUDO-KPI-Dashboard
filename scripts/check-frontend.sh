#!/usr/bin/env bash
# Frontend unit tests (Vitest) with coverage thresholds in vite.config.js.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

if [[ ! -d node_modules ]]; then
  npm install --no-fund --no-audit
fi

CI=true npm run test:ci
