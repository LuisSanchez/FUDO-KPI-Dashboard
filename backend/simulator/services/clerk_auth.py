"""Verify a Clerk session token and decide who may change AI settings.

The browser sends the session JWT. The email is not in that token, so the
backend reads it from Clerk with the secret key. The client never gets to
claim an email. The allowed address lives in SUPER_ADMIN_EMAIL, not in code.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request

from django.conf import settings

_JWKS_URL = "https://api.clerk.com/v1/jwks"
_USERS_URL = "https://api.clerk.com/v1/users/"
_CACHE_SECONDS = 300

_lock = threading.Lock()
_jwks_cache: dict = {"at": 0.0, "keys": None}
_email_cache: dict[str, tuple[float, str]] = {}


class ClerkAuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


def clerk_enabled() -> bool:
    return bool((getattr(settings, "CLERK_SECRET_KEY", "") or "").strip())


def super_admin_email() -> str:
    return (getattr(settings, "SUPER_ADMIN_EMAIL", "") or "").strip().lower()


def is_super_admin(email: str | None) -> bool:
    expected = super_admin_email()
    if not expected:
        return False
    return (email or "").strip().lower() == expected


def can_manage_settings(request) -> bool:
    """Settings stay open on a machine with Clerk off. Otherwise only the configured address."""
    if not clerk_enabled():
        return True
    return is_super_admin(getattr(request, "clerk_email", ""))


def clear_auth_cache() -> None:
    with _lock:
        _jwks_cache["at"] = 0.0
        _jwks_cache["keys"] = None
        _email_cache.clear()


def identity_from_request(request) -> dict:
    header = request.META.get("HTTP_AUTHORIZATION", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ClerkAuthError("Inicia sesión para continuar.")
    user_id = verify_session_token(token.strip())
    return {"user_id": user_id, "email": email_for_user(user_id)}


def verify_session_token(token: str) -> str:
    jwt = _jwt()
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise ClerkAuthError("La sesión no es válida. Vuelve a entrar.") from exc
    key = _signing_key(jwt, header.get("kid"))
    try:
        payload = jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False})
    except jwt.PyJWTError as exc:
        raise ClerkAuthError("La sesión no es válida. Vuelve a entrar.") from exc
    user_id = str(payload.get("sub") or "").strip()
    if not user_id:
        raise ClerkAuthError("La sesión no es válida. Vuelve a entrar.")
    return user_id


def email_for_user(user_id: str) -> str:
    now = time.monotonic()
    with _lock:
        cached = _email_cache.get(user_id)
        if cached and now - cached[0] < _CACHE_SECONDS:
            return cached[1]
    email = _email_from_payload(_fetch_json(f"{_USERS_URL}{user_id}"))
    with _lock:
        _email_cache[user_id] = (now, email)
    return email


def _signing_key(jwt, kid: str | None):
    now = time.monotonic()
    with _lock:
        cached = _jwks_cache["keys"]
        fresh = cached is not None and now - _jwks_cache["at"] < _CACHE_SECONDS
    if not fresh:
        fetched = jwt.PyJWKSet.from_dict(_fetch_json(_JWKS_URL))
        with _lock:
            _jwks_cache["keys"] = fetched
            _jwks_cache["at"] = now
        cached = fetched
    for item in cached.keys:
        if item.key_id == kid:
            return item.key
    raise ClerkAuthError("La sesión no es válida. Vuelve a entrar.")


def _email_from_payload(payload: dict) -> str:
    addresses = payload.get("email_addresses") if isinstance(payload, dict) else None
    if not isinstance(addresses, list):
        return ""
    primary_id = payload.get("primary_email_address_id")
    chosen = None
    for item in addresses:
        if isinstance(item, dict) and item.get("id") == primary_id:
            chosen = item
            break
    if chosen is None:
        chosen = next((item for item in addresses if isinstance(item, dict)), None)
    if not chosen:
        return ""
    verification = chosen.get("verification") or {}
    status = verification.get("status") if isinstance(verification, dict) else ""
    if status != "verified":
        return ""
    return str(chosen.get("email_address") or "").strip().lower()


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {_secret()}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise ClerkAuthError("CLERK_SECRET_KEY fue rechazada.", 503) from exc
        if exc.code == 404:
            raise ClerkAuthError("La sesión no es válida. Vuelve a entrar.") from exc
        raise ClerkAuthError("No pude confirmar la sesión con Clerk.", 503) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ClerkAuthError("No pude confirmar la sesión con Clerk.", 503) from exc
    if not isinstance(payload, dict):
        raise ClerkAuthError("No pude confirmar la sesión con Clerk.", 503)
    return payload


def _secret() -> str:
    return (getattr(settings, "CLERK_SECRET_KEY", "") or "").strip()


def _jwt():
    try:
        import jwt
    except ImportError as exc:
        raise ClerkAuthError(
            "Falta PyJWT en el backend. Reinicia el servidor después de instalar las dependencias.",
            503,
        ) from exc
    return jwt
