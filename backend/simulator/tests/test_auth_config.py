import pytest
from django.test import override_settings


@pytest.mark.django_db
def test_auth_config_disabled_by_default(api_client):
    resp = api_client.get("/api/auth/config/")
    assert resp.status_code == 200
    assert resp.data["oauth_enabled"] is False


@pytest.mark.django_db
@override_settings(GOOGLE_OAUTH_ENABLED=False, GOOGLE_CLIENT_ID="")
def test_google_auth_returns_503_when_disabled(api_client):
    resp = api_client.post("/api/auth/google/", {"credential": "x"}, format="json")
    assert resp.status_code == 503


@pytest.mark.django_db
def test_auth_me_anonymous(api_client):
    resp = api_client.get("/api/auth/me/")
    assert resp.status_code == 200
    assert resp.data["authenticated"] is False
