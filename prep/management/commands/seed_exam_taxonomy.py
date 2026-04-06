from django.core.management.base import BaseCommand

from prep.services.taxonomy import ensure_default_taxonomy


class Command(BaseCommand):
    help = "Seed the default banking exam taxonomy."

    def handle(self, *args, **options):
        ensure_default_taxonomy()
        self.stdout.write(self.style.SUCCESS("Default banking exam taxonomy is available."))
