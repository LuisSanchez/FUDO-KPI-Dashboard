"""Auth endpoints — safe defaults when OAuth disabled (Railway default)."""
import pytest
from django.test import Client, override_settings


@pytest.mark.django_db
def test_auth_config_oauth_disabled_by_default():
    client = Client()
    resp = client.get("/api/auth/config/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["oauth_enabled"] is False
    assert data["google_client_id"] == ""


@pytest.mark.django_db
def test_auth_me_anonymous():
    client = Client()
    resp = client.get("/api/auth/me/")
    assert resp.status_code == 200
    assert resp.json()["authenticated"] is False


@pytest.mark.django_db
@override_settings(GOOGLE_OAUTH_ENABLED=False)
def test_google_login_disabled_returns_503():
    client = Client()
    resp = client.post(
        "/api/auth/google/",
        data={"credential": "fake"},
        content_type="application/json",
    )
    assert resp.status_code == 503
    assert resp.json()["error"] == "google_oauth_disabled"
