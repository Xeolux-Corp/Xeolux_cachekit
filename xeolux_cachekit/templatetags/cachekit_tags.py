"""
Template tags CacheKit.

Usage dans les templates Django :

    {% load cachekit_tags %}

    {# Détection automatique du type selon l'extension #}
    {% versioned_static "css/main.css" %}
    {% versioned_static "js/app.js" %}
    {% versioned_static "img/logo.svg" %}
    {% versioned_static "favicon.ico" %}

    {# Forcer le type manuellement #}
    {% versioned_static_as "css/main.css" "css" %}
    {% versioned_static_as "file.txt" "global" %}

    {# Afficher uniquement la version (utile pour data-version en JS) #}
    {% cache_version "css" %}

    {# SRI — balises <link> et <script> avec integrity= #}
    {% sri_tag "css/main.css" %}
    {% sri_tag "js/app.js" %}

    {# SRI — hash uniquement #}
    {% sri_hash "css/main.css" %}
"""

from django import template
from django.utils.html import format_html

from xeolux_cachekit.utils import versioned_static_url, get_cache_version
from xeolux_cachekit.sri import compute_sri_hash, get_sri_algorithm

register = template.Library()

_CSS_EXTENSIONS = {".css"}
_JS_EXTENSIONS = {".js"}


@register.simple_tag
def versioned_static(path: str) -> str:
    """Retourne l'URL statique versionnée (détection automatique du type)."""
    return versioned_static_url(path)


@register.simple_tag
def versioned_static_as(path: str, kind: str) -> str:
    """Retourne l'URL statique versionnée avec type forcé."""
    return versioned_static_url(path, kind=kind)


@register.simple_tag
def cache_version(kind: str) -> str:
    """
    Retourne uniquement la version pour un type donné.

    Usage :
        <body data-css-version="{% cache_version 'css' %}">
        <script>window.ASSET_VERSION = "{% cache_version 'assets' %}";</script>
    """
    return get_cache_version(kind)


@register.simple_tag
def sri_hash(path: str, algorithm: str = "") -> str:
    """
    Retourne le hash SRI d'un fichier statique.

    Exemple : {% sri_hash "css/main.css" %} → sha384-abc123...
    Retourne une chaîne vide si le fichier est introuvable.
    """
    algo = algorithm or get_sri_algorithm()
    result = compute_sri_hash(path, algo)
    return result or ""


@register.simple_tag
def sri_tag(path: str, algorithm: str = "", crossorigin: str = "anonymous") -> str:
    """
    Génère une balise <link> ou <script> sécurisée avec versionnage et SRI.

    - .css → <link rel="stylesheet" href="..." integrity="..." crossorigin="...">
    - .js  → <script src="..." integrity="..." crossorigin="..."></script>

    Dégradation gracieuse si le fichier est introuvable (pas d'integrity).

    Exemple :
        {% sri_tag "css/main.css" %}
        {% sri_tag "js/app.js" %}
        {% sri_tag "css/main.css" "sha512" %}
    """
    url = versioned_static_url(path)
    algo = algorithm or get_sri_algorithm()
    sri = compute_sri_hash(path, algo)

    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""

    if ext in _CSS_EXTENSIONS:
        if sri:
            return format_html(
                '<link rel="stylesheet" href="{}" integrity="{}" crossorigin="{}">',
                url, sri, crossorigin,
            )
        return format_html('<link rel="stylesheet" href="{}">', url)

    if ext in _JS_EXTENSIONS:
        if sri:
            return format_html(
                '<script src="{}" integrity="{}" crossorigin="{}"></script>',
                url, sri, crossorigin,
            )
        return format_html('<script src="{}"></script>', url)

    return url
