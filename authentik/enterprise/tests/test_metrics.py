"""Enterprise metrics tests"""

from django.test import TestCase
from prometheus_client import REGISTRY

from authentik.core.models import User
from authentik.core.tests.utils import create_test_user
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
