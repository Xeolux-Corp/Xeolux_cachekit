"""
Lecture de la configuration XEOLUX CacheKit depuis settings.py.

Priorité :
  1. XEOLUX_CACHEKIT (dict centralisé)
  2. Variables individuelles XEOLUX_CSS_VERSION, etc.
  3. Valeurs par défaut ("1.0.0" / "v")
"""

from django.conf import settings

# Valeurs par défaut
_DEFAULTS: dict = {
    "global": "1.0.0",
    "css": "1.0.0",
    "js": "1.0.0",
    "assets": "1.0.0",
    "cookies": "1.0.0",
    "query_param": "v",
    "strategy": "manual",  # "manual" ou "hash"
}

# Cache interne — invalider avec clear_config_cache() (utile dans les tests)
_config_cache: dict | None = None


def _get_config() -> dict:
    """Retourne la configuration résolue (mise en cache après le premier appel)."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    centralized = getattr(settings, "XEOLUX_CACHEKIT", None)
    if centralized and isinstance(centralized, dict):
        _config_cache = {**_DEFAULTS, **centralized}
    else:
        _config_cache = {
            "global": getattr(settings, "XEOLUX_GLOBAL_VERSION", _DEFAULTS["global"]),
            "css": getattr(settings, "XEOLUX_CSS_VERSION", _DEFAULTS["css"]),
            "js": getattr(settings, "XEOLUX_JS_VERSION", _DEFAULTS["js"]),
            "assets": getattr(settings, "XEOLUX_ASSETS_VERSION", _DEFAULTS["assets"]),
            "cookies": getattr(settings, "XEOLUX_COOKIE_VERSION", _DEFAULTS["cookies"]),
            "query_param": _DEFAULTS["query_param"],
        }

    return _config_cache


def clear_config_cache() -> None:
    """Invalide le cache de configuration et de hash (utile dans les tests ou après hot-reload)."""
    global _config_cache
    _config_cache = None
    # Invalide aussi le cache des hashes pour cohérence
    from .hashers import clear_hash_cache
    clear_hash_cache()


def get_setting(key: str) -> str:
    """Retourne la valeur d'une clé de configuration CacheKit."""
    config = _get_config()
    return config.get(key, _DEFAULTS.get(key, ""))
