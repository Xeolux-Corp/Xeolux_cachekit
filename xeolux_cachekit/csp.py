"""
CSP (Content Security Policy) — Xeolux CacheKit

Génère et injecte l'en-tête Content-Security-Policy dans toutes les réponses.
Protège contre les attaques XSS en déclarant quelles sources de contenu
sont autorisées par le navigateur.

Configuration dans settings.py :

    XEOLUX_CACHEKIT = {
        ...
        "csp": {
            "default-src":  ["'self'"],
            "script-src":   ["'self'"],
            "style-src":    ["'self'", "'unsafe-inline'"],
            "img-src":      ["'self'", "data:"],
            "font-src":     ["'self'"],
            "connect-src":  ["'self'"],
            "frame-src":    ["'none'"],
            "object-src":   ["'none'"],
            "base-uri":     ["'self'"],
            "form-action":  ["'self'"],
        }
    }

Middleware :

    MIDDLEWARE = [
        ...
        "xeolux_cachekit.csp.CSPMiddleware",
    ]

Mode report-only (ne bloque pas, journalise uniquement) :

    XEOLUX_CACHEKIT = {
        "csp": { ... },
        "csp_report_only": True,
    }
"""

from django.conf import settings as django_settings
from django.http import HttpRequest, HttpResponse

# Politique CSP par défaut — restrictive mais compatible avec la plupart des sites Django
_DEFAULT_CSP: dict[str, list[str]] = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "blob:"],
    "font-src": ["'self'"],
    "connect-src": ["'self'"],
    "frame-src": ["'none'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "upgrade-insecure-requests": [],
}


def build_csp_header(policy: dict[str, list[str]]) -> str:
    """
    Construit la valeur de l'en-tête CSP depuis un dictionnaire.

    Exemple :
        {"default-src": ["'self'"], "script-src": ["'self'", "cdn.example.com"]}
        → "default-src 'self'; script-src 'self' cdn.example.com"
    """
    parts = []
    for directive, sources in policy.items():
        if sources:
            parts.append(f"{directive} {' '.join(sources)}")
        else:
            parts.append(directive)
    return "; ".join(parts)


def get_csp_policy() -> dict[str, list[str]]:
    """Retourne la politique CSP fusionnant les defaults avec XEOLUX_CACHEKIT['csp']."""
    cachekit_conf = getattr(django_settings, "XEOLUX_CACHEKIT", {})
    custom = cachekit_conf.get("csp", {}) if isinstance(cachekit_conf, dict) else {}
    return {**_DEFAULT_CSP, **custom}


def is_report_only() -> bool:
    """Retourne True si le mode report-only est activé."""
    cachekit_conf = getattr(django_settings, "XEOLUX_CACHEKIT", {})
    if isinstance(cachekit_conf, dict):
        return bool(cachekit_conf.get("csp_report_only", False))
    return False


class CSPMiddleware:
    """
    Middleware qui injecte l'en-tête Content-Security-Policy (ou
    Content-Security-Policy-Report-Only si csp_report_only=True).

    Les réponses qui ont déjà un en-tête CSP ne sont pas modifiées.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        header_name = (
            "Content-Security-Policy-Report-Only"
            if is_report_only()
            else "Content-Security-Policy"
        )

        # Ne pas écraser un CSP déjà défini par la vue
        if header_name not in response:
            policy = get_csp_policy()
            response[header_name] = build_csp_header(policy)

        return response
