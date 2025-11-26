from json import loads

from django.urls import reverse
from django.utils.timezone import now
from jwt import decode
from rest_framework.test import APITestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.models import Group
from authentik.core.tests.utils import create_test_user
from authentik.endpoints.connectors.agent.api.connectors import AgentDeviceConnection
from authentik.endpoints.connectors.agent.models import AgentConnector, EnrollmentToken
from authentik.endpoints.models import Device, DeviceGroup
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider


class TestConnectorAuthFed(APITestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(name=generate_id())
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.device = Device.objects.create(
            name=generate_id(),
            identifier=generate_id(),
        )
        self.connection = AgentDeviceConnection.objects.create(
            device=self.device,
            connector=self.connector,
        )
        self.user = create_test_user()
        self.provider = OAuth2Provider.objects.create(name=generate_id())
        self.raw_token = self.provider.encode({"foo": "bar"})
        self.token = AccessToken.objects.create(
            provider=self.provider, user=self.user, token=self.raw_token, auth_time=now()
        )
        self.connector.jwt_federation_providers.add(self.provider)

    @reconcile_app("authentik_crypto")
    def test_auth_fed(self):
        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-fed") + f"?device={self.device.name}",
            HTTP_AUTHORIZATION=f"Bearer {self.raw_token}",
        )
        self.assertEqual(response.status_code, 200)
        res = loads(response.content)
        token = decode(res["token"], options={"verify_signature": False})
        self.assertEqual(token["iss"], "goauthentik.io/platform")
        self.assertEqual(token["aud"], str(self.device.pk))

    @reconcile_app("authentik_crypto")
    def test_auth_fed_policy_group(self):
        device_group = DeviceGroup.objects.create(name=generate_id())
        self.device.group = device_group
        self.device.save()

        group = Group.objects.create(name=generate_id())
        group.users.add(self.user)

        PolicyBinding.objects.create(target=device_group, group=group, order=0)

        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-fed") + f"?device={self.device.name}",
            HTTP_AUTHORIZATION=f"Bearer {self.raw_token}",
        )
        self.assertEqual(response.status_code, 200)
        res = loads(response.content)
        token = decode(res["token"], options={"verify_signature": False})
        self.assertEqual(token["iss"], "goauthentik.io/platform")
        self.assertEqual(token["aud"], str(self.device.pk))

    @reconcile_app("authentik_crypto")
    def test_auth_fed_policy_group_deny(self):
        device_group = DeviceGroup.objects.create(name=generate_id())
        self.device.group = device_group
        self.device.save()

        group = Group.objects.create(name=generate_id())
        # group.users.add(self.user)

        PolicyBinding.objects.create(target=device_group, group=group, order=0)

        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-fed") + f"?device={self.device.name}",
            HTTP_AUTHORIZATION=f"Bearer {self.raw_token}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {
                "policy_result": "Policy denied access",
                "policy_messages": [],
            },
        )

    @reconcile_app("authentik_crypto")
    def test_auth_fed_invalid(self):
        # No token
        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-fed") + f"?device={self.device.name}foo",
        )
        self.assertEqual(response.status_code, 400)
        # No device
        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-fed") + f"?device={self.device.name}foo",
            HTTP_AUTHORIZATION=f"Bearer {self.raw_token}",
        )
        self.assertEqual(response.status_code, 404)
        # invalid token
        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-fed") + f"?device={self.device.name}",
            HTTP_AUTHORIZATION=f"Bearer {self.raw_token}aa",
        )
        self.assertEqual(response.status_code, 404)
