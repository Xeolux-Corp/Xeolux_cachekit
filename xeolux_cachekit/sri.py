"""
SRI (Subresource Integrity) — Xeolux CacheKit

Calcule les hashes d'intégrité (sha256/sha384/sha512) pour les fichiers statiques.
Ces hashes sont placés dans l'attribut `integrity` des balises <link> et <script>,
permettant au navigateur de vérifier que le fichier n'a pas été altéré en transit.

Référence : https://developer.mozilla.org/fr/docs/Web/Security/Subresource_Integrity

Exemple de résultat :
    <link rel="stylesheet"
          href="/static/css/main.css?v=1.0.3"
          integrity="sha384-abc123..."
          crossorigin="anonymous">
"""

import hashlib
import base64
from pathlib import Path
from functools import lru_cache

from django.conf import settings

_SUPPORTED_ALGORITHMS = frozenset({"sha256", "sha384", "sha512"})

# Cache interne des hashes SRI — invalidé par clear_sri_cache()
_sri_cache: dict[str, str] = {}


def clear_sri_cache() -> None:
    """Invalide le cache SRI (utile après collectstatic ou dans les tests)."""
    _sri_cache.clear()


def _find_static_file(path: str) -> Path | None:
    """
    Localise un fichier statique dans STATIC_ROOT ou STATICFILES_DIRS.
    Retourne None si introuvable.
    """
    # Cherche d'abord dans STATIC_ROOT (après collectstatic)
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        candidate = Path(static_root) / path
        if candidate.is_file():
            return candidate

    # Cherche dans STATICFILES_DIRS (fichiers sources)
    for base in getattr(settings, "STATICFILES_DIRS", []):
        candidate = Path(base) / path
        if candidate.is_file():
            return candidate

    return None


def compute_sri_hash(path: str, algorithm: str = "sha384") -> str | None:
    """
    Calcule le hash d'intégrité SRI d'un fichier statique.

    Retourne une chaîne au format "sha384-<base64>" ou None si le fichier
    est introuvable (ex. en mode développement sans collectstatic).

    Args:
        path:      chemin relatif du fichier (ex. "css/main.css")
        algorithm: "sha256", "sha384" ou "sha512" (défaut: "sha384")
    """
    if algorithm not in _SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Algorithme SRI invalide : '{algorithm}'. "
            f"Valeurs supportées : {sorted(_SUPPORTED_ALGORITHMS)}"
        )

    cache_key = f"{algorithm}:{path}"
    if cache_key in _sri_cache:
        return _sri_cache[cache_key]

    file_path = _find_static_file(path)
    if file_path is None:
        return None

    content = file_path.read_bytes()
    digest = hashlib.new(algorithm, content).digest()
    encoded = base64.b64encode(digest).decode("ascii")
    result = f"{algorithm}-{encoded}"

    _sri_cache[cache_key] = result
    return result


def get_sri_algorithm() -> str:
    """Retourne l'algorithme SRI configuré (défaut : sha384)."""
    from .conf import get_setting
    return get_setting("sri_algorithm") or "sha384"
