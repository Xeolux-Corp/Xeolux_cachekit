"""
Tests pour les nouvelles fonctionnalités :
- cache de _get_config() et clear_config_cache()
- validation semver dans AppConfig.ready()
- commande bump_cache_version
"""

import warnings
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings


class TestConfigCache(TestCase):
    """Vérifie que le cache est actif et invalidé correctement."""

    def setUp(self):
        from xeolux_cachekit.conf import clear_config_cache
        clear_config_cache()

    def tearDown(self):
        from xeolux_cachekit.conf import clear_config_cache
        clear_config_cache()

    @override_settings(XEOLUX_CACHEKIT={"css": "2.0.0"})
    def test_cache_is_populated_on_first_call(self):
        from xeolux_cachekit.conf import _get_config, _config_cache
        # Avant le premier appel, le cache est vide (cleared in setUp)
        import xeolux_cachekit.conf as conf_module
        self.assertIsNone(conf_module._config_cache)
        _get_config()
        self.assertIsNotNone(conf_module._config_cache)

    @override_settings(XEOLUX_CACHEKIT={"css": "3.0.0"})
    def test_cache_returns_same_dict_on_second_call(self):
        from xeolux_cachekit.conf import _get_config
        first = _get_config()
        second = _get_config()
        self.assertIs(first, second)

    @override_settings(XEOLUX_CACHEKIT={"css": "4.0.0"})
    def test_clear_cache_forces_re_read(self):
        from xeolux_cachekit.conf import _get_config, clear_config_cache, get_setting

        # Premier appel — met en cache
        v1 = get_setting("css")
        self.assertEqual(v1, "4.0.0")

        # On invalide le cache et on simule un changement de setting
        clear_config_cache()
        with override_settings(XEOLUX_CACHEKIT={"css": "5.0.0"}):
            v2 = get_setting("css")
            self.assertEqual(v2, "5.0.0")


class TestSemverValidation(TestCase):
    """Vérifie que la validation semver émet un warning pour les versions invalides."""

    def setUp(self):
        from xeolux_cachekit.conf import clear_config_cache
        clear_config_cache()

    def tearDown(self):
        from xeolux_cachekit.conf import clear_config_cache
        clear_config_cache()

    def test_valid_semver_no_warning(self):
        from xeolux_cachekit.apps import _validate_config
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _validate_config({"css": "1.0.0", "js": "2.3.4", "global": "0.0.1",
                              "assets": "10.20.30", "cookies": "1.0.0"})
            self.assertEqual(len(w), 0)

    def test_invalid_semver_emits_warning(self):
        from xeolux_cachekit.apps import _validate_config
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _validate_config({"css": "abc", "js": "1.0.0", "global": "1.0.0",
                              "assets": "1.0.0", "cookies": "1.0.0"})
            self.assertEqual(len(w), 1)
            self.assertIn("css", str(w[0].message))

    def test_multiple_invalid_emit_multiple_warnings(self):
        from xeolux_cachekit.apps import _validate_config
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _validate_config({"css": "bad", "js": "also-bad", "global": "1.0.0",
                              "assets": "1.0.0", "cookies": "1.0.0"})
            self.assertEqual(len(w), 2)


class TestBumpVersion(TestCase):
    """Vérifie la logique d'incrémentation de version."""

    def test_bump_patch(self):
        from xeolux_cachekit.management.commands.bump_cache_version import _bump
        self.assertEqual(_bump("1.0.0", "patch"), "1.0.1")
        self.assertEqual(_bump("1.2.9", "patch"), "1.2.10")

    def test_bump_minor(self):
        from xeolux_cachekit.management.commands.bump_cache_version import _bump
        self.assertEqual(_bump("1.2.3", "minor"), "1.3.0")

    def test_bump_major(self):
        from xeolux_cachekit.management.commands.bump_cache_version import _bump
        self.assertEqual(_bump("1.2.3", "major"), "2.0.0")

    def test_invalid_version_raises(self):
        from django.core.management.base import CommandError
        from xeolux_cachekit.management.commands.bump_cache_version import _bump
        with self.assertRaises(CommandError):
            _bump("not-a-version", "patch")

    def test_replace_individual_setting(self):
        from pathlib import Path
        import tempfile
        from xeolux_cachekit.management.commands.bump_cache_version import _replace_version_in_file

        content = 'XEOLUX_CSS_VERSION = "1.0.0"\nXEOLUX_JS_VERSION = "2.0.0"\n'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = Path(f.name)

        changed = _replace_version_in_file(tmp, "XEOLUX_CSS_VERSION", "1.0.0", "1.0.1")
        self.assertTrue(changed)
        result = tmp.read_text(encoding="utf-8")
        self.assertIn('XEOLUX_CSS_VERSION = "1.0.1"', result)
        self.assertIn('XEOLUX_JS_VERSION = "2.0.0"', result)  # inchangé
        tmp.unlink()

    def test_replace_returns_false_when_not_found(self):
        from pathlib import Path
        import tempfile
        from xeolux_cachekit.management.commands.bump_cache_version import _replace_version_in_file

        content = 'XEOLUX_CSS_VERSION = "1.0.0"\n'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = Path(f.name)

        changed = _replace_version_in_file(tmp, "XEOLUX_CSS_VERSION", "9.9.9", "9.9.10")
        self.assertFalse(changed)
        tmp.unlink()


class TestIsFromEnv(TestCase):
    """Vérifie la détection des versions définies via variable d'environnement."""

    def _make_settings_file(self, content: str):
        import tempfile
        from pathlib import Path
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
        f.write(content)
        f.close()
        return Path(f.name)

    def test_hardcoded_value_is_not_from_env(self):
        from xeolux_cachekit.management.commands.bump_cache_version import _is_from_env
        tmp = self._make_settings_file('XEOLUX_CSS_VERSION = "1.0.0"\n')
        self.assertFalse(_is_from_env(tmp, "XEOLUX_CSS_VERSION"))
        tmp.unlink()

    def test_os_environ_detected(self):
        from xeolux_cachekit.management.commands.bump_cache_version import _is_from_env
        tmp = self._make_settings_file(
            'XEOLUX_CSS_VERSION = os.environ.get("XEOLUX_CSS_VERSION", "1.0.0")\n'
        )
        self.assertTrue(_is_from_env(tmp, "XEOLUX_CSS_VERSION"))
        tmp.unlink()

    def test_os_getenv_detected(self):
        from xeolux_cachekit.management.commands.bump_cache_version import _is_from_env
        tmp = self._make_settings_file(
            'XEOLUX_JS_VERSION = os.getenv("XEOLUX_JS_VERSION", "1.0.0")\n'
        )
        self.assertTrue(_is_from_env(tmp, "XEOLUX_JS_VERSION"))
        tmp.unlink()

    def test_django_environ_env_detected(self):
        from xeolux_cachekit.management.commands.bump_cache_version import _is_from_env
        tmp = self._make_settings_file(
            'XEOLUX_ASSETS_VERSION = env("XEOLUX_ASSETS_VERSION", default="1.0.0")\n'
        )
        self.assertTrue(_is_from_env(tmp, "XEOLUX_ASSETS_VERSION"))
        tmp.unlink()
