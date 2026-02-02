from unittest.mock import patch

from django.test import TestCase

from authentik.core.models import User
from authentik.sources.kerberos.signals import kerberos_sync_password


class TestKerberosPasswordSignals(TestCase):
    def test_kerberos_sync_password_skips_when_password_unavailable(self):
        with patch(
            "authentik.sources.kerberos.signals.UserKerberosSourceConnection.objects.select_related"
        ) as select_related_mock:
            kerberos_sync_password(sender=self.__class__, user=User(), password=None)

        select_related_mock.assert_not_called()
