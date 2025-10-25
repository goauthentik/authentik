"""Test WebAuthn API"""

from base64 import b64decode

from django.urls import reverse
from webauthn.helpers.bytes_to_base64url import bytes_to_base64url

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_webauthn.models import (
    UNKNOWN_DEVICE_TYPE_AAGUID,
    AuthenticatorWebAuthnStage,
    WebAuthnDevice,
    WebAuthnDeviceType,
)
from authentik.stages.authenticator_webauthn.stage import PLAN_CONTEXT_WEBAUTHN_CHALLENGE
from authentik.stages.authenticator_webauthn.tasks import webauthn_mds_import


class TestAuthenticatorWebAuthnStage(FlowTestCase):
    """Test WebAuthn API"""

    def setUp(self) -> None:
        self.stage = AuthenticatorWebAuthnStage.objects.create(
            name=generate_id(),
        )
        self.flow = create_test_flow()
        self.binding = FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )
        self.user = create_test_admin_user()

    def test_api_delete(self):
        """Test api delete"""
        self.client.force_login(self.user)
        dev = WebAuthnDevice.objects.create(user=self.user)
        response = self.client.delete(
            reverse("authentik_api:webauthndevice-detail", kwargs={"pk": dev.pk})
        )
        self.assertEqual(response.status_code, 204)

    def test_registration_options(self):
        """Test registration options"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )

        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            registration={
                "rp": {"name": "authentik", "id": "testserver"},
                "user": {
                    "id": bytes_to_base64url(self.user.uid.encode("utf-8")),
                    "name": self.user.username,
                    "displayName": self.user.name,
                },
                "challenge": bytes_to_base64url(plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE]),
                "pubKeyCredParams": [
                    {"type": "public-key", "alg": -7},
                    {"type": "public-key", "alg": -8},
                    {"type": "public-key", "alg": -36},
                    {"type": "public-key", "alg": -37},
                    {"type": "public-key", "alg": -38},
                    {"type": "public-key", "alg": -39},
                    {"type": "public-key", "alg": -257},
                    {"type": "public-key", "alg": -258},
                    {"type": "public-key", "alg": -259},
                ],
                "timeout": 60000,
                "excludeCredentials": [],
                "authenticatorSelection": {
                    "residentKey": "preferred",
                    "requireResidentKey": False,
                    "userVerification": "preferred",
                },
                "attestation": "direct",
            },
        )

    def test_register(self):
        """Test registration"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE] = b64decode(
            b"03Xodi54gKsfnP5I9VFfhaGXVVE2NUyZpBBXns/JI+x6V9RY2Tw2QmxRJkhh7174EkRazUntIwjMVY9bFG60Lw=="
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={
                "component": "ak-stage-authenticator-webauthn",
                "response": {
                    "id": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "rawId": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "type": "public-key",
                    "registrationClientExtensions": "{}",
                    "response": {
                        "clientDataJSON": (
                            "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmd"
                            "lIjoiMDNYb2RpNTRnS3NmblA1STlWRmZoYUdYVlZFMk5VeV"
                            "pwQkJYbnNfSkkteDZWOVJZMlR3MlFteFJKa2hoNzE3NEVrU"
                            "mF6VW50SXdqTVZZOWJGRzYwTHciLCJvcmlnaW4iOiJodHRw"
                            "Oi8vbG9jYWxob3N0OjkwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9"
                        ),
                        "attestationObject": (
                            "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YViYSZYN5Yg"
                            "OjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NdAAAAAPv8MA"
                            "cVTk7MjAtuAgVX170AFJKp5q1S5wxvjsLEjR5IoWGWjc-bp"
                            "QECAyYgASFYIKtcZHPumH37XHs0IM1v3pUBRIqHVV_SE-Lq"
                            "2zpJAOVXIlgg74Fg_WdB0kuLYqCKbxogkEPaVtR_iR3IyQFIJAXBzds"
                        ),
                    },
                },
            },
            SERVER_NAME="localhost",
            SERVER_PORT="9000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(WebAuthnDevice.objects.filter(user=self.user).exists())

    def test_register_restricted_device_type_deny(self):
        """Test registration with restricted devices (fail)"""
        webauthn_mds_import.send(force=True)
        self.stage.device_type_restrictions.set(
            WebAuthnDeviceType.objects.filter(description="YubiKey 5 Series")
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE] = b64decode(
            b"03Xodi54gKsfnP5I9VFfhaGXVVE2NUyZpBBXns/JI+x6V9RY2Tw2QmxRJkhh7174EkRazUntIwjMVY9bFG60Lw=="
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={
                "component": "ak-stage-authenticator-webauthn",
                "response": {
                    "id": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "rawId": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "type": "public-key",
                    "registrationClientExtensions": "{}",
                    "response": {
                        "clientDataJSON": (
                            "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmd"
                            "lIjoiMDNYb2RpNTRnS3NmblA1STlWRmZoYUdYVlZFMk5VeV"
                            "pwQkJYbnNfSkkteDZWOVJZMlR3MlFteFJKa2hoNzE3NEVrU"
                            "mF6VW50SXdqTVZZOWJGRzYwTHciLCJvcmlnaW4iOiJodHRw"
                            "Oi8vbG9jYWxob3N0OjkwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9"
                        ),
                        "attestationObject": (
                            "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YViYSZYN5Yg"
                            "OjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NdAAAAAPv8MA"
                            "cVTk7MjAtuAgVX170AFJKp5q1S5wxvjsLEjR5IoWGWjc-bp"
                            "QECAyYgASFYIKtcZHPumH37XHs0IM1v3pUBRIqHVV_SE-Lq"
                            "2zpJAOVXIlgg74Fg_WdB0kuLYqCKbxogkEPaVtR_iR3IyQFIJAXBzds"
                        ),
                    },
                },
            },
            SERVER_NAME="localhost",
            SERVER_PORT="9000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-authenticator-webauthn",
            response_errors={
                "response": [
                    {
                        "string": (
                            "Invalid device type. Contact your authentik administrator for help."
                        ),
                        "code": "invalid",
                    }
                ]
            },
        )
        self.assertFalse(WebAuthnDevice.objects.filter(user=self.user).exists())

    def test_register_restricted_device_type_allow(self):
        """Test registration with restricted devices (allow)"""
        webauthn_mds_import.send(force=True)
        self.stage.device_type_restrictions.set(
            WebAuthnDeviceType.objects.filter(description="iCloud Keychain")
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE] = b64decode(
            b"03Xodi54gKsfnP5I9VFfhaGXVVE2NUyZpBBXns/JI+x6V9RY2Tw2QmxRJkhh7174EkRazUntIwjMVY9bFG60Lw=="
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={
                "component": "ak-stage-authenticator-webauthn",
                "response": {
                    "id": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "rawId": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "type": "public-key",
                    "registrationClientExtensions": "{}",
                    "response": {
                        "clientDataJSON": (
                            "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmd"
                            "lIjoiMDNYb2RpNTRnS3NmblA1STlWRmZoYUdYVlZFMk5VeV"
                            "pwQkJYbnNfSkkteDZWOVJZMlR3MlFteFJKa2hoNzE3NEVrU"
                            "mF6VW50SXdqTVZZOWJGRzYwTHciLCJvcmlnaW4iOiJodHRw"
                            "Oi8vbG9jYWxob3N0OjkwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9"
                        ),
                        "attestationObject": (
                            "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YViYSZYN5Yg"
                            "OjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NdAAAAAPv8MA"
                            "cVTk7MjAtuAgVX170AFJKp5q1S5wxvjsLEjR5IoWGWjc-bp"
                            "QECAyYgASFYIKtcZHPumH37XHs0IM1v3pUBRIqHVV_SE-Lq"
                            "2zpJAOVXIlgg74Fg_WdB0kuLYqCKbxogkEPaVtR_iR3IyQFIJAXBzds"
                        ),
                    },
                },
            },
            SERVER_NAME="localhost",
            SERVER_PORT="9000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(WebAuthnDevice.objects.filter(user=self.user).exists())

    def test_register_restricted_device_type_allow_unknown(self):
        """Test registration with restricted devices (allow, unknown device type)"""
        webauthn_mds_import.send(force=True)
        WebAuthnDeviceType.objects.filter(description="iCloud Keychain").delete()
        self.stage.device_type_restrictions.set(
            WebAuthnDeviceType.objects.filter(aaguid=UNKNOWN_DEVICE_TYPE_AAGUID)
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE] = b64decode(
            b"03Xodi54gKsfnP5I9VFfhaGXVVE2NUyZpBBXns/JI+x6V9RY2Tw2QmxRJkhh7174EkRazUntIwjMVY9bFG60Lw=="
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={
                "component": "ak-stage-authenticator-webauthn",
                "response": {
                    "id": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "rawId": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "type": "public-key",
                    "registrationClientExtensions": "{}",
                    "response": {
                        "clientDataJSON": (
                            "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmd"
                            "lIjoiMDNYb2RpNTRnS3NmblA1STlWRmZoYUdYVlZFMk5VeV"
                            "pwQkJYbnNfSkkteDZWOVJZMlR3MlFteFJKa2hoNzE3NEVrU"
                            "mF6VW50SXdqTVZZOWJGRzYwTHciLCJvcmlnaW4iOiJodHRw"
                            "Oi8vbG9jYWxob3N0OjkwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9"
                        ),
                        "attestationObject": (
                            "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YViYSZYN5Yg"
                            "OjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NdAAAAAPv8MA"
                            "cVTk7MjAtuAgVX170AFJKp5q1S5wxvjsLEjR5IoWGWjc-bp"
                            "QECAyYgASFYIKtcZHPumH37XHs0IM1v3pUBRIqHVV_SE-Lq"
                            "2zpJAOVXIlgg74Fg_WdB0kuLYqCKbxogkEPaVtR_iR3IyQFIJAXBzds"
                        ),
                    },
                },
            },
            SERVER_NAME="localhost",
            SERVER_PORT="9000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(WebAuthnDevice.objects.filter(user=self.user).exists())

    def test_register_max_retries(self):
        """Test registration (exceeding max retries)"""
        self.stage.max_attempts = 2
        self.stage.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE] = b64decode(
            b"03Xodi54gKsfnP5I9VFfhaGXVVE2NUyZpBBXns/JI+x6V9RY2Tw2QmxRJkhh7174EkRazUntIwjMVY9bFG60Lw=="
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        # first failed request
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={
                "component": "ak-stage-authenticator-webauthn",
                "response": {
                    "id": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "rawId": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "type": "public-key",
                    "registrationClientExtensions": "{}",
                    "response": {
                        "clientDataJSON": (
                            "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmd"
                            "lIjoiMDNYb2RpNTRnS3NmblA1STlWRmZoYUdYVlZFMk5VeV"
                            "pwQkJYbnNfSkkteDZWOVJZMlR3MlFteFJKa2hoNzE3NEVrU"
                            "mF6VW50SXdqTVZZOWJGRzYwTHciLCJvcmlnaW4iOiJodHRw"
                            "Oi8vbG9jYWxob3N0OjkwMDAiLCJjcm9zc09yaWdpbiI6ZmF"
                        ),
                        "attestationObject": (
                            "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YViYSZYN5Yg"
                            "OjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NdAAAAAPv8MA"
                            "cVTk7MjAtuAgVX170AFJKp5q1S5wxvjsLEjR5IoWGWjc-bp"
                            "QECAyYgASFYIKtcZHPumH37XHs0IM1v3pUBRIqHVV_SE-Lq"
                            "2zpJAOVXIlgg74Fg_WdB0kuLYqCKbxogkEPaVtR_iR3IyQFIJAXBzds"
                        ),
                    },
                },
            },
            SERVER_NAME="localhost",
            SERVER_PORT="9000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-authenticator-webauthn",
            response_errors={
                "response": [
                    {
                        "string": (
                            "Registration failed. Error: Unable to decode "
                            "client_data_json bytes as JSON"
                        ),
                        "code": "invalid",
                    }
                ]
            },
        )
        self.assertFalse(WebAuthnDevice.objects.filter(user=self.user).exists())

        # Second failed request
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={
                "component": "ak-stage-authenticator-webauthn",
                "response": {
                    "id": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "rawId": "kqnmrVLnDG-OwsSNHkihYZaNz5s",
                    "type": "public-key",
                    "registrationClientExtensions": "{}",
                    "response": {
                        "clientDataJSON": (
                            "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmd"
                            "lIjoiMDNYb2RpNTRnS3NmblA1STlWRmZoYUdYVlZFMk5VeV"
                            "pwQkJYbnNfSkkteDZWOVJZMlR3MlFteFJKa2hoNzE3NEVrU"
                            "mF6VW50SXdqTVZZOWJGRzYwTHciLCJvcmlnaW4iOiJodHRw"
                            "Oi8vbG9jYWxob3N0OjkwMDAiLCJjcm9zc09yaWdpbiI6ZmF"
                        ),
                        "attestationObject": (
                            "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YViYSZYN5Yg"
                            "OjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NdAAAAAPv8MA"
                            "cVTk7MjAtuAgVX170AFJKp5q1S5wxvjsLEjR5IoWGWjc-bp"
                            "QECAyYgASFYIKtcZHPumH37XHs0IM1v3pUBRIqHVV_SE-Lq"
                            "2zpJAOVXIlgg74Fg_WdB0kuLYqCKbxogkEPaVtR_iR3IyQFIJAXBzds"
                        ),
                    },
                },
            },
            SERVER_NAME="localhost",
            SERVER_PORT="9000",
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-access-denied",
            error_message=(
                "Exceeded maximum attempts. Contact your authentik administrator for help."
            ),
        )
        self.assertFalse(WebAuthnDevice.objects.filter(user=self.user).exists())
