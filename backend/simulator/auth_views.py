"""Google OAuth endpoints — disabled unless GOOGLE_OAUTH_ENABLED=True."""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import UserProfile
from .services.session_store import get_or_create_store


def _oauth_enabled() -> bool:
    return bool(getattr(settings, "GOOGLE_OAUTH_ENABLED", False) and settings.GOOGLE_CLIENT_ID)


@api_view(["GET"])
@permission_classes([AllowAny])
def auth_config(request):
    """Public config for the SPA (whether to show Google button)."""
    return Response(
        {
            "oauth_enabled": _oauth_enabled(),
            "client_id": settings.GOOGLE_CLIENT_ID if _oauth_enabled() else "",
            "require_auth": bool(getattr(settings, "REQUIRE_AUTH", False)),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def auth_me(request):
    if not request.user.is_authenticated:
        return Response({"authenticated": False})
    profile = getattr(request.user, "profile", None)
    return Response(
        {
            "authenticated": True,
            "email": request.user.email,
            "display_name": (profile.display_name if profile else request.user.get_username()),
            "avatar_url": profile.avatar_url if profile else "",
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_logout(request):
    logout(request)
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_google(request):
    """Verify Google Identity Services ID token and establish Django session."""
    if not _oauth_enabled():
        return Response(
            {"error": "Google OAuth is disabled"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    credential = request.data.get("credential") or request.data.get("id_token")
    if not credential:
        return Response({"error": "Missing credential"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:  # noqa: BLE001 — surface verification failures
        return Response(
            {"error": "Invalid Google token", "detail": str(exc)},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    google_sub = idinfo.get("sub")
    email = idinfo.get("email") or ""
    name = idinfo.get("name") or email
    picture = idinfo.get("picture") or ""

    if not google_sub:
        return Response({"error": "Token missing subject"}, status=status.HTTP_400_BAD_REQUEST)

    UserModel = get_user_model()
    profile = UserProfile.objects.filter(google_id=google_sub).select_related("user").first()
    if profile:
        user = profile.user
        profile.email = email or profile.email
        profile.display_name = name or profile.display_name
        profile.avatar_url = picture or profile.avatar_url
        profile.save(update_fields=["email", "display_name", "avatar_url", "updated_at"])
    else:
        username = (email or f"google_{google_sub}")[:150]
        user, created = UserModel.objects.get_or_create(
            username=username,
            defaults={"email": email, "first_name": name[:30]},
        )
        if not created and email:
            user.email = email
            user.save(update_fields=["email"])
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "google_id": google_sub,
                "email": email,
                "display_name": name,
                "avatar_url": picture,
            },
        )

    login(request, user)
    store = get_or_create_store(request)
    if store.user_id != user.id:
        store.user = user
        store.save(update_fields=["user", "updated_at"])

    return Response(
        {
            "authenticated": True,
            "email": email,
            "display_name": name,
            "avatar_url": picture,
        }
    )
