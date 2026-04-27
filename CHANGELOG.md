# Changelog

Toutes les modifications notables de `xeolux-cachekit` sont documentées ici.

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).
Ce projet suit [Semantic Versioning](https://semver.org/lang/fr/).

---

## [0.1.0] — 2026-04-27

### Ajouté

**Configuration**
- Configuration centralisée via `XEOLUX_CACHEKIT` (dict) ou variables individuelles
- Priorité : `XEOLUX_CACHEKIT` > variables individuelles > valeurs par défaut
- Cache interne de la configuration avec invalidation automatique via signal `setting_changed`
- Validation du format semver au démarrage (`AppConfig.ready`)
- Strategy `manual` (versions définies manuellement) ou `hash` (MD5 calculé depuis le contenu des fichiers)

**Versionnement des fichiers statiques**
- `get_cache_version(kind)` — retourne la version ou le hash pour un type donné
- `versioned_static_url(path)` — URL statique avec paramètre de version
- Détection automatique du type selon l'extension (`.css`, `.js`, assets, global)
- `query_param` configurable (défaut : `v`)

**Template tags** (`{% load cachekit_tags %}`)
- `{% versioned_static "path" %}` — URL versionnée avec détection auto
- `{% versioned_static_as "path" "kind" %}` — URL versionnée avec type forcé
- `{% cache_version "kind" %}` — version seule (pour `data-version` ou JS)
- `{% sri_tag "path" %}` — balise `<link>` ou `<script>` avec `integrity=` (SRI)
- `{% sri_hash "path" %}` — hash SRI seul

**Context processor**
- `xeolux_cachekit.context_processors.cache_versions` — injecte `CACHEKIT_*_VERSION` dans tous les templates

**Cookies versionnés**
- `versioned_cookie_name(name)` — suffixe `_v1_0_0`
- `set_versioned_cookie(response, name, value, **kwargs)`
- `get_versioned_cookie(request, name, default=None)`

**SRI (Subresource Integrity)**
- `xeolux_cachekit.sri` — calcul sha256/sha384/sha512 avec cache interne
- Dégradation gracieuse si le fichier est introuvable

**Middlewares**
- `CacheControlMiddleware` — `Cache-Control: max-age=31536000, immutable` sur les statiques versionnées
- `SecurityHeadersMiddleware` — 6 en-têtes de sécurité (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, COOP, CORP)
- `CSPMiddleware` — Content-Security-Policy configurable, mode report-only supporté

**Commandes Django**
- `python manage.py show_cache_versions` — affiche la configuration active
- `python manage.py bump_cache_version <kind> [--minor|--major] [--dry-run]` — incrémente une version dans `settings.py`, détecte les variables d'environnement

**Django System Checks**
- `W001` — version non conforme au format semver
- `W002` — `SecurityHeadersMiddleware` absent de `MIDDLEWARE`
- `W003` — context processor absent de `TEMPLATES`
- `E001` — strategy invalide
- `E002` — sri_algorithm invalide
- `E003` — query_param avec caractères invalides

**Packaging**
- Compatible Django 4.2, 5.0, 5.1 — Python 3.10, 3.11, 3.12
- CI GitHub Actions (matrice 3×3)
- 75 tests unitaires
