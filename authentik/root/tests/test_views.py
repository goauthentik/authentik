"""root tests"""

from django.test import TransactionTestCase
from django.urls import reverse


class TestRoot(TransactionTestCase):
    """Test root application"""

    def test_monitoring(self):
        """Test monitoring with credentials"""
        self.assertEqual(self.client.get(reverse("metrics")).status_code, 204)

    def test_monitoring_live(self):
        """Test LiveView"""

        # The liveness probe should not make any database queries
        with self.assertNumQueries(0):
            self.assertEqual(self.client.get(reverse("health-live")).status_code, 200)

    def test_monitoring_ready(self):
        """Test ReadyView"""
        self.assertEqual(self.client.get(reverse("health-ready")).status_code, 200)
