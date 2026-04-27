"""
Tests pour le context processor et les template tags CacheKit.
"""

from django.test import TestCase, RequestFactory, override_settings
from django.template import Context, Template, engines


class TestCacheVersionsContextProcessor(TestCase):
    """Vérifie que le context processor injecte les bonnes variables."""

    @override_settings(XEOLUX_CACHEKIT={
        "global": "1.1.1",
        "css": "1.2.0",
        "js": "1.3.0",
        "assets": "1.4.0",
        "cookies": "1.5.0",
    })
    def test_context_processor_injects_versions(self):
        from xeolux_cachekit.context_processors import cache_versions

        factory = RequestFactory()
        request = factory.get("/")
        context = cache_versions(request)

        self.assertEqual(context["CACHEKIT_GLOBAL_VERSION"], "1.1.1")
        self.assertEqual(context["CACHEKIT_CSS_VERSION"], "1.2.0")
        self.assertEqual(context["CACHEKIT_JS_VERSION"], "1.3.0")
        self.assertEqual(context["CACHEKIT_ASSETS_VERSION"], "1.4.0")
        self.assertEqual(context["CACHEKIT_COOKIE_VERSION"], "1.5.0")


class TestVersionedStaticTag(TestCase):
    """Vérifie les template tags versioned_static et versioned_static_as."""

    @override_settings(
        XEOLUX_CACHEKIT={"css": "3.0.0", "js": "3.1.0", "assets": "3.2.0", "query_param": "v"},
        STATIC_URL="/static/",
    )
    def test_versioned_static_css(self):
        engine = engines["django"]
        template = engine.from_string(
            '{% load cachekit_tags %}{% versioned_static "css/main.css" %}'
        )
        result = template.render({})
        self.assertEqual(result, "/static/css/main.css?v=3.0.0")

    @override_settings(
        XEOLUX_CACHEKIT={"js": "3.1.0", "query_param": "v"},
        STATIC_URL="/static/",
    )
    def test_versioned_static_js(self):
        engine = engines["django"]
        template = engine.from_string(
            '{% load cachekit_tags %}{% versioned_static "js/app.js" %}'
        )
        result = template.render({})
        self.assertEqual(result, "/static/js/app.js?v=3.1.0")

    @override_settings(
        XEOLUX_CACHEKIT={"assets": "3.2.0", "query_param": "v"},
        STATIC_URL="/static/",
    )
    def test_versioned_static_svg(self):
        engine = engines["django"]
        template = engine.from_string(
            '{% load cachekit_tags %}{% versioned_static "img/logo.svg" %}'
        )
        result = template.render({})
        self.assertEqual(result, "/static/img/logo.svg?v=3.2.0")

    @override_settings(
        XEOLUX_CACHEKIT={"global": "9.0.0", "query_param": "v"},
        STATIC_URL="/static/",
    )
    def test_versioned_static_as_global(self):
        engine = engines["django"]
        template = engine.from_string(
            '{% load cachekit_tags %}{% versioned_static_as "data/file.txt" "global" %}'
        )
        result = template.render({})
        self.assertEqual(result, "/static/data/file.txt?v=9.0.0")

    @override_settings(
        XEOLUX_CACHEKIT={"css": "5.0.0", "query_param": "version"},
        STATIC_URL="/static/",
    )
    def test_custom_query_param_in_tag(self):
        engine = engines["django"]
        template = engine.from_string(
            '{% load cachekit_tags %}{% versioned_static "css/main.css" %}'
        )
        result = template.render({})
        self.assertEqual(result, "/static/css/main.css?version=5.0.0")
