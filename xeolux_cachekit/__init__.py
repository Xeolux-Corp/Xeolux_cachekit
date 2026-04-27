"""
xeolux_cachekit — Gestion des versions de cache pour fichiers statiques et cookies Django.
"""

__version__ = "0.1.0"
__author__ = "XEOLUX"

from .utils import get_cache_version, versioned_static_url
from .cookies import versioned_cookie_name, get_versioned_cookie, set_versioned_cookie

__all__ = [
    "get_cache_version",
    "versioned_static_url",
    "versioned_cookie_name",
    "get_versioned_cookie",
    "set_versioned_cookie",
]
