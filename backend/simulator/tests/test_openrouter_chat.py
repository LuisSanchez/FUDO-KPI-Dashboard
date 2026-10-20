"""OpenRouter tool loop for questions about the local numbers."""

import io
import json
import urllib.error
from pathlib import Path

import pytest

from simulator.services.analytics_db import write_database
from simulator.services.openrouter_chat import ChatError, _post, ask
from simulator.tests.test_analytics_db import _expenses, _sales


def _database(tmp_path):
    dest = tmp_path / "chat.sqlite3"
    write_database(_sales(), _expenses(), {}, [], dest, "sesion", "firma")
    return dest


def test_missing_key_keeps_the_chat_off(settings, tmp_path):
    settings.OPENROUTER_API_KEY = "  "
    with pytest.raises(ChatError) as caught:
        ask(tmp_path / "missing.sqlite3", [{"role": "user", "content": "hola"}])
    assert caught.value.status_code == 503


def test_ask_searches_and_then_answers(settings, tmp_path):
    settings.OPENROUTER_API_KEY = "secret"
    settings.OPENROUTER_MODEL = "x-ai/grok-4.7"
    seen = []

    def transport(url, body, key):
        seen.append((url, body, key))
        if len(seen) == 1:
            return {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "reasoning_details": [{"step": 1}],
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "consultar_sql",
                                        "arguments": json.dumps(
                                            {
                                                "sql": "SELECT SUM(cobrado) AS total FROM ventas",
                                                "razon": "cobrado de septiembre",
                                            }
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        assistant = [item for item in body["messages"] if item["role"] == "assistant"][-1]
        tool = [item for item in body["messages"] if item["role"] == "tool"][-1]
        assert assistant["reasoning_details"] == [{"step": 1}]
        assert "16980" in tool["content"]
        return {"choices": [{"message": {"content": "El cobrado fue $16.980."}}]}

    result = ask(
        _database(tmp_path),
        [{"role": "user", "content": "¿Cuánto se cobró en septiembre?"}],
        transport=transport,
    )
    assert result["reply"] == "El cobrado fue $16.980."
    assert result["modelo"] == "x-ai/grok-4.7"
    assert result["consultas"] == [{"razon": "cobrado de septiembre", "filas": 1, "error": None}]
    assert seen[0][2] == "secret"
    assert seen[0][0].endswith("/chat/completions")
    assert seen[0][1]["tools"][0]["function"]["name"] == "consultar_sql"


def test_a_rejected_query_is_handed_back_to_the_model(settings, tmp_path):
    settings.OPENROUTER_API_KEY = "secret"
    calls = {"n": 0}

    def transport(_url, body, _key):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "call-2",
                                    "type": "function",
                                    "function": {
                                        "name": "consultar_sql",
                                        "arguments": json.dumps({"sql": "DELETE FROM ventas"}),
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        tool = [item for item in body["messages"] if item["role"] == "tool"][-1]
        assert "Solo se acepta un SELECT de lectura." in tool["content"]
        return {"choices": [{"message": {"content": "No pude borrar nada. El cobrado sigue."}}]}

    result = ask(
        _database(tmp_path), [{"role": "user", "content": "borra las ventas"}], transport=transport
    )
    assert result["consultas"][0]["error"]
    assert result["reply"].startswith("No pude borrar")


def test_blank_question_is_rejected(settings, tmp_path):
    settings.OPENROUTER_API_KEY = "secret"
    with pytest.raises(ChatError) as caught:
        ask(tmp_path / "x.sqlite3", [{"role": "assistant", "content": "hola"}])
    assert caught.value.status_code == 400


def test_unauthorized_key_is_a_clear_error(monkeypatch):
    def boom(*_args, **_kwargs):
        raise urllib.error.HTTPError(
            url="https://openrouter.ai",
            code=401,
            msg="unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"error":{"message":"bad key"}}'),
        )

    monkeypatch.setattr("simulator.services.openrouter_chat.urllib.request.urlopen", boom)
    with pytest.raises(ChatError) as caught:
        _post("https://openrouter.ai/api/v1/chat/completions", {}, "secret")
    assert caught.value.status_code == 502
    assert "OPENROUTER_API_KEY" in str(caught.value)


@pytest.mark.django_db
def test_chat_endpoint_stays_off_without_a_key(api_client, settings):
    settings.OPENROUTER_API_KEY = ""
    response = api_client.post(
        "/api/chat/",
        {"messages": [{"role": "user", "content": "hola"}]},
        format="json",
    )
    assert response.status_code == 503
    assert "OPENROUTER_API_KEY" in response.data["error"]


@pytest.mark.django_db
def test_chat_endpoint_returns_the_model_answer(api_client, settings, monkeypatch):
    settings.OPENROUTER_API_KEY = "secret"

    monkeypatch.setattr(
        "simulator.views.ensure_chat_database", lambda _store: Path("cache.sqlite3")
    )
    monkeypatch.setattr(
        "simulator.views.ask",
        lambda _path, messages: {
            "reply": "Septiembre quedó corto.",
            "consultas": [{"razon": "ebitda", "filas": 1, "error": None}],
            "modelo": "x-ai/grok-4.7",
        },
    )
    response = api_client.post(
        "/api/chat/",
        {"messages": [{"role": "user", "content": "¿cómo viene septiembre?"}]},
        format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["reply"] == "Septiembre quedó corto."
    assert response.data["consultas"][0]["filas"] == 1
