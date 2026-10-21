"""
Django settings for pizza_simulator project.
"""

import os
from pathlib import Path

import environ

env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY", default="django-insecure-development-key-for-testing-only")

DEBUG = env.bool("DEBUG", False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])


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
    "simulator.middleware.ClerkSessionMiddleware",
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
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Railway-safe default: SQLite. Set DATABASE_URL for Neon/Postgres (optional).
_database_url = env.str("DATABASE_URL", default="")
if _database_url:
    # django-environ parses postgres URLs; force SSL for Neon
    DATABASES = {"default": env.db("DATABASE_URL")}
    if DATABASES["default"].get("ENGINE", "").endswith("postgresql"):
        DATABASES["default"].setdefault("OPTIONS", {})
        DATABASES["default"]["OPTIONS"].setdefault("sslmode", "require")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# When running in Docker, frontend_build exists and we serve the React SPA from it.
# Vite writes hashed files under frontend_build/static (assetsDir), which WhiteNoise serves.
FRONTEND_BUILD_DIR = BASE_DIR / "frontend_build"
if FRONTEND_BUILD_DIR.exists():
    STATIC_ROOT = str(FRONTEND_BUILD_DIR / "static")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Session settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_SAVE_EVERY_REQUEST = False

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Media files (uploaded files)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ── Google OAuth (optional; off by default so Railway keeps working) ──────────
GOOGLE_OAUTH_ENABLED = env.bool("GOOGLE_OAUTH_ENABLED", default=False)
GOOGLE_CLIENT_ID = env.str("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env.str("GOOGLE_CLIENT_SECRET", default="")
# When True, API endpoints (except auth/config) require an authenticated user.
REQUIRE_AUTH = env.bool("REQUIRE_AUTH", default=False)

# Chat over the local numbers. The key stays server-side. Empty disables OpenRouter.
OPENROUTER_API_KEY = env.str("OPENROUTER_API_KEY", default="")
OPENROUTER_MODEL = env.str("OPENROUTER_MODEL", default="x-ai/grok-4.7")
OPENROUTER_BASE_URL = env.str("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

# Local Ollama. Docker overrides this so the container can reach the host.
OLLAMA_BASE_URL = env.str("OLLAMA_BASE_URL", default="http://127.0.0.1:11434")

# Clerk. Empty leaves the API open (single-user machine). Never expose the secret to the browser.
CLERK_SECRET_KEY = env.str("CLERK_SECRET_KEY", default="")
# The only account that may change AI settings once Clerk is on. Not sent to the browser.
SUPER_ADMIN_EMAIL = env.str("SUPER_ADMIN_EMAIL", default="")
