"""
Helpers Python publics pour la gestion des versions de cache.
"""

from urllib.parse import urlencode
from django.templatetags.static import static

from .conf import get_setting

# Extensions reconnues par type
_CSS_EXTENSIONS = {".css"}
_JS_EXTENSIONS = {".js"}
_ASSET_EXTENSIONS = {".ico", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".avif"}

_KIND_MAP = {
    "css": _CSS_EXTENSIONS,
    "js": _JS_EXTENSIONS,
    "assets": _ASSET_EXTENSIONS,
}

# Kinds compatibles avec la stratégie hash
_HASHABLE_KINDS = frozenset({"css", "js", "assets"})


def detect_kind(path: str) -> str:
    """Détecte automatiquement le type d'un fichier à partir de son extension."""
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    for kind, extensions in _KIND_MAP.items():
        if ext in extensions:
            return kind
    return "global"


def get_cache_version(kind: str) -> str:
    """
    Retourne la version de cache pour un type donné.

    Valeurs valides : "css", "js", "assets", "cookies", "global"

    Si strategy = "hash" et kind est hashable (css, js, assets),
    retourne le hash MD5 des fichiers statiques correspondants.
    Sinon, retourne la version configurée manuellement.
    """
    valid_kinds = {"css", "js", "assets", "cookies", "global"}
    if kind not in valid_kinds:
        raise ValueError(f"Type de cache inconnu : '{kind}'. Valeurs valides : {valid_kinds}")

    strategy = get_setting("strategy")
    if strategy == "hash" and kind in _HASHABLE_KINDS:
        from .hashers import compute_hash_for_kind
        return compute_hash_for_kind(kind)

    return get_setting(kind)


def versioned_static_url(path: str, kind: str | None = None) -> str:
    """
    Retourne l'URL statique Django avec le paramètre de version ajouté.

    Exemple :
        versioned_static_url("css/main.css") → /static/css/main.css?v=1.0.0
    """
    resolved_kind = kind if kind is not None else detect_kind(path)
    version = get_cache_version(resolved_kind)
    param = get_setting("query_param")
    url = static(path)
    return f"{url}?{urlencode({param: version})}"
