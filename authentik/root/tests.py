"""root tests"""

from pathlib import Path
from secrets import token_urlsafe
from tempfile import gettempdir
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test import TransactionTestCase as BaseTransactionTestCase
from django.urls import reverse
from rest_framework.test import APITransactionTestCase as BaseAPITransactionTestCase


def patched__get_ct_cached(app_label, codename):
    """Caches `ContentType` instances like its `QuerySet` does."""
    return ContentType.objects.get(app_label=app_label, permission__codename=codename)


@patch("guardian.shortcuts._get_ct_cached", patched__get_ct_cached)
class TransactionTestCase(BaseTransactionTestCase): ...


@patch("guardian.shortcuts._get_ct_cached", patched__get_ct_cached)
class APITransactionTestCase(BaseAPITransactionTestCase): ...


class TestRoot(TestCase):
    """Test root application"""

    def setUp(self):
        _tmp = Path(gettempdir())
        self.token = token_urlsafe(32)
        with open(_tmp / "authentik-core-metrics.key", "w") as _f:
            _f.write(self.token)

    def tearDown(self):
        _tmp = Path(gettempdir())
        (_tmp / "authentik-core-metrics.key").unlink()

    def test_monitoring_error(self):
        """Test monitoring without any credentials"""
        response = self.client.get(reverse("metrics"))
        self.assertEqual(response.status_code, 401)

    def test_monitoring_ok(self):
        """Test monitoring with credentials"""
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        response = self.client.get(reverse("metrics"), **auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_monitoring_live(self):
        """Test LiveView"""
        self.assertEqual(self.client.get(reverse("health-live")).status_code, 200)

    def test_monitoring_ready(self):
        """Test ReadyView"""
        self.assertEqual(self.client.get(reverse("health-ready")).status_code, 200)
