"""Require a Clerk session on /api/ once CLERK_SECRET_KEY is set."""

from django.http import JsonResponse

from simulator.services.clerk_auth import ClerkAuthError, clerk_enabled, identity_from_request


class ClerkSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not _protects(request):
            return self.get_response(request)
        try:
            identity = identity_from_request(request)
        except ClerkAuthError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=exc.status_code,
                json_dumps_params={"ensure_ascii": False},
            )
        request.clerk_user_id = identity["user_id"]
        request.clerk_email = identity["email"]
        return self.get_response(request)


def _protects(request) -> bool:
    if not clerk_enabled() or request.method == "OPTIONS":
        return False
    return request.path.startswith("/api/")
