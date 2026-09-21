"""Test RAC Devices API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.endpoints.models import DeviceAccessGroup, DeviceUserBinding
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.rac.models import Protocols, RACProvider
from authentik.providers.rac.tests import create_test_device


class TestRACDevicesAPI(APITestCase):
    """Test RAC devices API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.provider = RACProvider.objects.create(name=generate_id())
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.allowed = create_test_device(name=f"a-{generate_id()}", host=generate_id())
        self.denied = create_test_device(name=f"b-{generate_id()}", host=generate_id())
        PolicyBinding.objects.create(
            target=self.denied,
            policy=DummyPolicy.objects.create(name="deny", result=False, wait_min=1, wait_max=2),
            order=0,
        )

    def list_devices(self, **params) -> list[dict]:
        response = self.client.get(
            reverse("authentik_api:rac_device-list"),
            data={"provider": self.provider.pk, **params},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["results"]

    def test_list(self):
        """Only devices whose policies pass are listed"""
        self.client.force_login(self.user)
        self.assertEqual(
            self.list_devices(),
            [
                {
                    "device_uuid": str(self.allowed.pk),
                    "name": self.allowed.name,
                    "protocols": [
                        {
                            "protocol": Protocols.RDP,
                            "launch_url": (
                                f"/application/rac/{self.app.slug}/{self.allowed.pk}/rdp/"
                            ),
                        }
                    ],
                    "is_primary": False,
                    "override_pk": self.allowed.rac_override.pk,
                }
            ],
        )

    def test_list_requires_provider(self):
        """The provider is required, as it determines what is launchable"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentik_api:rac_device-list"))
        self.assertEqual(response.status_code, 400)

    def test_list_superuser_full_list(self):
        """Test list operation with superuser_full_list"""
        self.client.force_login(self.user)
        pks = [device["device_uuid"] for device in self.list_devices(superuser_full_list="true")]
        self.assertCountEqual(pks, [str(self.allowed.pk), str(self.denied.pk)])

    def test_list_access_group(self):
        """A provider limited to an access group only lists devices in it"""
        group = DeviceAccessGroup.objects.create(name=generate_id())
        self.provider.access_group = group
        self.provider.save()
        in_group = create_test_device(host=generate_id(), access_group=group)
        self.client.force_login(self.user)
        pks = [device["device_uuid"] for device in self.list_devices()]
        self.assertEqual(pks, [str(in_group.pk)])

    def test_list_access_group_policy(self):
        """Policies bound to the access group gate every device in it"""
        group = DeviceAccessGroup.objects.create(name=generate_id())
        PolicyBinding.objects.create(
            target=group,
            policy=DummyPolicy.objects.create(
                name=f"deny-{generate_id()}", result=False, wait_min=1, wait_max=2
            ),
            order=0,
        )
        create_test_device(host=generate_id(), access_group=group)
        self.client.force_login(self.user)
        pks = [device["device_uuid"] for device in self.list_devices()]
        self.assertEqual(pks, [str(self.allowed.pk)])

    def test_list_protocols(self):
        """Each protocol a device can be reached with has its own launch URL"""
        override = create_test_device(
            name=f"c-{generate_id()}", host=generate_id(), protocol=Protocols.SSH
        )
        # A device which says nothing about itself can be reached with either protocol
        unknown = create_test_device(name=f"d-{generate_id()}")
        self.client.force_login(self.user)
        listed = {d["device_uuid"]: d for d in self.list_devices()}
        self.assertEqual(
            listed[str(override.pk)]["protocols"],
            [
                {
                    "protocol": Protocols.SSH,
                    "launch_url": f"/application/rac/{self.app.slug}/{override.pk}/ssh/",
                }
            ],
        )
        self.assertEqual(
            [entry["protocol"] for entry in listed[str(unknown.pk)]["protocols"]],
            [Protocols.RDP, Protocols.SSH],
        )

    def test_list_primary_device(self):
        """A user's primary device is marked as such"""
        user = create_test_user()
        device = create_test_device(name=f"c-{generate_id()}", host=generate_id())
        DeviceUserBinding.objects.create(target=device, user=user, is_primary=True, order=0)
        self.client.force_login(user)
        listed = {d["device_uuid"]: d for d in self.list_devices()}
        self.assertTrue(listed[str(device.pk)]["is_primary"])
        self.assertFalse(listed[str(self.allowed.pk)]["is_primary"])

    def test_list_regular_user_denied_application(self):
        """A user who is denied the application receives no devices, even though the
        devices themselves have no policy bindings"""
        PolicyBinding.objects.create(
            target=self.app,
            policy=DummyPolicy.objects.create(
                name=f"deny-{generate_id()}", result=False, wait_min=1, wait_max=2
            ),
            order=0,
        )
        user = create_test_user()
        self.assertFalse(user.has_perm("authentik_endpoints.view_device"))
        self.client.force_login(user)
        self.assertEqual(self.list_devices(), [])

    def test_list_regular_user_allowed_application(self):
        """A user who passes an application's policies receives its devices without
        needing device permissions (this is the end-user launch picker)"""
        user = create_test_user()
        self.assertFalse(user.has_perm("authentik_endpoints.view_device"))
        self.client.force_login(user)
        pks = [device["device_uuid"] for device in self.list_devices()]
        self.assertEqual(pks, [str(self.allowed.pk)])

    def test_list_no_attributes_exposed(self):
        """A device's attributes are not exposed through the launch picker"""
        secret = generate_id()
        create_test_device(
            name=f"c-{generate_id()}",
            host=generate_id(),
            attributes={"internal": secret},
        )
        user = create_test_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("authentik_api:rac_device-list"),
            data={"provider": self.provider.pk},
        )
        self.assertNotIn(secret, response.content.decode())
