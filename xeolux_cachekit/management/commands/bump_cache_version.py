"""
Commande Django : bump_cache_version

Incrémente la version d'un type de cache dans XEOLUX_CACHEKIT ou dans les
variables individuelles hardcodées dans settings.py.

Si la version provient d'une variable d'environnement (os.environ, env(), etc.),
la commande le détecte et affiche un message indiquant de la modifier manuellement
dans le fichier .env.

Usage :
    python manage.py bump_cache_version css
    python manage.py bump_cache_version js --minor
    python manage.py bump_cache_version assets --major
    python manage.py bump_cache_version all
    python manage.py bump_cache_version css --dry-run
"""

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from xeolux_cachekit.conf import get_setting

_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")

_INDIVIDUAL_KEYS = {
    "global": "XEOLUX_GLOBAL_VERSION",
    "css": "XEOLUX_CSS_VERSION",
    "js": "XEOLUX_JS_VERSION",
    "assets": "XEOLUX_ASSETS_VERSION",
    "cookies": "XEOLUX_COOKIE_VERSION",
}

_ALL_KINDS = list(_INDIVIDUAL_KEYS.keys())

# Patterns indiquant que la valeur provient de l'environnement
_ENV_PATTERNS = re.compile(
    r'os\.environ|os\.getenv|env\(|environ\.get|config\(',
    re.IGNORECASE,
)


def _bump(version: str, part: str) -> str:
    """Incrémente une version semver X.Y.Z selon le composant demandé."""
    match = _SEMVER_RE.fullmatch(version.strip())
    if not match:
        raise CommandError(
            f"La version '{version}' ne respecte pas le format X.Y.Z. "
            f"Impossible d'incrémenter automatiquement."
        )
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def _find_settings_file() -> Path:
    """Localise le fichier settings.py du projet Django."""
    from django.conf import settings as djsettings
    import os

    module = getattr(djsettings, "SETTINGS_MODULE", None) or os.environ.get("DJANGO_SETTINGS_MODULE", "")

    if module:
        module_path = Path(module.replace(".", "/") + ".py")
        if module_path.exists():
            return module_path
        cwd_path = Path.cwd() / module_path
        if cwd_path.exists():
            return cwd_path

    raise CommandError(
        "Impossible de localiser le fichier settings.py. "
        "Assurez-vous que DJANGO_SETTINGS_MODULE est défini et que le fichier est accessible."
    )


def _is_from_env(settings_path: Path, setting_name: str) -> bool:
    """
    Retourne True si la clé settings_name est définie via une variable d'environnement
    (os.environ, os.getenv, env(), etc.) dans settings.py.
    """
    content = settings_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        # Cherche la ligne contenant le nom de la variable
        if setting_name in line and _ENV_PATTERNS.search(line):
            return True
    # Vérifie aussi si la clé dict (ex: "css") est dans XEOLUX_CACHEKIT avec env
    kind_key = {v: k for k, v in _INDIVIDUAL_KEYS.items()}.get(setting_name, "")
    if kind_key:
        in_block = False
        for line in content.splitlines():
            if "XEOLUX_CACHEKIT" in line:
                in_block = True
            if in_block and f'"{kind_key}"' in line or (in_block and f"'{kind_key}'" in line):
                if _ENV_PATTERNS.search(line):
                    return True
            if in_block and "}" in line:
                in_block = False
    return False


def _replace_version_in_file(settings_path: Path, setting_name: str, old_version: str, new_version: str) -> bool:
    """
    Remplace la version hardcodée dans settings.py.
    Supporte XEOLUX_CSS_VERSION = "..." et les clés dans XEOLUX_CACHEKIT = {...}.
    Retourne True si un remplacement a été effectué.
    """
    content = settings_path.read_text(encoding="utf-8")

    # Pattern pour variable individuelle : XEOLUX_CSS_VERSION = "1.0.0"
    pattern_individual = re.compile(
        rf'({re.escape(setting_name)}\s*=\s*["\']){re.escape(old_version)}(["\'])'
    )

    kind_key = {v: k for k, v in _INDIVIDUAL_KEYS.items()}.get(setting_name, "")
    pattern_dict = re.compile(
        rf'(["\'](?:cookies|{re.escape(kind_key)})["\']:\s*["\']){re.escape(old_version)}(["\'])'
    ) if kind_key else None

    new_content = pattern_individual.sub(rf'\g<1>{new_version}\g<2>', content)

    if new_content == content and pattern_dict:
        new_content = pattern_dict.sub(rf'\g<1>{new_version}\g<2>', content)

    if new_content == content:
        return False

    settings_path.write_text(new_content, encoding="utf-8")
    return True


