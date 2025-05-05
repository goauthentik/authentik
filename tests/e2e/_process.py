"""authentik e2e testing utilities"""

from datetime import timedelta
from time import mktime
from unittest.mock import MagicMock, patch

from daphne.testing import DaphneProcess
from django import setup as django_setup
from django.conf import settings
from django.utils.timezone import now

from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id


class TestDatabaseProcess(DaphneProcess):
    """Channels does not correctly switch to the test database by default.
    https://github.com/django/channels/issues/2048"""

    def run(self):
        if not settings.configured:  # Fix For raise AppRegistryNotReady("Apps aren't loaded yet.")
            django_setup()  # Ensure Django is fully set up before using settings
        if not settings.DATABASES[list(settings.DATABASES.keys())[0]]["NAME"].startswith("test_"):
            for _, db_settings in settings.DATABASES.items():
                db_settings["NAME"] = f"test_{db_settings['NAME']}"
        settings.TEST = True
        from authentik.enterprise.license import LicenseKey

        with (
            patch(
                "authentik.enterprise.license.LicenseKey.validate",
                MagicMock(
                    return_value=LicenseKey(
                        aud="",
                        exp=int(mktime((now() + timedelta(days=3000)).timetuple())),
                        name=generate_id(),
                        internal_users=100,
                        external_users=100,
                    )
                ),
            ),
            CONFIG.patch("email.port", 1025),
        ):
            return super().run()
