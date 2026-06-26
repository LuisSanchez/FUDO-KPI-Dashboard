"""Session-backed DataFrame storage — keeps views free of pickle I/O (DIP)."""
from __future__ import annotations

import pickle

import pandas as pd

from simulator.models import UserSessionData


def get_or_create_store(request) -> UserSessionData:
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


def dump_df(df: pd.DataFrame | None) -> bytes | None:
    """Serialize a DataFrame to bytes for BinaryField storage."""
    if df is None:
        return None
    return pickle.dumps(df)


def clear_store(store: UserSessionData) -> None:
    store.sales_df_pickle = None
    store.expenses_df_pickle = None
    store.products = []
    store.sales_months = []
    store.save()
