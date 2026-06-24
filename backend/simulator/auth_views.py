"""
Google OAuth endpoints (optional).

When GOOGLE_OAUTH_ENABLED=False (default), these endpoints return 503 so Railway
deployments without keys keep working unchanged.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import UserProfile
from .services import session_store

User = get_user_model()


def _oauth_disabled_response():
    return Response(
        {
            "error": "google_oauth_disabled",
            "detail": "Set GOOGLE_OAUTH_ENABLED=True and GOOGLE_CLIENT_ID to enable.",
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def _verify_google_id_token(id_token: str) -> dict | None:
    """Verify Google ID token and return claims, or None on failure."""
    if not settings.GOOGLE_CLIENT_ID:
        return None
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        return google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception:
        return None


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    """
    Exchange a Google ID token (from GIS button) for a Django session.

    Body: { "credential": "<google_id_token>" }
    """
    if not settings.GOOGLE_OAUTH_ENABLED:
        return _oauth_disabled_response()

    credential = request.data.get("credential") or request.data.get("id_token")
    if not credential:
        return Response(
            {"error": "missing_credential"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    claims = _verify_google_id_token(credential)
    if not claims:
        return Response(
            {"error": "invalid_token"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    google_id = claims.get("sub")
    email = claims.get("email", "")
    name = claims.get("name", "") or claims.get("given_name", "")
    picture = claims.get("picture", "")

    if not google_id:
        return Response(
            {"error": "invalid_claims"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    profile = UserProfile.objects.filter(google_id=google_id).select_related("user").first()
    if profile:
        user = profile.user
        # Refresh profile fields (additive update only)
        profile.email = email or profile.email
        profile.display_name = name or profile.display_name
        profile.avatar_url = picture or profile.avatar_url
        profile.save(update_fields=["email", "display_name", "avatar_url", "updated_at"])
    else:
        # Create Django user + profile (no deletion of existing data)
        username = f"google_{google_id[:32]}"
        user, _created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": name[:150] if name else "",
            },
        )
        if email and user.email != email:
            user.email = email
            user.save(update_fields=["email"])
        UserProfile.objects.create(
            user=user,
            google_id=google_id,
            email=email,
            display_name=name,
            avatar_url=picture,
        )

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    # Attach current session store to user (non-destructive)
    store = session_store.get_or_create_store(request)
    if store.user_id != user.id:
        store.user = user
        store.save(update_fields=["user", "updated_at"])

    return Response(
        {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": email or user.email,
                "name": name or user.get_full_name() or user.username,
                "avatar_url": picture,
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def auth_me(request):
    """Return current session user, or anonymous payload."""
    if not request.user.is_authenticated:
        return Response({"authenticated": False, "user": None})

    profile = getattr(request.user, "profile", None)
    return Response(
        {
            "authenticated": True,
            "user": {
                "id": request.user.id,
                "email": (profile.email if profile else request.user.email),
                "name": (
                    profile.display_name
                    if profile and profile.display_name
                    else request.user.get_full_name() or request.user.username
                ),
                "avatar_url": profile.avatar_url if profile else "",
            },
            "oauth_enabled": settings.GOOGLE_OAUTH_ENABLED,
            "require_auth": settings.REQUIRE_AUTH,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def auth_config(request):
    """Public config for frontend (client id only when OAuth enabled)."""
    return Response(
        {
            "oauth_enabled": settings.GOOGLE_OAUTH_ENABLED,
            "require_auth": settings.REQUIRE_AUTH,
            "google_client_id": (
                settings.GOOGLE_CLIENT_ID if settings.GOOGLE_OAUTH_ENABLED else ""
            ),
        }
    )


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def auth_logout(request):
    logout(request)
    return Response({"authenticated": False})
