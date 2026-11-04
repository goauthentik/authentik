"""OAuth Source tests"""

from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.models import Application, User
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)
from authentik.providers.oauth2.utils import pkce_s256_challenge
from authentik.sources.oauth.api.source import OAuthSourceSerializer
from authentik.sources.oauth.clients.oauth2 import SESSION_KEY_OAUTH_PKCE
from authentik.sources.oauth.models import OAuthSource, PKCEMethod
from authentik.stages.identification.models import IdentificationStage, UserFields


class TestOAuthSource(APITestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_api_read(self):
        """Test reading a source"""
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse(
                "authentik_api:oauthsource-detail",
                kwargs={
                    "slug": self.source.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_api_validate(self):
        """Test API validation"""
        self.assertTrue(
            OAuthSourceSerializer(
                data={
                    "name": "foo",
                    "slug": "bar",
                    "provider_type": "google",
                    "consumer_key": "foo",
                    "consumer_secret": "foo",
                    "oidc_well_known_url": "",
                    "oidc_jwks_url": "",
                }
            ).is_valid()
        )
        self.assertFalse(
            OAuthSourceSerializer(
                data={
                    "name": "foo",
                    "slug": "bar",
                    "provider_type": "openidconnect",
                    "consumer_key": "foo",
                    "consumer_secret": "foo",
                }
            ).is_valid()
        )

    def test_api_validate_openid_connect(self):
        """Test API validation (with OIDC endpoints)"""
        openid_config = {
            "issuer": "foo",
            "authorization_endpoint": "http://mock/oauth/authorize",
            "token_endpoint": "http://mock/oauth/token",
            "userinfo_endpoint": "http://mock/oauth/userinfo",
            "jwks_uri": "http://mock/oauth/discovery/keys",
            "code_challenge_methods_supported": ["S256"],
        }
        jwks_config = {"keys": []}
        with Mocker() as mocker:
            url = "http://mock/.well-known/openid-configuration"
            mocker.get(url, json=openid_config)
            mocker.get(openid_config["jwks_uri"], json=jwks_config)
            serializer = OAuthSourceSerializer(
                instance=self.source,
                data={
                    "name": "foo",
                    "slug": "bar",
                    "provider_type": "openidconnect",
                    "consumer_key": "foo",
                    "consumer_secret": "foo",
                    "oidc_well_known_url": url,
                    "oidc_jwks_url": "",
                },
            )
            self.assertTrue(serializer.is_valid())
            self.assertEqual(
                serializer.validated_data["authorization_url"], "http://mock/oauth/authorize"
            )
            self.assertEqual(
                serializer.validated_data["access_token_url"], "http://mock/oauth/token"
            )
            self.assertEqual(serializer.validated_data["profile_url"], "http://mock/oauth/userinfo")
            self.assertEqual(
                serializer.validated_data["oidc_jwks_url"], "http://mock/oauth/discovery/keys"
            )
            self.assertEqual(serializer.validated_data["oidc_jwks"], jwks_config)
            self.assertEqual(serializer.validated_data["pkce"], PKCEMethod.S256)

    def test_api_validate_openid_connect_invalid(self):
        """Test API validation (with OIDC endpoints)"""
        openid_config = {}
        with Mocker() as mocker:
            url = "http://mock/.well-known/openid-configuration"
            mocker.get(url, json=openid_config)
            serializer = OAuthSourceSerializer(
                instance=self.source,
                data={
                    "name": "foo",
                    "slug": "bar",
                    "provider_type": "openidconnect",
                    "consumer_key": "foo",
                    "consumer_secret": "foo",
                    "authorization_url": "http://foo",
                    "access_token_url": "http://foo",
                    "profile_url": "http://foo",
                    "oidc_well_known_url": url,
                    "oidc_jwks_url": "",
                },
            )
            self.assertFalse(serializer.is_valid())

    def test_source_redirect_login_hint_user(self):
        """test redirect view with login hint"""
        user = User(email="foo@authentik.company")
        session = self.client.session
        plan = FlowPlan(generate_id())
        plan.context[PLAN_CONTEXT_PENDING_USER] = user
        session[SESSION_KEY_PLAN] = plan
        session.save()

        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
        )
        self.assertEqual(res.status_code, 302)
        qs = parse_qs(res.url)
        self.assertEqual(qs["login_hint"], ["foo@authentik.company"])

    def test_source_redirect_login_hint_user_identifier(self):
        """test redirect view with login hint"""
        session = self.client.session
        plan = FlowPlan(generate_id())
        plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = "foo@authentik.company"
        session[SESSION_KEY_PLAN] = plan
        session.save()

        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
        )
        self.assertEqual(res.status_code, 302)
        qs = parse_qs(res.url)
        self.assertEqual(qs["login_hint"], ["foo@authentik.company"])

    def test_source_redirect(self):
        """test redirect view"""
        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
        )
        self.assertEqual(res.status_code, 302)
        qs = parse_qs(res.url)

        session = self.client.session
        state = session[f"oauth-client-{self.source.name}-request-state"]

        self.assertEqual(qs["redirect_uri"], ["http://testserver/source/oauth/callback/test/"])
        self.assertEqual(qs["response_type"], ["code"])
        self.assertEqual(qs["state"], [state])
        self.assertEqual(qs["scope"], ["email openid profile"])

    def test_source_redirect_pkce(self):
        """test redirect view"""
        self.source.pkce = PKCEMethod.S256
        self.source.save()
        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
        )
        self.assertEqual(res.status_code, 302)
        qs = parse_qs(res.url)

        session = self.client.session
        state = session[f"oauth-client-{self.source.name}-request-state"]
        verifier = session[SESSION_KEY_OAUTH_PKCE]
        self.assertEqual(len(verifier), 128)
        challenge = pkce_s256_challenge(verifier)

        self.assertEqual(qs["redirect_uri"], ["http://testserver/source/oauth/callback/test/"])
        self.assertEqual(qs["response_type"], ["code"])
        self.assertEqual(qs["state"], [state])
        self.assertEqual(qs["scope"], ["email openid profile"])
        self.assertEqual(qs["code_challenge"], [challenge])
        self.assertEqual(qs["code_challenge_method"], ["S256"])

    def test_source_redirect_forward_query_parameters(self):
        """test redirect view forwards configured query parameters"""
        self.source.forward_query_parameters = "idphint,selected_idp"
        self.source.save()
        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
            + "?idphint=urn:mace:incommon:uiuc.edu&selected_idp=foo&other_param=bar"
        )
        self.assertEqual(res.status_code, 302)
        qs = parse_qs(res.url)
        self.assertEqual(qs["idphint"], ["urn:mace:incommon:uiuc.edu"])
        self.assertEqual(qs["selected_idp"], ["foo"])
        self.assertNotIn("other_param", qs)

    def test_source_redirect_forward_query_parameters_empty(self):
        """test redirect view with empty forward_query_parameters"""
        self.source.forward_query_parameters = ""
        self.source.save()
        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
            + "?idphint=urn:mace:incommon:uiuc.edu"
        )
        self.assertEqual(res.status_code, 302)
        qs = parse_qs(res.url)
        self.assertNotIn("idphint", qs)

    def test_source_redirect_forward_query_parameters_not_present(self):
        """test redirect view when configured param is not in request"""
        self.source.forward_query_parameters = "idphint"
        self.source.save()
        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
        )
        self.assertEqual(res.status_code, 302)
        qs = parse_qs(res.url)
        self.assertNotIn("idphint", qs)

    def test_source_redirect_forward_query_parameters_reserved(self):
        """test redirect view never forwards parameters set by authentik itself"""
        self.source.forward_query_parameters = "state,redirect_uri,scope,idphint"
        self.source.save()
        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
            + "?state=foo&redirect_uri=http://attacker.invalid&scope=bar&idphint=baz"
        )
        self.assertEqual(res.status_code, 302)
        qs = parse_qs(urlparse(res.url).query)
        self.assertNotEqual(qs["state"], ["foo"])
        self.assertNotEqual(qs["redirect_uri"], ["http://attacker.invalid"])
        self.assertNotIn("bar", qs["scope"][0])
        self.assertEqual(qs["idphint"], ["baz"])

    def test_api_validate_forward_query_parameters_reserved(self):
        """Test API validation rejects forwarding reserved parameters"""
        serializer = OAuthSourceSerializer(
            data={
                "name": "foo",
                "slug": "bar",
                "provider_type": "google",
                "consumer_key": "foo",
                "consumer_secret": "foo",
                "oidc_well_known_url": "",
                "oidc_jwks_url": "",
                "forward_query_parameters": "prompt, state,redirect_uri",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("forward_query_parameters", serializer.errors)

    def test_source_callback(self):
        """test callback view"""
        res = self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-callback",
                kwargs={"source_slug": self.source.slug},
            )
        )
        self.assertEqual(res.status_code, 302)


