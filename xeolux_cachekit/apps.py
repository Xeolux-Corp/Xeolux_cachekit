import re
import warnings

from django.apps import AppConfig

# Format semver simplifié : X.Y.Z (chiffres uniquement)
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_VERSION_KEYS = ("global", "css", "js", "assets", "cookies")


def _validate_config(config: dict) -> None:
    """Émet un warning si une version ne respecte pas le format X.Y.Z."""
    for key in _VERSION_KEYS:
        value = config.get(key, "")
        if value and not _SEMVER_RE.match(value):
            warnings.warn(
                f"[xeolux-cachekit] La version '{key}' = \"{value}\" "
                f"ne respecte pas le format semver X.Y.Z.",
                UserWarning,
                stacklevel=2,
            )


class XeoluxCacheKitConfig(AppConfig):
    name = "xeolux_cachekit"
    verbose_name = "Xeolux CacheKit"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from django.test.signals import setting_changed

        from .conf import _get_config, clear_config_cache

        # Invalide le cache quand @override_settings modifie une clé liée
        _WATCHED = {"XEOLUX_CACHEKIT", "XEOLUX_GLOBAL_VERSION", "XEOLUX_CSS_VERSION",
                    "XEOLUX_JS_VERSION", "XEOLUX_ASSETS_VERSION", "XEOLUX_COOKIE_VERSION"}

        def _on_setting_changed(*, setting, **kwargs):
            if setting in _WATCHED:
                clear_config_cache()

        setting_changed.connect(_on_setting_changed)

        # Valide la config courante au démarrage
        _validate_config(_get_config())

        # Enregistre les system checks Django
        from . import checks  # noqa: F401