class Command(BaseCommand):
    help = "Incrémente la version de cache d'un type (css, js, assets, cookies, global, all)."

    def add_arguments(self, parser):
        parser.add_argument(
            "kind",
            choices=_ALL_KINDS + ["all"],
            help="Type de cache à incrémenter, ou 'all' pour tout incrémenter.",
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--minor",
            action="store_true",
            default=False,
            help="Incrémenter le composant mineur (X.Y.Z → X.Y+1.0).",
        )
        group.add_argument(
            "--major",
            action="store_true",
            default=False,
            help="Incrémenter le composant majeur (X.Y.Z → X+1.0.0).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Afficher les changements sans modifier le fichier settings.py.",
        )

    def handle(self, *args, **options) -> None:
        kind = options["kind"]
        dry_run = options["dry_run"]
        part = "major" if options["major"] else ("minor" if options["minor"] else "patch")

        kinds_to_bump = _ALL_KINDS if kind == "all" else [kind]

        try:
            settings_path = _find_settings_file()
        except CommandError as e:
            raise e

        self.stdout.write(f"\nFichier settings : {settings_path}")
        self.stdout.write(f"Composant        : {part}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode dry-run — aucune modification ne sera écrite.\n"))
        else:
            self.stdout.write("")

        any_changed = False
        for k in kinds_to_bump:
            old_version = get_setting(k)
            new_version = _bump(old_version, part)
            setting_name = _INDIVIDUAL_KEYS[k]

            # Détecter si la version vient d'une variable d'environnement
            from_env = _is_from_env(settings_path, setting_name)

            if from_env:
                self.stdout.write(
                    f"  {k:10s}  {old_version}  "
                    + self.style.WARNING(
                        f"→ défini via variable d'environnement. "
                        f"Modifiez manuellement XEOLUX_{k.upper()}_VERSION (ou la clé \"{k}\") "
                        f"dans votre fichier .env."
                    )
                )
                continue

            if dry_run:
                self.stdout.write(
                    f"  {k:10s}  {old_version}  →  {self.style.SUCCESS(new_version)}  "
                    f"(settings.py — hardcodé)"
                )
            else:
                changed = _replace_version_in_file(settings_path, setting_name, old_version, new_version)
                if changed:
                    self.stdout.write(
                        f"  {k:10s}  {old_version}  →  {self.style.SUCCESS(new_version)}  ✓"
                    )
                    any_changed = True
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  {k:10s}  {old_version}  — aucun pattern trouvé dans settings.py"
                        )
                    )

        if not dry_run and any_changed:
            self.stdout.write(
                self.style.SUCCESS("\nVersions mises à jour. Relancez le serveur pour appliquer les changements.")
            )
        self.stdout.write("")



def _bump(version: str, part: str) -> str:
    """Incrémente une version semver X.Y.Z selon le composant demandé."""
    match = _SEMVER_RE.fullmatch(version.strip())
    if not match:
        raise CommandError(
            f"La version '{version}' ne respecte pas le format X.Y.Z. "
            f"Impossible d'incrémenter automatiquement."
        )
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def _find_settings_file() -> Path:
    """Localise le fichier settings.py du projet Django."""
    from django.conf import settings as djsettings

    module = djsettings.SETTINGS_MODULE if hasattr(djsettings, "SETTINGS_MODULE") else None
    if not module:
        import os
        module = os.environ.get("DJANGO_SETTINGS_MODULE", "")

    if module:
        module_path = Path(module.replace(".", "/") + ".py")
        if module_path.exists():
            return module_path
        # Recherche relative au cwd
        cwd_path = Path.cwd() / module_path
        if cwd_path.exists():
            return cwd_path

    raise CommandError(
        "Impossible de localiser le fichier settings.py. "
        "Assurez-vous que DJANGO_SETTINGS_MODULE est défini et que le fichier est accessible."
    )


