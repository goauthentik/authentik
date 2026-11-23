"""Radius Provider API tests"""

from base64 import b64decode
from json import loads
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.outposts.models import Outpost, OutpostType
from authentik.policies.models import PolicyBinding
from authentik.providers.radius.models import RadiusProvider, RadiusProviderPropertyMapping


class TestRadiusProviderAPI(APITestCase):
    """Radius Provider API tests"""

    def setUp(self):
        self.user = create_test_user()
        self.provider = RadiusProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.RADIUS)

    def test_outpost_config(self):
        """Test outpost config retrieval"""
        self.outpost.providers.add(self.provider)
        self.client.force_login(self.outpost.user)
        res = self.client.get(reverse("authentik_api:radiusprovideroutpost-list"))
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertEqual(data["pagination"]["count"], 1)
        self.assertEqual(data["results"][0]["application_slug"], self.app.slug)

    def test_outpost_config_no_outpost(self):
        """Test outpost config is not accessible to non-outpost users"""
        self.client.force_login(create_test_admin_user())
        res = self.client.get(reverse("authentik_api:radiusprovideroutpost-list"))
        self.assertEqual(res.status_code, 403)

    def test_check_access(self):
        """Test access check without any policies bound"""
        self.client.force_login(self.user)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=self.outpost.user),
        ):
            res = self.client.get(
                reverse(
                    "authentik_api:radiusprovideroutpost-check-access",
                    kwargs={"pk": self.provider.pk},
                ),
                data={"app_slug": self.app.slug},
            )
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertTrue(data["access"]["passing"])
        self.assertIsNotNone(data["attributes"])

    def test_check_access_denied(self):
        """Test access check with a group binding the user is not part of"""
        PolicyBinding.objects.create(
            target=self.app, group=Group.objects.create(name=generate_id()), order=0
        )
        self.client.force_login(self.user)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=self.outpost.user),
        ):
            res = self.client.get(
                reverse(
                    "authentik_api:radiusprovideroutpost-check-access",
                    kwargs={"pk": self.provider.pk},
                ),
                data={"app_slug": self.app.slug},
            )
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertFalse(data["access"]["passing"])
        self.assertIsNone(data["attributes"])

    def test_check_access_no_outpost(self):
        """Test access check requires an outpost-delegated request"""
        self.client.force_login(self.user)
        res = self.client.get(
            reverse(
                "authentik_api:radiusprovideroutpost-check-access",
                kwargs={"pk": self.provider.pk},
            ),
            data={"app_slug": self.app.slug},
        )
        self.assertEqual(res.status_code, 403)

    def test_mapping_returned_packet(self):
        """Test property mapping that returns the packet"""
        self.provider.property_mappings.add(
            RadiusProviderPropertyMapping.objects.create(
                name=generate_id(),
                expression="""
define_attribute(
    vendor_code=9,
    vendor_name="Cisco",
    attribute_name="AV-Pair",
    attribute_code=1,
    attribute_type="string",
)
packet["Cisco-AV-Pair"] = "shell:priv-lvl=15"
return packet
                """,
            )
        )
        self.client.force_login(self.user)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=self.outpost.user),
        ):
            res = self.client.get(
                reverse(
                    "authentik_api:radiusprovideroutpost-check-access",
                    kwargs={"pk": self.provider.pk},
                ),
                data={"app_slug": self.app.slug},
            )
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertIn(b"shell:priv-lvl=15", b64decode(data["attributes"]))

    def test_mapping_return_custom(self):
        """Test property mapping that returns a custom attribute"""
        self.provider.property_mappings.add(
            RadiusProviderPropertyMapping.objects.create(
                name=generate_id(),
                expression="""
return {
    vendor_attribute(
        vendor_code=9,
        vendor_name="Cisco",
        attribute_name="AV-Pair",
        attribute_code=1,
        attribute_type="string",
    ): "shell:priv-lvl=15"
}
                """,
            )
        )
        self.client.force_login(self.user)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=self.outpost.user),
        ):
            res = self.client.get(
                reverse(
                    "authentik_api:radiusprovideroutpost-check-access",
                    kwargs={"pk": self.provider.pk},
                ),
                data={"app_slug": self.app.slug},
            )
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertIn(b"shell:priv-lvl=15", b64decode(data["attributes"]))

    def test_mapping_returned_none(self):
        """Test property mapping that only mutates the packet and returns nothing"""
        self.provider.property_mappings.add(
            RadiusProviderPropertyMapping.objects.create(
                name=generate_id(),
                expression="""packet["Reply-Message"] = "foo\"""",
            )
        )
        self.client.force_login(self.user)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=self.outpost.user),
        ):
            res = self.client.get(
                reverse(
                    "authentik_api:radiusprovideroutpost-check-access",
                    kwargs={"pk": self.provider.pk},
                ),
                data={"app_slug": self.app.slug},
            )
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertIn(b"foo", b64decode(data["attributes"]))
        self.assertFalse(Event.objects.filter(action=EventAction.CONFIGURATION_ERROR).exists())

    def test_mapping_error(self):
        """Test that a failing property mapping doesn't stop the other mappings"""
        self.provider.property_mappings.add(
            RadiusProviderPropertyMapping.objects.create(
                name="a-failing",
                expression="raise ValueError",
            ),
            RadiusProviderPropertyMapping.objects.create(
                name="b-working",
                expression="""return {"Reply-Message": "foo"}""",
            ),
        )
        self.client.force_login(self.user)
        with patch(
            "authentik.root.middleware.ClientIPMiddleware.get_outpost_user",
            MagicMock(return_value=self.outpost.user),
        ):
            res = self.client.get(
                reverse(
                    "authentik_api:radiusprovideroutpost-check-access",
                    kwargs={"pk": self.provider.pk},
                ),
                data={"app_slug": self.app.slug},
            )
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertIn(b"foo", b64decode(data["attributes"]))
        self.assertTrue(Event.objects.filter(action=EventAction.CONFIGURATION_ERROR).exists())
