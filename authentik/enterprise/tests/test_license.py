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
                name="",
                users=100,
                external_users=100,
            )
        ),
    )
    def test_valid(self):
        """Check license verification"""
        lic = License.objects.create(key=generate_id())
        self.assertTrue(lic.status.is_valid())

    def test_invalid(self):
        """Test invalid license"""
        with self.assertRaises(ValidationError):
            License.objects.create(key=generate_id())
