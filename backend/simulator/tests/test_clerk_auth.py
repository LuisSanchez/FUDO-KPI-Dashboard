"""Clerk session checks. No network: the JWKS and the user record are faked."""

import io
import json
import time
import urllib.error

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from simulator.services.clerk_auth import (
    ClerkAuthError,
    clear_auth_cache,
    identity_from_request,
    is_super_admin,
)

OWNER = "owner@example.com"


@pytest.fixture(autouse=True)
def _empty_cache():
    clear_auth_cache()
    yield
    clear_auth_cache()


@pytest.fixture
def signer():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private.public_key()))
    jwk.update({"kid": "kid-1", "alg": "RS256", "use": "sig"})

    def mint(sub="user_1", exp_delta=120):
        token = jwt.encode(
            {"sub": sub, "exp": int(time.time()) + exp_delta},
            private,
            algorithm="RS256",
            headers={"kid": "kid-1"},
        )
        return token if isinstance(token, str) else token.decode()

    return jwk, mint


def _request(token):
    return type("Request", (), {"META": {"HTTP_AUTHORIZATION": f"Bearer {token}"}})()


def _user(email, status="verified"):
    return {
        "primary_email_address_id": "em_1",
        "email_addresses": [
            {
                "id": "em_1",
                "email_address": email,
                "verification": {"status": status},
            }
        ],
    }


def test_super_admin_is_the_configured_address(settings):
    settings.SUPER_ADMIN_EMAIL = "  Owner@Example.com "
    assert is_super_admin("owner@example.com")
    assert not is_super_admin("otro@gmail.com")
    assert not is_super_admin("")
    assert not is_super_admin(None)

    settings.SUPER_ADMIN_EMAIL = ""
    assert not is_super_admin("owner@example.com")


def test_a_verified_session_resolves_the_super_admin(monkeypatch, signer, settings):
    settings.SUPER_ADMIN_EMAIL = OWNER
    jwk, mint = signer
    calls = {"users": 0}

    def fake(url):
        if url.endswith("/jwks"):
            return {"keys": [jwk]}
        calls["users"] += 1
        assert url.endswith("/users/user_1")
        return _user("Owner@Example.com")

    monkeypatch.setattr("simulator.services.clerk_auth._fetch_json", fake)
    identity = identity_from_request(_request(mint()))
    again = identity_from_request(_request(mint()))
    assert identity == {"user_id": "user_1", "email": OWNER}
    assert again["email"] == identity["email"]
    assert calls["users"] == 1
    assert is_super_admin(identity["email"])


def test_an_unverified_email_is_not_a_super_admin(monkeypatch, signer):
    jwk, mint = signer

    def fake(url):
        if url.endswith("/jwks"):
            return {"keys": [jwk]}
        return _user(OWNER, status="unverified")

    monkeypatch.setattr("simulator.services.clerk_auth._fetch_json", fake)
    identity = identity_from_request(_request(mint()))
    assert identity["email"] == ""
    assert not is_super_admin(identity["email"])


def test_missing_or_expired_session_is_rejected(monkeypatch, signer):
    jwk, mint = signer
    monkeypatch.setattr(
        "simulator.services.clerk_auth._fetch_json",
        lambda url: {"keys": [jwk]} if url.endswith("/jwks") else _user("a@b.c"),
    )
    with pytest.raises(ClerkAuthError) as missing:
        identity_from_request(type("Request", (), {"META": {}})())
    assert missing.value.status_code == 401

    with pytest.raises(ClerkAuthError):
        identity_from_request(_request(mint(exp_delta=-30)))

    monkeypatch.setattr(
        "simulator.services.clerk_auth._fetch_json",
        lambda url: {"keys": [{**jwk, "kid": "other"}]} if url.endswith("/jwks") else {},
    )
    clear_auth_cache()
    with pytest.raises(ClerkAuthError):
        identity_from_request(_request(mint()))


