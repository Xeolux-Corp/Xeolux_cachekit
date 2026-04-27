"""
CacheControlMiddleware — Xeolux CacheKit

Ajoute automatiquement l'en-tête :

    Cache-Control: max-age=31536000, immutable

sur toutes les réponses de fichiers statiques qui portent le paramètre
de version CacheKit (ex. ?v=1.0.0).

Cela indique aux navigateurs et aux CDN que le fichier peut être mis en
cache pour un an, et qu'il ne changera jamais à cette URL (immutable).

Ajout dans settings.py :

    MIDDLEWARE = [
        ...
        "xeolux_cachekit.middleware.CacheControlMiddleware",
    ]

Note : ne pas activer sur les URLs statiques sans paramètre de version
(fichiers non versionnés), car ils seraient mis en cache indéfiniment.
"""

from django.conf import settings as django_settings
from django.http import HttpRequest, HttpResponse

from .conf import get_setting

# Un an en secondes
_ONE_YEAR = 60 * 60 * 24 * 365


class CacheControlMiddleware:
    """
    Middleware qui ajoute Cache-Control: max-age=31536000, immutable
    sur les réponses statiques portant le paramètre de version CacheKit.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        static_url: str = getattr(django_settings, "STATIC_URL", "/static/")
        query_param: str = get_setting("query_param")

        # Applique uniquement si :
        # 1. la requête cible un fichier statique
        # 2. le paramètre de version est présent dans la query string
        if (
            request.path.startswith(static_url)
            and query_param in request.GET
        ):
            response["Cache-Control"] = f"max-age={_ONE_YEAR}, immutable"

        return response
