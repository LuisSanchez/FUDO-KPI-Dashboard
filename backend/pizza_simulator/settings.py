"""
Django settings for pizza_simulator project.

Deploy targets (Railway single Docker image, local Docker, make run):
- Prefer explicit SECRET_KEY / ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS in env.
- Railway is auto-detected so existing deploys keep working without new vars.
"""

from pathlib import Path
import environ
import os
import warnings

env = environ.Env()
# Prefer project .env next to settings, fall back to process env.
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent, ".env"))
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Environment detection ─────────────────────────────────────────────────────
# Railway sets RAILWAY_* vars. Single-container app serves SPA + API on one host.
_IS_RAILWAY = bool(
    os.environ.get("RAILWAY_ENVIRONMENT")
    or os.environ.get("RAILWAY_PROJECT_ID")
    or os.environ.get("RAILWAY_SERVICE_ID")
)
_RAILWAY_PUBLIC_DOMAIN = (
    os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    or os.environ.get("RAILWAY_STATIC_URL")
    or ""
).strip().rstrip("/")
# Railway sometimes passes full URL in STATIC_URL-style vars.
if _RAILWAY_PUBLIC_DOMAIN.startswith("http"):
    from urllib.parse import urlparse

    _RAILWAY_PUBLIC_DOMAIN = urlparse(_RAILWAY_PUBLIC_DOMAIN).netloc or ""

# SECURITY WARNING: keep the secret key used in production secret!
_INSECURE_DEFAULT_KEY = "django-insecure-development-key-for-testing-only"
SECRET_KEY = env.str("SECRET_KEY", default=_INSECURE_DEFAULT_KEY)

DEBUG = env.bool("DEBUG", default=False)

# Hard-fail only when explicitly enforcing strict prod (opt-in) so Railway
# deploys that already run without SECRET_KEY are not killed on deploy.
_STRICT_PROD = env.bool("STRICT_PRODUCTION_SETTINGS", default=False)
if not DEBUG and SECRET_KEY == _INSECURE_DEFAULT_KEY:
    if _STRICT_PROD:
        raise RuntimeError(
            "SECRET_KEY must be set via environment when DEBUG=False. "
            "Generate one with: python -c \"from django.core.management.utils "
            "import get_random_secret_key; print(get_random_secret_key())\""
        )
    warnings.warn(
        "Using insecure default SECRET_KEY in non-DEBUG mode. "
        "Set SECRET_KEY in Railway/env (and STRICT_PRODUCTION_SETTINGS=1 later).",
        RuntimeWarning,
        stacklevel=1,
    )
elif DEBUG and SECRET_KEY == _INSECURE_DEFAULT_KEY:
    warnings.warn(
        "Using insecure default SECRET_KEY — set SECRET_KEY in the environment "
        "before deploying.",
        RuntimeWarning,
        stacklevel=1,
    )


def _default_allowed_hosts():
    """Hosts that never break existing Railway / local Docker deploys."""
    hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
    if DEBUG or not _IS_RAILWAY:
        # Preserve previous permissive default for non-Railway prod Docker.
        hosts.append("*")
    if _IS_RAILWAY:
        hosts.extend([".railway.app", ".up.railway.app"])
        if _RAILWAY_PUBLIC_DOMAIN:
            hosts.append(_RAILWAY_PUBLIC_DOMAIN)
    return hosts


# Hosts: explicit env wins; otherwise Railway-aware safe defaults (never empty).
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=_default_allowed_hosts())
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = _default_allowed_hosts()
if not DEBUG and "*" not in ALLOWED_HOSTS and _STRICT_PROD and not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS must be set when DEBUG=False")


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "simulator",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pizza_simulator.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "pizza_simulator.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"

# When running in Docker, frontend_build exists and we serve the React SPA from it.
# Point STATIC_ROOT at frontend_build/static so /static/js/... maps to the CRA build.
FRONTEND_BUILD_DIR = BASE_DIR / "frontend_build"
if FRONTEND_BUILD_DIR.exists():
    STATIC_ROOT = str(FRONTEND_BUILD_DIR / "static")

# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Session settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = False
# Secure cookies behind Railway HTTPS; allow override for local http Docker.
_default_secure_cookies = (not DEBUG) or _IS_RAILWAY
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=_default_secure_cookies)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=_default_secure_cookies)
# Trust Railway / reverse-proxy HTTPS termination.
if _IS_RAILWAY or env.bool("SECURE_PROXY_SSL_HEADER", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CORS / CSRF
# Single-origin Railway deploy: SPA and API share the host, so CORS is secondary.
# Prefer explicit origins. CORS_ALLOW_ALL_ORIGINS only honoured while DEBUG=True
# unless running on Railway without explicit origins (same-origin SPA is fine).
_default_cors = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if _RAILWAY_PUBLIC_DOMAIN:
    _default_cors.append(f"https://{_RAILWAY_PUBLIC_DOMAIN}")

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=_default_cors)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=DEBUG)
if not DEBUG and not _IS_RAILWAY:
    # Standalone multi-origin prod: never wildcard unless explicitly set above.
    if not env.bool("CORS_ALLOW_ALL_ORIGINS", default=False):
        CORS_ALLOW_ALL_ORIGINS = False

_csrf_defaults = list(_default_cors)
if _IS_RAILWAY:
    _csrf_defaults.extend(
        [
            "https://*.railway.app",
            "https://*.up.railway.app",
        ]
    )
    if _RAILWAY_PUBLIC_DOMAIN:
        _csrf_defaults.append(f"https://{_RAILWAY_PUBLIC_DOMAIN}")

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=_csrf_defaults if (DEBUG or _IS_RAILWAY) else _default_cors,
)

# Extra security headers when not in debug mode
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "same-origin"

# Media files (uploaded files)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Max saved scenarios per browser session (optional multi-month snapshots)
MAX_SAVED_SCENARIOS_PER_SESSION = env.int("MAX_SAVED_SCENARIOS_PER_SESSION", default=12)
