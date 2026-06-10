"""Test OAuth authorize user selection behavior."""

from json import dumps as json_dumps
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse

from authentik.common.oauth.constants import PROMPT_SELECT_ACCOUNT, QS_LOGIN_HINT
from authentik.core.models import Application
from authentik.core.tests.user_selection import (
    create_browser_session,
    create_test_user_selection_flow,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.core.user_selection import QS_USER_UID, append_user_selection_hint
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


class TestAuthorizeUserSelection(OAuthTestCase):
    """Test OAuth authorize user selection behavior."""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def create_provider(self, flow, redirect_uri: str = "foo://localhost") -> OAuth2Provider:
        """Create an OAuth2 provider for user-selection authorize tests."""
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

    def test_append_user_selection_hint_preserves_repeated_params(self):
        """Test user-selection hints don't collapse repeated authorization params."""
        user = create_test_admin_user()
        authorize_url = (
            reverse("authentik_providers_oauth2:authorize")
            + "?scope=openid&resource=one&resource=two"
        )

        hinted_url = append_user_selection_hint(authorize_url, user)

        parsed = parse_qs(urlparse(hinted_url).query)
        self.assertEqual(parsed["resource"], ["one", "two"])
        self.assertEqual(parsed[QS_USER_UID], [user.uuid.hex])
        self.assertEqual(parsed[QS_LOGIN_HINT], [user.email])

    def test_prompt_select_account(self):
        """Test prompt=select_account parsing."""
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
        """Test prompt=select_account is advertised in provider metadata."""
        provider = self.create_provider(
            create_test_flow(),
            redirect_uri="http://local.invalid/Foo",
        )
        view = ProviderInfoView()
        view.request = self.factory.get("/")
        self.assertIn(PROMPT_SELECT_ACCOUNT, view.get_info(provider)["prompt_values_supported"])

    def test_prompt_select_account_shows_user_selection(self):
        """Test prompt=select_account starts the brand user selection flow."""
        flow = create_test_flow()
        user_selection_flow, _ = create_test_user_selection_flow()
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
        self.assertIn(user_selection_flow.slug, response.url)
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": user_selection_flow.slug})
        )
        self.assertEqual(challenge_response.json()["component"], "ak-stage-user-selection")
        self.assertEqual(challenge_response.json()["accounts"][0]["username"], user.username)

    def test_multiple_sessions_show_user_selection_by_default(self):
        """Test multiple live browser logins show the user selection stage."""
        flow = create_test_flow()
        user_selection_flow, _ = create_test_user_selection_flow()
        self.create_provider(flow)
        user = create_test_admin_user()
        other_user = create_test_admin_user("other-user")
        self.client.force_login(user)
        create_browser_session(self, other_user)

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
        self.assertIn(user_selection_flow.slug, response.url)
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": user_selection_flow.slug})
        )
        self.assertEqual(
            [account["username"] for account in challenge_response.json()["accounts"]],
            [user.username, other_user.username],
        )

    def test_selecting_other_user_switches_session(self):
        """Test selecting another live login switches sessions and returns to authorize."""
        flow = create_test_flow()
        user_selection_flow, _ = create_test_user_selection_flow()
        self.create_provider(flow)
        user = create_test_admin_user()
        other_user = create_test_admin_user("other-user")
        self.client.force_login(user)
        target = create_browser_session(self, other_user)
        current_session_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value

        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": generate_id(),
                "redirect_uri": "foo://localhost",
            },
        )
        self.assertIn(user_selection_flow.slug, response.url)
        self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": user_selection_flow.slug})
        )
        selection_response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": user_selection_flow.slug}),
            data=json_dumps(
                {
                    "component": "ak-stage-user-selection",
                    "action": "continue",
                    "selected_user": other_user.uuid.hex,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(selection_response.json()["component"], "xak-flow-redirect")
        redirect = selection_response.json()["to"]
        self.assertEqual(urlparse(redirect).path, reverse("authentik_providers_oauth2:authorize"))
        authorize_query = parse_qs(urlparse(redirect).query)
        self.assertEqual(authorize_query[QS_USER_UID], [other_user.uuid.hex])
        self.assertEqual(
            self.client.cookies[settings.SESSION_COOKIE_NAME].value,
            target.session.session_key,
        )
        self.assertNotEqual(
            self.client.cookies[settings.SESSION_COOKIE_NAME].value,
            current_session_cookie,
        )
        me_response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(me_response.json()["user"]["username"], other_user.username)
        # Returning to authorize with the selected user must not re-prompt for selection
        response = self.client.get(redirect)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(user_selection_flow.slug, response.url)

    def test_signed_out_browser_is_offered_selection(self):
        """Test a signed-out browser with live logins is sent to the chooser, not login."""
        flow = create_test_flow()
        user_selection_flow, _ = create_test_user_selection_flow()
        self.create_provider(flow)
        other_user = create_test_admin_user("other-user")
        create_browser_session(self, other_user)

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
        self.assertIn(user_selection_flow.slug, response.url)

    def test_prompt_select_account_ignores_login_hint(self):
        """Test prompt=select_account suggests but doesn't auto-select the login_hint user."""
        flow = create_test_flow()
        user_selection_flow, _ = create_test_user_selection_flow()
        self.create_provider(flow, redirect_uri="http://localhost")
        user = create_test_admin_user()
        other_user = create_test_admin_user("other-user")
        self.client.force_login(user)
        create_browser_session(self, other_user)

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
        self.assertIn(user_selection_flow.slug, response.url)
        plan = self.client.session.get(SESSION_KEY_PLAN)
        self.assertNotIn(PLAN_CONTEXT_PENDING_USER_IDENTIFIER, plan.context)
        challenge_response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": user_selection_flow.slug})
        )
        accounts = challenge_response.json()["accounts"]
        self.assertEqual(accounts[0]["username"], other_user.username)
        self.assertTrue(accounts[0]["is_hint"])

    def test_prompt_none_select_account(self):
        """Test prompt=none and prompt=select_account return account_selection_required."""
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
