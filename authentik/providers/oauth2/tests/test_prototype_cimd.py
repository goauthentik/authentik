"""PROTOTYPE (01b), never merge: smoke test the CIMD prototype path"""

from tempfile import NamedTemporaryFile

from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from jwt import decode
from requests_mock import Mocker

from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    PKCE_METHOD_S256,
    SCOPE_BOUND_KEY,
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.errors import RedirectUriError
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientType,
    GrantType,
    OAuth2DynamicClientRegistration,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)
from authentik.providers.oauth2.prototype_cimd import METADATA_KIND, _cache, scoped_resolver
from authentik.providers.oauth2.tests.test_dpop import DPoPProofBuilder
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.utils import pkce_s256_challenge
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams

CLIENT_ID = "https://client.invalid/oauth/metadata.json"
DOCUMENT = {
    "client_id": CLIENT_ID,
    "client_name": "Test MCP client",
    "redirect_uris": ["http://127.0.0.1:33418/callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
}


class TestPrototypeCIMD(OAuthTestCase):
    def setUp(self) -> None:
        super().setUp()
        _cache.clear()
        self.slug = generate_id()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_type=ClientType.PUBLIC,
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
            redirect_uris=[],
            signing_key=self.keypair,
        )
        Application.objects.create(name=generate_id(), slug=self.slug, provider=self.provider)
        self.log = NamedTemporaryFile(suffix=".jsonl")
        self.patches = [
            CONFIG.patch("cimd_prototype.applications", self.slug),
            CONFIG.patch("cimd_prototype.log", self.log.name),
        ]
        for patch in self.patches:
            patch.__enter__()

    def tearDown(self) -> None:
        for patch in reversed(self.patches):
            patch.__exit__(None, None, None)
        self.log.close()
        super().tearDown()

    def test_discovery(self):
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2_root:providers-oauth2-authorization-server-metadata",
                kwargs={"application_slug": self.slug},
            )
        )
        body = response.json()
        self.assertTrue(body["client_id_metadata_document_supported"])
        self.assertTrue(body["authorization_endpoint"].endswith(f"/{self.slug}/authorize/"))
        self.assertTrue(body["token_endpoint"].endswith(f"/{self.slug}/token/"))

    def test_discovery_omits_scoped_dcr_but_preserves_legacy(self):
        OAuth2DynamicClientRegistration.objects.create(
            provider=self.provider,
            override_authorization_flow=self.provider.authorization_flow,
        )
        for route in (
            "authentik_providers_oauth2:provider-info",
            "authentik_providers_oauth2_root:providers-oauth2-authorization-server-metadata",
        ):
            with self.subTest(route=route):
                url = reverse(route, kwargs={"application_slug": self.slug})
                self.assertNotIn("registration_endpoint", self.client.get(url).json())
                with CONFIG.patch("cimd_prototype.applications", ""):
                    body = self.client.get(url).json()
                self.assertNotIn("client_id_metadata_document_supported", body)
                self.assertTrue(body["token_endpoint"].endswith("/application/o/token/"))
                self.assertIn("registration_endpoint", body)

    @Mocker()
    def test_code_and_refresh_client_audiences_and_dpop_targets(self, mock: Mocker):
        mock.get(CLIENT_ID, json=DOCUMENT)
        redirect_uri = DOCUMENT["redirect_uris"][0]
        self.provider.redirect_uris = [RedirectURI(RedirectURIMatchingMode.STRICT, redirect_uri)]
        self.provider.refresh_token_threshold = "seconds=0"
        self.provider.save()
        user = create_test_admin_user()
        scoped_path = reverse(
            "authentik_providers_oauth2:prototype-scoped-token",
            kwargs={"application_slug": self.slug},
        )
        shared_path = reverse("authentik_providers_oauth2:token")
        for path, client_id in (
            (scoped_path, CLIENT_ID),
            (scoped_path, self.provider.client_id),
            (shared_path, self.provider.client_id),
        ):
            for bound in (False, True):
                with self.subTest(path=path, client_id=client_id, bound=bound):
                    proof = DPoPProofBuilder()
                    verifier = generate_id(64)
                    scopes = [SCOPE_OPENID, SCOPE_OFFLINE_ACCESS]
                    if bound:
                        scopes.append(SCOPE_BOUND_KEY)
                    code = AuthorizationCode.objects.create(
                        code=generate_id(),
                        provider=self.provider,
                        user=user,
                        auth_time=timezone.now(),
                        scope=scopes,
                        code_challenge=pkce_s256_challenge(verifier),
                        code_challenge_method=PKCE_METHOD_S256,
                        dpop_jkt=proof.jkt if bound else None,
                    )
                    data = {
                        "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                        "client_id": client_id,
                        "code": code.code,
                        "code_verifier": verifier,
                        "redirect_uri": redirect_uri,
                    }
                    headers = {
                        "HTTP_HOST": "issuer.example:8443",
                        "HTTP_X_FORWARDED_PROTO": "https",
                        "HTTP_X_FORWARDED_HOST": "untrusted.example",
                    }
                    wrong_path = shared_path if path == scoped_path else scoped_path
                    for grant in (GRANT_TYPE_AUTHORIZATION_CODE, GRANT_TYPE_REFRESH_TOKEN):
                        with self.subTest(grant=grant):
                            if bound:
                                challenge = (
                                    pkce_s256_challenge(code.code)
                                    if grant == GRANT_TYPE_AUTHORIZATION_CODE
                                    else None
                                )
                                headers["HTTP_DPOP"] = proof.build(
                                    htu=f"https://issuer.example:8443{wrong_path}",
                                    c_s256=challenge,
                                    jti=generate_id(),
                                )
                                rejected = self.client.post(path, data, **headers)
                                self.assertEqual(rejected.status_code, 400, rejected.content)
                                self.assertEqual(rejected.json()["error"], "invalid_request")
                                headers["HTTP_DPOP"] = proof.build(
                                    htu=f"https://issuer.example:8443{path}",
                                    c_s256=challenge,
                                    jti=generate_id(),
                                )
                            response = self.client.post(f"{path}?probe=1", data, **headers)
                            self.assertEqual(response.status_code, 200, response.content)
                            body = response.json()
                            claims = decode(
                                body["id_token"],
                                self.keypair.public_key,
                                algorithms=["RS256"],
                                audience=client_id,
                            )
                            self.assertEqual(claims["aud"], client_id)
                            self.assertEqual("cnf" in claims, bound)
                            access_claims = decode(
                                body["access_token"],
                                self.keypair.public_key,
                                algorithms=["RS256"],
                                audience=self.provider.client_id,
                            )
                            self.assertEqual(access_claims["aud"], self.provider.client_id)
                            self.assertEqual(access_claims["azp"], self.provider.client_id)
                            data = {
                                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                                "client_id": client_id,
                                "refresh_token": body["refresh_token"],
                            }

    @Mocker()
    def test_client_audience_does_not_change_access_claims_or_provider_boundary(self, mock: Mocker):
        mock.get(CLIENT_ID, json=DOCUMENT)
        client = scoped_resolver(self.provider).resolve(None, CLIENT_ID)
        token = IDToken(aud=self.provider.client_id, claims={"aud": "mapped-audience"})
        encoded = token.to_jwt(self.provider, client=client)
        claims = decode(encoded, self.keypair.public_key, algorithms=["RS256"], audience=CLIENT_ID)
        self.assertEqual(claims["aud"], CLIENT_ID)
        self.assertEqual(token.to_dict()["aud"], "mapped-audience")
        legacy = scoped_resolver(self.provider).resolve(None, self.provider.client_id)
        claims = decode(
            token.to_jwt(self.provider, client=legacy),
            self.keypair.public_key,
            algorithms=["RS256"],
            audience="mapped-audience",
        )
        self.assertEqual(claims["aud"], "mapped-audience")
        other_provider = OAuth2Provider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        with self.assertRaises(ValueError):
            token.to_jwt(other_provider, client=client)
        self.assertIsNone(scoped_resolver(self.provider).resolve(None, other_provider.client_id))

    @Mocker()
    def test_shared_endpoint_does_not_resolve_metadata_clients(self, mock: Mocker):
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {"grant_type": GRANT_TYPE_AUTHORIZATION_CODE, "client_id": CLIENT_ID},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_client")
        self.assertFalse(mock.called)

    @Mocker()
    def test_authorize_loopback_port(self, mock: Mocker):
        mock.get(CLIENT_ID, json=DOCUMENT)
        request = RequestFactory().get(
            "/",
            data={
                "response_type": "code",
                "client_id": CLIENT_ID,
                "redirect_uri": "http://127.0.0.1:51234/callback",
                "code_challenge": "x" * 43,
                "code_challenge_method": PKCE_METHOD_S256,
            },
        )
        params = OAuthAuthorizationParams.from_request(
            request, resolver=scoped_resolver(self.provider)
        )
        self.assertEqual(params.client.registration_kind, METADATA_KIND)
        self.assertEqual(params.provider, self.provider)
        # Wrong path is rejected
        request = RequestFactory().get(
            "/",
            data={
                "response_type": "code",
                "client_id": CLIENT_ID,
                "redirect_uri": "http://127.0.0.1:51234/other",
            },
        )
        with self.assertRaises(RedirectUriError):
            OAuthAuthorizationParams.from_request(request, resolver=scoped_resolver(self.provider))

    @Mocker()
    def test_token(self, mock: Mocker):
        mock.get(CLIENT_ID, json=DOCUMENT)
        verifier = generate_id(64)
        code = AuthorizationCode.objects.create(
            code=generate_id(),
            provider=self.provider,
            user=create_test_admin_user(),
            auth_time=timezone.now(),
            code_challenge=pkce_s256_challenge(verifier),
            code_challenge_method=PKCE_METHOD_S256,
        )
        # Real clients send no CSRF token
        response = Client(enforce_csrf_checks=True).post(
            reverse(
                "authentik_providers_oauth2:prototype-scoped-token",
                kwargs={"application_slug": self.slug},
            ),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "client_id": CLIENT_ID,
                "code": code.code,
                "code_verifier": verifier,
                "redirect_uri": "http://127.0.0.1:51234/callback",
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(AccessToken.objects.filter(provider=self.provider).exists())
        with open(self.log.name) as log:
            self.assertIn('"kind": "metadata_fetch"', log.read())

    def test_disabled_slug_404(self):
        Application.objects.create(
            name=generate_id(),
            slug="other",
            provider=OAuth2Provider.objects.create(
                name=generate_id(), authorization_flow=create_test_flow()
            ),
        )
        response = self.client.post(
            reverse(
                "authentik_providers_oauth2:prototype-scoped-token",
                kwargs={"application_slug": "other"},
            ),
            data={"grant_type": GRANT_TYPE_AUTHORIZATION_CODE, "client_id": CLIENT_ID},
        )
        self.assertEqual(response.status_code, 404)
