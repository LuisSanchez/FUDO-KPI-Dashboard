"""
URL configuration for pizza_simulator project.
"""

from pathlib import Path

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("simulator.urls")),
]

# Serve React SPA when frontend build is present (e.g. Docker)
_frontend_index = settings.BASE_DIR / "frontend_build" / "index.html"
if _frontend_index.exists():

    def serve_spa(request):
        return FileResponse(open(_frontend_index, "rb"), content_type="text/html")

    urlpatterns += [
        re_path(r"^.*$", serve_spa),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
