"""The saved choice between OpenRouter and a local Ollama."""

from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings
from django.db import OperationalError, ProgrammingError

from simulator.models import AiSettings

PROVIDERS = {"openrouter", "ollama"}
_MAX_MODEL = 120
_MAX_URL = 300


class AiSettingsError(Exception):
    """The super admin sent a choice this server will not store."""


def get_row() -> AiSettings:
    row, _created = AiSettings.objects.get_or_create(pk=1, defaults={"provider": "openrouter"})
    return row


def chat_provider() -> str:
    """openrouter or ollama. A missing table still means OpenRouter, so chat keeps its old 503."""
    try:
        row = get_row()
    except (OperationalError, ProgrammingError):
        return "openrouter"
    if row.provider == "ollama":
        return "ollama"
    return "openrouter"


def snapshot(row: AiSettings | None = None) -> dict:
    row = row or get_row()
    provider = row.provider if row.provider in PROVIDERS else "openrouter"
    return {
        "provider": provider,
        "openrouter_model": row.openrouter_model,
        "ollama_model": row.ollama_model,
        "ollama_base_url": row.ollama_base_url,
        "defaults": {
            "openrouter_model": _default_openrouter_model(),
            "ollama_base_url": _default_ollama_base(),
        },
        "openrouter_configured": bool((getattr(settings, "OPENROUTER_API_KEY", "") or "").strip()),
    }


def update_settings(payload) -> dict:
    if not isinstance(payload, dict):
        raise AiSettingsError("La configuración llegó en un formato inválido.")
    provider = str(payload.get("provider") or "").strip().lower()
    if provider not in PROVIDERS:
        raise AiSettingsError("Elige OpenRouter u Ollama.")
    openrouter_model = _clean_model(payload.get("openrouter_model"))
    ollama_model = _clean_model(payload.get("ollama_model"))
    ollama_base_url = _clean_url(payload.get("ollama_base_url"))
    if provider == "ollama" and not ollama_model:
        raise AiSettingsError("Elige un modelo de Ollama.")
    row = get_row()
    row.provider = provider
    row.openrouter_model = openrouter_model
    row.ollama_model = ollama_model
    row.ollama_base_url = ollama_base_url
    row.save()
    return snapshot(row)


def effective_openrouter_model(row: AiSettings | None = None) -> str:
    row = row or get_row()
    return (row.openrouter_model or "").strip() or _default_openrouter_model()


def effective_ollama_base(row: AiSettings | None = None) -> str:
    row = row or get_row()
    return (row.ollama_base_url or "").strip() or _default_ollama_base()


def resolve_ollama_base(value) -> str:
    """Use the typed address when the dialog asks for models, otherwise the saved one."""
    if value is None or not str(value).strip():
        return effective_ollama_base()
    return _clean_url(value) or _default_ollama_base()


def _default_openrouter_model() -> str:
    return (getattr(settings, "OPENROUTER_MODEL", "") or "x-ai/grok-4.7").strip()


def _default_ollama_base() -> str:
    return (getattr(settings, "OLLAMA_BASE_URL", "") or "http://127.0.0.1:11434").rstrip("/")


def _clean_model(value) -> str:
    text = str(value or "").strip()
    if any(char in text for char in "\n\r\t"):
        raise AiSettingsError("El nombre del modelo no es válido.")
    if len(text) > _MAX_MODEL:
        raise AiSettingsError("El nombre del modelo es demasiado largo.")
    return text


def _clean_url(value) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > _MAX_URL or any(char.isspace() for char in text):
        raise AiSettingsError("La dirección de Ollama no es válida.")
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AiSettingsError("La dirección de Ollama tiene que empezar por http:// o https://.")
    return text.rstrip("/")
