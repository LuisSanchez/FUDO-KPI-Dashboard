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
def test_history_builds_from_the_session_and_keeps_other_months(api_client, seeded_store):
    first = api_client.get("/api/history/")
    assert first.status_code == 200
    assert [row["month"] for row in first.data["months"]] == ["2026-03"]
    march = first.data["months"][0]
    assert march["uber"]["cobrado"] > 0
    assert (
        march["uber"]["neto_estimado"] == march["uber"]["cobrado"] - march["uber"]["tasa_servicio"]
    )
    assert "commission_rate" in first.data
    assert first.data["default_sueldos"] == 1_300_000
    assert march["sueldos_usados"] == 1_300_000
    assert march["gastos_sin_sueldos"] == march["gastos_ops"] - march["sueldos_fudo"]
    assert march["ebitda"] == (
        march["cobrado_sin_iva"] - march["gastos_sin_sueldos"] - march["sueldos_usados"]
    )
    assert march["resultado"] == march["ebitda"] - march["comision_uber"]

    # A later sales upload only drops the months inside that file.
    seeded_store.refresh_from_db()
    history = dict(seeded_store.month_history)
    history["2026-01"] = {
        "month": "2026-01",
        "cobrado_sin_iva": 10,
        "ebitda": 1,
        "tickets": 1,
        "cobrado": 12,
        "descuentos": 0,
        "gastos_ops": 0,
        "sueldos": 0,
        "materia_prima": 0,
        "channels": {},
        "uber": {"cobrado": 0, "neto_estimado": 0, "tasa_servicio": 0},
    }
    seeded_store.month_history = history
    seeded_store.save()
    from django.core.files.uploadedfile import SimpleUploadedFile

    sales = pd.DataFrame(
        {
            "Id. Venta": [1],
            "Creación": ["2026-04-01 12:00:00"],
            "Producto": ["Pizza Margarita"],
            "Categoría": ["Especialidades"],
            "Cantidad": [1],
            "Precio": [8990],
            "Costo base": [2000],
            "Costo modificadores": [0],
            "Costo total": [2000],
            "Creada por": ["caja1"],
        }
    )
    payload = _xlsx_bytes("Adiciones", sales)
    upload = SimpleUploadedFile(
        "abril.xlsx",
        payload,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response = api_client.post("/api/upload-sales/", {"file": upload}, format="multipart")
    assert response.status_code == 200, response.data
    seeded_store.refresh_from_db()
    assert "2026-01" in seeded_store.month_history
    assert "2026-03" in seeded_store.month_history
    assert "2026-04" not in seeded_store.month_history


@pytest.mark.django_db
def test_sueldos_override_changes_the_presented_month_only(api_client, seeded_store):
    from simulator.models import MonthAssumption

    first = api_client.get("/api/history/")
    march = first.data["months"][0]
    seeded_store.refresh_from_db()
    stored_ebitda = seeded_store.month_history["2026-03"]["ebitda"]

    updated = api_client.post(
        "/api/history/sueldos/",
        {"month": "2026-03", "sueldos": 2_000_000},
        format="json",
    )
    assert updated.status_code == 200, updated.data
    row = updated.data["months"][0]
    assert row["sueldos_usados"] == 2_000_000
    assert row["ebitda"] == march["ebitda"] - 700_000
    assert row["resultado"] == row["ebitda"] - row["comision_uber"]
    seeded_store.refresh_from_db()
    assert seeded_store.month_history["2026-03"]["ebitda"] == stored_ebitda

    zero = api_client.post(
        "/api/history/sueldos/",
        {"month": "2026-03", "sueldos": 0},
        format="json",
    )
    assert zero.status_code == 200, zero.data
    assert zero.data["months"][0]["sueldos_usados"] == 0
    assert zero.data["months"][0]["ebitda"] == row["ebitda"] + 2_000_000

    as_text = api_client.post(
        "/api/history/sueldos/",
        {"month": "2026-03", "sueldos": "1500000"},
        format="json",
    )
    assert as_text.status_code == 200, as_text.data
    assert as_text.data["sueldos"] == 1_500_000
    assert as_text.data["months"][0]["sueldos_usados"] == 1_500_000

    reset = api_client.post(
        "/api/history/sueldos/",
        {"month": "2026-03", "reset": True},
        format="json",
    )
    assert reset.status_code == 200, reset.data
    assert reset.data["months"][0]["sueldos_usados"] == 1_300_000
    assert reset.data["months"][0]["ebitda"] == march["ebitda"]
    assert MonthAssumption.objects.filter(month="2026-03").count() == 0


@pytest.mark.django_db
def test_sueldos_override_rejects_bad_input(api_client):
    cases = [
        {"month": "marzo", "sueldos": 1},
        {"month": "2026-13", "sueldos": 1},
        {"month": "2026-03", "sueldos": -1},
        {"month": "2026-03", "sueldos": 100_000_001},
        {"month": "2026-03", "sueldos": True},
        {"month": "2026-03", "sueldos": 1.5},
        {"month": "2026-03", "sueldos": "1.300.000"},
        {"month": "2026-03"},
    ]
    for payload in cases:
        response = api_client.post("/api/history/sueldos/", payload, format="json")
        assert response.status_code == 400, payload


@pytest.mark.django_db
def test_present_history_uses_the_pdf_fee_without_rewriting_the_row(monkeypatch):
    from simulator.models import UserSessionData
    from simulator.services.month_history import present_history

    monkeypatch.setattr(
        "simulator.services.month_history.load_uber_statements",
        lambda _directory: {
            "2026-09": {
                "tasa": -864_581,
                "neto": 655_892,
                "anuncios": -330_468,
                "ajustes": -918_264,
            }
        },
    )
    store = UserSessionData.objects.create(
        session_key="present-history",
        month_history={
            "2026-09": {
                "month": "2026-09",
                "cobrado_sin_iva": 5_000_000,
                "gastos_ops": 1_300_000,
                "sueldos": 300_000,
                "ebitda": 3_700_000,
                "tickets": 10,
                "cobrado": 5_950_000,
                "descuentos": 0,
                "materia_prima": 0,
                "channels": {},
                "uber": {
                    "cobrado": 400_000,
                    "comision_neta": 100_000,
                    "tasa_servicio": 0,
                    "neto_estimado": 0,
                },
            }
        },
    )
    shown = present_history(store)[0]
    assert shown["gastos_sin_sueldos"] == 1_000_000
    assert shown["sueldos_usados"] == 1_300_000
    assert shown["ebitda"] == 5_000_000 - 1_000_000 - 1_300_000
    assert shown["comision_fuente"] == "pdf"
    assert shown["comision_uber"] == 726_539
    assert shown["uber"]["comision_neta"] == 100_000
    store.refresh_from_db()
    assert store.month_history["2026-09"]["ebitda"] == 3_700_000
    assert "resultado" not in store.month_history["2026-09"]
    assert shown["sueldos_sugerido"] == 1_300_000


@pytest.mark.django_db
def test_remuneraciones_month_starts_from_the_file_payment():
    from simulator.models import UserSessionData
    from simulator.services.month_history import present_history

    store = UserSessionData.objects.create(
        session_key="file-pay",
        month_history={
            "2026-02": {
                "month": "2026-02",
                "cobrado_sin_iva": 4_000_000,
                "gastos_ops": 3_000_000,
                "sueldos": 2_400_000,
                "pago_gente": 1_900_000,
                "previred": 500_000,
                "tiene_remuneraciones": True,
                "ebitda": 1_000_000,
                "tickets": 1,
                "cobrado": 4_760_000,
                "descuentos": 0,
                "materia_prima": 0,
                "channels": {},
                "uber": {"comision_neta": 10},
            }
        },
    )
    shown = present_history(store)[0]
    assert shown["sueldos_usados"] == 1_900_000
    assert shown["sueldos_sugerido"] == 1_900_000
    assert shown["sueldos_fudo"] == 1_900_000
    assert shown["previred"] == 500_000
    assert shown["gastos_sin_sueldos"] == 1_100_000
    assert shown["ebitda"] == 1_000_000


@pytest.mark.django_db
def test_import_archive_missing(api_client, monkeypatch):
    monkeypatch.setattr("simulator.views.archive_root", lambda: None)
    response = api_client.post("/api/history/import-archive/")
    assert response.status_code == 404


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
