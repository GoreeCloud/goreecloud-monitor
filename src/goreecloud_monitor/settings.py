"""Django settings for GoreeCloud Monitor."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "development-only-not-for-production"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY is required when DJANGO_DEBUG is false")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost" if DEBUG else "")
if not ALLOWED_HOSTS and not DEBUG:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS is required when DJANGO_DEBUG is false")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = ["django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "monitoring.apps.MonitoringConfig"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "monitoring.middleware.WardveilSecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "monitoring.middleware.OperationalRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "goreecloud_monitor.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "goreecloud_monitor.wsgi.application"
ASGI_APPLICATION = "goreecloud_monitor.asgi.application"

DATABASE_ENGINE = os.getenv("DATABASE_ENGINE", "sqlite").strip().lower()
if DATABASE_ENGINE == "postgres":
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": os.getenv("POSTGRES_DB", "goreecloud_monitor"), "USER": os.getenv("POSTGRES_USER", "goreecloud_monitor"), "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""), "HOST": os.getenv("POSTGRES_HOST", "db"), "PORT": int(os.getenv("POSTGRES_PORT", "5432")), "CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 14}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG else "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "monitoring:dashboard"
LOGOUT_REDIRECT_URL = "login"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "goreecloud_monitor_sessionid" if DEBUG else "__Host-goreecloud_monitor_session"
CSRF_COOKIE_NAME = "goreecloud_monitor_csrftoken" if DEBUG else "__Host-goreecloud_monitor_csrf"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = False
MONITOR_CONTENT_SECURITY_POLICY = "default-src 'self'; base-uri 'self'; connect-src 'self'; font-src 'self'; form-action 'self'; frame-ancestors 'none'; img-src 'self' data:; manifest-src 'self'; media-src 'none'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'"
MONITOR_PERMISSIONS_POLICY = "accelerometer=(), browsing-topics=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

MONITOR_MAX_CONCURRENCY = max(1, int(os.getenv("MONITOR_MAX_CONCURRENCY", "10")))
MONITOR_MAX_RESPONSE_BYTES = max(1024, int(os.getenv("MONITOR_MAX_RESPONSE_BYTES", str(1024 * 1024))))
MONITOR_CHECK_RETENTION_DAYS = max(1, int(os.getenv("MONITOR_CHECK_RETENTION_DAYS", "30")))
MONITOR_POLL_SECONDS = max(1, int(os.getenv("MONITOR_POLL_SECONDS", "1")))
MONITOR_ALLOW_PUBLIC_TARGETS = env_bool("MONITOR_ALLOW_PUBLIC_TARGETS", True)
MONITOR_ALLOWED_NETWORKS = env_list("MONITOR_ALLOWED_NETWORKS", "127.0.0.0/8,::1/128")
MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS = env_bool("MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS", False)
MANAGER_API_TOKEN = os.getenv("MANAGER_API_TOKEN", "")
NTFY_BASE_URL = os.getenv("NTFY_BASE_URL", "").rstrip("/")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
NTFY_TOKEN = os.getenv("NTFY_TOKEN", "")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}, "json": {"format": "%(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "standard"}, "json_console": {"class": "logging.StreamHandler", "formatter": "json"}, "null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
    "loggers": {
        "monitoring.wardveil": {"handlers": ["json_console"], "level": os.getenv("WARDVEIL_LOG_LEVEL", "INFO"), "propagate": False},
        "monitoring.access": {"handlers": ["json_console"], "level": os.getenv("MONITOR_ACCESS_LOG_LEVEL", "INFO"), "propagate": False},
        # Django's default request/server messages contain raw URL paths. Monitor emits its own
        # route-name-only access events instead so credentials and query strings cannot enter
        # the application log through these framework loggers.
        "django.request": {"handlers": ["null"], "propagate": False},
        "django.server": {"handlers": ["null"], "propagate": False},
    },
}