class TestOAuthSourceForwardQueryParametersFlow(APITestCase):
    """Test that forwarded query parameters survive the full path from a downstream
    OAuth2 /authorize request, through the authentication flow, to the upstream IdP"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="google",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            forward_query_parameters="prompt,idphint",
        )
        self.stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[UserFields.USERNAME],
        )
        self.stage.sources.set([self.source])
        self.authn_flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        FlowStageBinding.objects.create(target=self.authn_flow, stage=self.stage, order=0)
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            authorization_flow=create_test_flow(),
            authentication_flow=self.authn_flow,
            grant_types=[GrantType.AUTHORIZATION_CODE],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=self.provider)

    def _upstream_redirect(self, **authorize_params: str) -> dict[str, list[str]]:
        """Send a downstream /authorize request, follow it into the authentication flow,
        click the source's login button and return the query of the upstream redirect"""
        res = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": self.provider.client_id,
                "redirect_uri": "http://local.invalid",
                "scope": "openid",
                "state": generate_id(),
                **authorize_params,
            },
        )
        # Not logged in, so we're sent to the authentication flow interface
        self.assertEqual(res.status_code, 302)
        flow_url = urlparse(res.url)
        self.assertEqual(
            flow_url.path,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.authn_flow.slug}),
        )
        # The flow interface passes its own query string to the executor as ?query=
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.authn_flow.slug}),
            data={"query": flow_url.query},
        )
        self.assertEqual(res.status_code, 200)
        sources = res.json()["sources"]
        self.assertEqual(len(sources), 1)
        # Clicking the source's login button
        res = self.client.get(sources[0]["challenge"]["to"])
        self.assertEqual(res.status_code, 302)
        upstream_url = urlparse(res.url)
        self.assertEqual(upstream_url.netloc, "accounts.google.com")
        return parse_qs(upstream_url.query)

    def test_prompt_select_account(self):
        """prompt=select_account is not handled by authentik itself, but must still reach
        the upstream IdP unchanged"""
        qs = self._upstream_redirect(prompt="select_account")
        self.assertEqual(qs["prompt"], ["select_account"])

    def test_prompt_multiple_values(self):
        """Space-separated prompt values are forwarded as-is"""
        qs = self._upstream_redirect(prompt="login select_account")
        self.assertEqual(qs["prompt"], ["login select_account"])

    def test_idphint(self):
        """Arbitrary parameters such as idphint are forwarded"""
        qs = self._upstream_redirect(idphint="urn:mace:incommon:uiuc.edu")
        self.assertEqual(qs["idphint"], ["urn:mace:incommon:uiuc.edu"])
        self.assertNotIn("prompt", qs)

    def test_not_configured(self):
        """Parameters are not forwarded when not listed on the source"""
        self.source.forward_query_parameters = ""
        self.source.save()
        qs = self._upstream_redirect(prompt="select_account")
        self.assertNotIn("prompt", qs)
