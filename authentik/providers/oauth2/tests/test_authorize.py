"""Test authorize view"""
from unittest.mock import MagicMock, patch

from django.test import RequestFactory
from django.urls import reverse
from django.utils.timezone import now

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.flows.challenge import ChallengeTypes
from authentik.lib.generators import generate_id
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.constants import TOKEN_TYPE
from authentik.providers.oauth2.errors import AuthorizeError, ClientIdError, RedirectUriError
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    GrantTypes,
    OAuth2Provider,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD


class TestAuthorize(OAuthTestCase):
    """Test authorize view"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def test_invalid_grant_type(self):
        """Test with invalid grant type"""
        with self.assertRaises(AuthorizeError):
            request = self.factory.get("/", data={"response_type": "invalid"})
            OAuthAuthorizationParams.from_request(request)

    def test_invalid_client_id(self):
        """Test invalid client ID"""
        with self.assertRaises(ClientIdError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "invalid"})
            OAuthAuthorizationParams.from_request(request)

    def test_request(self):
        """test request param"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid/Foo",
        )
        with self.assertRaises(AuthorizeError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid/Foo",
                    "request": "foo",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_invalid_redirect_uri(self):
        """test missing/invalid redirect URI"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
            OAuthAuthorizationParams.from_request(request)
        with self.assertRaises(RedirectUriError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://localhost",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_invalid_redirect_uri_empty(self):
        """test missing/invalid redirect URI"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="",
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
            OAuthAuthorizationParams.from_request(request)
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": "test",
                "redirect_uri": "+",
            },
        )
        OAuthAuthorizationParams.from_request(request)
        provider.refresh_from_db()
        self.assertEqual(provider.redirect_uris, "+")

    def test_invalid_redirect_uri_regex(self):
        """test missing/invalid redirect URI"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid?",
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
            OAuthAuthorizationParams.from_request(request)
        with self.assertRaises(RedirectUriError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://localhost",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_redirect_uri_invalid_regex(self):
        """test missing/invalid redirect URI (invalid regex)"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="+",
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
            OAuthAuthorizationParams.from_request(request)
        with self.assertRaises(RedirectUriError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://localhost",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_empty_redirect_uri(self):
        """test empty redirect URI (configure in provider)"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
            OAuthAuthorizationParams.from_request(request)
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": "test",
                "redirect_uri": "http://localhost",
            },
        )
        OAuthAuthorizationParams.from_request(request)

    def test_response_type(self):
        """test response_type"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid/Foo",
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": "test",
                "redirect_uri": "http://local.invalid/Foo",
            },
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).grant_type,
            GrantTypes.AUTHORIZATION_CODE,
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).redirect_uri,
            "http://local.invalid/Foo",
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "id_token",
                "client_id": "test",
                "redirect_uri": "http://local.invalid/Foo",
                "scope": "openid",
                "state": "foo",
                "nonce": generate_id(),
            },
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).grant_type,
            GrantTypes.IMPLICIT,
        )
        # Implicit without openid scope
        with self.assertRaises(AuthorizeError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "id_token",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid/Foo",
                    "state": "foo",
                },
            )
            self.assertEqual(
                OAuthAuthorizationParams.from_request(request).grant_type,
                GrantTypes.IMPLICIT,
            )
        request = self.factory.get(
            "/",
            data={
                "response_type": "code token",
                "client_id": "test",
                "redirect_uri": "http://local.invalid/Foo",
                "scope": "openid",
                "state": "foo",
            },
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).grant_type, GrantTypes.HYBRID
        )
        with self.assertRaises(AuthorizeError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "invalid",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid/Foo",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_full_code(self):
        """Test full authorization"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris="foo://localhost",
            access_code_validity="seconds=100",
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        # Step 1, initiate params and get redirect to flow
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
            },
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
        self.assertJSONEqual(
            response.content.decode(),
            {
                "component": "xak-flow-redirect",
                "type": ChallengeTypes.REDIRECT.value,
                "to": f"foo://localhost?code={code.code}&state={state}",
            },
        )
        self.assertAlmostEqual(
            code.expires.timestamp() - now().timestamp(),
            timedelta_from_string(provider.access_code_validity).total_seconds(),
            delta=5,
        )

    def test_full_implicit(self):
        """Test full authorization"""
        flow = create_test_flow()
        provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris="http://localhost",
            signing_key=self.keypair,
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        with patch(
            "authentik.providers.oauth2.id_token.get_login_event",
            MagicMock(
                return_value=Event(
                    action=EventAction.LOGIN,
                    context={PLAN_CONTEXT_METHOD: "password"},
                    created=now(),
                )
            ),
        ):
            # Step 1, initiate params and get redirect to flow
            self.client.get(
                reverse("authentik_providers_oauth2:authorize"),
                data={
                    "response_type": "id_token",
                    "client_id": "test",
                    "state": state,
                    "scope": "openid",
                    "redirect_uri": "http://localhost",
                    "nonce": generate_id(),
                },
            )
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            )
            token: AccessToken = AccessToken.objects.filter(user=user).first()
            expires = timedelta_from_string(provider.access_token_validity).total_seconds()
            self.assertJSONEqual(
                response.content.decode(),
                {
                    "component": "xak-flow-redirect",
                    "type": ChallengeTypes.REDIRECT.value,
                    "to": (
                        f"http://localhost#access_token={token.token}"
                        f"&id_token={provider.encode(token.id_token.to_dict())}"
                        f"&token_type={TOKEN_TYPE}"
                        f"&expires_in={int(expires)}&state={state}"
                    ),
                },
            )
            jwt = self.validate_jwt(token, provider)
            self.assertEqual(jwt["amr"], ["pwd"])
            self.assertAlmostEqual(
                jwt["exp"] - now().timestamp(),
                expires,
                delta=5,
            )

    def test_full_fragment_code(self):
        """Test full authorization"""
        flow = create_test_flow()
        provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris="http://localhost",
            signing_key=self.keypair,
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        with patch(
            "authentik.providers.oauth2.id_token.get_login_event",
            MagicMock(
                return_value=Event(
                    action=EventAction.LOGIN,
                    context={PLAN_CONTEXT_METHOD: "password"},
                    created=now(),
                )
            ),
        ):
            # Step 1, initiate params and get redirect to flow
            self.client.get(
                reverse("authentik_providers_oauth2:authorize"),
                data={
                    "response_type": "code",
                    "response_mode": "fragment",
                    "client_id": "test",
                    "state": state,
                    "scope": "openid",
                    "redirect_uri": "http://localhost",
                    "nonce": generate_id(),
                },
            )
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            )
            code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
            self.assertJSONEqual(
                response.content.decode(),
                {
                    "component": "xak-flow-redirect",
                    "type": ChallengeTypes.REDIRECT.value,
                    "to": (f"http://localhost#code={code.code}" f"&state={state}"),
                },
            )
            self.assertAlmostEqual(
                code.expires.timestamp() - now().timestamp(),
                timedelta_from_string(provider.access_code_validity).total_seconds(),
                delta=5,
            )

    def test_full_form_post_id_token(self):
        """Test full authorization (form_post response)"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            authorization_flow=flow,
            redirect_uris="http://localhost",
            signing_key=self.keypair,
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        # Step 1, initiate params and get redirect to flow
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "id_token",
                "response_mode": "form_post",
                "client_id": provider.client_id,
                "state": state,
                "scope": "openid",
                "redirect_uri": "http://localhost",
                "nonce": generate_id(),
            },
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        token: AccessToken = AccessToken.objects.filter(user=user).first()
        self.assertJSONEqual(
            response.content.decode(),
            {
                "component": "ak-stage-autosubmit",
                "type": ChallengeTypes.NATIVE.value,
                "url": "http://localhost",
                "title": f"Redirecting to {app.name}...",
                "attrs": {
                    "access_token": token.token,
                    "id_token": provider.encode(token.id_token.to_dict()),
                    "token_type": TOKEN_TYPE,
                    "expires_in": "3600",
                    "state": state,
                },
            },
        )
        self.validate_jwt(token, provider)

    def test_full_form_post_code(self):
        """Test full authorization (form_post response, code type)"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            authorization_flow=flow,
            redirect_uris="http://localhost",
            signing_key=self.keypair,
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        # Step 1, initiate params and get redirect to flow
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "response_mode": "form_post",
                "client_id": provider.client_id,
                "state": state,
                "scope": "openid",
                "redirect_uri": "http://localhost",
            },
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
        self.assertJSONEqual(
            response.content.decode(),
            {
                "component": "ak-stage-autosubmit",
                "type": ChallengeTypes.NATIVE.value,
                "url": "http://localhost",
                "title": f"Redirecting to {app.name}...",
                "attrs": {
                    "code": code.code,
                    "state": state,
                },
            },
        )
