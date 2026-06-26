import pytest


@pytest.mark.django_db
def test_reset_endpoint(api_client):
    resp = api_client.post("/api/reset/")
    assert resp.status_code == 200
    assert resp.data.get("message") == "Data reset successfully"


@pytest.mark.django_db
def test_products_without_upload_returns_400(api_client):
    resp = api_client.get("/api/products/")
    assert resp.status_code == 400
    assert "error" in resp.data


@pytest.mark.django_db
def test_calculate_without_data_returns_400(api_client):
    resp = api_client.post("/api/calculate/", {}, format="json")
    assert resp.status_code == 400
