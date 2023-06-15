"""Enterprise license tests"""
from datetime import timedelta
from time import mktime
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from authentik.enterprise.models import License, LicenseKey
from authentik.lib.generators import generate_id

_exp = int(mktime((now() + timedelta(days=3000)).timetuple()))


class TestEnterpriseLicense(TestCase):
    """Enterprise license tests"""

    @patch(
        "authentik.enterprise.models.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=_exp,
                name=generate_id(),
                users=100,
                external_users=100,
            )
        ),
    )
    def test_valid(self):
        """Check license verification"""
        lic = License.objects.create(key=generate_id())
        self.assertTrue(lic.status.is_valid())
        self.assertEqual(lic.users, 100)

    def test_invalid(self):
        """Test invalid license"""
        with self.assertRaises(ValidationError):
            License.objects.create(key=generate_id())

    @patch(
        "authentik.enterprise.models.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=_exp,
                name=generate_id(),
                users=100,
                external_users=100,
            )
        ),
    )
    def test_valid_multiple(self):
        """Check license verification"""
        lic = License.objects.create(key=generate_id())
        self.assertTrue(lic.status.is_valid())
        lic2 = License.objects.create(key=generate_id())
        self.assertTrue(lic2.status.is_valid())
        total = LicenseKey.get_total()
        self.assertEqual(total.users, 200)
        self.assertEqual(total.external_users, 200)
        self.assertEqual(total.exp, _exp)
        self.assertTrue(total.is_valid())
