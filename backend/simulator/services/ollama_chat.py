"""Talk to a local Ollama with the same tool loop as OpenRouter."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from simulator.services.ai_settings import effective_ollama_base, get_row
from simulator.services.openrouter_chat import ChatError, ask

_CHAT_TIMEOUT = 90
_TAGS_TIMEOUT = 5


def list_models(base_url: str | None = None) -> list[str]:
    root = _host_root(base_url or effective_ollama_base())
    payload = _get_json(f"{root}/api/tags", _TAGS_TIMEOUT)
    models = payload.get("models") if isinstance(payload, dict) else None
    names = []
    for item in models or []:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return names


def ask_ollama(db_path, messages) -> dict:
    row = get_row()
    model = (row.ollama_model or "").strip()
    if not model:
        raise ChatError("Elige un modelo de Ollama en Configuración.", 400)
    return ask(
        db_path,
        messages,
        transport=ollama_transport,
        model=model,
        base_url=_openai_base(effective_ollama_base(row)),
        api_key="local",
        allow_without_key=True,
    )


def ollama_transport(url: str, body: dict, _api_key: str) -> dict:
    payload = {key: value for key, value in body.items() if key != "reasoning"}
    return _post_json(url, payload, _CHAT_TIMEOUT)


def _openai_base(base_url: str) -> str:
    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        return root
    return f"{root}/v1"


def _host_root(base_url: str) -> str:
    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        return root[: -len("/v1")]
    return root


def _get_json(url: str, timeout: int) -> dict:
    request = urllib.request.Request(url, method="GET")
    return _read(request, timeout)


def _post_json(url: str, body: dict, timeout: int) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return _read(request, timeout)


def _read(request: urllib.request.Request, timeout: int) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in {400, 404} and request.get_method() == "POST":
            raise ChatError(
                "Ese modelo de Ollama no acepta herramientas. Elige otro en Configuración.",
                502,
            ) from exc
        if exc.code in {400, 404}:
            raise ChatError("Ollama no devolvió la lista de modelos.", 502) from exc
        raise ChatError(f"Ollama respondió {exc.code}.", 502) from exc
    except urllib.error.URLError as exc:
        raise ChatError(
            "No pude llegar a Ollama. Revisa que esté corriendo y la dirección en Configuración.",
            502,
        ) from exc
    except TimeoutError as exc:
        raise ChatError("Ollama no respondió a tiempo.", 502) from exc
    try:
        parsed = json.loads(raw.decode())
    except json.JSONDecodeError as exc:
        raise ChatError("Ollama respondió algo que no es JSON.", 502) from exc
    if not isinstance(parsed, dict):
        raise ChatError("Ollama respondió algo que no es JSON.", 502)
    return parsed
