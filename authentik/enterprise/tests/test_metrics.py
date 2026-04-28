"""Enterprise metrics tests"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from prometheus_client import REGISTRY

from authentik.core.models import User
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import License
from authentik.enterprise.tests.test_license import expiry_valid
from authentik.lib.generators import generate_id
from authentik.root.monitoring import monitoring_set


class TestEnterpriseMetrics(TestCase):
    """Enterprise metrics tests"""

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    def test_usage_empty(self):
        """Test usage (no users)"""
        License.objects.create(key=generate_id())
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
