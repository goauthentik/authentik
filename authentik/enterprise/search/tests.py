from json import loads
from unittest.mock import PropertyMock, patch
from urllib.parse import urlencode

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user


@patch(
    "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
    PropertyMock(return_value=True),
)
class QLTest(APITestCase):

    def setUp(self):
        self.user = create_test_admin_user()
        # ensure we have more than 1 user
        create_test_admin_user()

    def test_search(self):
        """Test simple search query"""
        self.client.force_login(self.user)
        query = f'username = "{self.user.username}"'
        res = self.client.get(
            reverse(
                "authentik_api:user-list",
            )
            + f"?{urlencode({"search": query})}"
        )
        self.assertEqual(res.status_code, 200)
        content = loads(res.content)
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(content["results"][0]["username"], self.user.username)

    def test_no_search(self):
        """Ensure works with no search query"""
        self.client.force_login(self.user)
        res = self.client.get(
            reverse(
                "authentik_api:user-list",
            )
        )
        self.assertEqual(res.status_code, 200)
        content = loads(res.content)
        self.assertNotEqual(content["pagination"]["count"], 1)

    def test_search_no_ql(self):
        """Test simple search query (no QL)"""
        self.client.force_login(self.user)
        res = self.client.get(
            reverse(
                "authentik_api:user-list",
            )
            + f"?{urlencode({"search": self.user.username})}"
        )
        self.assertEqual(res.status_code, 200)
        content = loads(res.content)
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(content["results"][0]["username"], self.user.username)

    def test_search_json(self):
        """Test search query with a JSON attribute"""
        self.user.attributes = {"foo": {"bar": "baz"}}
        self.user.save()
        self.client.force_login(self.user)
        query = 'attributes.foo.bar = "baz"'
        res = self.client.get(
            reverse(
                "authentik_api:user-list",
            )
            + f"?{urlencode({"search": query})}"
        )
        self.assertEqual(res.status_code, 200)
        content = loads(res.content)
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(content["results"][0]["username"], self.user.username)
