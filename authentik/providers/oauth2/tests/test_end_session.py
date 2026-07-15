"""Test OAuth2 End Session (RP-Initiated Logout) implementation"""

from django.test import RequestFactory
from django.urls import reverse
from django.utils.timezone import now

from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding, in_memory_stage
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.models import (
    AccessToken,
    OAuth2LogoutMethod,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RedirectURIType,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.end_session import EndSessionView
from authentik.stages.dummy.stage import DummyStageView
from authentik.stages.user_login.models import UserLoginStage
from authentik.stages.user_logout.models import UserLogoutStage
from authentik.stages.user_logout.stage import flow_pre_user_logout


class TestEndSessionView(OAuthTestCase):
    """Test EndSessionView validation"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.invalidation_flow = create_test_flow()
        self.app = Application.objects.create(name=generate_id(), slug="test-app")
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            invalidation_flow=self.invalidation_flow,
            redirect_uris=[
                RedirectURI(
                    RedirectURIMatchingMode.STRICT,
                    "http://testserver/callback",
                    RedirectURIType.AUTHORIZATION,
                ),
                RedirectURI(
                    RedirectURIMatchingMode.STRICT,
                    "http://testserver/logout",
                    RedirectURIType.LOGOUT,
                ),
                RedirectURI(
                    RedirectURIMatchingMode.REGEX,
                    r"https://.*\.example\.com/logout",
                    RedirectURIType.LOGOUT,
                ),
            ],
        )
        self.app.provider = self.provider
        self.app.save()
        # Ensure brand has an invalidation flow
        self.brand = create_test_brand()
        self.brand.flow_invalidation = self.invalidation_flow
        self.brand.save()

    def _id_token_hint(self, host: str) -> str:
        """Issue a valid id_token_hint for the test provider under the given host."""
        return self.provider.encode(
            {
                "iss": f"http://{host}/application/o/{self.app.slug}/",
                "aud": self.provider.client_id,
                "sub": str(self.user.pk),
            }
        )

    def test_post_logout_redirect_uri_strict_match(self):
        """Test strict URI matching redirects to flow"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {
                "post_logout_redirect_uri": "http://testserver/logout",
                "id_token_hint": self._id_token_hint(self.brand.domain),
            },
            HTTP_HOST=self.brand.domain,
        )
        # Should redirect to the invalidation flow
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.invalidation_flow.slug, response.url)

    def test_post_logout_redirect_uri_strict_no_match(self):
        """Test strict URI not matching returns an error and does not start logout flow.

        Required by OIDC RP-Initiated Logout 1.0: on an unregistered
        post_logout_redirect_uri, the OP MUST NOT redirect and MUST NOT proceed with
        logout that targets the RP.
        """
        self.client.force_login(self.user)
        invalid_uri = "http://testserver/other"
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {
                "post_logout_redirect_uri": invalid_uri,
                "id_token_hint": self._id_token_hint(self.brand.domain),
            },
            HTTP_HOST=self.brand.domain,
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(invalid_uri, response.content.decode())

    def test_post_logout_redirect_uri_regex_match(self):
        """Test regex URI matching redirects to flow"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {
                "post_logout_redirect_uri": "https://app.example.com/logout",
                "id_token_hint": self._id_token_hint(self.brand.domain),
            },
            HTTP_HOST=self.brand.domain,
        )
        # Should redirect to the invalidation flow
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.invalidation_flow.slug, response.url)

    def test_post_logout_redirect_uri_regex_no_match(self):
        """Test regex URI not matching returns an error and does not start logout flow."""
        self.client.force_login(self.user)
        invalid_uri = "https://malicious.com/logout"
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {
                "post_logout_redirect_uri": invalid_uri,
                "id_token_hint": self._id_token_hint(self.brand.domain),
            },
            HTTP_HOST=self.brand.domain,
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(invalid_uri, response.content.decode())

    def test_state_parameter_appended_to_uri(self):
        """Test state parameter is appended to validated redirect URI"""
        factory = RequestFactory()
        request = factory.get(
            "/end-session/",
            {
                "post_logout_redirect_uri": "http://testserver/logout",
                "state": "test-state-123",
                "id_token_hint": self._id_token_hint("testserver"),
            },
        )
        request.user = self.user
        request.brand = self.brand

        view = EndSessionView()
        view.request = request
        view.kwargs = {"application_slug": self.app.slug}
        view.resolve_provider_application()
        view.validate()

        self.assertIn("state=test-state-123", view.post_logout_redirect_uri)

    def test_post_method(self):
        """Test POST requests work same as GET"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {
                "post_logout_redirect_uri": "http://testserver/logout",
                "state": "xyz789",
                "id_token_hint": self._id_token_hint(self.brand.domain),
            },
            HTTP_HOST=self.brand.domain,
        )
        self.assertEqual(response.status_code, 302)

    def _brand_authentication_flow(self) -> None:
        """Give the brand a usable authentication flow.

        Without one, `handle_no_permission` raises Http404 instead of planning a flow, which
        would mask the regression these tests guard against.
        """
        authentication_flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        FlowStageBinding.objects.create(
            target=authentication_flow,
            stage=UserLoginStage.objects.create(name=generate_id()),
            order=0,
        )
        self.brand.flow_authentication = authentication_flow
        self.brand.save()

    def test_active_flow_plan_returns_early(self):
        """An end-session request during an active flow plan must not touch that plan.

        Front-channel logout iframes reach this endpoint while the invalidation flow is
        still running. Falling through to PolicyAccessView would plan an authentication
        flow and overwrite SESSION_KEY_PLAN.
        """
        self._brand_authentication_flow()
        plan = FlowPlan(flow_pk=self.invalidation_flow.pk.hex)
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            HTTP_HOST=self.brand.domain,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session[SESSION_KEY_PLAN].flow_pk, plan.flow_pk)

    def test_frontchannel_iframe_callback_preserves_injected_stages(self):
        """Stages injected into the logout plan survive the iframe's end-session hit.

        Regression test: the hidden logout iframe navigates to end-session after
        UserLogoutStage has already logged the user out, so the request is anonymous.
        Planning an authentication flow there replaces SESSION_KEY_PLAN, and the executor
        then discards the invalidation plan and re-plans it from the flow's bindings. Stages
        injected by `flow_pre_user_logout` receivers exist only in memory, so they are lost.
        """
        self._brand_authentication_flow()
        logout_flow = create_test_flow(FlowDesignation.INVALIDATION)
        FlowStageBinding.objects.create(
            target=logout_flow,
            stage=UserLogoutStage.objects.create(name=generate_id()),
            order=0,
        )
        self.brand.flow_invalidation = logout_flow
        self.brand.save()

        self.provider.logout_method = OAuth2LogoutMethod.FRONTCHANNEL
        self.provider.logout_uri = "https://rp.example.com/logout"
        self.provider.invalidation_flow = logout_flow
        self.provider.save()

        # Mirror a provider signal injecting a front-channel logout stage after the iframe
        # stage, the way the SAML native logout and SAML source SLO stages do.
        def inject_stage(sender, executor, **_):
            executor.plan.append_stage(
                in_memory_stage(DummyStageView, name="injected", throw_error=False)
            )

        flow_pre_user_logout.connect(inject_stage, weak=False)
        self.addCleanup(flow_pre_user_logout.disconnect, inject_stage)

        self.client.force_login(self.user)
        session = Session.objects.filter(session_key=self.client.session.session_key).first()
        auth_session = AuthenticatedSession.objects.filter(session=session).first()
        AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=auth_session,
            token=generate_id(),
            _scope="openid",
            auth_time=now(),
            expires=now() + timedelta_from_string("days=1"),
        )

        executor = reverse("authentik_api:flow-executor", kwargs={"flow_slug": logout_flow.slug})
        response = self.client.get(executor, follow=True)
        self.assertEqual(response.json()["component"], "ak-provider-iframe-logout")

        # The hidden logout iframe navigates back into authentik. The user is anonymous now.
        self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
        )
        self.assertEqual(
            self.client.session[SESSION_KEY_PLAN].flow_pk,
            logout_flow.pk.hex,
            "end-session replaced the in-flight invalidation plan",
        )

        # The stage injected after the iframe logout stage must still run.
        self.client.post(
            executor,
            data={"component": "ak-provider-iframe-logout"},
            content_type="application/json",
        )
        response = self.client.get(executor)
        self.assertEqual(response.json()["component"], "ak-stage-dummy")


