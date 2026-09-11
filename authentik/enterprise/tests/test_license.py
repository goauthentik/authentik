"""Enterprise license tests"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from authentik.core.models import User
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import (
    THRESHOLD_READ_ONLY_WEEKS,
    THRESHOLD_WARNING_ADMIN_WEEKS,
    THRESHOLD_WARNING_USER_WEEKS,
    License,
    LicenseUsage,
    LicenseUsageStatus,
)
from authentik.enterprise.tests import (
    enterprise_test,
    expiry_expired,
    expiry_expired_read_only,
    expiry_soon,
    expiry_valid,
)
from authentik.lib.generators import generate_id


class TestEnterpriseLicense(TestCase):
    """Enterprise license tests"""

    @enterprise_test()
    def test_valid(self):
        """Check license verification"""
        lic = License.objects.create(key=generate_id())
        self.assertTrue(lic.status.status().is_valid)
        self.assertEqual(lic.internal_users, 100)

    def test_invalid(self):
        """Test invalid license"""
        with self.assertRaises(ValidationError):
            License.objects.create(key=generate_id())

    @enterprise_test(create_key=False)
    def test_valid_multiple(self):
        """Check license verification"""
        lic = License.objects.create(key=generate_id(), expiry=expiry_valid)
        self.assertTrue(lic.status.status().is_valid)
        lic2 = License.objects.create(key=generate_id(), expiry=expiry_valid)
        self.assertTrue(lic2.status.status().is_valid)
        total = LicenseKey.get_total()
        self.assertEqual(total.internal_users, 200)
        self.assertEqual(total.external_users, 200)
        self.assertEqual(total.exp, expiry_valid)
        self.assertTrue(total.status().is_valid)

    @enterprise_test()
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
        usage = LicenseUsage.objects.create(
            internal_user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=THRESHOLD_READ_ONLY_WEEKS + 1)
        usage.save(update_fields=["record_date"])
        self.assertEqual(LicenseKey.get_total().summary().status, LicenseUsageStatus.READ_ONLY)

    @enterprise_test()
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
        usage = LicenseUsage.objects.create(
            internal_user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=THRESHOLD_WARNING_USER_WEEKS + 1)
        usage.save(update_fields=["record_date"])
        self.assertEqual(
            LicenseKey.get_total().summary().status, LicenseUsageStatus.LIMIT_EXCEEDED_USER
        )

    @enterprise_test()
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
        usage = LicenseUsage.objects.create(
            internal_user_count=100,
            external_user_count=100,
            status=LicenseUsageStatus.VALID,
        )
        usage.record_date = now() - timedelta(weeks=THRESHOLD_WARNING_ADMIN_WEEKS + 1)
        usage.save(update_fields=["record_date"])
        self.assertEqual(
            LicenseKey.get_total().summary().status, LicenseUsageStatus.LIMIT_EXCEEDED_ADMIN
        )

    @enterprise_test(expiry=expiry_expired_read_only)
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_expiry_read_only(self):
        """Check license verification"""
        self.assertEqual(LicenseKey.get_total().summary().status, LicenseUsageStatus.READ_ONLY)

    @enterprise_test(expiry=expiry_expired)
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_expiry_expired(self):
        """Check license verification"""
        User.objects.all().delete()
        License.objects.all().delete()
        License.objects.create(key=generate_id(), expiry=expiry_expired)
        self.assertEqual(LicenseKey.get_total().summary().status, LicenseUsageStatus.EXPIRED)

    @enterprise_test(expiry=expiry_soon)
    @patch(
        "authentik.enterprise.license.LicenseKey.record_usage",
        MagicMock(),
    )
    def test_expiry_soon(self):
        """Check license verification"""
        self.assertEqual(LicenseKey.get_total().summary().status, LicenseUsageStatus.EXPIRY_SOON)
