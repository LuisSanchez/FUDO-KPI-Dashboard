"""API smoke tests — session endpoints respond without 500."""
import pytest
from django.test import Client


@pytest.mark.django_db
def test_products_without_session_returns_empty_or_ok():
    client = Client()
    resp = client.get("/api/products/")
    assert resp.status_code in (200, 400)


@pytest.mark.django_db
def test_reset_endpoint():
    client = Client()
    resp = client.post("/api/reset/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_upload_sales_rejects_non_excel():
    client = Client()
    resp = client.post("/api/upload-sales/", {"file": ("bad.txt", b"not excel", "text/plain")})
    assert resp.status_code == 400
