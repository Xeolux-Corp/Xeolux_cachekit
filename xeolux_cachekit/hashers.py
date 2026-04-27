"""
Calcul de hash MD5 des fichiers statiques par type.

Utilisé quand XEOLUX_CACHEKIT["strategy"] = "hash".

Le hash est calculé sur le contenu de tous les fichiers du type concerné
trouvés dans STATIC_ROOT et STATICFILES_DIRS.
Les cookies et global n'ont pas de fichiers associés — ils restent en mode manuel.
"""

import hashlib
from pathlib import Path

from django.conf import settings

# Extensions par type (cohérent avec utils.py)
_EXTENSIONS_BY_KIND: dict[str, frozenset[str]] = {
    "css": frozenset({".css"}),
    "js": frozenset({".js"}),
    "assets": frozenset({".ico", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".avif"}),
}

# Kinds pour lesquels le hash n'a pas de sens (pas de fichiers statiques)
_MANUAL_ONLY_KINDS = frozenset({"cookies", "global"})

# Cache interne des hashes calculés — invalidé par clear_hash_cache()
_hash_cache: dict[str, str] = {}


def clear_hash_cache() -> None:
    """Invalide le cache des hashes (utile après collectstatic ou dans les tests)."""
    _hash_cache.clear()


def _collect_dirs() -> list[Path]:
    """Retourne les répertoires de fichiers statiques à scanner."""
    dirs: list[Path] = []

    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        p = Path(static_root)
        if p.exists():
            dirs.append(p)

    for d in getattr(settings, "STATICFILES_DIRS", []):
        p = Path(d)
        if p.exists():
            dirs.append(p)

    return dirs


def compute_hash_for_kind(kind: str, length: int = 8) -> str:
    """
    Calcule un hash MD5 combiné de tous les fichiers statiques d'un type donné.

    Retourne les `length` premiers caractères du hash hexadécimal.
    Si aucun fichier n'est trouvé, retourne "00000000".

    Les kinds "cookies" et "global" ne sont pas hashables — ValueError levée.
    """
    if kind in _MANUAL_ONLY_KINDS:
        raise ValueError(
            f"Le kind '{kind}' ne peut pas être hashé (pas de fichiers statiques associés). "
            f"Utilisez strategy='manual' pour ce type."
        )

    if kind in _hash_cache:
        return _hash_cache[kind]

    extensions = _EXTENSIONS_BY_KIND.get(kind, frozenset())
    if not extensions:
        return "00000000"

    dirs = _collect_dirs()
    if not dirs:
        return "00000000"

    # Collecte et tri déterministe pour un hash stable
    files: list[Path] = []
    for base in dirs:
        for f in base.rglob("*"):
            if f.is_file() and f.suffix.lower() in extensions:
                files.append(f)

    if not files:
        return "00000000"

    hasher = hashlib.md5()
    for f in sorted(files):
        hasher.update(f.read_bytes())

    result = hasher.hexdigest()[:length]
    _hash_cache[kind] = result
    return result
