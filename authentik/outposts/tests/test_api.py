"""Test outpost service connection API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.models import PropertyMapping
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.crypto.generators import generate_id
from authentik.outposts.api.outposts import OutpostSerializer
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost, OutpostType, default_outpost_config
from authentik.providers.ldap.models import LDAPProvider
from authentik.providers.proxy.models import ProxyProvider


class TestOutpostServiceConnectionsAPI(APITestCase):
    """Test outpost service connection API"""

    def setUp(self) -> None:
        super().setUp()
        self.mapping = PropertyMapping.objects.create(
            name=generate_id(), expression="""return {'foo': 'bar'}"""
        )
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    @reconcile_app("authentik_outposts")
    def test_managed_name_change(self):
        """Test name change for embedded outpost"""
        embedded_outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
        self.assertIsNotNone(embedded_outpost)
        response = self.client.patch(
            reverse("authentik_api:outpost-detail", kwargs={"pk": embedded_outpost.pk}),
            {"name": "foo"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content, {"name": ["Embedded outpost's name cannot be changed"]}
        )

    @reconcile_app("authentik_outposts")
    def test_managed_without_managed(self):
        """Test name change for embedded outpost"""
        embedded_outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
        self.assertIsNotNone(embedded_outpost)
        embedded_outpost.managed = ""
        embedded_outpost.save()
        response = self.client.patch(
            reverse("authentik_api:outpost-detail", kwargs={"pk": embedded_outpost.pk}),
            {"name": "foo"},
        )
        self.assertEqual(response.status_code, 200)
        embedded_outpost.refresh_from_db()
        self.assertEqual(embedded_outpost.managed, MANAGED_OUTPOST)

    def test_outpost_validation(self):
        """Test Outpost validation"""
        valid = OutpostSerializer(
            data={
                "name": generate_id(),
                "type": OutpostType.PROXY,
                "config": default_outpost_config(),
                "providers": [
                    ProxyProvider.objects.create(
                        name=generate_id(), authorization_flow=create_test_flow()
                    ).pk
                ],
            }
        )
        self.assertTrue(valid.is_valid())
        invalid = OutpostSerializer(
            data={
                "name": generate_id(),
                "type": OutpostType.PROXY,
                "config": default_outpost_config(),
                "providers": [
                    LDAPProvider.objects.create(
                        name=generate_id(), authorization_flow=create_test_flow()
                    ).pk
                ],
            }
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn("providers", invalid.errors)

    def test_types(self):
        """Test OutpostServiceConnections's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:outpostserviceconnection-types"),
        )
        self.assertEqual(response.status_code, 200)

    def test_outpost_config(self):
        """Test Outpost's config field"""
        provider = ProxyProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        invalid = OutpostSerializer(
            data={"name": generate_id(), "providers": [provider.pk], "config": ""}
        )
        self.assertFalse(invalid.is_valid())
        self.assertIn("config", invalid.errors)
        valid = OutpostSerializer(
            data={
                "name": generate_id(),
                "providers": [provider.pk],
                "config": default_outpost_config(generate_id()),
                "type": OutpostType.PROXY,
            }
        )
        self.assertTrue(valid.is_valid())
