"""Test config API"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase


class TestConfig(APITestCase):
    """Test config API"""

    def test_config(self):
        """Test YAML generation"""
        response = self.client.get(
            reverse("authentik_api:config"),
        )
        self.assertTrue(loads(response.content.decode()))
