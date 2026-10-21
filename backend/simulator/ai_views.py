"""Super-admin choice of the model that answers the data chat."""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.ai_settings import (
    AiSettingsError,
    resolve_ollama_base,
    snapshot,
    update_settings,
)
from .services.clerk_auth import can_manage_settings, clerk_enabled, super_admin_email
from .services.ollama_chat import list_models
from .services.openrouter_chat import ChatError


def _deny_unless_super_admin(request):
    if can_manage_settings(request):
        return None
    if clerk_enabled() and not super_admin_email():
        return Response(
            {"error": "Falta SUPER_ADMIN_EMAIL en el servidor."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response(
        {"error": "Solo el super admin puede cambiar esta configuración."},
        status=status.HTTP_403_FORBIDDEN,
    )


@api_view(["GET", "PUT"])
def ai_settings(request):
    denied = _deny_unless_super_admin(request)
    if denied is not None:
        return denied
    if request.method == "GET":
        return Response(snapshot())
    try:
        saved = update_settings(request.data)
    except AiSettingsError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(saved)


@api_view(["GET"])
def ollama_models(request):
    denied = _deny_unless_super_admin(request)
    if denied is not None:
        return denied
    try:
        base_url = resolve_ollama_base(request.query_params.get("base_url"))
    except AiSettingsError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    try:
        names = list_models(base_url)
    except ChatError as exc:
        return Response({"error": str(exc)}, status=exc.status_code)
    return Response({"models": names})
