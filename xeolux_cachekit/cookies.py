"""
Helpers pour la gestion des cookies versionnés.

La version des cookies est lue depuis la configuration CacheKit (clé "cookies").
Les points de la version sont remplacés par des underscores dans le nom du cookie.

Exemple :
    versioned_cookie_name("xeolux_consent")  → "xeolux_consent_v1_0_0"
"""

from django.http import HttpRequest, HttpResponse

from .conf import get_setting


def versioned_cookie_name(name: str) -> str:
    """
    Retourne le nom du cookie suffixé avec la version courante.

    Exemple :
        versioned_cookie_name("xeolux_consent") → "xeolux_consent_v1_0_0"
    """
    version = get_setting("cookies").replace(".", "_")
    return f"{name}_v{version}"


def set_versioned_cookie(
    response: HttpResponse,
    name: str,
    value: str,
    **kwargs,
) -> None:
    """
    Définit un cookie versionné sur la réponse HTTP.

    Exemple :
        set_versioned_cookie(response, "xeolux_consent", "true", max_age=3600)
    """
    response.set_cookie(versioned_cookie_name(name), value, **kwargs)


def get_versioned_cookie(
    request: HttpRequest,
    name: str,
    default: str | None = None,
) -> str | None:
    """
    Lit un cookie versionné depuis la requête HTTP.

    Exemple :
        get_versioned_cookie(request, "xeolux_consent")
    """
    return request.COOKIES.get(versioned_cookie_name(name), default)
