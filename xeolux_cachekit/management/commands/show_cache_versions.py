"""
Commande Django : show_cache_versions

Usage :
    python manage.py show_cache_versions
"""

from django.core.management.base import BaseCommand

from xeolux_cachekit.conf import get_setting


class Command(BaseCommand):
    help = "Affiche les versions de cache configurées dans XEOLUX CacheKit."

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("\nXEOLUX CacheKit versions:"))
        self.stdout.write(f"  - Global      : {get_setting('global')}")
        self.stdout.write(f"  - CSS         : {get_setting('css')}")
        self.stdout.write(f"  - JS          : {get_setting('js')}")
        self.stdout.write(f"  - Assets      : {get_setting('assets')}")
        self.stdout.write(f"  - Cookies     : {get_setting('cookies')}")
        self.stdout.write(f"  - Query param : {get_setting('query_param')}")
        self.stdout.write("")
