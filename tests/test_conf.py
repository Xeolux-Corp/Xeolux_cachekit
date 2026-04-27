"""
Tests pour xeolux_cachekit.conf — Lecture de la configuration.
"""

import django
from django.test import TestCase, override_settings


class TestDefaultConfig(TestCase):
    """Vérifie les valeurs par défaut quand aucune config n'est définie."""

    @override_settings()
    def test_default_values(self):
        from xeolux_cachekit.conf import get_setting

        # Supprime toute config existante
        from django.conf import settings
        for attr in ("XEOLUX_CACHEKIT", "XEOLUX_GLOBAL_VERSION", "XEOLUX_CSS_VERSION",
                     "XEOLUX_JS_VERSION", "XEOLUX_ASSETS_VERSION", "XEOLUX_COOKIE_VERSION"):
            if hasattr(settings, attr):
                delattr(settings, attr)

        self.assertEqual(get_setting("global"), "1.0.0")
        self.assertEqual(get_setting("css"), "1.0.0")
        self.assertEqual(get_setting("js"), "1.0.0")
        self.assertEqual(get_setting("assets"), "1.0.0")
        self.assertEqual(get_setting("cookies"), "1.0.0")
        self.assertEqual(get_setting("query_param"), "v")


class TestCentralizedConfig(TestCase):
    """Vérifie que XEOLUX_CACHEKIT est prioritaire."""

    @override_settings(XEOLUX_CACHEKIT={
        "global": "2.0.0",
        "css": "2.1.0",
        "js": "2.2.0",
        "assets": "2.3.0",
        "cookies": "2.4.0",
        "query_param": "version",
    })
    def test_centralized_config(self):
        from xeolux_cachekit.conf import get_setting

        self.assertEqual(get_setting("global"), "2.0.0")
        self.assertEqual(get_setting("css"), "2.1.0")
        self.assertEqual(get_setting("js"), "2.2.0")
        self.assertEqual(get_setting("assets"), "2.3.0")
        self.assertEqual(get_setting("cookies"), "2.4.0")
        self.assertEqual(get_setting("query_param"), "version")

    @override_settings(XEOLUX_CACHEKIT={"css": "3.0.0"})
    def test_partial_centralized_config_uses_defaults_for_missing(self):
        from xeolux_cachekit.conf import get_setting

        self.assertEqual(get_setting("css"), "3.0.0")
        self.assertEqual(get_setting("js"), "1.0.0")  # valeur par défaut


class TestIndividualVariables(TestCase):
    """Vérifie que les variables individuelles sont lues correctement."""

    @override_settings(
        XEOLUX_CSS_VERSION="1.5.0",
        XEOLUX_JS_VERSION="1.6.0",
        XEOLUX_GLOBAL_VERSION="1.7.0",
        XEOLUX_ASSETS_VERSION="1.8.0",
        XEOLUX_COOKIE_VERSION="1.9.0",
    )
    def test_individual_variables(self):
        from django.conf import settings

        # S'assurer qu'il n'y a pas de XEOLUX_CACHEKIT
        if hasattr(settings, "XEOLUX_CACHEKIT"):
            delattr(settings, "XEOLUX_CACHEKIT")

        from xeolux_cachekit.conf import get_setting

        self.assertEqual(get_setting("css"), "1.5.0")
        self.assertEqual(get_setting("js"), "1.6.0")
        self.assertEqual(get_setting("global"), "1.7.0")
        self.assertEqual(get_setting("assets"), "1.8.0")
        self.assertEqual(get_setting("cookies"), "1.9.0")
