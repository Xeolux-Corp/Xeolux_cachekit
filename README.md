# xeolux-cachekit

[![Tests](https://github.com/Xeolux-Corp/Xeolux_cachekit/actions/workflows/tests.yml/badge.svg)](https://github.com/Xeolux-Corp/Xeolux_cachekit/actions)
[![PyPI version](https://img.shields.io/pypi/v/xeolux-cachekit)](https://pypi.org/project/xeolux-cachekit/)
[![Python](https://img.shields.io/pypi/pyversions/xeolux-cachekit)](https://pypi.org/project/xeolux-cachekit/)
[![Django](https://img.shields.io/badge/django-4.2%20%7C%205.0%20%7C%205.1-green)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Package Django réutilisable pour gérer les **versions de cache** des fichiers statiques (CSS, JS, assets) et des cookies. Développé par [XEOLUX](https://github.com/Xeolux-Corp).

---

## Fonctionnalités

- ✅ Versionnement des URLs statiques : `/static/css/main.css?v=1.0.3`
- ✅ Détection automatique du type selon l'extension de fichier
- ✅ Strategy `hash` : version calculée depuis le contenu des fichiers (zéro gestion manuelle)
- ✅ Cookies versionnés : `xeolux_consent_v1_0_0`
- ✅ Context processor pour exposer les versions dans tous les templates
- ✅ Template tags `{% versioned_static %}`, `{% versioned_static_as %}`, `{% cache_version %}`
- ✅ Middleware `Cache-Control: max-age=31536000, immutable` sur les statiques versionnées
- ✅ Commande `show_cache_versions` pour diagnostiquer la configuration
- ✅ Commande `bump_cache_version` pour incrémenter une version (patch/minor/major)
- ✅ Compatible Django 4.2, 5.0, 5.1 — Python 3.10, 3.11, 3.12

---

## Installation

```bash
pip install xeolux-cachekit
```

Ou en local depuis les sources :

```bash
pip install -e /chemin/vers/xeolux-cachekit
```

---

## Configuration

### 1. `INSTALLED_APPS`

```python
# settings.py
INSTALLED_APPS = [
    ...
    "xeolux_cachekit",
]
```

### 2. Context processor

```python
TEMPLATES = [
    {
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "xeolux_cachekit.context_processors.cache_versions",
            ],
        },
    }
]
```

### 3. Middleware (optionnel)

Ajoute automatiquement `Cache-Control: max-age=31536000, immutable` sur les fichiers statiques versionnés.

```python
MIDDLEWARE = [
    ...
    "xeolux_cachekit.middleware.CacheControlMiddleware",
]
```

### 4. Versions — Configuration

**Option A — Configuration centralisée (recommandée) :**

```python
XEOLUX_CACHEKIT = {
    "global":      "1.0.0",
    "css":         "1.0.3",
    "js":          "1.2.0",
    "assets":      "1.0.8",
    "cookies":     "1.0.0",
    "query_param": "v",       # nom du paramètre dans l'URL
    "strategy":    "manual",  # "manual" ou "hash"
}
```

**Option B — Strategy `hash` (zéro gestion manuelle) :**

```python
XEOLUX_CACHEKIT = {
    "strategy":    "hash",   # hash MD5 calculé depuis le contenu des fichiers
    "cookies":     "1.0.0",  # toujours manuel (pas de fichiers statiques)
    "global":      "1.0.0",
    "query_param": "v",
}
# → /static/css/main.css?v=a3f2c1d4
```

**Option C — Variables individuelles :**

```python
XEOLUX_GLOBAL_VERSION = "1.0.0"
XEOLUX_CSS_VERSION    = "1.0.3"
XEOLUX_JS_VERSION     = "1.2.0"
XEOLUX_ASSETS_VERSION = "1.0.8"
XEOLUX_COOKIE_VERSION = "1.0.0"
```

**Priorité :** `XEOLUX_CACHEKIT` > variables individuelles > valeurs par défaut (`"1.0.0"` / `"v"` / `"manual"`).

---

## Utilisation dans les templates

```html
{% load cachekit_tags %}

<!-- Détection automatique du type selon l'extension -->
<link rel="stylesheet" href="{% versioned_static 'css/main.css' %}">
<script src="{% versioned_static 'js/app.js' %}"></script>
<img src="{% versioned_static 'img/logo.svg' %}">
<link rel="icon" href="{% versioned_static 'favicon.ico' %}">

<!-- Forcer le type manuellement -->
<link rel="stylesheet" href="{% versioned_static_as 'css/main.css' 'css' %}">
<a href="{% versioned_static_as 'data/file.txt' 'global' %}">Télécharger</a>

<!-- Afficher uniquement la version (utile pour les attributs data- ou JS) -->
<body data-css-version="{% cache_version 'css' %}">
<script>window.ASSET_VERSION = "{% cache_version 'assets' %}";</script>
```

Variables du context processor disponibles directement :

```html
<p>CSS : {{ CACHEKIT_CSS_VERSION }}</p>
<p>JS  : {{ CACHEKIT_JS_VERSION }}</p>
```

### Types détectés automatiquement

| Extension | Type |
|-----------|------|
| `.css` | `css` |
| `.js` | `js` |
| `.ico`, `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`, `.gif`, `.avif` | `assets` |
| Autre | `global` |

---

## Utilisation en Python

```python
from xeolux_cachekit import get_cache_version, versioned_static_url

get_cache_version("css")     # "1.0.3"
get_cache_version("js")      # "1.2.0"
get_cache_version("assets")  # "1.0.8" ou hash "a3f2c1d4"
get_cache_version("cookies") # "1.0.0"
get_cache_version("global")  # "1.0.0"

versioned_static_url("css/main.css")                    # "/static/css/main.css?v=1.0.3"
versioned_static_url("data/file.txt", kind="global")    # "/static/data/file.txt?v=1.0.0"
```

---

## Gestion des cookies versionnés

```python
from xeolux_cachekit import (
    versioned_cookie_name,
    set_versioned_cookie,
    get_versioned_cookie,
)

versioned_cookie_name("xeolux_consent")
# → "xeolux_consent_v1_0_0"

# Dans une vue Django
def ma_vue(request):
    response = HttpResponse("OK")
    set_versioned_cookie(response, "xeolux_consent", "true", max_age=365 * 24 * 3600)
    return response

def ma_vue(request):
    consent = get_versioned_cookie(request, "xeolux_consent", default="false")
```

---

## Commandes Django

### Afficher les versions configurées

```bash
python manage.py show_cache_versions
```

```
XEOLUX CacheKit versions:
  - Global      : 1.0.0
  - CSS         : 1.0.3
  - JS          : 1.2.0
  - Assets      : 1.0.8
  - Cookies     : 1.0.0
  - Query param : v
```

### Incrémenter une version

```bash
python manage.py bump_cache_version css             # 1.0.3 → 1.0.4  (patch, défaut)
python manage.py bump_cache_version js --minor      # 1.2.0 → 1.3.0
python manage.py bump_cache_version assets --major  # 1.0.8 → 2.0.0
python manage.py bump_cache_version all             # tout incrémenter
python manage.py bump_cache_version css --dry-run   # aperçu sans écriture
```

> Si la version est définie via une variable d'environnement (`os.environ`, `env()`, etc.), la commande le détecte et affiche un message demandant de modifier le `.env` manuellement.

---

## Lancer les tests

```bash
pip install pytest pytest-django
pytest
```

---

## Configuration complète — Exemple

```python
# settings.py

INSTALLED_APPS = [
    ...
    "xeolux_cachekit",
]

MIDDLEWARE = [
    ...
    "xeolux_cachekit.middleware.CacheControlMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "xeolux_cachekit.context_processors.cache_versions",
            ],
        },
    }
]

XEOLUX_CACHEKIT = {
    "global":      "1.0.0",
    "css":         "1.0.3",
    "js":          "1.2.0",
    "assets":      "1.0.8",
    "cookies":     "1.0.0",
    "query_param": "v",
    "strategy":    "manual",  # ou "hash" pour hash automatique
}
```

---

## Licence

MIT — voir [LICENSE](LICENSE).


Package Django interne **XEOLUX** pour gérer les versions de cache des fichiers statiques (CSS, JS, assets) et des cookies.

---

## Présentation

`xeolux-cachekit` permet d'ajouter automatiquement un paramètre de version aux URLs de fichiers statiques dans vos templates Django :

```
/static/css/main.css?v=1.0.3
/static/js/app.js?v=1.2.0
/static/img/logo.svg?v=1.0.8
```

Il fournit également des helpers pour nommer et manipuler les cookies avec un suffixe de version.

---

## Installation locale

```bash
pip install -e /chemin/vers/xeolux-cachekit
```

Ou ajoutez dans votre `requirements.txt` / `pyproject.toml` :

```
xeolux-cachekit @ file:///chemin/vers/xeolux-cachekit
```

---

## Configuration

### 1. Ajout dans INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    ...
    "xeolux_cachekit",
]
```

### 2. Ajout du context processor

```python
# settings.py
TEMPLATES = [
    {
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "xeolux_cachekit.context_processors.cache_versions",
            ],
        },
    }
]
```

### 3. Configuration des versions

**Option A — Configuration centralisée (recommandée) :**

```python
# settings.py
XEOLUX_CACHEKIT = {
    "global": "1.0.0",
    "css": "1.0.3",
    "js": "1.2.0",
    "assets": "1.0.8",
    "cookies": "1.0.0",
    "query_param": "v",    # nom du paramètre dans l'URL (?v=...)
}
```

**Option B — Variables individuelles :**

```python
# settings.py
XEOLUX_GLOBAL_VERSION = "1.0.0"
XEOLUX_CSS_VERSION    = "1.0.3"
XEOLUX_JS_VERSION     = "1.2.0"
XEOLUX_ASSETS_VERSION = "1.0.8"
XEOLUX_COOKIE_VERSION = "1.0.0"
```

**Priorité :** `XEOLUX_CACHEKIT` > variables individuelles > valeurs par défaut (`"1.0.0"` / `"v"`).

---

## Utilisation dans les templates

```html
{% load cachekit_tags %}

<!-- Détection automatique du type selon l'extension -->
<link rel="stylesheet" href="{% versioned_static 'css/main.css' %}">
<script src="{% versioned_static 'js/app.js' %}"></script>
<img src="{% versioned_static 'img/logo.svg' %}">
<link rel="icon" href="{% versioned_static 'favicon.ico' %}">

<!-- Forcer le type manuellement -->
<link rel="stylesheet" href="{% versioned_static_as 'css/main.css' 'css' %}">
<script src="{% versioned_static_as 'js/app.js' 'js' %}"></script>
<img src="{% versioned_static_as 'img/logo.png' 'assets' %}">
<a href="{% versioned_static_as 'data/file.txt' 'global' %}">Télécharger</a>
```

Les variables injectées par le context processor sont aussi disponibles directement :

```html
<p>Version CSS : {{ CACHEKIT_CSS_VERSION }}</p>
<p>Version JS : {{ CACHEKIT_JS_VERSION }}</p>
```

### Types détectés automatiquement

| Extension                                      | Type     |
|------------------------------------------------|----------|
| `.css`                                         | `css`    |
| `.js`                                          | `js`     |
| `.ico`, `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`, `.gif`, `.avif` | `assets` |
| Autre                                          | `global` |

---

## Utilisation en Python

```python
from xeolux_cachekit import get_cache_version, versioned_static_url

# Obtenir une version
get_cache_version("css")       # "1.0.3"
get_cache_version("js")        # "1.2.0"
get_cache_version("assets")    # "1.0.8"
get_cache_version("cookies")   # "1.0.0"
get_cache_version("global")    # "1.0.0"

# Générer une URL versionnée
versioned_static_url("css/main.css")               # "/static/css/main.css?v=1.0.3"
versioned_static_url("img/logo.svg")               # "/static/img/logo.svg?v=1.0.8"
versioned_static_url("data/file.txt", kind="global")  # "/static/data/file.txt?v=1.0.0"
```

---

## Gestion des cookies versionnés

```python
from xeolux_cachekit import (
    versioned_cookie_name,
    set_versioned_cookie,
    get_versioned_cookie,
)

# Nom du cookie avec suffixe de version
versioned_cookie_name("xeolux_consent")
# → "xeolux_consent_v1_0_0"

# Définir un cookie versionné dans une vue Django
def ma_vue(request):
    response = HttpResponse("OK")
    set_versioned_cookie(response, "xeolux_consent", "true", max_age=365 * 24 * 3600)
    return response

# Lire un cookie versionné
def ma_vue(request):
    consent = get_versioned_cookie(request, "xeolux_consent", default="false")
    ...
```

---

## Commande de diagnostic

```bash
python manage.py show_cache_versions
```

Sortie :

```
XEOLUX CacheKit versions:
  - Global      : 1.0.0
  - CSS         : 1.0.3
  - JS          : 1.2.0
  - Assets      : 1.0.8
  - Cookies     : 1.0.0
  - Query param : v
```

---

## Lancer les tests

```bash
pip install pytest pytest-django
pytest
```

---

## Exemple de configuration complète

```python
# settings.py

INSTALLED_APPS = [
    ...
    "xeolux_cachekit",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "xeolux_cachekit.context_processors.cache_versions",
            ],
        },
    }
]

XEOLUX_CACHEKIT = {
    "global": "1.0.0",
    "css": "1.0.3",
    "js": "1.2.0",
    "assets": "1.0.8",
    "cookies": "1.0.0",
    "query_param": "v",
}
```