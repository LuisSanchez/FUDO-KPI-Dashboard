#!/usr/bin/env bash
# Backend unit tests with coverage gate (fail_under=75 via .coveragerc).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="${PYTHON:-python3}"
fi

export DEBUG="${DEBUG:-True}"
export DJANGO_SETTINGS_MODULE=pizza_simulator.settings

# Prefer venv pytest; fall back to module invocation.
if [[ -x "${ROOT}/.venv/bin/pytest" ]]; then
  "${ROOT}/.venv/bin/pytest"
else
  "$PY" -m pytest
fi
