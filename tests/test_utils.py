"""
Tests pour xeolux_cachekit.utils — Détection de type et génération d'URL.
"""

from django.test import TestCase, override_settings


class TestDetectKind(TestCase):
    """Vérifie la détection automatique du type selon l'extension."""

    def test_css_detection(self):
        from xeolux_cachekit.utils import detect_kind
        self.assertEqual(detect_kind("css/main.css"), "css")

    def test_js_detection(self):
        from xeolux_cachekit.utils import detect_kind
        self.assertEqual(detect_kind("js/app.js"), "js")

    def test_asset_extensions(self):
        from xeolux_cachekit.utils import detect_kind
        for ext in ["ico", "png", "jpg", "jpeg", "svg", "webp", "gif", "avif"]:
            with self.subTest(ext=ext):
                self.assertEqual(detect_kind(f"img/image.{ext}"), "assets")

    def test_unknown_extension_falls_back_to_global(self):
        from xeolux_cachekit.utils import detect_kind
        self.assertEqual(detect_kind("data/file.txt"), "global")
        self.assertEqual(detect_kind("archive.zip"), "global")

    def test_file_without_extension(self):
        from xeolux_cachekit.utils import detect_kind
        self.assertEqual(detect_kind("somefile"), "global")


class TestGetCacheVersion(TestCase):
    """Vérifie get_cache_version."""

    @override_settings(XEOLUX_CACHEKIT={"css": "9.9.9"})
    def test_get_css_version(self):
        from xeolux_cachekit.utils import get_cache_version
        self.assertEqual(get_cache_version("css"), "9.9.9")

    def test_invalid_kind_raises(self):
        from xeolux_cachekit.utils import get_cache_version
        with self.assertRaises(ValueError):
            get_cache_version("unknown_type")


class TestVersionedStaticUrl(TestCase):
    """Vérifie versioned_static_url."""

    @override_settings(
        XEOLUX_CACHEKIT={"css": "1.2.3", "query_param": "v"},
        STATIC_URL="/static/",
    )
    def test_versioned_css_url(self):
        from xeolux_cachekit.utils import versioned_static_url
        url = versioned_static_url("css/main.css")
        self.assertEqual(url, "/static/css/main.css?v=1.2.3")

    @override_settings(
        XEOLUX_CACHEKIT={"js": "4.5.6", "query_param": "ver"},
        STATIC_URL="/static/",
    )
    def test_versioned_js_url_custom_param(self):
        from xeolux_cachekit.utils import versioned_static_url
        url = versioned_static_url("js/app.js")
        self.assertEqual(url, "/static/js/app.js?ver=4.5.6")

    @override_settings(
        XEOLUX_CACHEKIT={"global": "0.0.1", "query_param": "v"},
        STATIC_URL="/static/",
    )
    def test_versioned_url_with_forced_kind(self):
        from xeolux_cachekit.utils import versioned_static_url
        url = versioned_static_url("data/file.txt", kind="global")
        self.assertEqual(url, "/static/data/file.txt?v=0.0.1")
