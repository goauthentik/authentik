"""Test Transactional API"""

from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import OAuth2Provider


class TestTransactionalApplicationsAPI(APITestCase):
    """Test Transactional API"""

    def setUp(self) -> None:
        self.user = create_test_user()
        assign_perm("authentik_core.add_application", self.user)
        assign_perm("authentik_providers_oauth2.add_oauth2provider", self.user)

    def test_create_transactional(self):
        """Test transactional Application + provider creation"""
        self.client.force_login(self.user)
        uid = generate_id()
        response = self.client.put(
            reverse("authentik_api:core-transactional-application"),
            data={
                "app": {
                    "name": uid,
                    "slug": uid,
                },
                "provider_model": "authentik_providers_oauth2.oauth2provider",
                "provider": {
                    "name": uid,
                    "authorization_flow": str(create_test_flow().pk),
                    "invalidation_flow": str(create_test_flow().pk),
                    "redirect_uris": [],
                },
            },
        )
        self.assertJSONEqual(response.content.decode(), {"applied": True, "logs": []})
        provider = OAuth2Provider.objects.filter(name=uid).first()
        self.assertIsNotNone(provider)
        app = Application.objects.filter(slug=uid).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.provider.pk, provider.pk)

    def test_create_transactional_permission_denied(self):
        """Test transactional Application + provider creation (missing permissions)"""
        self.client.force_login(self.user)
        uid = generate_id()
        response = self.client.put(
            reverse("authentik_api:core-transactional-application"),
            data={
                "app": {
                    "name": uid,
                    "slug": uid,
                },
                "provider_model": "authentik_providers_saml.samlprovider",
                "provider": {
                    "name": uid,
                    "authorization_flow": str(create_test_flow().pk),
                    "invalidation_flow": str(create_test_flow().pk),
                    "acs_url": "https://goauthentik.io",
                },
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"provider": "User lacks permission to create authentik_providers_saml.samlprovider"},
        )

    def test_create_transactional_bindings(self):
        """Test transactional Application + provider creation"""
        assign_perm("authentik_policies.add_policybinding", self.user)
        self.client.force_login(self.user)
        uid = generate_id()
        group = Group.objects.create(name=generate_id())
        authorization_flow = create_test_flow()
        response = self.client.put(
            reverse("authentik_api:core-transactional-application"),
            data={
                "app": {
                    "name": uid,
                    "slug": uid,
                },
                "provider_model": "authentik_providers_oauth2.oauth2provider",
                "provider": {
                    "name": uid,
                    "authorization_flow": str(authorization_flow.pk),
                    "invalidation_flow": str(authorization_flow.pk),
                    "redirect_uris": [],
                },
                "policy_bindings": [{"group": group.pk, "order": 0}],
            },
        )
        self.assertJSONEqual(response.content.decode(), {"applied": True, "logs": []})
        provider = OAuth2Provider.objects.filter(name=uid).first()
        self.assertIsNotNone(provider)
        app = Application.objects.filter(slug=uid).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.provider.pk, provider.pk)
        binding = PolicyBinding.objects.filter(target=app).first()
        self.assertIsNotNone(binding)
        self.assertEqual(binding.target, app)
        self.assertEqual(binding.group, group)

    def test_create_transactional_invalid(self):
        """Test transactional Application + provider creation"""
        self.client.force_login(self.user)
        uid = generate_id()
        response = self.client.put(
            reverse("authentik_api:core-transactional-application"),
            data={
                "app": {
                    "name": uid,
                    "slug": uid,
                },
                "provider_model": "authentik_providers_oauth2.oauth2provider",
                "provider": {
                    "name": uid,
                    "authorization_flow": "",
                    "invalidation_flow": "",
                    "redirect_uris": [],
                },
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {
                "provider": {
                    "authorization_flow": ["This field may not be null."],
                    "invalidation_flow": ["This field may not be null."],
                }
            },
        )

    def test_create_transactional_duplicate_name_provider(self):
        """Test transactional Application + provider creation"""
        self.client.force_login(self.user)
        uid = generate_id()
        OAuth2Provider.objects.create(
            name=uid,
            authorization_flow=create_test_flow(),
            invalidation_flow=create_test_flow(),
        )
        response = self.client.put(
            reverse("authentik_api:core-transactional-application"),
            data={
                "app": {
                    "name": uid,
                    "slug": uid,
                },
                "provider_model": "authentik_providers_oauth2.oauth2provider",
                "provider": {
                    "name": uid,
                    "authorization_flow": str(create_test_flow().pk),
                    "invalidation_flow": str(create_test_flow().pk),
                },
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"provider": {"name": ["State is set to must_created and object exists already"]}},
        )
