"""Ask Grok, through OpenRouter, about the local analytics database.

The model only sees the numbers by calling `consultar_sql`. Nothing is sent
to the browser except the answer and a short note of each search.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings

from simulator.services.analytics_db import QueryError, run_select

_MAX_MESSAGES = 16
_MAX_CHARS = 4000
_MAX_ROUNDS = 4
_TIMEOUT_SECONDS = 90

_SYSTEM = """Eres el analista de Oh My Pizza Cantagallo. Respondes en español, claro y corto, con pesos chilenos.

Solo puedes usar la base SQLite que consultas con la herramienta consultar_sql. Si el dato no está, dilo. No completes huecos ni uses conocimientos externos para inventar un monto.

Tablas:
- meses: un resumen por mes, ya cuadrado con la pantalla. Úsala para EBITDA, resultado, sueldos y depósitos.
- ventas: una fila por línea de FUDO. precio, descuento y cobrado traen IVA. costo_sin_iva es solo ingredientes, neto de IVA.
- gastos: una fila por gasto. importe como lo registró FUDO. entra_en_ebitda=0 queda fuera (préstamo, activo fijo o cancelado). es_pago_gente y es_previred parten el personal.
- uber: liquidación PDF del mes. tasa, anuncios y ajustes vienen con el signo del PDF (negativo es un cargo). deposito es el total neto. comision_neta es la tasa sin IVA.
- reglas: las definiciones. Léelas antes de explicar un total.
- meta: fuente (sesion, archivo o vacio) y firma.

Reglas que no puedes romper:
- EBITDA y resultado salen de meses. No los reconstruyas sumando líneas salvo que pidan el detalle, y entonces respeta entra_en_ebitda y meses.sueldos_usados.
- No dividas los gastos por 1.19.
- No restes el depósito ni los anuncios del resultado. Esos números se muestran aparte.
- Los sueldos de meses.sueldos_usados reemplazan el pago a la gente. El Previred sigue dentro de los gastos.
- Si meta.fuente es vacio, di que todavía no hay archivos cargados.

Cuando des un total, di el mes y la cifra. Si comparas meses, usa la misma columna."""


class ChatError(Exception):
    """The chat could not answer. `status_code` is the HTTP status to return."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def ask(
    db_path: Path,
    messages,
    *,
    transport=None,
    model=None,
    base_url=None,
    api_key=None,
    allow_without_key=False,
) -> dict:
    """Run the tool loop and return the Spanish answer plus the searches made.

    OpenRouter is the default. Ollama passes its own transport, model and base
    URL and sets allow_without_key so a missing OpenRouter key does not block it.
    """
    if api_key is None:
        key = getattr(settings, "OPENROUTER_API_KEY", "") or ""
    else:
        key = api_key
    if not allow_without_key and not str(key).strip():
        raise ChatError(
            "Falta OPENROUTER_API_KEY en el entorno. El chat queda apagado hasta que la agregues.",
            503,
        )
    conversation = [_system_message(), *normalize_messages(messages)]
    model = (model or _openrouter_model()).strip()
    base = (
        base_url or getattr(settings, "OPENROUTER_BASE_URL", "") or "https://openrouter.ai/api/v1"
    ).rstrip("/")
    send = transport or _post
    searches = []
    for _ in range(_MAX_ROUNDS):
        payload = send(
            f"{base}/chat/completions",
            {
                "model": model,
                "messages": conversation,
                "tools": [_TOOL],
                "tool_choice": "auto",
                "temperature": 0.2,
                "max_tokens": 2500,
                "reasoning": {"effort": "medium"},
            },
            key,
        )
        message = _choice_message(payload)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            reply = _content_text(message.get("content")).strip()
            if not reply:
                raise ChatError("El modelo no devolvió una respuesta.")
            return {"reply": reply, "consultas": searches, "modelo": model}
        conversation.append(_assistant_message(message))
        for call in tool_calls:
            result, search = _run_tool(db_path, call)
            searches.append(search)
            conversation.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id") or "",
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
    raise ChatError("La consulta quedó a medias. Prueba con una pregunta más acotada.")


