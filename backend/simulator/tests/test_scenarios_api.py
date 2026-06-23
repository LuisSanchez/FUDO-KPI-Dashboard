"""API tests for saved scenarios and core session endpoints."""

from django.test import TestCase, Client
from django.urls import reverse
import io

import pandas as pd

from simulator.models import SavedScenario, UserSessionData


class ScenariosAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def _session_cookie(self):
        # Touch session so session_key exists for subsequent calls.
        self.client.get("/api/scenarios/")

    def test_list_scenarios_empty(self):
        res = self.client.get("/api/scenarios/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["scenarios"], [])

    def test_create_requires_sales(self):
        res = self.client.post(
            "/api/scenarios/",
            data={"name": "Marzo"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_create_load_delete_scenario(self):
        # Seed session store with minimal sales pickle via ORM.
        self._session_cookie()
        session_key = self.client.session.session_key
        self.assertTrue(session_key)

        df = pd.DataFrame(
            {
                "Producto": ["Pizza Test"],
                "Categoría": ["Especialidades"],
                "Cantidad": [1],
                "Precio": [10000],
                "Costo base": [2000],
                "Costo modificadores": [0],
                "Creada por": ["fudo"],
                "created_at": [pd.Timestamp("2026-03-15")],
                "ingreso_sin_iva": [8403.36],
                "costo_ingredientes_sin_iva": [1680.67],
                "costo_sin_iva": [1680.67],
                "margen_sin_iva": [6722.69],
                "comision": [0.0],
                "cost_imputed": [False],
            }
        )
        import pickle

        store, _ = UserSessionData.objects.get_or_create(session_key=session_key)
        store.sales_df_pickle = pickle.dumps(df)
        store.products = ["Pizza Test"]
        store.sales_months = ["2026-03"]
        store.save()

        create = self.client.post(
            "/api/scenarios/",
            data={"name": "Marzo 2026", "month": "2026-03"},
            content_type="application/json",
        )
        self.assertEqual(create.status_code, 201, create.content)
        body = create.json()
        self.assertEqual(body["name"], "Marzo 2026")
        sid = body["id"]

        listed = self.client.get("/api/scenarios/")
        self.assertEqual(len(listed.json()["scenarios"]), 1)

        loaded = self.client.post(f"/api/scenarios/{sid}/")
        self.assertEqual(loaded.status_code, 200)
        self.assertIn("months", loaded.json())

        deleted = self.client.delete(f"/api/scenarios/{sid}/")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(SavedScenario.objects.filter(id=sid).count(), 0)
