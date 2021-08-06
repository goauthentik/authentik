"""Test Applications API"""
from django.urls import reverse
from django.utils.encoding import force_str
from rest_framework.test import APITestCase

from authentik.core.models import Application, User
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding


class TestApplicationsAPI(APITestCase):
    """Test applications API"""

    def setUp(self) -> None:
        self.user = User.objects.get(username="akadmin")
        self.allowed = Application.objects.create(name="allowed", slug="allowed")
        self.denied = Application.objects.create(name="denied", slug="denied")
        PolicyBinding.objects.create(
            target=self.denied,
            policy=DummyPolicy.objects.create(name="deny", result=False, wait_min=1, wait_max=2),
            order=0,
        )

    def test_check_access(self):
        """Test check_access operation"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_api:application-check-access",
                kwargs={"slug": self.allowed.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_str(response.content), {"messages": [], "passing": True})
        response = self.client.get(
            reverse(
                "authentik_api:application-check-access",
                kwargs={"slug": self.denied.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(force_str(response.content), {"messages": ["dummy"], "passing": False})

    def test_list(self):
        """Test list operation without superuser_full_list"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentik_api:application-list"))
        self.assertJSONEqual(
            force_str(response.content),
            {
                "pagination": {
                    "next": 0,
                    "previous": 0,
                    "count": 2,
                    "current": 1,
                    "total_pages": 1,
                    "start_index": 1,
                    "end_index": 2,
                },
                "results": [
                    {
                        "pk": str(self.allowed.pk),
                        "name": "allowed",
                        "slug": "allowed",
                        "provider": None,
                        "provider_obj": None,
                        "launch_url": None,
                        "meta_launch_url": "",
                        "meta_icon": None,
                        "meta_description": "",
                        "meta_publisher": "",
                        "policy_engine_mode": "any",
                    },
                ],
            },
        )

    def test_list_superuser_full_list(self):
        """Test list operation with superuser_full_list"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("authentik_api:application-list") + "?superuser_full_list=true"
        )
        self.assertJSONEqual(
            force_str(response.content),
            {
                "pagination": {
                    "next": 0,
                    "previous": 0,
                    "count": 2,
                    "current": 1,
                    "total_pages": 1,
                    "start_index": 1,
                    "end_index": 2,
                },
                "results": [
                    {
                        "pk": str(self.allowed.pk),
                        "name": "allowed",
                        "slug": "allowed",
                        "provider": None,
                        "provider_obj": None,
                        "launch_url": None,
                        "meta_launch_url": "",
                        "meta_icon": None,
                        "meta_description": "",
                        "meta_publisher": "",
                        "policy_engine_mode": "any",
                    },
                    {
                        "launch_url": None,
                        "meta_description": "",
                        "meta_icon": None,
                        "meta_launch_url": "",
                        "meta_publisher": "",
                        "name": "denied",
                        "pk": str(self.denied.pk),
                        "policy_engine_mode": "any",
                        "provider": None,
                        "provider_obj": None,
                        "slug": "denied",
                    },
                ],
            },
        )
