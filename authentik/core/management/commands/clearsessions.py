"""Change user type"""

from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Delete all sessions"""

    def handle(self, **options):
        engine = import_module(settings.SESSION_ENGINE)
        engine.SessionStore.clear_expired()