def test_a_rejected_secret_is_a_server_error(monkeypatch, settings, signer):
    settings.CLERK_SECRET_KEY = "sk_test_dummy"
    _jwk, mint = signer

    def boom(*_args, **_kwargs):
        raise urllib.error.HTTPError(
            url="https://api.clerk.com/v1/jwks",
            code=401,
            msg="unauthorized",
            hdrs=None,
            fp=io.BytesIO(b"{}"),
        )

    monkeypatch.setattr("simulator.services.clerk_auth.urllib.request.urlopen", boom)
    with pytest.raises(ClerkAuthError) as malformed:
        identity_from_request(_request("not-a-jwt"))
    assert malformed.value.status_code == 401

    with pytest.raises(ClerkAuthError) as rejected:
        identity_from_request(_request(mint()))
    assert rejected.value.status_code == 503
    assert "CLERK_SECRET_KEY" in str(rejected.value)


@pytest.mark.django_db
def test_api_stays_open_until_the_clerk_secret_exists(api_client, settings):
    settings.CLERK_SECRET_KEY = ""
    response = api_client.get("/api/auth/config/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_api_requires_a_session_when_clerk_is_on(api_client, settings):
    settings.CLERK_SECRET_KEY = "sk_test_dummy"
    response = api_client.get("/api/auth/config/")
    assert response.status_code == 401
    assert "sesión" in response.json()["error"]
    options = api_client.options("/api/auth/config/")
    assert options.status_code != 401


@pytest.mark.django_db
def test_settings_follow_the_configured_email(api_client, settings, monkeypatch):
    settings.CLERK_SECRET_KEY = "sk_test_dummy"
    settings.SUPER_ADMIN_EMAIL = OWNER

    def identify(request):
        email = request.META.get("HTTP_X_TEST_EMAIL", "")
        if not email:
            raise ClerkAuthError("Inicia sesión para continuar.")
        return {"user_id": "user_1", "email": email}

    monkeypatch.setattr("simulator.middleware.identity_from_request", identify)
    payload = {
        "provider": "ollama",
        "ollama_model": "llama3.1",
        "ollama_base_url": "http://127.0.0.1:11434",
        "openrouter_model": "",
    }
    blocked_models = api_client.get(
        "/api/settings/ai/ollama-models/",
        HTTP_AUTHORIZATION="Bearer token",
        HTTP_X_TEST_EMAIL="otro@gmail.com",
    )
    assert blocked_models.status_code == 403

    other = api_client.put(
        "/api/settings/ai/",
        payload,
        format="json",
        HTTP_AUTHORIZATION="Bearer token",
        HTTP_X_TEST_EMAIL="otro@gmail.com",
    )
    assert other.status_code == 403

    saved = api_client.put(
        "/api/settings/ai/",
        payload,
        format="json",
        HTTP_AUTHORIZATION="Bearer token",
        HTTP_X_TEST_EMAIL="Owner@Example.com",
    )
    assert saved.status_code == 200, saved.data
    assert saved.data["provider"] == "ollama"
    assert saved.data["ollama_model"] == "llama3.1"

    dashboard = api_client.get(
        "/api/auth/config/",
        HTTP_AUTHORIZATION="Bearer token",
        HTTP_X_TEST_EMAIL="otro@gmail.com",
    )
    assert dashboard.status_code == 200

    owner = api_client.get(
        "/api/auth/me/",
        HTTP_AUTHORIZATION="Bearer token",
        HTTP_X_TEST_EMAIL="Owner@Example.com",
    )
    assert owner.status_code == 200
    assert owner.data["authenticated"] is False
    assert owner.data["can_manage_settings"] is True


@pytest.mark.django_db
def test_settings_refuse_everyone_when_the_address_is_unset(api_client, settings, monkeypatch):
    settings.CLERK_SECRET_KEY = "sk_test_dummy"
    settings.SUPER_ADMIN_EMAIL = ""
    monkeypatch.setattr(
        "simulator.middleware.identity_from_request",
        lambda request: {"user_id": "user_1", "email": OWNER},
    )
    response = api_client.get(
        "/api/settings/ai/",
        HTTP_AUTHORIZATION="Bearer token",
    )
    assert response.status_code == 503
    assert "SUPER_ADMIN_EMAIL" in response.json()["error"]
