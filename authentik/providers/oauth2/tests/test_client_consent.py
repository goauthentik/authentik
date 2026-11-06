"""Test consent, policy context and session logins isolated by client within a provider"""

from dataclasses import asdict
from json import dumps
from unittest.mock import Mock, patch

from django.urls import reverse
from django.utils import timezone
from requests import Response

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowStageBinding
from authentik.flows.tests import _FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.client import (
    LegacyClientAdapter,
    OAuthClientContext,
    OAuthClientResolver,
    ProviderSelector,
)
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    GrantType,
    OAuth2LogoutMethod,
    OAuth2Provider,
    OAuth2SessionLogin,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.test_client_bound_grants import (
    CLIENT_A,
    CLIENT_B,
    REDIRECT_A,
    REDIRECT_B,
    SyntheticAdapter,
    synthetic_client,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.authorize import (
    PLAN_CONTEXT_OAUTH_CLIENT,
    AuthorizationFlowInitView,
    OAuthAuthorizationParams,
)
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent
from authentik.stages.consent.stage import PLAN_CONTEXT_CONSENT_CLIENT


class FreshSelector(ProviderSelector):
    """Selects one provider, loaded from the database for every request like the legacy
    selector, so that nothing cached on a test's instance ends up in flow plans"""

    def __init__(self, provider: OAuth2Provider):
        self.pk = provider.pk

    def select(self, request, client_id):
        return OAuth2Provider.objects.get(pk=self.pk)


class TestClientConsent(_FlowTestCase, OAuthTestCase):
    """Consent and authorization flow state are kept per client"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.flow = create_test_flow()
        FlowStageBinding.objects.create(
            target=self.flow,
            stage=ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.PERMANENT),
            order=0,
        )
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            grant_types=[GrantType.AUTHORIZATION_CODE],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_A)],
            signing_key=self.keypair,
        )
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(managed="goauthentik.io/providers/oauth2/scope-openid")
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.executor = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        resolver = OAuthClientResolver(
            FreshSelector(self.provider), [LegacyClientAdapter(), SyntheticAdapter()]
        )
        patcher = patch.object(
            AuthorizationFlowInitView, "get_client_resolver", return_value=resolver
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def authorize(self, client_id: str, redirect_uri: str, **params):
        """Start an authorization request, which plans the authorization flow"""
        return self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": "openid",
                "state": generate_id(),
                **params,
            },
        )

    def challenge(self) -> dict:
        """Current stage of the authorization flow, which must be the consent prompt"""
        response = self.client.get(self.executor)
        return self.assertStageResponse(response, component="ak-stage-consent")

    def accept(self, challenge: dict):
        """Accept a consent prompt, following the executor to the flow's next challenge"""
        return self.client.post(
            self.executor,
            data=dumps({"token": challenge["token"]}),
            content_type="application/json",
            follow=True,
        )

    def consent(self, client_id: str, redirect_uri: str) -> AuthorizationCode:
        """Authorize `client_id`, accepting the consent prompt, which must be shown"""
        self.authorize(client_id, redirect_uri)
        self.assertRedirectsTo(self.accept(self.challenge()), redirect_uri)
        return AuthorizationCode.objects.filter(user=self.user).order_by("-expires").first()

    def assertRedirectsTo(self, response, redirect_uri: str):
        """The flow finished by sending the user back to `redirect_uri`"""
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["component"], "xak-flow-redirect")
        self.assertTrue(body["to"].startswith(redirect_uri), body["to"])

    def assertRemembered(self, client_id: str, redirect_uri: str):
        """Authorizing `client_id` again completes without a consent prompt"""
        self.authorize(client_id, redirect_uri)
        self.assertRedirectsTo(self.client.get(self.executor, follow=True), redirect_uri)

    def test_registered_client_consent_unchanged(self):
        """The registered client's consent is given to the application, as before"""
        code = self.consent(self.provider.client_id, REDIRECT_A)
        self.assertTrue(code.is_bound_to_registered_client())
        consent = UserConsent.objects.get(user=self.user, application=self.app)
        self.assertIsNone(consent.client_id)
        self.assertIsNone(consent.resource)
        self.assertIsNone(consent.binding_hash)
        self.assertRemembered(self.provider.client_id, REDIRECT_A)

    def test_registered_client_challenge_unchanged(self):
        """The registered client's consent prompt has no client fields"""
        self.authorize(self.provider.client_id, REDIRECT_A)
        challenge = self.challenge()
        for field in ("client_id", "client_name", "redirect_host"):
            self.assertNotIn(field, challenge)
        self.assertNotIn(PLAN_CONTEXT_CONSENT_CLIENT, self.get_flow_plan().context)

    def test_client_consent_recorded_and_shown(self):
        """Consent for another client is recorded for that client, which the prompt names"""
        self.authorize(CLIENT_A, REDIRECT_A)
        challenge = self.challenge()
        self.assertEqual(challenge["client_id"], CLIENT_A)
        # The code is delivered to another host than the client identifier's
        self.assertEqual(challenge["redirect_host"], "127.0.0.1")
        self.assertRedirectsTo(self.accept(challenge), REDIRECT_A)
        code = AuthorizationCode.objects.get(user=self.user)
        self.assertEqual(code.client_id, CLIENT_A)
        consent = UserConsent.objects.get(user=self.user, application=self.app)
        self.assertEqual(consent.client_id, CLIENT_A)
        self.assertIsNone(consent.resource)
        self.assertRemembered(CLIENT_A, REDIRECT_A)

    def test_application_consent_never_authorizes_client(self):
        """Consent given for the registered client does not authorize another client"""
        self.consent(self.provider.client_id, REDIRECT_A)
        self.authorize(CLIENT_A, REDIRECT_A)
        self.assertEqual(self.challenge()["client_id"], CLIENT_A)

    def test_client_consent_never_authorizes_others(self):
        """Consent for client A authorizes neither client B nor the registered client"""
        self.consent(CLIENT_A, REDIRECT_A)
        self.authorize(CLIENT_B, REDIRECT_B)
        self.assertEqual(self.challenge()["client_id"], CLIENT_B)
        self.authorize(self.provider.client_id, REDIRECT_A)
        self.assertNotIn("client_id", self.challenge())

    def test_scope_expansion_prompts(self):
        """Requesting more scopes than a client was granted prompts again"""
        self.provider.property_mappings.add(
            ScopeMapping.objects.get(managed="goauthentik.io/providers/oauth2/scope-email")
        )
        self.consent(CLIENT_A, REDIRECT_A)
        self.authorize(CLIENT_A, REDIRECT_A, scope="openid email")
        challenge = self.challenge()
        self.assertEqual([perm["id"] for perm in challenge["additional_permissions"]], ["email"])

    def test_consent_for_one_client_cannot_complete_another(self):
        """Starting a second authorization in the same session replaces the plan, and consent
        accepted on the first client's prompt cannot complete the second client's flow"""
        self.authorize(CLIENT_A, REDIRECT_A)
        challenge_a = self.challenge()
        self.authorize(CLIENT_B, REDIRECT_B)
        response = self.accept(challenge_a)
        self.assertStageResponse(response, component="ak-stage-consent")
        self.assertFalse(UserConsent.objects.filter(user=self.user).exists())
        self.assertFalse(AuthorizationCode.objects.filter(user=self.user).exists())
        # The prompt shown now is client B's, and completes client B's flow only
        challenge_b = self.challenge()
        self.assertEqual(challenge_b["client_id"], CLIENT_B)
        self.assertRedirectsTo(self.accept(challenge_b), REDIRECT_B)
        code = AuthorizationCode.objects.get(user=self.user)
        self.assertEqual(code.client_id, CLIENT_B)
        self.assertEqual(code.redirect_uri, REDIRECT_B)
        self.assertEqual(
            list(UserConsent.objects.filter(user=self.user).values_list("client_id", flat=True)),
            [CLIENT_B],
        )

    def test_flow_round_trip_keeps_client(self):
        """The client survives storing the plan in the session"""
        self.authorize(CLIENT_A, REDIRECT_A)
        plan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_OAUTH_CLIENT].client_id, CLIENT_A)
        self.assertEqual(plan.context[PLAN_CONTEXT_CONSENT_CLIENT].client_id, CLIENT_A)

    def test_client_in_policy_context(self):
        """Application access policies can tell clients apart"""
        policy = ExpressionPolicy.objects.create(
            name=generate_id(),
            expression=f"return request.context['oauth_client'].client_id != {CLIENT_B!r}",
        )
        PolicyBinding.objects.create(target=self.app, policy=policy, order=0)
        self.authorize(CLIENT_A, REDIRECT_A)
        self.assertEqual(self.challenge()["client_id"], CLIENT_A)
        self.authorize(CLIENT_B, REDIRECT_B)
        # Access was denied before planning, so client A's flow is still the current one
        self.assertEqual(
            self.get_flow_plan().context[PLAN_CONTEXT_OAUTH_CLIENT].client_id, CLIENT_A
        )
        self.assertFalse(AuthorizationCode.objects.filter(user=self.user).exists())

    def test_redirect_host_hidden_when_same_as_client(self):
        """The redirect host is only shown when it differs from the client's host"""
        client = synthetic_client(self.provider, "https://127.0.0.1/client.json")
        params = Mock(redirect_uri=REDIRECT_A)
        params.bound_client.return_value = client
        result = OAuthAuthorizationParams.consent_client(params)
        self.assertEqual(result.client_id, client.client_id)
        self.assertIsNone(result.redirect_host)
        params.redirect_uri = "com.example.app:/callback"
        self.assertEqual(
            OAuthAuthorizationParams.consent_client(params).redirect_host, "com.example.app"
        )


