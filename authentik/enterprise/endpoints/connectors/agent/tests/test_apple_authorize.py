from urllib.parse import parse_qs, urlencode, urlparse

from cryptography.hazmat.primitives import serialization
from django.urls import reverse
from jwt import encode

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.crypto.builder import PrivateKeyAlg
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AppleAuthorizationCode,
)
from authentik.endpoints.models import Device, DeviceAccessGroup
from authentik.enterprise.endpoints.connectors.agent.views.apple_authorize import REDIRECT_URI
from authentik.enterprise.tests import enterprise_test
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import JWTAlgorithms


class TestAppleAuthorize(FlowTestCase):

    def setUp(self):
        self.apple_sign_key = create_test_cert(PrivateKeyAlg.ECDSA)
        self.connector = AgentConnector.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        self.device = Device.objects.create(name=generate_id(), identifier=generate_id())
        self.connection = AgentDeviceConnection.objects.create(
            device=self.device,
            connector=self.connector,
            apple_sign_key_id=self.apple_sign_key.kid,
            apple_signing_key=self.apple_sign_key.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode(),
        )
        self.user = create_test_user()
        self.url = reverse(
            "authentik_enterprise_endpoints_connectors_agent:psso-authorize",
            kwargs={"connector_uuid": str(self.connector.pk)},
        )

    @enterprise_test()
    def test_authorize_binds_device(self):
        """The issued code is bound to the device that signed the request object"""
        # Device policies are deny-by-default, bind a passing policy for self.user
        group = Group.objects.create(name=generate_id())
        group.users.add(self.user)
        self.device.access_group = DeviceAccessGroup.objects.create(name=generate_id())
        self.device.save()
        PolicyBinding.objects.create(target=self.device.access_group, group=group, order=0)

        self.client.force_login(self.user)
        request_object = encode(
            {"iss": str(self.connector.pk)},
            self.apple_sign_key.private_key,
            headers={"kid": self.apple_sign_key.kid},
            algorithm=JWTAlgorithms.from_private_key(self.apple_sign_key.private_key),
        )
        res = self.client.post(
            f"{self.url}?redirect_uri={REDIRECT_URI}",
            # Platform SSO posts the request object as a form field, the API test client
            # would otherwise default to JSON
            data=urlencode({"request": request_object}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(res.status_code, 302)
        # The flow is empty, so running the executor once reaches the fulfillment stage
        res = self.client.get(
            reverse(
                "authentik_api:flow-executor",
                kwargs={"flow_slug": self.connector.authorization_flow.slug},
            )
        )
        to = self.assertStageResponse(res, component="xak-flow-redirect")["to"]
        code = parse_qs(urlparse(to).query)["code"][0]
        auth_code = AppleAuthorizationCode.objects.get(code=code)
        self.assertEqual(auth_code.device_connection, self.connection)
        self.assertEqual(auth_code.user, self.user)

    @enterprise_test()
    def test_authorize_without_request_object(self):
        """Plain federation carries no device identity and is not supported"""
        group = Group.objects.create(name=generate_id())
        group.users.add(self.user)
        self.device.access_group = DeviceAccessGroup.objects.create(name=generate_id())
        self.device.save()
        PolicyBinding.objects.create(target=self.device.access_group, group=group, order=0)

        self.client.force_login(self.user)
        res = self.client.post(f"{self.url}?redirect_uri={REDIRECT_URI}")
        self.assertEqual(res.status_code, 404)

    @enterprise_test()
    def test_authorize_unknown_device(self):
        """A request object signed by a key no enrolled device uses is rejected"""
        group = Group.objects.create(name=generate_id())
        group.users.add(self.user)
        self.device.access_group = DeviceAccessGroup.objects.create(name=generate_id())
        self.device.save()
        PolicyBinding.objects.create(target=self.device.access_group, group=group, order=0)

        self.client.force_login(self.user)
        other_key = create_test_cert(PrivateKeyAlg.ECDSA)
        request_object = encode(
            {"iss": str(self.connector.pk)},
            other_key.private_key,
            headers={"kid": other_key.kid},
            algorithm=JWTAlgorithms.from_private_key(other_key.private_key),
        )
        res = self.client.post(
            f"{self.url}?redirect_uri={REDIRECT_URI}",
            data=urlencode({"request": request_object}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(res.status_code, 404)

    @enterprise_test()
    def test_authorize_device_policy_denied(self):
        """Without a passing device policy no code is issued"""
        self.client.force_login(self.user)
        request_object = encode(
            {"iss": str(self.connector.pk)},
            self.apple_sign_key.private_key,
            headers={"kid": self.apple_sign_key.kid},
            algorithm=JWTAlgorithms.from_private_key(self.apple_sign_key.private_key),
        )
        res = self.client.post(
            f"{self.url}?redirect_uri={REDIRECT_URI}",
            data=urlencode({"request": request_object}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertNotEqual(res.status_code, 302)
        self.assertFalse(AppleAuthorizationCode.objects.exists())
