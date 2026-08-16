"""Device flow end-to-end tests"""

from json import loads

from django.urls import reverse
from rest_framework.test import APIClient

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_DEVICE_CODE,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.events.signals import get_login_event
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    DeviceToken,
    GrantType,
    OAuth2Provider,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestOAuth2DeviceFlow(OAuthTestCase):
    """Walk the whole device code flow: back channel, user code entry, finish stage,
    token exchange. Nothing else in the suite executes OAuthDeviceCodeFinishStage."""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=self.keypair,
            grant_types=[GrantType.DEVICE_CODE],
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.device_flow = create_test_flow()
        self.brand = create_test_brand(flow_device_code=self.device_flow)
        self.user = create_test_admin_user()
        # A single client for the whole user-facing walk: the flow plan lives in the session,
        # so splitting the walk across clients would lose it.
        self.user_client = APIClient()
        self.user_client.force_login(self.user)

    def request_device_code(self, scope: str = f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL}") -> dict:
        """Run the back channel and return the device authorization response"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": self.provider.client_id,
                "scope": scope,
            },
        )
        self.assertEqual(res.status_code, 200)
        return loads(res.content.decode())

    def exchange(self, device_code: str):
        """Poll the token endpoint for the given device code"""
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "grant_type": GRANT_TYPE_DEVICE_CODE,
                "device_code": device_code,
            },
        )

    def authorize_via_query_param(self, device: dict):
        """Follow verification_uri_complete and run the resulting flow up to the finish stage"""
        res = self.user_client.get(device["verification_uri_complete"])
        self.assertEqual(res.status_code, 302)
        self.assertIn(self.provider.authorization_flow.slug, res.url)
        res = self.user_client.get(
            reverse(
                "authentik_api:flow-executor",
                kwargs={"flow_slug": self.provider.authorization_flow.slug},
            ),
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            loads(res.content.decode())["component"],
            "ak-provider-oauth2-device-code-finish",
        )
        return res

    def test_device_flow_end_to_end(self):
        """Full flow: back channel, authorize via query param, exchange the code"""
        device = self.request_device_code()
        token = DeviceToken.objects.filter(device_code=device["device_code"]).first()
        self.assertIsNotNone(token)
        self.assertIsNone(token.user)

        # Nothing has authorized the code yet
        res = self.exchange(device["device_code"])
        self.assertEqual(res.status_code, 400)
        self.assertEqual(loads(res.content.decode())["error"], "authorization_pending")

        self.authorize_via_query_param(device)

        token.refresh_from_db()
        self.assertEqual(token.user, self.user)

        # Acknowledge the finish challenge, which completes the flow
        res = self.user_client.post(
            reverse(
                "authentik_api:flow-executor",
                kwargs={"flow_slug": self.provider.authorization_flow.slug},
            ),
            data={"component": "ak-provider-oauth2-device-code-finish"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(loads(res.content.decode())["component"], "xak-flow-redirect")

        # The device can now exchange its code
        res = self.exchange(device["device_code"])
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        access_token = AccessToken.objects.filter(token=body["access_token"]).first()
        self.assertIsNotNone(access_token)
        self.assertEqual(access_token.user, self.user)
        self.assertSetEqual(set(access_token.scope), {SCOPE_OPENID, SCOPE_OPENID_EMAIL})
        # Device code is single-use
        self.assertFalse(
            DeviceToken.objects.including_expired()
            .filter(device_code=device["device_code"])
            .exists()
        )

    def test_device_flow_end_to_end_code_entry(self):
        """Full flow, but the user types the code into the brand's device flow"""
        device = self.request_device_code()

        res = self.user_client.get(reverse("authentik_providers_oauth2_root:device-login"))
        self.assertEqual(res.status_code, 302)
        self.assertIn(self.device_flow.slug, res.url)

        executor = reverse(
            "authentik_api:flow-executor",
            kwargs={"flow_slug": self.device_flow.slug},
        )
        res = self.user_client.get(executor)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(loads(res.content.decode())["component"], "ak-provider-oauth2-device-code")

        res = self.user_client.post(
            executor,
            data={
                "component": "ak-provider-oauth2-device-code",
                "code": device["user_code"],
            },
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertEqual(body["component"], "xak-flow-redirect")
        self.assertIn(self.provider.authorization_flow.slug, body["to"])

        res = self.user_client.get(
            reverse(
                "authentik_api:flow-executor",
                kwargs={"flow_slug": self.provider.authorization_flow.slug},
            ),
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            loads(res.content.decode())["component"],
            "ak-provider-oauth2-device-code-finish",
        )

        token = DeviceToken.objects.filter(device_code=device["device_code"]).first()
        self.assertEqual(token.user, self.user)
        self.assertTrue(Event.objects.filter(action=EventAction.AUTHORIZE_APPLICATION).exists())

    def test_authorize_application_event_context(self):
        """The finish stage logs an application authorization, same shape as authorize.py"""
        device = self.request_device_code()
        self.assertFalse(Event.objects.filter(action=EventAction.AUTHORIZE_APPLICATION).exists())

        self.authorize_via_query_param(device)

        event = Event.objects.filter(action=EventAction.AUTHORIZE_APPLICATION).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["authorized_application"]["name"], self.application.name)
        self.assertEqual(event.context["authorized_application"]["pk"], self.application.pk.hex)
        self.assertEqual(event.context["flow"], self.provider.authorization_flow.pk.hex)
        self.assertSetEqual(
            set(event.context["scopes"].split()), {SCOPE_OPENID, SCOPE_OPENID_EMAIL}
        )
        self.assertEqual(event.user["username"], self.user.username)

    def test_finish_stage_binds_session(self):
        """The finish stage binds the user's session, which the access token inherits"""
        device = self.request_device_code()
        self.authorize_via_query_param(device)

        token = DeviceToken.objects.filter(device_code=device["device_code"]).first()
        self.assertIsNotNone(token.session)
        self.assertEqual(token.session.user, self.user)

        res = self.exchange(device["device_code"])
        self.assertEqual(res.status_code, 200)
        access_token = AccessToken.objects.filter(
            token=loads(res.content.decode())["access_token"]
        ).first()
        self.assertIsNotNone(access_token.session)
        self.assertEqual(access_token.session.session_id, token.session.session_id)

    def test_finish_stage_auth_time_from_login_event(self):
        """With a session bound, auth_time comes from the login event instead of now()"""
        device = self.request_device_code()
        self.authorize_via_query_param(device)

        token = DeviceToken.objects.filter(device_code=device["device_code"]).first()
        login_event = get_login_event(token.session)
        self.assertIsNotNone(login_event)

        res = self.exchange(device["device_code"])
        self.assertEqual(res.status_code, 200)
        access_token = AccessToken.objects.filter(
            token=loads(res.content.decode())["access_token"]
        ).first()
        self.assertEqual(access_token.auth_time, login_event.created)
