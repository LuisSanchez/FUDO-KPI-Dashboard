"""
Session-scoped DataFrame storage (DIP: views depend on this adapter, not pickle).

Keeps UserSessionData I/O out of views so auth/user-backed storage can be
swapped without changing endpoint handlers.
"""
from __future__ import annotations

import pickle
from typing import Optional

import pandas as pd
from django.http import HttpRequest

from simulator.models import UserSessionData


def get_or_create_store(request: HttpRequest) -> UserSessionData:
    """Return (or create) the UserSessionData row for the current browser session."""
    if not request.session.session_key:
        request.session.create()
    store, _ = UserSessionData.objects.get_or_create(
        session_key=request.session.session_key
    )
    return store


def load_df(blob) -> pd.DataFrame:
    """Deserialize a pickled DataFrame from a BinaryField value."""
    if blob is None:
        return pd.DataFrame()
    return pickle.loads(bytes(blob))


def dump_df(df: Optional[pd.DataFrame]) -> Optional[bytes]:
    """Serialize a DataFrame to bytes for BinaryField storage."""
    if df is None:
        return None
    return pickle.dumps(df)


def load_sales(store: UserSessionData) -> pd.DataFrame:
    return load_df(store.sales_df_pickle)


def load_expenses(store: UserSessionData) -> pd.DataFrame:
    return load_df(store.expenses_df_pickle)


def save_sales(store: UserSessionData, df: pd.DataFrame, *, products=None, sales_months=None) -> None:
    store.sales_df_pickle = dump_df(df)
    if products is not None:
        store.products = products
    if sales_months is not None:
        store.sales_months = sales_months
    store.save()


def save_expenses(store: UserSessionData, df: pd.DataFrame) -> None:
    store.expenses_df_pickle = dump_df(df)
    store.save()


def clear_store(store: UserSessionData) -> None:
    store.sales_df_pickle = None
    store.expenses_df_pickle = None
    store.products = []
    store.sales_months = []
    store.save()
