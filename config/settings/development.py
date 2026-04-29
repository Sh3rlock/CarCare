from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")  # noqa: F405

# SQLite for local development — no Postgres setup required
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Show emails in console during development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable ManifestStaticFilesStorage in dev (no collectstatic needed)
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
