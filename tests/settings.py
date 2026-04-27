"""
Configuration Django minimale pour les tests unitaires du package xeolux-cachekit.
"""

SECRET_KEY = "xeolux-cachekit-test-secret-key-not-for-production"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "xeolux_cachekit",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

STATIC_URL = "/static/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "xeolux_cachekit.context_processors.cache_versions",
            ],
        },
    }
]

USE_TZ = True
