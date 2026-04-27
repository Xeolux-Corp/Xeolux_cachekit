"""
Tests pour les 3 nouvelles fonctionnalités :
- Strategy "hash" (hashers.py)
- CacheControlMiddleware
- Tag {% cache_version %}
"""

import hashlib
import tempfile
from pathlib import Path

from django.test import TestCase, RequestFactory, override_settings


class TestHashers(TestCase):
    """Vérifie le calcul de hash MD5 des fichiers statiques."""

    def setUp(self):
        from xeolux_cachekit.conf import clear_config_cache
        from xeolux_cachekit.hashers import clear_hash_cache
        clear_config_cache()
        clear_hash_cache()

    def tearDown(self):
        from xeolux_cachekit.conf import clear_config_cache
        from xeolux_cachekit.hashers import clear_hash_cache
        clear_config_cache()
        clear_hash_cache()

    def _make_static_dir(self, files: dict[str, bytes]) -> Path:
        """Crée un répertoire temporaire avec des fichiers statiques fictifs."""
        d = Path(tempfile.mkdtemp())
        for name, content in files.items():
            (d / name).write_bytes(content)
        return d

    def test_hash_returns_8_chars(self):
        from xeolux_cachekit.hashers import compute_hash_for_kind
        d = self._make_static_dir({"main.css": b"body { color: red; }"})
        with override_settings(STATICFILES_DIRS=[str(d)], STATIC_ROOT=None):
            result = compute_hash_for_kind("css")
        self.assertEqual(len(result), 8)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_hash_is_deterministic(self):
        from xeolux_cachekit.hashers import compute_hash_for_kind, clear_hash_cache
        d = self._make_static_dir({"app.js": b"console.log('hello');"})
        with override_settings(STATICFILES_DIRS=[str(d)], STATIC_ROOT=None):
            h1 = compute_hash_for_kind("js")
            clear_hash_cache()
            h2 = compute_hash_for_kind("js")
        self.assertEqual(h1, h2)

    def test_hash_changes_when_file_changes(self):
        from xeolux_cachekit.hashers import compute_hash_for_kind, clear_hash_cache
        d = self._make_static_dir({"main.css": b"body { color: red; }"})
        with override_settings(STATICFILES_DIRS=[str(d)], STATIC_ROOT=None):
            h1 = compute_hash_for_kind("css")

        clear_hash_cache()
        (d / "main.css").write_bytes(b"body { color: blue; }")
        with override_settings(STATICFILES_DIRS=[str(d)], STATIC_ROOT=None):
            h2 = compute_hash_for_kind("css")

        self.assertNotEqual(h1, h2)

    def test_no_files_returns_zeros(self):
        from xeolux_cachekit.hashers import compute_hash_for_kind
        d = self._make_static_dir({})  # répertoire vide
        with override_settings(STATICFILES_DIRS=[str(d)], STATIC_ROOT=None):
            result = compute_hash_for_kind("css")
        self.assertEqual(result, "00000000")

    def test_no_dirs_returns_zeros(self):
        from xeolux_cachekit.hashers import compute_hash_for_kind
        with override_settings(STATICFILES_DIRS=[], STATIC_ROOT=None):
            result = compute_hash_for_kind("js")
        self.assertEqual(result, "00000000")

    def test_cookies_raises_value_error(self):
        from xeolux_cachekit.hashers import compute_hash_for_kind
        with self.assertRaises(ValueError):
            compute_hash_for_kind("cookies")

    def test_global_raises_value_error(self):
        from xeolux_cachekit.hashers import compute_hash_for_kind
        with self.assertRaises(ValueError):
            compute_hash_for_kind("global")

    def test_hash_is_cached(self):
        from xeolux_cachekit.hashers import compute_hash_for_kind, _hash_cache
        d = self._make_static_dir({"style.css": b"a { color: green; }"})
        with override_settings(STATICFILES_DIRS=[str(d)], STATIC_ROOT=None):
            compute_hash_for_kind("css")
        self.assertIn("css", _hash_cache)


