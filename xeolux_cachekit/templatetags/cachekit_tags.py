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
    {% cache_version "js" %}
"""

from django import template

from xeolux_cachekit.utils import versioned_static_url, get_cache_version

register = template.Library()


@register.simple_tag
def versioned_static(path: str) -> str:
    """
    Retourne l'URL statique versionnée avec détection automatique du type.

    Exemple : {% versioned_static "css/main.css" %} → /static/css/main.css?v=1.0.0
    """
    return versioned_static_url(path)


@register.simple_tag
def versioned_static_as(path: str, kind: str) -> str:
    """
    Retourne l'URL statique versionnée avec un type forcé manuellement.

    Exemple : {% versioned_static_as "file.txt" "global" %} → /static/file.txt?v=1.0.0
    """
    return versioned_static_url(path, kind=kind)


@register.simple_tag
def cache_version(kind: str) -> str:
    """
    Retourne uniquement la chaîne de version pour un type donné.

    Utile pour les attributs data-version ou les variables JS.

    Exemple :
        {% cache_version "css" %}          → 1.0.3
        {% cache_version "js" %}           → 1.2.0

    Usage dans un template :
        <body data-css-version="{% cache_version 'css' %}">
        <script>window.ASSET_VERSION = "{% cache_version 'assets' %}";</script>
    """
    return get_cache_version(kind)

