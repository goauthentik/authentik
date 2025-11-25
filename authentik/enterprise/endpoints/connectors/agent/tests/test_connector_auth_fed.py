from json import loads

from django.urls import reverse
from django.utils.timezone import now
from jwt import decode
from rest_framework.test import APITestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.tests.utils import create_test_user
from authentik.endpoints.connectors.agent.api.connectors import AgentDeviceConnection
from authentik.endpoints.connectors.agent.models import AgentConnector, EnrollmentToken
from authentik.endpoints.models import Device
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider


class TestConnectorAuthFed(APITestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(
            name=generate_id(),
            domain_name=generate_id(),
        )
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.device = Device.objects.create(
            name=generate_id(),
            identifier=generate_id(),
        )
        self.connection = AgentDeviceConnection.objects.create(
            device=self.device,
            connector=self.connector,
        )
        user = create_test_user()
        self.provider = OAuth2Provider.objects.create(name=generate_id())
        self.raw_token = self.provider.encode({"foo": "bar"})
        self.token = AccessToken.objects.create(
            provider=self.provider, user=user, token=self.raw_token, auth_time=now()
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
