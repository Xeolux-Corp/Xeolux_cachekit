"""
Tests pour xeolux_cachekit.cookies — Noms et helpers de cookies versionnés.
"""

from unittest.mock import MagicMock

from django.test import TestCase, RequestFactory, override_settings


class TestVersionedCookieName(TestCase):
    """Vérifie la génération du nom de cookie versionné."""

    @override_settings(XEOLUX_CACHEKIT={"cookies": "1.0.0"})
    def test_basic_name(self):
        from xeolux_cachekit.cookies import versioned_cookie_name
        self.assertEqual(versioned_cookie_name("xeolux_consent"), "xeolux_consent_v1_0_0")

    @override_settings(XEOLUX_CACHEKIT={"cookies": "2.3.4"})
    def test_version_dots_replaced(self):
        from xeolux_cachekit.cookies import versioned_cookie_name
        self.assertEqual(versioned_cookie_name("my_cookie"), "my_cookie_v2_3_4")


class TestSetVersionedCookie(TestCase):
    """Vérifie set_versioned_cookie."""

    @override_settings(XEOLUX_CACHEKIT={"cookies": "1.0.0"})
    def test_set_cookie_called_with_versioned_name(self):
        from xeolux_cachekit.cookies import set_versioned_cookie

        response = MagicMock()
        set_versioned_cookie(response, "xeolux_consent", "true", max_age=3600)

        response.set_cookie.assert_called_once_with(
            "xeolux_consent_v1_0_0", "true", max_age=3600
        )


class TestGetVersionedCookie(TestCase):
    """Vérifie get_versioned_cookie."""

    @override_settings(XEOLUX_CACHEKIT={"cookies": "1.0.0"})
    def test_get_existing_cookie(self):
        from xeolux_cachekit.cookies import get_versioned_cookie

        factory = RequestFactory()
        request = factory.get("/")
        request.COOKIES = {"xeolux_consent_v1_0_0": "true"}

        self.assertEqual(get_versioned_cookie(request, "xeolux_consent"), "true")

    @override_settings(XEOLUX_CACHEKIT={"cookies": "1.0.0"})
    def test_get_missing_cookie_returns_default(self):
        from xeolux_cachekit.cookies import get_versioned_cookie

        factory = RequestFactory()
        request = factory.get("/")
        request.COOKIES = {}

        self.assertIsNone(get_versioned_cookie(request, "xeolux_consent"))
        self.assertEqual(get_versioned_cookie(request, "xeolux_consent", default="fallback"), "fallback")
