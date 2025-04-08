"""Test RAC Provider"""

from datetime import timedelta
from time import mktime
from unittest.mock import MagicMock, patch

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import License
from authentik.lib.generators import generate_id


class TestAPI(APITestCase):
    """Test Provider API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=int(mktime((now() + timedelta(days=3000)).timetuple())),
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    def test_create(self):
        """Test creation of RAC Provider"""
        License.objects.create(key=generate_id())
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:racprovider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
            },
        )
        self.assertEqual(response.status_code, 201)