class TestStrategyHash(TestCase):
    """Vérifie que get_cache_version utilise le hasher quand strategy='hash'."""

    def setUp(self):
        from xeolux_cachekit.conf import clear_config_cache
        from xeolux_cachekit.hashers import clear_hash_cache
        clear_config_cache()
        clear_hash_cache()

    def tearDown(self):
        from xeolux_cachekit.conf import clear_config_cache
        from xeolux_cachekit.hashers import clear_hash_cache
        clear_config_cache()
        clear_hash_cache()

    def test_strategy_hash_uses_file_hash(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        (d / "main.css").write_bytes(b"body { margin: 0; }")

        with override_settings(
            XEOLUX_CACHEKIT={"strategy": "hash"},
            STATICFILES_DIRS=[str(d)],
            STATIC_ROOT=None,
        ):
            from xeolux_cachekit.utils import get_cache_version
            result = get_cache_version("css")

        self.assertEqual(len(result), 8)
        self.assertNotEqual(result, "1.0.0")

    def test_strategy_manual_uses_configured_version(self):
        with override_settings(XEOLUX_CACHEKIT={"strategy": "manual", "css": "7.7.7"}):
            from xeolux_cachekit.utils import get_cache_version
            self.assertEqual(get_cache_version("css"), "7.7.7")

    @override_settings(XEOLUX_CACHEKIT={"strategy": "hash", "cookies": "2.0.0"})
    def test_strategy_hash_cookies_falls_back_to_manual(self):
        from xeolux_cachekit.utils import get_cache_version
        # cookies n'est pas hashable → utilise la version configurée
        self.assertEqual(get_cache_version("cookies"), "2.0.0")


class TestCacheControlMiddleware(TestCase):
    """Vérifie que le middleware ajoute Cache-Control sur les statiques versionnées."""

    def setUp(self):
        from xeolux_cachekit.conf import clear_config_cache
        clear_config_cache()

    def tearDown(self):
        from xeolux_cachekit.conf import clear_config_cache
        clear_config_cache()

    def _make_middleware(self, response_factory=None):
        from django.http import HttpResponse
        from xeolux_cachekit.middleware import CacheControlMiddleware

        def get_response(request):
            return response_factory(request) if response_factory else HttpResponse("ok")

        return CacheControlMiddleware(get_response)

    @override_settings(STATIC_URL="/static/", XEOLUX_CACHEKIT={"query_param": "v"})
    def test_adds_cache_control_on_versioned_static(self):
        middleware = self._make_middleware()
        factory = RequestFactory()
        request = factory.get("/static/css/main.css", {"v": "1.0.0"})
        response = middleware(request)
        self.assertIn("Cache-Control", response)
        self.assertIn("immutable", response["Cache-Control"])
        self.assertIn("max-age=31536000", response["Cache-Control"])

    @override_settings(STATIC_URL="/static/", XEOLUX_CACHEKIT={"query_param": "v"})
    def test_no_cache_control_without_version_param(self):
        middleware = self._make_middleware()
        factory = RequestFactory()
        request = factory.get("/static/css/main.css")  # pas de ?v=
        response = middleware(request)
        self.assertNotIn("Cache-Control", response)

    @override_settings(STATIC_URL="/static/", XEOLUX_CACHEKIT={"query_param": "v"})
    def test_no_cache_control_on_non_static_url(self):
        middleware = self._make_middleware()
        factory = RequestFactory()
        request = factory.get("/api/data/", {"v": "1.0.0"})
        response = middleware(request)
        self.assertNotIn("Cache-Control", response)

    @override_settings(STATIC_URL="/static/", XEOLUX_CACHEKIT={"query_param": "version"})
    def test_respects_custom_query_param(self):
        middleware = self._make_middleware()
        factory = RequestFactory()
        request = factory.get("/static/js/app.js", {"version": "2.0.0"})
        response = middleware(request)
        self.assertIn("Cache-Control", response)


class TestCacheVersionTag(TestCase):
    """Vérifie le tag {% cache_version %}."""

    def setUp(self):
        from xeolux_cachekit.conf import clear_config_cache
        clear_config_cache()

    def tearDown(self):
        from xeolux_cachekit.conf import clear_config_cache
        clear_config_cache()

    @override_settings(XEOLUX_CACHEKIT={"css": "3.5.0"})
    def test_cache_version_tag_css(self):
        from django.template import engines
        engine = engines["django"]
        tpl = engine.from_string('{% load cachekit_tags %}{% cache_version "css" %}')
        self.assertEqual(tpl.render({}), "3.5.0")

    @override_settings(XEOLUX_CACHEKIT={"js": "8.0.1"})
    def test_cache_version_tag_js(self):
        from django.template import engines
        engine = engines["django"]
        tpl = engine.from_string('{% load cachekit_tags %}{% cache_version "js" %}')
        self.assertEqual(tpl.render({}), "8.0.1")

    @override_settings(XEOLUX_CACHEKIT={"assets": "0.9.9"})
    def test_cache_version_tag_assets(self):
        from django.template import engines
        engine = engines["django"]
        tpl = engine.from_string('{% load cachekit_tags %}{% cache_version "assets" %}')
        self.assertEqual(tpl.render({}), "0.9.9")
