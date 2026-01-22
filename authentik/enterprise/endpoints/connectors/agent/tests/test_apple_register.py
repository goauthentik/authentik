from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.tests.utils import create_test_user
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    DeviceAuthenticationToken,
    DeviceToken,
    EnrollmentToken,
)
from authentik.endpoints.models import Device
from authentik.enterprise.tests import enterprise_test
from authentik.lib.generators import generate_id


class TestAppleRegister(APITestCase):

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
        self.device_token = DeviceToken.objects.create(device=self.connection)

    @enterprise_test()
    @reconcile_app("authentik_crypto")
    def test_register_device(self):
        response = self.client.post(
            reverse("authentik_api:psso-register-device"),
            data={
                "device_signing_key": generate_id(),
                "device_encryption_key": generate_id(),
                "sign_key_id": generate_id(),
                "enc_key_id": generate_id(),
            },
            HTTP_AUTHORIZATION=f"Bearer+agent {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "client_id": str(self.connector.pk),
                "audience": str(self.device.pk),
                "issuer": "http://testserver/endpoints/agent/psso/token/",
                "jwks_endpoint": "http://testserver/endpoints/agent/psso/jwks/",
                "nonce_endpoint": "http://testserver/endpoints/agent/psso/nonce/",
                "token_endpoint": "http://testserver/endpoints/agent/psso/token/",
            },
        )

    @enterprise_test()
    @reconcile_app("authentik_crypto")
    def test_register_user(self):
        device_auth = DeviceAuthenticationToken.objects.create(
            device=self.device,
            device_token=self.device_token,
            connector=self.connector,
            user=self.user,
            token=generate_id(),
        )
        response = self.client.post(
            reverse("authentik_api:psso-register-user"),
            data={
                "user_auth": device_auth.token,
                "user_secure_enclave_key": generate_id(),
                "enclave_key_id": generate_id(),
            },
            HTTP_AUTHORIZATION=f"Bearer+agent {self.device_token.key}",
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["username"], self.user.username)
