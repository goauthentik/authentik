"""Enterprise metrics tests"""

from unittest import mock

from django.test import TestCase
from prometheus_client import REGISTRY

from authentik.core.models import User
from authentik.core.tests.utils import create_test_user
from authentik.enterprise import signals
from authentik.enterprise.models import LicenseUsageStatus
from authentik.enterprise.tests import enterprise_test
from authentik.root.monitoring import monitoring_set


class TestEnterpriseMetrics(TestCase):
    """Enterprise metrics tests"""

    @enterprise_test()
    def test_usage_empty(self):
        """Test usage (no users)"""
        User.objects.all().delete()
        create_test_user()
        monitoring_set.send_robust(self)
        self.assertEqual(
            REGISTRY.get_sample_value(
                "authentik_enterprise_license_usage", {"user_type": "internal"}
            ),
            1.0,
        )
        self.assertEqual(
            REGISTRY.get_sample_value(
                "authentik_enterprise_license_usage", {"user_type": "external"}
            ),
            0,
        )

    def test_unlicensed_metrics_are_reset(self):
        """Removing a license replaces previously exported values with zero."""
        summary = mock.Mock(status=LicenseUsageStatus.UNLICENSED)
        usage_children = {
            "internal": mock.Mock(),
            "external": mock.Mock(),
        }
        with (
            mock.patch.object(signals.LicenseKey, "cached_summary", return_value=summary),
            mock.patch.object(signals, "GAUGE_LICENSE_USAGE") as usage_gauge,
            mock.patch.object(signals, "GAUGE_LICENSE_EXPIRY") as expiry_gauge,
        ):
            usage_gauge.labels.side_effect = lambda user_type: usage_children[user_type]
            signals.monitoring_set_enterprise(sender=self)

        usage_children["internal"].set.assert_called_once_with(0)
        usage_children["external"].set.assert_called_once_with(0)
        expiry_gauge.set.assert_called_once_with(0)
