"""
Middlewares de sécurité — Xeolux CacheKit

CacheControlMiddleware
    Ajoute Cache-Control: max-age=31536000, immutable sur les statiques versionnées.

SecurityHeadersMiddleware
    Ajoute les en-têtes de sécurité HTTP essentiels sur toutes les réponses :
    - X-Content-Type-Options: nosniff         — empêche le MIME sniffing
    - X-Frame-Options: DENY                  — protection contre le clickjacking
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy                      — désactive les APIs sensibles
    - Cross-Origin-Opener-Policy: same-origin — isolation des contextes de navigation
    - Cross-Origin-Resource-Policy: same-origin

    Ces en-têtes complètent (sans remplacer) django.middleware.security.SecurityMiddleware.

Configuration dans settings.py :

    MIDDLEWARE = [
        ...
        "xeolux_cachekit.middleware.CacheControlMiddleware",
        "xeolux_cachekit.middleware.SecurityHeadersMiddleware",
    ]

    # Personnalisation optionnelle des en-têtes de sécurité :
    XEOLUX_CACHEKIT = {
        ...
        "security_headers": {
            "X-Frame-Options": "SAMEORIGIN",        # DENY (défaut) ou SAMEORIGIN
            "Referrer-Policy": "no-referrer",        # surcharger la valeur par défaut
            "Permissions-Policy": "camera=(), ...",  # politique personnalisée
        }
    }
"""

from django.conf import settings as django_settings
from django.http import HttpRequest, HttpResponse

from .conf import get_setting

# Un an en secondes
_ONE_YEAR = 60 * 60 * 24 * 365

# En-têtes de sécurité par défaut
_DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


class CacheControlMiddleware:
    """
    Ajoute Cache-Control: max-age=31536000, immutable sur les réponses
    statiques portant le paramètre de version CacheKit.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        static_url: str = getattr(django_settings, "STATIC_URL", "/static/")
        query_param: str = get_setting("query_param")

        if (
            request.path.startswith(static_url)
            and query_param in request.GET
        ):
            response["Cache-Control"] = f"max-age={_ONE_YEAR}, immutable"

        return response


class SecurityHeadersMiddleware:
    """
    Ajoute les en-têtes de sécurité HTTP essentiels sur toutes les réponses.

    Protège contre :
    - MIME sniffing (X-Content-Type-Options)
    - Clickjacking (X-Frame-Options)
    - Fuite du Referer cross-origin (Referrer-Policy)
    - Accès aux APIs sensibles du navigateur (Permissions-Policy)
    - Cross-origin isolation attacks (COOP, CORP)

    Les en-têtes déjà présents dans la réponse ne sont PAS écrasés,
    ce qui permet aux vues de surcharger les valeurs si nécessaire.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Fusionne les defaults avec la config XEOLUX_CACHEKIT["security_headers"]
        custom = {}
        try:
            cachekit_conf = getattr(django_settings, "XEOLUX_CACHEKIT", {})
            if isinstance(cachekit_conf, dict):
                custom = cachekit_conf.get("security_headers", {})
        except Exception:
            pass
        self._headers = {**_DEFAULT_SECURITY_HEADERS, **custom}

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        for header, value in self._headers.items():
            if header not in response:
                response[header] = value
        return response

