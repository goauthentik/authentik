"""Test OAuth authorize account selection behavior."""

from json import dumps as json_dumps
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.core.signing import dumps
from django.test import RequestFactory
from django.urls import reverse

from authentik.common.oauth.constants import PROMPT_SELECT_ACCOUNT, QS_LOGIN_HINT
from authentik.core.account_selection import (
    COOKIE_NAME_KNOWN_ACCOUNTS,
    QS_ACCOUNT_UID,
    QS_ADD_ACCOUNT,
    append_account_selection_hint,
)
from authentik.core.models import Application, Session
from authentik.core.tests.account_selection import (
    create_test_account_selection_flow,
    remember_live_accounts,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowStageBinding
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams
from authentik.providers.oauth2.views.provider import ProviderInfoView
from authentik.stages.dummy.models import DummyStage


class TestAuthorizeAccountSelection(OAuthTestCase):
    """Test OAuth authorize account selection behavior."""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def create_provider(self, flow, redirect_uri: str = "foo://localhost") -> OAuth2Provider:
        """Create an OAuth2 provider for account-selection authorize tests."""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, redirect_uri)],
            access_code_validity="seconds=100",
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        return provider

    def test_append_account_selection_hint_preserves_repeated_params(self):
        """Test account-selection hints don't collapse repeated authorization params."""
        user = create_test_admin_user()
        authorize_url = (
            reverse("authentik_providers_oauth2:authorize")
            + "?scope=openid&resource=one&resource=two"
        )

        hinted_url = append_account_selection_hint(authorize_url, user)

        parsed = parse_qs(urlparse(hinted_url).query)
        self.assertEqual(parsed["resource"], ["one", "two"])
        self.assertEqual(parsed[QS_ACCOUNT_UID], [user.uuid.hex])
        self.assertEqual(parsed[QS_LOGIN_HINT], [user.email])

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

    def test_prompt_select_account_shows_account_selection(self):
        """Test prompt=select_account starts the brand account selection flow."""
        flow = create_test_flow()
        account_flow, _, _ = create_test_account_selection_flow()
        self.create_provider(flow)
        user = create_test_admin_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "foo://localhost",
                "prompt": PROMPT_SELECT_ACCOUNT,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(account_flow.slug, response.url)
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": account_flow.slug})
        )
        self.assertEqual(challenge_response.json()["component"], "ak-stage-account-selection")
        self.assertEqual(challenge_response.json()["accounts"][0]["username"], user.username)

    def test_prompt_select_account_shows_before_authorization_flow_stages(self):
        """Test prompt=select_account is shown before the provider authorization flow."""
        flow = create_test_flow()
        account_flow, _, _ = create_test_account_selection_flow()
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=10
        )
        self.create_provider(flow)
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "foo://localhost",
                "prompt": PROMPT_SELECT_ACCOUNT,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(account_flow.slug, response.url)
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": account_flow.slug})
        )
        self.assertEqual(challenge_response.json()["component"], "ak-stage-account-selection")

    def test_known_accounts_show_account_selection_by_default(self):
        """Test multiple remembered browser accounts show the account selection stage"""
        flow = create_test_flow()
        account_flow, _, _ = create_test_account_selection_flow()
        self.create_provider(flow)
        user = create_test_admin_user()
        other_user = create_test_admin_user("other-user")
        remember_live_accounts(self, user, other_user)
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "foo://localhost",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(account_flow.slug, response.url)
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": account_flow.slug})
        )
        challenge = challenge_response.json()
        self.assertEqual(challenge["component"], "ak-stage-account-selection")
        self.assertEqual(
            [account["username"] for account in challenge["accounts"]],
            [user.username, other_user.username],
        )

    def test_stale_known_accounts_do_not_show_account_selection_by_default(self):
        """Test stale remembered browser accounts are not enough to show selection."""
        flow = create_test_flow()
        self.create_provider(flow, redirect_uri="http://localhost")
        user = create_test_admin_user()
        stale_user = create_test_admin_user("stale-user")
        remember_live_accounts(self, user)
        session = Session.objects.get(session_key=self.client.session.session_key)
        self.client.cookies[COOKIE_NAME_KNOWN_ACCOUNTS] = dumps(
            [
                {"uid": user.uuid.hex, "session": session.session_key},
                {"uid": stale_user.uuid.hex, "session": "missing"},
            ]
        )
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "response_mode": "form_post",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "http://localhost",
            },
        )
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(challenge_response.json()["component"], "ak-stage-autosubmit")

    def test_account_selection_switch_requests_authentication(self):
        """Test selecting a remembered non-current account runs the switch flow."""
        flow = create_test_flow()
        account_flow, _, _ = create_test_account_selection_flow()
        self.create_provider(flow)
        user = create_test_admin_user()
        other_user = create_test_admin_user("other-user")
        remember_live_accounts(self, user, other_user)
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "foo://localhost",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(account_flow.slug, response.url)
        self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": account_flow.slug})
        )
        switch_response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": account_flow.slug}),
            data=json_dumps(
                {
                    "component": "ak-stage-account-selection",
                    "action": "switch",
                    "selected_account": other_user.uuid.hex,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(switch_response.status_code, 302)
        switch_response = self.client.get(switch_response.url)
        self.assertEqual(switch_response.json()["component"], "xak-flow-redirect")
        redirect = switch_response.json()["to"]
        parsed = parse_qs(urlparse(redirect).query)
        self.assertEqual(parsed["login_hint"], [other_user.email])
        self.assertEqual(parsed["account_uid"], [other_user.uuid.hex])
        self.assertEqual(urlparse(redirect).path, reverse("authentik_providers_oauth2:authorize"))

    def test_account_selection_login_requests_authentication(self):
        """Test using another account restarts authorization with normal OAuth parameters."""
        flow = create_test_flow()
        account_flow, _, _ = create_test_account_selection_flow()
        self.create_provider(flow)
        self.client.force_login(create_test_admin_user())
        current_session_key = self.client.session.session_key
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "foo://localhost",
                "prompt": PROMPT_SELECT_ACCOUNT,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(account_flow.slug, response.url)
        self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": account_flow.slug})
        )
        login_response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": account_flow.slug}),
            data=json_dumps(
                {
                    "component": "ak-stage-account-selection",
                    "action": "login",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(login_response.json()["component"], "xak-flow-redirect")
        self.assertIn(settings.SESSION_COOKIE_NAME, login_response.cookies)
        self.assertNotEqual(
            login_response.cookies[settings.SESSION_COOKIE_NAME].value,
            current_session_key,
        )
        redirect = login_response.json()["to"]
        parsed = parse_qs(urlparse(redirect).query)
        self.assertEqual(
            urlparse(redirect).path,
            reverse("authentik_flows:default-authentication"),
        )
        self.assertNotIn(QS_ADD_ACCOUNT, parsed)
        authorize_url = parsed["next"][0]
        authorize_query = parse_qs(urlparse(authorize_url).query)
        self.assertEqual(authorize_query["client_id"], ["test"])
        self.assertEqual(authorize_query["prompt"], [PROMPT_SELECT_ACCOUNT])
        self.assertNotIn("query", authorize_query)

    def test_prompt_select_account_ignores_login_hint(self):
        """Test prompt=select_account suggests but doesn't auto-select the login_hint user."""
        flow = create_test_flow()
        account_flow, _, _ = create_test_account_selection_flow()
        self.create_provider(flow, redirect_uri="http://localhost")
        user = create_test_admin_user()
        other_user = create_test_admin_user("other-user")
        remember_live_accounts(self, user, other_user)
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "http://localhost",
                "prompt": PROMPT_SELECT_ACCOUNT,
                QS_LOGIN_HINT: other_user.email,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(account_flow.slug, response.url)
        plan = self.client.session.get(SESSION_KEY_PLAN)
        self.assertNotIn(PLAN_CONTEXT_PENDING_USER_IDENTIFIER, plan.context)
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": account_flow.slug})
        )
        accounts = challenge_response.json()["accounts"]
        self.assertEqual(accounts[0]["username"], other_user.username)
        self.assertTrue(accounts[0]["is_hint"])

    def test_prompt_none_select_account(self):
        """Test prompt=none and prompt=select_account return account_selection_required"""
        flow = create_test_flow()
        self.create_provider(flow, redirect_uri="http://localhost")
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