class TestClientSessionLogins(OAuthTestCase):
    """Session logins are recorded per client; logout only reaches the registered client"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_A)],
            signing_key=self.keypair,
            logout_uri="http://testserver/backchannel_logout",
            logout_method=OAuth2LogoutMethod.BACKCHANNEL,
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=self.provider)
        self.session = Session.objects.create(
            session_key=generate_id(), last_ip="255.255.255.255", last_user_agent=""
        )
        self.auth_session = AuthenticatedSession.objects.create(
            session=self.session, user=self.user
        )

    def record(self, client_id: str | None) -> AccessToken:
        """Record a login of `client_id`, the registered client when None"""
        token = AccessToken(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid",
        )
        if client_id:
            token.bind_client(synthetic_client(self.provider, client_id))
        else:
            token.bind_client(OAuthClientContext.for_provider(self.provider))
        id_token = IDToken(iss="http://testserver", sub=str(self.user.uid))
        token._id_token = dumps(asdict(id_token))
        token.save()
        OAuth2SessionLogin.record(token, id_token)
        return token

    def test_logins_recorded_per_client(self):
        """Each client gets its own login; the registered client's has no client ID"""
        self.record(None)
        self.record(CLIENT_A)
        self.record(CLIENT_A)
        self.record(CLIENT_B)
        logins = OAuth2SessionLogin.objects.filter(session=self.auth_session)
        self.assertEqual(
            sorted(logins.values_list("client_id", flat=True), key=lambda x: x or ""),
            [None, CLIENT_A, CLIENT_B],
        )
        self.assertEqual(logins.filter(OAuth2SessionLogin.registered_client_q()).count(), 1)

    @patch("authentik.providers.oauth2.tasks.get_http_session")
    def test_backchannel_logout_only_registered_client(self, mock_get_session):
        """Deleting the session sends one back-channel logout, for the registered client"""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        response = Mock(spec=Response)
        response.status_code = 200
        mock_session.post.return_value = response
        self.record(None)
        self.record(CLIENT_A)

        self.session.delete()

        mock_session.post.assert_called_once()
        self.assertEqual(mock_session.post.call_args.args[0], self.provider.logout_uri)

    @patch("authentik.providers.oauth2.tasks.get_http_session")
    def test_backchannel_logout_skips_client_logins(self, mock_get_session):
        """A session only logged in by another client sends no back-channel logout"""
        self.record(CLIENT_A)

        self.session.delete()

        mock_get_session.return_value.post.assert_not_called()
