"""API unit tests with pre-seeded session store (no Excel files)."""

import io

import pandas as pd
import pytest
from openpyxl import Workbook


def _xlsx_bytes(sheet_name, df, skiprows=0):
    """Build a minimal xlsx. If skiprows>0, pad header rows (expenses sheet)."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    for _ in range(skiprows):
        ws.append([])
    ws.append(list(df.columns))
    for row in df.itertuples(index=False):
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.django_db
def test_data_endpoints_with_seeded_store(api_client, seeded_store):
    r = api_client.get("/api/products/")
    assert r.status_code == 200
    assert "products" in r.data
    assert len(r.data["products"]) > 0

    r = api_client.post("/api/calculate/", {"month": "2026-03"}, format="json")
    assert r.status_code == 200
    assert "ebitda" in r.data

    r = api_client.get("/api/data/sales/", {"month": "2026-03"})
    assert r.status_code == 200
    assert isinstance(r.data, list)

    r = api_client.get("/api/data/expenses/", {"month": "2026-03"})
    assert r.status_code == 200

    r = api_client.get("/api/data/charts/", {"month": "2026-03"})
    assert r.status_code == 200
    assert "hourly" in r.data

    r = api_client.get("/api/data/product-prices/", {"month": "2026-03"})
    assert r.status_code == 200

    r = api_client.get(
        "/api/simulate/price-cost/",
        {"price_increase": 500, "cost_increase": 5, "month": "2026-03"},
    )
    assert r.status_code == 200
    assert "projected_ebitda" in r.data

    r = api_client.get("/api/advisor/promotions/", {"month": "2026-03"})
    assert r.status_code == 200

    r = api_client.get("/api/uber-eats/analysis/", {"month": "2026-03"})
    assert r.status_code == 200
    assert r.data.get("has_uber_data") is True

    r = api_client.get("/api/sunday-analysis/", {"month": "2026-03"})
    assert r.status_code == 200
    assert r.data.get("has_data") is True

    r = api_client.get("/api/report/excel/", {"categoria": "Especialidades", "month": "2026-03"})
    assert r.status_code == 200
    assert (
        r["Content-Type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        or "spreadsheet" in r["Content-Type"]
        or len(r.content) > 0
    )

    r = api_client.get("/api/report/pdf/", {"month": "2026-03"})
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


@pytest.mark.django_db
def test_upload_sales_and_expenses_happy_path(api_client, sample_sales_df, sample_expenses_df):
    from django.core.files.uploadedfile import SimpleUploadedFile

    sales_bytes = _xlsx_bytes("Adiciones", sample_sales_df)
    sales_file = SimpleUploadedFile(
        "sales.xlsx",
        sales_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    r = api_client.post("/api/upload-sales/", {"file": sales_file}, format="multipart")
    assert r.status_code == 200, r.data
    assert r.data["months"]

    exp_bytes = _xlsx_bytes("Gastos", sample_expenses_df, skiprows=3)
    exp_file = SimpleUploadedFile(
        "expenses.xlsx",
        exp_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    r = api_client.post("/api/upload-expenses/", {"file": exp_file}, format="multipart")
    assert r.status_code == 200, r.data


@pytest.mark.django_db
def test_upload_rejects_non_excel(api_client):
    from django.core.files.uploadedfile import SimpleUploadedFile

    f = SimpleUploadedFile("x.txt", b"not excel", content_type="text/plain")
    r = api_client.post("/api/upload-sales/", {"file": f}, format="multipart")
    assert r.status_code == 400


@pytest.mark.django_db
def test_upload_sales_missing_file(api_client):
    r = api_client.post("/api/upload-sales/", {}, format="multipart")
    assert r.status_code == 400


@pytest.mark.django_db
def test_auth_logout(api_client):
    r = api_client.post("/api/auth/logout/")
    assert r.status_code == 200
    assert r.data.get("ok") is True


@pytest.mark.django_db
def test_calculate_missing_expenses(api_client, cleaned_sales):
    from simulator.services.session_store import dump_df, get_or_create_store

    session = api_client.session
    session.save()
    request = type("R", (), {"session": session})()
    store = get_or_create_store(request)
    store.sales_df_pickle = dump_df(cleaned_sales)
    store.expenses_df_pickle = None
    store.save()
    r = api_client.post("/api/calculate/", {}, format="json")
    assert r.status_code == 400
