"""
Context processor CacheKit.

Injecte les versions de cache dans le contexte de tous les templates.

Ajout dans settings.py :
    TEMPLATES = [{
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "xeolux_cachekit.context_processors.cache_versions",
            ],
        },
    }]
"""

from django.http import HttpRequest

from .conf import get_setting


def cache_versions(request: HttpRequest) -> dict:
    """Injecte les variables CACHEKIT_* dans le contexte des templates."""
    return {
        "CACHEKIT_GLOBAL_VERSION": get_setting("global"),
        "CACHEKIT_CSS_VERSION": get_setting("css"),
        "CACHEKIT_JS_VERSION": get_setting("js"),
        "CACHEKIT_ASSETS_VERSION": get_setting("assets"),
        "CACHEKIT_COOKIE_VERSION": get_setting("cookies"),
    }
