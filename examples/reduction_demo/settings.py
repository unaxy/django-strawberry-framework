"""Settings for the reduction demo: in-memory SQLite, three snapshots of one app, two each of two others."""

SECRET_KEY = "reduction-demo"
DEBUG = True
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_strawberry_framework",
    "astronomy_opaque",
    "astronomy_declared",
    "astronomy_reduced",
    "pricing_restated",
    "pricing_reduced",
    "suspension_restated",
    "suspension_reduced",
]

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DJANGO_STRAWBERRY_FRAMEWORK = {}
