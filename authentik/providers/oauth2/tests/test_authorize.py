"""Test authorize view"""

from json import dumps as json_dumps
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlencode, urlparse

from django.core.signing import dumps
from django.test import RequestFactory
from django.urls import reverse
from django.utils import translation
from django.utils.timezone import now

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    PROMPT_SELECT_ACCOUNT,
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
    TOKEN_TYPE,
)
from authentik.core.account_selection import COOKIE_NAME_KNOWN_ACCOUNTS, QS_ADD_ACCOUNT
from authentik.core.models import Application, AuthenticatedSession, Session, User
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowStageBinding
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.views.executor import QS_QUERY, SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.errors import AuthorizeError, ClientIdError, RedirectUriError
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.authorize import (
    OAuthAuthorizationParams,
)
from authentik.providers.oauth2.views.provider import ProviderInfoView
from authentik.stages.dummy.models import DummyStage
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD


class TestAuthorize(OAuthTestCase):
    """Test authorize view"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def get_flow_executor_url(self, flow, authorize_query: dict[str, str]) -> str:
        """Build the API endpoint used by the web flow executor."""
        return (
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
            + f"?{urlencode({QS_QUERY: urlencode(authorize_query)})}"
        )

    def remember_live_accounts(self, *users: User) -> None:
        """Store browser-local accounts backed by live authenticated sessions."""
        accounts = []
        for index, user in enumerate(users):
            client = self.client if index == 0 else self.client_class()
            client.force_login(user)
            session = Session.objects.get(session_key=client.session.session_key)
            AuthenticatedSession.objects.update_or_create(
                session=session,
                defaults={"user": user},
            )
            accounts.append({"uid": user.uuid.hex, "session": session.session_key})
        self.client.cookies[COOKIE_NAME_KNOWN_ACCOUNTS] = dumps(accounts)

    def test_disallowed_grant_type(self):
        """Test with disallowed grant type"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            grant_types=[],
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/Foo")],
        )
        with self.assertRaises(AuthorizeError) as cm:
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid/Foo",
                },
            )
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.error, "invalid_request")

    def test_invalid_grant_type(self):
        """Test with invalid grant type"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/Foo")],
        )
        with self.assertRaises(AuthorizeError) as cm:
            request = self.factory.get(
                "/",
                data={
                    "response_type": "invalid",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid/Foo",
                },
            )
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.error, "unsupported_response_type")

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
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/Foo")],
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        with self.assertRaises(AuthorizeError) as cm:
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
        self.assertEqual(cm.exception.error, "request_not_supported")

    def test_prompt_select_account(self):
        """Test prompt=select_account parsing"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/Foo")],
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": "test",
                "redirect_uri": "http://local.invalid/Foo",
                "prompt": PROMPT_SELECT_ACCOUNT,
            },
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).prompt,
            {PROMPT_SELECT_ACCOUNT},
        )

    def test_provider_info_prompt_select_account(self):
        """Test prompt=select_account is advertised in provider metadata"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/Foo")],
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        view = ProviderInfoView()
        view.request = self.factory.get("/")
        self.assertIn(PROMPT_SELECT_ACCOUNT, view.get_info(provider)["prompt_values_supported"])

    def test_invalid_redirect_uri_missing(self):
        """test missing redirect URI"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
        )
        with self.assertRaises(RedirectUriError) as cm:
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.cause, "redirect_uri_missing")

    def test_invalid_redirect_uri(self):
        """test invalid redirect URI"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
        )
        with self.assertRaises(RedirectUriError) as cm:
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://localhost",
                },
            )
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.cause, "redirect_uri_no_match")

    def test_blocked_redirect_uri(self):
        """test missing/invalid redirect URI"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "data:localhost")],
        )
        with self.assertRaises(RedirectUriError) as cm:
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "data:localhost",
                },
            )
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.cause, "redirect_uri_forbidden_scheme")

    def test_invalid_redirect_uri_regex(self):
        """test missing/invalid redirect URI"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.REGEX, "http://local.invalid?")],
        )
        with self.assertRaises(RedirectUriError) as cm:
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://localhost",
                },
            )
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.cause, "redirect_uri_no_match")

    def test_redirect_uri_invalid_regex(self):
        """test missing/invalid redirect URI (invalid regex)"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.REGEX, "+")],
        )
        with self.assertRaises(RedirectUriError) as cm:
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://localhost",
                },
            )
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.cause, "redirect_uri_no_match")

    def test_redirect_uri_regex(self):
        """test valid redirect URI (regex)"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.REGEX, ".+")],
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": "test",
                "redirect_uri": "http://foo.bar.baz",
            },
        )
        OAuthAuthorizationParams.from_request(request)

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_response_type(self):
        """test response_type"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/Foo")],
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-email",
                    "goauthentik.io/providers/oauth2/scope-profile",
                ]
            )
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
            GrantType.AUTHORIZATION_CODE,
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).redirect_uri,
            "http://local.invalid/Foo",
        )
        provider.grant_types = [GrantType.IMPLICIT]
        provider.save()
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
            GrantType.IMPLICIT,
        )
        # Implicit without openid scope
        with self.assertRaises(AuthorizeError) as cm:
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
                GrantType.IMPLICIT,
            )
        provider.grant_types = [GrantType.HYBRID]
        provider.save()
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
            OAuthAuthorizationParams.from_request(request).grant_type, GrantType.HYBRID
        )
        with self.assertRaises(AuthorizeError) as cm:
            request = self.factory.get(
                "/",
                data={
                    "response_type": "invalid",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid/Foo",
                },
            )
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.error, "unsupported_response_type")

    def test_full_code(self):
        """Test full authorization"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        # Step 1, initiate params and get redirect to flow
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
            },
        )
        code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
        self.assertEqual(
            response.url,
            f"foo://localhost?code={code.code}&state={state}",
        )
        self.assertAlmostEqual(
            code.expires.timestamp() - now().timestamp(),
            timedelta_from_string(provider.access_code_validity).total_seconds(),
            delta=5,
        )

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_full_implicit(self):
        """Test full authorization"""
        flow = create_test_flow()
        provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            signing_key=self.keypair,
            grant_types=[GrantType.IMPLICIT],
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-email",
                    "goauthentik.io/providers/oauth2/scope-profile",
                ]
            )
        )
        provider.property_mappings.add(
            ScopeMapping.objects.create(
                name=generate_id(), scope_name="test", expression="""return {"sub": "foo"}"""
            )
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
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
            response = self.client.get(
                reverse("authentik_providers_oauth2:authorize"),
                data={
                    "response_type": "id_token",
                    "client_id": "test",
                    "state": state,
                    "scope": "openid test",
                    "redirect_uri": "http://localhost",
                    "nonce": generate_id(),
                },
            )
            token = AccessToken.objects.filter(user=user).first()
            expires = timedelta_from_string(provider.access_token_validity).total_seconds()
            self.assertEqual(
                response.url,
                (
                    f"http://localhost#id_token={provider.encode(token.id_token.to_dict())}"
                    f"&token_type={TOKEN_TYPE}"
                    f"&expires_in={int(expires)}&state={state}"
                ),
            )
            jwt = self.validate_jwt(token, provider)
            self.assertEqual(jwt["amr"], ["pwd"])
            self.assertEqual(jwt["sub"], "foo")
            self.assertAlmostEqual(
                jwt["exp"] - now().timestamp(),
                expires,
                delta=5,
            )

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_full_implicit_enc(self):
        """Test full authorization with encryption"""
        flow = create_test_flow()
        provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            signing_key=self.keypair,
            encryption_key=self.keypair,
            grant_types=[GrantType.IMPLICIT],
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-email",
                    "goauthentik.io/providers/oauth2/scope-profile",
                ]
            )
        )
        provider.property_mappings.add(
            ScopeMapping.objects.create(
                name=generate_id(), scope_name="test", expression="""return {"sub": "foo"}"""
            )
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
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
            response = self.client.get(
                reverse("authentik_providers_oauth2:authorize"),
                data={
                    "response_type": "id_token",
                    "client_id": "test",
                    "state": state,
                    "scope": "openid test",
                    "redirect_uri": "http://localhost",
                    "nonce": generate_id(),
                },
            )
            self.assertEqual(response.status_code, 302)
            token = AccessToken.objects.filter(user=user).first()
            expires = timedelta_from_string(provider.access_token_validity).total_seconds()
            jwt = self.validate_jwe(token, provider)
            self.assertEqual(jwt["amr"], ["pwd"])
            self.assertEqual(jwt["sub"], "foo")
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
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            signing_key=self.keypair,
            grant_types=[GrantType.AUTHORIZATION_CODE],
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
            response = self.client.get(
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
            code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
            self.assertEqual(
                response.url,
                f"http://localhost#code={code.code}&state={state}",
            )
            self.assertAlmostEqual(
                code.expires.timestamp() - now().timestamp(),
                timedelta_from_string(provider.access_code_validity).total_seconds(),
                delta=5,
            )

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_full_form_post_id_token(self):
        """Test full authorization (form_post response)"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            signing_key=self.keypair,
            grant_types=[GrantType.IMPLICIT],
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-email",
                    "goauthentik.io/providers/oauth2/scope-profile",
                ]
            )
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
        token = AccessToken.objects.filter(user=user).first()
        self.assertIsNotNone(token)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "component": "ak-stage-autosubmit",
                "url": "http://localhost",
                "title": f"Redirecting to {app.name}...",
                "attrs": {
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
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            signing_key=self.keypair,
            grant_types=[GrantType.AUTHORIZATION_CODE],
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
                "url": "http://localhost",
                "title": f"Redirecting to {app.name}...",
                "attrs": {
                    "code": code.code,
                    "state": state,
                },
            },
        )

    def test_openid_missing_invalid(self):
        """test request requiring an OpenID scope to be set"""
        OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.IMPLICIT],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "id_token",
                "client_id": "test",
                "redirect_uri": "http://localhost",
                "scope": "",
            },
        )
        with self.assertRaises(AuthorizeError) as cm:
            OAuthAuthorizationParams.from_request(request)
        self.assertEqual(cm.exception.cause, "scope_openid_missing")

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_offline_access_invalid(self):
        """test request for offline_access with invalid response type"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            grant_types=[GrantType.IMPLICIT],
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-offline_access",
                ]
            )
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "id_token",
                "client_id": "test",
                "redirect_uri": "http://localhost",
                "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
                "nonce": generate_id(),
            },
        )
        parsed = OAuthAuthorizationParams.from_request(request)
        self.assertNotIn(SCOPE_OFFLINE_ACCESS, parsed.scope)

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_ui_locales(self):
        """Test OIDC ui_locales authorization"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        self.client.logout()
        try:
            response = self.client.get(
                reverse("authentik_providers_oauth2:authorize"),
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "state": state,
                    "redirect_uri": "foo://localhost",
                    "ui_locales": "invalid fr",
                },
            )
            parsed = parse_qs(urlparse(response.url).query)
            self.assertEqual(parsed["locale"], ["fr"])
        finally:
            translation.deactivate()

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_ui_locales_invalid(self):
        """Test OIDC ui_locales authorization"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        self.client.logout()
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
                "ui_locales": "invalid",
            },
        )
        parsed = parse_qs(urlparse(response.url).query)
        self.assertNotIn("locale", parsed)

    def test_authentication_flow(self):
        """Test custom authentication flow"""
        brand = create_test_brand()
        global_auth = create_test_flow()
        FlowStageBinding.objects.create(
            target=global_auth, stage=DummyStage.objects.create(name=generate_id()), order=10
        )
        brand.flow_authentication = global_auth
        brand.save()

        flow = create_test_flow()
        auth_flow = create_test_flow()
        FlowStageBinding.objects.create(
            target=auth_flow, stage=DummyStage.objects.create(name=generate_id()), order=10
        )
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            authentication_flow=auth_flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(auth_flow.slug, response.url)
        self.assertNotIn(global_auth.slug, response.url)

    def test_prompt_select_account_shows_account_selection(self):
        """Test prompt=select_account shows the account selection stage"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        user = create_test_admin_user()
        self.client.force_login(user)
        authorize_query = {
            "response_type": "code",
            "client_id": "test",
            "state": generate_id(),
            "redirect_uri": "foo://localhost",
            "prompt": PROMPT_SELECT_ACCOUNT,
        }
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data=authorize_query,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(flow.slug, response.url)
        challenge_response = self.client.get(self.get_flow_executor_url(flow, authorize_query))
        self.assertEqual(challenge_response.json()["component"], "ak-stage-oauth-account-selection")
        self.assertEqual(challenge_response.json()["accounts"][0]["username"], user.username)

    def test_prompt_select_account_shows_before_authorization_flow_stages(self):
        """Test prompt=select_account is shown before the provider authorization flow."""
        flow = create_test_flow()
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=10
        )
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        user = create_test_admin_user()
        self.client.force_login(user)
        authorize_query = {
            "response_type": "code",
            "client_id": "test",
            "state": generate_id(),
            "redirect_uri": "foo://localhost",
            "prompt": PROMPT_SELECT_ACCOUNT,
        }
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data=authorize_query,
        )
        self.assertEqual(response.status_code, 302)
        challenge_response = self.client.get(self.get_flow_executor_url(flow, authorize_query))
        self.assertEqual(challenge_response.json()["component"], "ak-stage-oauth-account-selection")

    def test_known_accounts_show_account_selection_by_default(self):
        """Test multiple remembered browser accounts show the account selection stage"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        user = create_test_admin_user()
        other_user = create_test_admin_user("other-user")
        self.remember_live_accounts(user, other_user)
        authorize_query = {
            "response_type": "code",
            "client_id": "test",
            "state": generate_id(),
            "redirect_uri": "foo://localhost",
        }
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data=authorize_query,
        )
        self.assertEqual(response.status_code, 302)
        challenge_response = self.client.get(self.get_flow_executor_url(flow, authorize_query))
        challenge = challenge_response.json()
        self.assertEqual(challenge["component"], "ak-stage-oauth-account-selection")
        self.assertEqual(
            [account["username"] for account in challenge["accounts"]],
            [user.username, other_user.username],
        )

    def test_stale_known_accounts_do_not_show_account_selection_by_default(self):
        """Test stale remembered browser accounts are not enough to show selection."""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        user = create_test_admin_user()
        stale_user = create_test_admin_user("stale-user")
        self.remember_live_accounts(user)
        session = Session.objects.get(session_key=self.client.session.session_key)
        self.client.cookies[COOKIE_NAME_KNOWN_ACCOUNTS] = dumps(
            [
                {"uid": user.uuid.hex, "session": session.session_key},
                {"uid": stale_user.uuid.hex, "session": "missing"},
            ]
        )
        authorize_query = {
            "response_type": "code",
            "response_mode": "form_post",
            "client_id": "test",
            "state": generate_id(),
            "redirect_uri": "http://localhost",
        }
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data=authorize_query,
        )
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(challenge_response.json()["component"], "ak-stage-autosubmit")

    def test_account_selection_switch_requests_authentication(self):
        """Test selecting a remembered non-current account starts authentication"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        user = create_test_admin_user()
        other_user = create_test_admin_user("other-user")
        self.remember_live_accounts(user, other_user)
        authorize_query = {
            "response_type": "code",
            "client_id": "test",
            "state": generate_id(),
            "redirect_uri": "foo://localhost",
        }
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data=authorize_query,
        )
        self.assertEqual(response.status_code, 302)
        self.client.get(self.get_flow_executor_url(flow, authorize_query))
        switch_response = self.client.post(
            self.get_flow_executor_url(flow, authorize_query),
            data=json_dumps(
                {
                    "component": "ak-stage-oauth-account-selection",
                    "action": "switch",
                    "selected_account": other_user.uuid.hex,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(switch_response.json()["component"], "xak-flow-redirect")
        redirect = switch_response.json()["to"]
        parsed = parse_qs(urlparse(redirect).query)
        self.assertEqual(
            urlparse(redirect).path,
            reverse("authentik_flows:default-authentication"),
        )
        self.assertEqual(parsed["login_hint"], [other_user.email])
        self.assertEqual(parsed["account_uid"], [other_user.uuid.hex])
        authorize_query = parse_qs(urlparse(parsed["next"][0]).query)
        self.assertEqual(authorize_query["client_id"], ["test"])
        self.assertNotIn("query", authorize_query)
        self.assertEqual(authorize_query["login_hint"], [other_user.email])
        self.assertEqual(authorize_query["account_uid"], [other_user.uuid.hex])

    def test_account_selection_login_requests_authentication(self):
        """Test using another account restarts authorization with normal OAuth parameters."""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        self.client.force_login(create_test_admin_user())
        authorize_query = {
            "response_type": "code",
            "client_id": "test",
            "state": generate_id(),
            "redirect_uri": "foo://localhost",
            "prompt": PROMPT_SELECT_ACCOUNT,
        }
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data=authorize_query,
        )
        self.assertEqual(response.status_code, 302)
        self.client.get(self.get_flow_executor_url(flow, authorize_query))
        login_response = self.client.post(
            self.get_flow_executor_url(flow, authorize_query),
            data=json_dumps(
                {
                    "component": "ak-stage-oauth-account-selection",
                    "action": "login",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(login_response.json()["component"], "xak-flow-redirect")
        redirect = login_response.json()["to"]
        parsed = parse_qs(urlparse(redirect).query)
        self.assertEqual(
            urlparse(redirect).path,
            reverse("authentik_flows:default-authentication"),
        )
        self.assertEqual(parsed[QS_ADD_ACCOUNT], ["true"])
        authorize_url = parsed["next"][0]
        authorize_query = parse_qs(urlparse(authorize_url).query)
        self.assertEqual(authorize_query["client_id"], ["test"])
        self.assertEqual(authorize_query["prompt"], [PROMPT_SELECT_ACCOUNT])
        self.assertNotIn("query", authorize_query)

    def test_prompt_select_account_ignores_login_hint(self):
        """Test prompt=select_account doesn't auto-select the login_hint user"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "http://localhost",
                "prompt": PROMPT_SELECT_ACCOUNT,
                "login_hint": "foo",
            },
        )
        self.assertEqual(response.status_code, 302)
        plan = self.client.session.get(SESSION_KEY_PLAN)
        self.assertNotIn(PLAN_CONTEXT_PENDING_USER_IDENTIFIER, plan.context)

    def test_prompt_none_select_account(self):
        """Test prompt=none and prompt=select_account return account_selection_required"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": "foo",
                "redirect_uri": "http://localhost",
                "prompt": "none select_account",
            },
        )
        self.assertEqual(response.status_code, 302)
        parsed = parse_qs(urlparse(response.url).query)
        self.assertEqual(parsed["error"], ["account_selection_required"])
        self.assertEqual(parsed["state"], ["foo"])

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_login_hint(self):
        """Login hint"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "foo://localhost")],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
                "login_hint": "foo",
            },
        )
        self.assertEqual(response.status_code, 302)
        plan = self.client.session.get(SESSION_KEY_PLAN)
        self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER], "foo")
