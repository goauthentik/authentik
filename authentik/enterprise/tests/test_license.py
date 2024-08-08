"""Enterprise license tests"""

from datetime import timedelta
from time import mktime
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import License, LicenseUsage, LicenseUsageStatus
from authentik.lib.generators import generate_id

_exp = int(mktime((now() + timedelta(days=3000)).timetuple()))


class TestEnterpriseLicense(TestCase):
    """Enterprise license tests"""

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=_exp,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    def test_valid(self):
        """Check license verification"""
        lic = License.objects.create(key=generate_id())
        self.assertTrue(lic.status.is_valid())
        self.assertEqual(lic.internal_users, 100)

    def test_invalid(self):
        """Test invalid license"""
        with self.assertRaises(ValidationError):
            License.objects.create(key=generate_id())

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=_exp,
                name=generate_id(),
                internal_users=100,
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
        self.assertEqual(total.internal_users, 200)
        self.assertEqual(total.external_users, 200)
        self.assertEqual(total.exp, _exp)
        self.assertTrue(total.is_valid())

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=_exp,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_internal_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_external_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_limit_exceeded_read_only(self):
        """Check license verification"""
        License.objects.create(key=generate_id())
        usage = LicenseUsage.objects.create(
            user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=10)
        usage.save(update_fields=["record_date"])
        self.assertEqual(LicenseKey.get_total().summary().status, LicenseUsageStatus.READ_ONLY)

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=_exp,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_internal_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_external_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_limit_exceeded_user_warning(self):
        """Check license verification"""
        License.objects.create(key=generate_id())
        usage = LicenseUsage.objects.create(
            user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=5)
        usage.save(update_fields=["record_date"])
        self.assertEqual(
            LicenseKey.get_total().summary().status, LicenseUsageStatus.LIMIT_EXCEEDED_USER
        )

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=_exp,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_internal_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.get_external_user_count",
        MagicMock(return_value=1000),
    )
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_limit_exceeded_admin_warning(self):
        """Check license verification"""
        License.objects.create(key=generate_id())
        usage = LicenseUsage.objects.create(
            user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=3)
        usage.save(update_fields=["record_date"])
        self.assertEqual(
            LicenseKey.get_total().summary().status, LicenseUsageStatus.LIMIT_EXCEEDED_ADMIN
        )