class TestEndSessionAPI(OAuthTestCase):
    """Test End Session API functionality"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_post_logout_redirect_uris_create(self):
        """Test creating provider with post_logout redirect_uris"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/callback",
                        "redirect_uri_type": "authorization",
                    },
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/logout",
                        "redirect_uri_type": "logout",
                    },
                    {
                        "matching_mode": "regex",
                        "url": "https://.*\\.example\\.com/logout",
                        "redirect_uri_type": "logout",
                    },
                ],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        provider_data = response.json()
        post_logout_uris = [
            u for u in provider_data["redirect_uris"] if u["redirect_uri_type"] == "logout"
        ]
        self.assertEqual(len(post_logout_uris), 2)

    def test_post_logout_redirect_uris_invalid_regex(self):
        """Test that invalid regex patterns are rejected"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/callback",
                        "redirect_uri_type": "authorization",
                    },
                    {
                        "matching_mode": "regex",
                        "url": "**invalid**",
                        "redirect_uri_type": "logout",
                    },
                ],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("redirect_uris", response.json())

    def test_post_logout_redirect_uris_update(self):
        """Test updating redirect_uris with logout type"""
        # First create a provider
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[
                RedirectURI(
                    RedirectURIMatchingMode.STRICT,
                    "http://testserver/callback",
                    RedirectURIType.AUTHORIZATION,
                ),
            ],
        )

        # Update with post_logout redirect URIs
        response = self.client.patch(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider.pk}),
            data={
                "redirect_uris": [
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/callback",
                        "redirect_uri_type": "authorization",
                    },
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/logout",
                        "redirect_uri_type": "logout",
                    },
                ],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify the update
        provider.refresh_from_db()
        self.assertEqual(len(provider.post_logout_redirect_uris), 1)
        self.assertEqual(provider.post_logout_redirect_uris[0].url, "http://testserver/logout")