def _openrouter_model() -> str:
    """Saved choice in Configuración, then the env default. A missing table stays on the env."""
    try:
        from simulator.services.ai_settings import effective_openrouter_model

        return effective_openrouter_model()
    except Exception:
        return getattr(settings, "OPENROUTER_MODEL", "") or "x-ai/grok-4.7"


def normalize_messages(messages) -> list[dict]:
    """Keep a short user/assistant history. The last turn has to be the user."""
    if not isinstance(messages, list) or not messages:
        raise ChatError("Escribe una pregunta.", 400)
    cleaned = []
    for item in messages[-_MAX_MESSAGES:]:
        if not isinstance(item, dict):
            raise ChatError("La conversación llegó en un formato inválido.", 400)
        role = item.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = _content_text(item.get("content")).strip()
        if not content:
            continue
        cleaned.append({"role": role, "content": content[:_MAX_CHARS]})
    if not cleaned or cleaned[-1]["role"] != "user":
        raise ChatError("Escribe una pregunta.", 400)
    return cleaned


def _run_tool(db_path: Path, call: dict) -> tuple[dict, dict]:
    function = call.get("function") or {}
    name = function.get("name") or ""
    arguments = function.get("arguments") or "{}"
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    sql = str(arguments.get("sql") or "")
    reason = str(arguments.get("razon") or "").strip()[:300]
    search = {"razon": reason, "filas": 0, "error": None}
    if name != "consultar_sql":
        search["error"] = "Herramienta desconocida."
        return {"error": search["error"]}, search
    try:
        found = run_select(db_path, sql)
    except QueryError as exc:
        search["error"] = str(exc)
        return {"error": str(exc)}, search
    search["filas"] = len(found["filas"])
    return found, search


def _choice_message(payload: dict) -> dict:
    try:
        return payload["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ChatError("OpenRouter respondió sin una respuesta utilizable.") from exc


def _assistant_message(message: dict) -> dict:
    kept = {"role": "assistant", "content": message.get("content")}
    if message.get("tool_calls"):
        kept["tool_calls"] = message["tool_calls"]
    for key in ("reasoning", "reasoning_details"):
        if message.get(key):
            kept[key] = message[key]
    return kept


def _content_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(str(part.get("text") or ""))
        return "".join(parts)
    return str(content)


def _system_message() -> dict:
    return {"role": "system", "content": _SYSTEM}


def _post(url: str, body: dict, api_key: str) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "FUDO Analytics",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = _http_detail(exc)
        if exc.code in {401, 403}:
            raise ChatError("OpenRouter rechazó la clave. Revisa OPENROUTER_API_KEY.", 502) from exc
        raise ChatError(detail or f"OpenRouter respondió {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise ChatError("No pude llegar a OpenRouter.") from exc
    except TimeoutError as exc:
        raise ChatError("OpenRouter no respondió a tiempo.") from exc
    try:
        parsed = json.loads(raw.decode())
    except json.JSONDecodeError as exc:
        raise ChatError("OpenRouter respondió algo que no es JSON.") from exc
    if not isinstance(parsed, dict):
        raise ChatError("OpenRouter respondió algo que no es JSON.")
    return parsed


def _http_detail(exc: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(exc.read().decode())
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return ""
    error = body.get("error") if isinstance(body, dict) else None
    if isinstance(error, dict):
        return str(error.get("message") or "")
    if isinstance(error, str):
        return error
    return ""


_TOOL = {
    "type": "function",
    "function": {
        "name": "consultar_sql",
        "description": (
            "Ejecuta un SELECT de solo lectura sobre la base de Oh My Pizza. "
            "Una sola sentencia, sin comentarios. Como máximo 200 filas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "Un SELECT o WITH."},
                "razon": {
                    "type": "string",
                    "description": "Para qué es la consulta, en una frase corta.",
                },
            },
            "required": ["sql"],
        },
    },
}
