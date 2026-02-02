from unittest.mock import patch

from django.test import TestCase

from authentik.core.models import User
from authentik.sources.ldap.signals import ldap_sync_password


class TestLDAPPasswordSignals(TestCase):
    def test_ldap_sync_password_skips_when_password_unavailable(self):
        with patch("authentik.sources.ldap.signals.LDAPSource.objects.filter") as filter_mock:
            ldap_sync_password(sender=self.__class__, user=User(), password=None)

        filter_mock.assert_not_called()