def _replace_version_in_file(settings_path: Path, setting_name: str, old_version: str, new_version: str) -> bool:
    """
    Remplace la version dans le fichier settings.py.
    Supporte XEOLUX_CSS_VERSION = "..." et les clés dans XEOLUX_CACHEKIT = {...}.
    Retourne True si un remplacement a été effectué.
    """
    content = settings_path.read_text(encoding="utf-8")

    # Pattern pour variable individuelle : XEOLUX_CSS_VERSION = "1.0.0"
    pattern_individual = re.compile(
        rf'({re.escape(setting_name)}\s*=\s*["\']){re.escape(old_version)}(["\'])'
    )

    # Pattern pour clé dans XEOLUX_CACHEKIT : "css": "1.0.0"
    # On extrait le kind depuis le nom de la variable individuelle
    kind_match = re.match(r"XEOLUX_(?:GLOBAL|CSS|JS|ASSETS|COOKIE)_VERSION", setting_name)
    kind_key = {
        "XEOLUX_GLOBAL_VERSION": "global",
        "XEOLUX_CSS_VERSION": "css",
        "XEOLUX_JS_VERSION": "js",
        "XEOLUX_ASSETS_VERSION": "assets",
        "XEOLUX_COOKIE_VERSION": "cookies",
    }.get(setting_name, "")

    pattern_dict = re.compile(
        rf'(["\'](?:cookies|{re.escape(kind_key)})["\']:\s*["\']){re.escape(old_version)}(["\'])'
    ) if kind_key else None

    new_content = pattern_individual.sub(rf'\g<1>{new_version}\g<2>', content)

    if new_content == content and pattern_dict:
        new_content = pattern_dict.sub(rf'\g<1>{new_version}\g<2>', content)

    if new_content == content:
        return False

    settings_path.write_text(new_content, encoding="utf-8")
    return True


class Command(BaseCommand):
    help = "Incrémente la version de cache d'un type (css, js, assets, cookies, global, all)."

    def add_arguments(self, parser):
        parser.add_argument(
            "kind",
            choices=_ALL_KINDS + ["all"],
            help="Type de cache à incrémenter, ou 'all' pour tout incrémenter.",
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--minor",
            action="store_true",
            default=False,
            help="Incrémenter le composant mineur (X.Y.Z → X.Y+1.0).",
        )
        group.add_argument(
            "--major",
            action="store_true",
            default=False,
            help="Incrémenter le composant majeur (X.Y.Z → X+1.0.0).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Afficher les changements sans modifier le fichier settings.py.",
        )

    def handle(self, *args, **options) -> None:
        kind = options["kind"]
        dry_run = options["dry_run"]
        part = "major" if options["major"] else ("minor" if options["minor"] else "patch")

        kinds_to_bump = _ALL_KINDS if kind == "all" else [kind]

        try:
            settings_path = _find_settings_file()
        except CommandError as e:
            raise e

        self.stdout.write(f"\nFichier settings : {settings_path}")
        self.stdout.write(f"Composant        : {part}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode dry-run — aucune modification ne sera écrite.\n"))

        any_changed = False
        for k in kinds_to_bump:
            old_version = get_setting(k)
            new_version = _bump(old_version, part)
            setting_name = _INDIVIDUAL_KEYS[k]

            if dry_run:
                self.stdout.write(
                    f"  {k:10s}  {old_version}  →  {self.style.SUCCESS(new_version)}"
                )
            else:
                changed = _replace_version_in_file(settings_path, setting_name, old_version, new_version)
                if changed:
                    self.stdout.write(
                        f"  {k:10s}  {old_version}  →  {self.style.SUCCESS(new_version)}"
                    )
                    any_changed = True
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  {k:10s}  {old_version}  — aucun pattern trouvé dans settings.py"
                        )
                    )

        if not dry_run and any_changed:
            self.stdout.write(
                self.style.SUCCESS("\nVersions mises à jour. Relancez le serveur pour appliquer les changements.")
            )
        self.stdout.write("")
