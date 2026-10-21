"""OpenRouter or local Ollama, saved once and used by the chat."""

import json
import urllib.error
from pathlib import Path

import pytest

from simulator.models import AiSettings
from simulator.services.ai_settings import AiSettingsError, snapshot, update_settings
from simulator.services.ollama_chat import ask_ollama, list_models
from simulator.services.openrouter_chat import ChatError, ask


class _Body:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode()

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_a_blank_model_name_and_a_bad_url_are_rejected():
    with pytest.raises(AiSettingsError):
        update_settings({"provider": "gpt", "openrouter_model": "", "ollama_model": ""})
    with pytest.raises(AiSettingsError):
        update_settings("no")
    with pytest.raises(AiSettingsError):
        update_settings(
            {
                "provider": "ollama",
                "ollama_model": "llama3.1",
                "ollama_base_url": "file:///tmp/models",
            }
        )
    with pytest.raises(AiSettingsError):
        update_settings(
            {
                "provider": "ollama",
                "ollama_model": "",
                "ollama_base_url": "http://127.0.0.1:11434",
            }
        )
    with pytest.raises(AiSettingsError):
        update_settings(
            {
                "provider": "openrouter",
                "openrouter_model": "x-ai/grok\n4",
                "ollama_model": "",
            }
        )
    with pytest.raises(AiSettingsError):
        update_settings(
            {
                "provider": "openrouter",
                "openrouter_model": "x" * 121,
                "ollama_model": "",
            }
        )
    with pytest.raises(AiSettingsError):
        update_settings(
            {
                "provider": "ollama",
                "ollama_model": "llama3.1",
                "ollama_base_url": "http://bad host",
            }
        )


@pytest.mark.django_db
def test_the_choice_is_saved_and_a_blank_model_keeps_the_default(settings):
    settings.OPENROUTER_MODEL = "x-ai/grok-4.7"
    settings.OLLAMA_BASE_URL = "http://127.0.0.1:11434"
    saved = update_settings(
        {
            "provider": "openrouter",
            "openrouter_model": "",
            "ollama_model": "",
            "ollama_base_url": "",
        }
    )
    assert saved["provider"] == "openrouter"
    assert saved["openrouter_model"] == ""
    assert saved["defaults"]["openrouter_model"] == "x-ai/grok-4.7"
    assert saved["defaults"]["ollama_base_url"] == "http://127.0.0.1:11434"
    assert snapshot()["provider"] == "openrouter"
    row = AiSettings.objects.get(pk=1)
    row.provider = "weird"
    row.openrouter_model = "openai/gpt-test"
    row.save()
    assert snapshot()["provider"] == "openrouter"

    seen = {}

    def transport(_url, body, _key):
        seen["model"] = body["model"]
        return {"choices": [{"message": {"content": "ok"}}]}

    settings.OPENROUTER_API_KEY = "secret"
    settings.OPENROUTER_MODEL = "x-ai/grok-4.7"
    row.provider = "openrouter"
    row.save()
    result = ask(Path("unused.sqlite3"), [{"role": "user", "content": "hola"}], transport=transport)
    assert seen["model"] == "openai/gpt-test"
    assert result["modelo"] == "openai/gpt-test"


@pytest.mark.django_db
def test_ollama_answers_without_an_openrouter_key(settings, monkeypatch):
    settings.OPENROUTER_API_KEY = ""
    AiSettings.objects.update_or_create(
        pk=1,
        defaults={
            "provider": "ollama",
            "ollama_model": "llama3.1",
            "ollama_base_url": "http://127.0.0.1:11434",
            "openrouter_model": "",
        },
    )
    seen = {}

    def fake(request, timeout=90):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data.decode())
        return _Body({"choices": [{"message": {"content": "Septiembre quedó en rojo."}}]})

    monkeypatch.setattr("simulator.services.ollama_chat.urllib.request.urlopen", fake)
    result = ask_ollama(Path("unused.sqlite3"), [{"role": "user", "content": "¿y septiembre?"}])
    assert result["reply"] == "Septiembre quedó en rojo."
    assert result["modelo"] == "llama3.1"
    assert seen["url"] == "http://127.0.0.1:11434/v1/chat/completions"
    assert "reasoning" not in seen["body"]


