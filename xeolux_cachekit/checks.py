"""
Django System Checks — Xeolux CacheKit

Vérifie la configuration du package au démarrage et alerte si :
- La version n'est pas au format semver X.Y.Z
- Un middleware recommandé est absent
- strategy a une valeur inconnue
- sri_algorithm a une valeur non supportée
- query_param contient des caractères invalides pour une query string

Ces checks s'exécutent via `python manage.py check` ou au lancement du serveur.
"""

import re

from django.core.checks import Error, Warning, register, Tags

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_VERSION_KEYS = ("global", "css", "js", "assets", "cookies")
_VALID_STRATEGIES = {"manual", "hash"}
_VALID_SRI_ALGORITHMS = {"sha256", "sha384", "sha512"}
_QUERY_PARAM_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


@register(Tags.security)
def check_cachekit_config(app_configs, **kwargs):
    """Vérifie la cohérence de la configuration XEOLUX CacheKit."""
    from .conf import _get_config

    errors = []
    config = _get_config()

    # Vérifie le format semver des versions
    for key in _VERSION_KEYS:
        value = config.get(key, "")
        if value and not _SEMVER_RE.match(value):
            errors.append(
                Warning(
                    f"La version CacheKit '{key}' = \"{value}\" ne respecte pas "
                    f"le format X.Y.Z (semver).",
                    hint=f"Définissez XEOLUX_CACHEKIT[\"{key}\"] avec un format type \"1.0.0\".",
                    obj="xeolux_cachekit",
                    id="xeolux_cachekit.W001",
                )
            )

    # Vérifie la strategy
    strategy = config.get("strategy", "manual")
    if strategy not in _VALID_STRATEGIES:
        errors.append(
            Error(
                f"XEOLUX_CACHEKIT[\"strategy\"] = \"{strategy}\" est invalide.",
                hint=f"Valeurs acceptées : {sorted(_VALID_STRATEGIES)}.",
                obj="xeolux_cachekit",
                id="xeolux_cachekit.E001",
            )
        )

    # Vérifie l'algorithme SRI
    sri_algo = config.get("sri_algorithm", "sha384")
    if sri_algo not in _VALID_SRI_ALGORITHMS:
        errors.append(
            Error(
                f"XEOLUX_CACHEKIT[\"sri_algorithm\"] = \"{sri_algo}\" est invalide.",
                hint=f"Valeurs acceptées : {sorted(_VALID_SRI_ALGORITHMS)}.",
                obj="xeolux_cachekit",
                id="xeolux_cachekit.E002",
            )
        )

    # Vérifie que query_param est un nom de paramètre URL valide
    query_param = config.get("query_param", "v")
    if not _QUERY_PARAM_RE.match(query_param):
        errors.append(
            Error(
                f"XEOLUX_CACHEKIT[\"query_param\"] = \"{query_param}\" contient "
                f"des caractères invalides pour un paramètre d'URL.",
                hint="Utilisez uniquement des lettres, chiffres, tirets et underscores.",
                obj="xeolux_cachekit",
                id="xeolux_cachekit.E003",
            )
        )

    return errors


@register(Tags.security)
def check_cachekit_middleware(app_configs, **kwargs):
    """Vérifie que les middlewares CacheKit recommandés sont configurés."""
    from django.conf import settings

    warnings = []
    middleware = getattr(settings, "MIDDLEWARE", [])

    if "xeolux_cachekit.middleware.SecurityHeadersMiddleware" not in middleware:
        warnings.append(
            Warning(
                "SecurityHeadersMiddleware n'est pas dans MIDDLEWARE.",
                hint=(
                    "Ajoutez \"xeolux_cachekit.middleware.SecurityHeadersMiddleware\" "
                    "dans MIDDLEWARE pour activer les en-têtes de sécurité HTTP."
                ),
                obj="xeolux_cachekit",
                id="xeolux_cachekit.W002",
            )
        )

    context_processors = []
    for tpl in getattr(settings, "TEMPLATES", []):
        context_processors += (
            tpl.get("OPTIONS", {}).get("context_processors", [])
        )

    if "xeolux_cachekit.context_processors.cache_versions" not in context_processors:
        warnings.append(
            Warning(
                "Le context processor cache_versions n'est pas configuré.",
                hint=(
                    "Ajoutez \"xeolux_cachekit.context_processors.cache_versions\" "
                    "dans TEMPLATES[OPTIONS][context_processors] pour exposer les "
                    "versions de cache dans vos templates."
                ),
                obj="xeolux_cachekit",
                id="xeolux_cachekit.W003",
            )
        )

    return warnings
