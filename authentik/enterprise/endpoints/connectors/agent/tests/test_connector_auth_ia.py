from hashlib import sha256
from json import loads
from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from jwt import decode
from rest_framework.test import APITestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.models import Group
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.endpoints.connectors.agent.api.connectors import AgentDeviceConnection
from authentik.endpoints.connectors.agent.models import AgentConnector, AuthenticationProfile, DeviceToken, EnrollmentToken
from authentik.endpoints.models import Device, DeviceTag
from authentik.enterprise.endpoints.connectors.agent.views.auth_interactive import QS_AGENT_IA_TOKEN
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding


class TestConnectorAuthIA(APITestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
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
        self.device_token = DeviceToken.objects.create(
            device=self.connection,
            key=generate_id(),
        )
        self.user = create_test_user()

    def test_auth_ia_initiate(self):
        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-ia"),
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 200)

    @reconcile_app("authentik_crypto")
    def test_auth_ia_fulfill(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-ia"),
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
            HTTP_X_AUTHENTIK_PLATFORM_AUTH_DTH=sha256(self.device_token.key.encode()).hexdigest(),
        )
        self.assertEqual(response.status_code, 200)
        res = loads(response.content)
        response = self.client.get(
            res["url"],
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
            HTTP_X_AUTHENTIK_PLATFORM_AUTH_DTH=sha256(self.device_token.key.encode()).hexdigest(),
        )
        self.assertEqual(response.status_code, 302)
        url = urlparse(response.url)
        self.assertEqual(url.scheme, "goauthentik.io")
        qs = parse_qs(url.query)
        raw_token = qs[QS_AGENT_IA_TOKEN][0]
        token = decode(raw_token.encode(), options={"verify_signature": False})
        self.assertEqual(token["iss"], "goauthentik.io/platform")
        self.assertEqual(token["aud"], str(self.device.pk))

    @reconcile_app("authentik_crypto")
    def test_auth_ia_fulfill_policy(self):
        device_tag = DeviceTag.objects.create(name=generate_id())
        self.device.tags.add(device_tag)
        self.device.save()

        group = Group.objects.create(name=generate_id())
        group.users.add(self.user)

        profile = AuthenticationProfile.objects.create(
            name=generate_id()
        )
        profile.tags.add(device_tag)

        PolicyBinding.objects.create(target=profile, group=group, order=0)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:agentconnector-auth-ia"),
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
            HTTP_X_AUTHENTIK_PLATFORM_AUTH_DTH=sha256(self.device_token.key.encode()).hexdigest(),
        )
        self.assertEqual(response.status_code, 200)
        res = loads(response.content)
        response = self.client.get(
            res["url"],
            HTTP_AUTHORIZATION=f"Bearer {self.device_token.key}",
            HTTP_X_AUTHENTIK_PLATFORM_AUTH_DTH=sha256(self.device_token.key.encode()).hexdigest(),
        )
        self.assertEqual(response.status_code, 302)
        url = urlparse(response.url)
        self.assertEqual(url.scheme, "goauthentik.io")
        qs = parse_qs(url.query)
        raw_token = qs[QS_AGENT_IA_TOKEN][0]
        token = decode(raw_token.encode(), options={"verify_signature": False})
        self.assertEqual(token["iss"], "goauthentik.io/platform")
        self.assertEqual(token["aud"], str(self.device.pk))