def test_listing_models_and_a_stopped_server(monkeypatch):
    def tags(request, timeout=5):
        assert request.full_url == "http://127.0.0.1:11434/api/tags"
        return _Body({"models": [{"name": "llama3.1:latest"}, {"name": ""}]})

    monkeypatch.setattr("simulator.services.ollama_chat.urllib.request.urlopen", tags)
    assert list_models("http://127.0.0.1:11434/v1") == ["llama3.1:latest"]

    def down(request, timeout=5):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("simulator.services.ollama_chat.urllib.request.urlopen", down)
    with pytest.raises(ChatError) as caught:
        list_models("http://127.0.0.1:11434")
    assert caught.value.status_code == 502
    assert "Ollama" in str(caught.value)


@pytest.mark.django_db
def test_chat_uses_ollama_when_openrouter_has_no_key(api_client, settings, monkeypatch):
    settings.OPENROUTER_API_KEY = ""
    settings.CLERK_SECRET_KEY = ""
    AiSettings.objects.update_or_create(
        pk=1,
        defaults={"provider": "ollama", "ollama_model": "llama3.1", "ollama_base_url": ""},
    )
    monkeypatch.setattr(
        "simulator.views.ensure_chat_database", lambda _store: Path("cache.sqlite3")
    )

    def fake(request, timeout=90):
        return _Body({"choices": [{"message": {"content": "Listo desde Ollama."}}]})

    monkeypatch.setattr("simulator.services.ollama_chat.urllib.request.urlopen", fake)
    response = api_client.post(
        "/api/chat/",
        {"messages": [{"role": "user", "content": "¿cómo viene septiembre?"}]},
        format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["reply"] == "Listo desde Ollama."
    assert response.data["modelo"] == "llama3.1"


@pytest.mark.django_db
def test_chat_asks_for_an_ollama_model_before_calling_it(api_client, settings, monkeypatch):
    settings.OPENROUTER_API_KEY = ""
    settings.CLERK_SECRET_KEY = ""
    AiSettings.objects.update_or_create(
        pk=1,
        defaults={"provider": "ollama", "ollama_model": "", "ollama_base_url": ""},
    )
    monkeypatch.setattr(
        "simulator.views.ensure_chat_database", lambda _store: Path("cache.sqlite3")
    )
    response = api_client.post(
        "/api/chat/",
        {"messages": [{"role": "user", "content": "hola"}]},
        format="json",
    )
    assert response.status_code == 400
    assert "Ollama" in response.data["error"]


@pytest.mark.django_db
def test_settings_endpoints_when_clerk_is_off(api_client, settings, monkeypatch):
    settings.CLERK_SECRET_KEY = ""
    settings.OPENROUTER_API_KEY = ""
    current = api_client.get("/api/settings/ai/")
    assert current.status_code == 200
    assert current.data["provider"] == "openrouter"

    saved = api_client.put(
        "/api/settings/ai/",
        {
            "provider": "ollama",
            "openrouter_model": "x-ai/grok-4.7",
            "ollama_model": "qwen2.5",
            "ollama_base_url": "http://127.0.0.1:11434",
        },
        format="json",
    )
    assert saved.status_code == 200, saved.data
    assert saved.data["ollama_model"] == "qwen2.5"

    def tags(request, timeout=5):
        return _Body({"models": [{"name": "qwen2.5"}]})

    monkeypatch.setattr("simulator.services.ollama_chat.urllib.request.urlopen", tags)
    models = api_client.get("/api/settings/ai/ollama-models/")
    assert models.status_code == 200
    assert models.data["models"] == ["qwen2.5"]

    rejected = api_client.get(
        "/api/settings/ai/ollama-models/",
        {"base_url": "notaurl"},
    )
    assert rejected.status_code == 400

    invalid = api_client.put(
        "/api/settings/ai/",
        {"provider": "nope"},
        format="json",
    )
    assert invalid.status_code == 400

    def down(_request, timeout=5):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("simulator.services.ollama_chat.urllib.request.urlopen", down)
    stopped = api_client.get("/api/settings/ai/ollama-models/")
    assert stopped.status_code == 502
    assert "Ollama" in stopped.data["error"]
