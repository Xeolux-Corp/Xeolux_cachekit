"""
conftest.py — Configuration pytest globale pour xeolux-cachekit.

Invalide le cache de configuration CacheKit avant chaque test,
pour que @override_settings soit toujours pris en compte.
"""

import pytest


@pytest.fixture(autouse=True)
def clear_cachekit_config():
    """Vide le cache de conf avant et après chaque test."""
    from xeolux_cachekit.conf import clear_config_cache
    clear_config_cache()
    yield
    clear_config_cache()
