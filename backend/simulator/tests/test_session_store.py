"""Unit tests for session_store service."""

import pandas as pd
import pytest

from simulator.models import UserSessionData
from simulator.services.session_store import clear_store, dump_df, get_or_create_store, load_df


def test_dump_load_roundtrip():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    blob = dump_df(df)
    assert blob is not None
    restored = load_df(blob)
    assert list(restored.columns) == ["a", "b"]
    assert len(restored) == 2


def test_dump_none_and_load_none():
    assert dump_df(None) is None
    empty = load_df(None)
    assert isinstance(empty, pd.DataFrame)
    assert empty.empty


@pytest.mark.django_db
def test_get_or_create_and_clear(api_client):
    session = api_client.session
    session.save()
    request = type("R", (), {"session": session})()
    store = get_or_create_store(request)
    assert store.session_key
    store.sales_df_pickle = dump_df(pd.DataFrame({"x": [1]}))
    store.products = ["A"]
    store.sales_months = ["2026-03"]
    store.save()

    clear_store(store)
    store.refresh_from_db()
    assert store.sales_df_pickle is None
    assert store.products == []
    assert store.sales_months == []
