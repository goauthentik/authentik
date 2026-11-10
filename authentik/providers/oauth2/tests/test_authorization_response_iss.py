"""RFC 9207 issuer identification in authorization responses"""

from base64 import urlsafe_b64encode
from http import HTTPStatus
from json import dumps, loads
from urllib.parse import parse_qs, urlsplit

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory, TransactionTestCase
from django.urls import reverse
from django.utils.timezone import now
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.blueprints.v1.importer import Importer
from authentik.common.oauth.constants import SCOPE_AUTHENTIK_DCR
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.errors import AuthorizeError
from authentik.providers.oauth2.models import (
    AccessToken,
    GrantType,
    OAuth2DynamicClientRegistration,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ResponseMode,
    ResponseTypes,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase

REDIRECT_URI = "https://app.example/cb?tenant=one"

# (response_type, response_mode) pairs for every supported response type, in the default
# response mode of its grant and in every mode that can carry it
SUCCESS_CASES = [
    (ResponseTypes.CODE, ResponseMode.QUERY),
    (ResponseTypes.CODE, ResponseMode.FRAGMENT),
    (ResponseTypes.CODE, ResponseMode.FORM_POST),
    (ResponseTypes.ID_TOKEN, ResponseMode.FRAGMENT),
    (ResponseTypes.ID_TOKEN, ResponseMode.FORM_POST),
    (ResponseTypes.ID_TOKEN_TOKEN, ResponseMode.FRAGMENT),
    (ResponseTypes.ID_TOKEN_TOKEN, ResponseMode.FORM_POST),
    (ResponseTypes.CODE_TOKEN, ResponseMode.FRAGMENT),
    (ResponseTypes.CODE_TOKEN, ResponseMode.FORM_POST),
    (ResponseTypes.CODE_ID_TOKEN, ResponseMode.FRAGMENT),
    (ResponseTypes.CODE_ID_TOKEN, ResponseMode.FORM_POST),
    (ResponseTypes.CODE_ID_TOKEN_TOKEN, ResponseMode.FRAGMENT),
    (ResponseTypes.CODE_ID_TOKEN_TOKEN, ResponseMode.FORM_POST),
]


class TestAuthorizationResponseIssuer(OAuthTestCase):
    """The `iss` authorization response parameter (RFC 9207)"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.flow = create_test_flow()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            authorization_flow=self.flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_URI)],
            signing_key=self.keypair,
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.IMPLICIT, GrantType.HYBRID],
        )
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(managed="goauthentik.io/providers/oauth2/scope-openid")
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.user = create_test_admin_user()
        self.state = "value &=# +%&iss=https://other.example/"

    def set_enabled(self, enabled: bool):
        self.provider.include_issuer_in_authorization_response = enabled
        self.provider.save()

    def discovery(self) -> dict:
        return self.client.get(
            reverse(
                "authentik_providers_oauth2:provider-info",
                kwargs={"application_slug": self.app.slug},
            )
        ).json()

    def authorize(self, **data) -> dict:
        """Send an authorization request, return the parameters returned to the client"""
        params = {
            "client_id": self.provider.client_id,
            "redirect_uri": REDIRECT_URI,
            "state": self.state,
            "scope": "openid",
            "nonce": generate_id(),
        }
        params.update(data)
        params = {key: value for key, value in params.items() if value is not None}
        response = self.client.get(reverse("authentik_providers_oauth2:authorize"), data=params)
        response_mode = params.get("response_mode")
        if response_mode == ResponseMode.FORM_POST:
            # Errors raised before the flow starts are rendered directly
            if response.status_code == HTTPStatus.OK:
                self.assertTemplateUsed(response, "if/oauth_form_post.html")
                self.assertEqual(response.context_data["redirect_uri"], REDIRECT_URI)
                return response.context_data["attrs"]
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            )
            body = response.json()
            self.assertEqual(body["component"], "ak-stage-autosubmit")
            self.assertEqual(body["url"], REDIRECT_URI)
            return body["attrs"]
        self.assertEqual(response.status_code, 302)
        uri = urlsplit(response.url)
        self.assertEqual(f"{uri.scheme}://{uri.netloc}{uri.path}", "https://app.example/cb")
        if uri.fragment:
            self.assertEqual(uri.query, "tenant=one")
            encoded = uri.fragment
        else:
            encoded = uri.query
        returned = {key: values[-1] for key, values in parse_qs(encoded).items()}
        returned.pop("tenant", None)
        return returned

    def assert_issuer(self, params: dict, enabled: bool):
        """`iss` is present exactly when enabled, and identifies the same issuer as the
        discovery document and any returned ID token"""
        if not enabled:
            self.assertNotIn("iss", params)
            return
        issuer = self.discovery()["issuer"]
        self.assertEqual(params["iss"], issuer)
        self.assertEqual(params["iss"], self.provider.get_issuer(self.factory.get("/")))
        if "id_token" in params:
            id_token = decode(params["id_token"], options={"verify_signature": False})
            self.assertEqual(id_token["iss"], params["iss"])

    def test_discovery(self):
        """Discovery advertises whether the parameter is returned"""
        for enabled in [True, False]:
            with self.subTest(enabled=enabled):
                self.set_enabled(enabled)
                self.assertIs(
                    self.discovery()["authorization_response_iss_parameter_supported"], enabled
                )

    def test_success(self):
        """Successful responses of every response type and mode"""
        self.client.force_login(self.user)
        for enabled in [True, False]:
            self.set_enabled(enabled)
            for response_type, response_mode in SUCCESS_CASES:
                with self.subTest(
                    enabled=enabled, response_type=response_type, response_mode=response_mode
                ):
                    params = self.authorize(
                        response_type=response_type, response_mode=response_mode
                    )
                    self.assertEqual(params["state"], self.state)
                    self.assertNotIn("error", params)
                    self.assert_issuer(params, enabled)

    def test_success_default_response_mode(self):
        """Responses in the default response mode of each grant"""
        self.client.force_login(self.user)
        for enabled in [True, False]:
            self.set_enabled(enabled)
            for response_type in [ResponseTypes.CODE, ResponseTypes.ID_TOKEN]:
                with self.subTest(enabled=enabled, response_type=response_type):
                    params = self.authorize(response_type=response_type)
                    self.assertEqual(params["state"], self.state)
                    self.assert_issuer(params, enabled)

    def test_success_without_state(self):
        """`iss` doesn't depend on the client sending a state"""
        self.client.force_login(self.user)
        params = self.authorize(response_type=ResponseTypes.CODE, state=None)
        self.assertNotIn("state", params)
        self.assert_issuer(params, True)

    def test_error_request_validation(self):
        """Errors found while validating the request, in every response mode"""
        self.client.force_login(self.user)
        for enabled in [True, False]:
            self.set_enabled(enabled)
            for response_type, response_mode, data, error in [
                # Unsupported PKCE method
                (
                    ResponseTypes.CODE,
                    None,
                    {"code_challenge": generate_id(), "code_challenge_method": "foo"},
                    "invalid_request",
                ),
                (
                    ResponseTypes.CODE,
                    ResponseMode.FRAGMENT,
                    {"code_challenge": generate_id(), "code_challenge_method": "foo"},
                    "invalid_request",
                ),
                (
                    ResponseTypes.CODE,
                    ResponseMode.FORM_POST,
                    {"code_challenge": generate_id(), "code_challenge_method": "foo"},
                    "invalid_request",
                ),
                # Missing nonce
                (ResponseTypes.ID_TOKEN, None, {"nonce": None}, "invalid_request"),
                (ResponseTypes.CODE_ID_TOKEN, None, {"nonce": None}, "invalid_request"),
                (
                    ResponseTypes.ID_TOKEN_TOKEN,
                    ResponseMode.FORM_POST,
                    {"nonce": None},
                    "invalid_request",
                ),
                # Unknown response type
                ("foo", ResponseMode.QUERY, {}, "unsupported_response_type"),
                # Request objects
                (
                    ResponseTypes.CODE,
                    ResponseMode.FORM_POST,
                    {"request": "e30.e30."},
                    "request_not_supported",
                ),
            ]:
                with self.subTest(
                    enabled=enabled,
                    response_type=response_type,
                    response_mode=response_mode,
                    error=error,
                ):
                    params = self.authorize(
                        response_type=response_type, response_mode=response_mode, **data
                    )
                    self.assertEqual(params["error"], error)
                    self.assertEqual(params["state"], self.state)
                    self.assert_issuer(params, enabled)

    def test_error_request_object_routing(self):
        """Errors for request objects use the response mode set in the request object"""
        claims = urlsafe_b64encode(
            dumps({"response_type": "id_token", "response_mode": "fragment"}).encode()
        ).decode()
        for enabled in [True, False]:
            self.set_enabled(enabled)
            with self.subTest(enabled=enabled):
                params = self.authorize(request=f"e30.{claims}.")
                self.assertEqual(params["error"], "request_not_supported")
                self.assert_issuer(params, enabled)

    def test_error_login_required(self):
        """prompt=none without a session"""
        for enabled in [True, False]:
            self.set_enabled(enabled)
            for response_mode in [ResponseMode.QUERY, ResponseMode.FRAGMENT]:
                with self.subTest(enabled=enabled, response_mode=response_mode):
                    params = self.authorize(
                        response_type=ResponseTypes.CODE,
                        response_mode=response_mode,
                        prompt="none",
                    )
                    self.assertEqual(params["error"], "login_required")
                    self.assert_issuer(params, enabled)

    def test_error_consent_required(self):
        """Errors returned by the final stage of the authorization flow"""
        self.client.force_login(self.user)
        executor = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        for enabled in [True, False]:
            self.set_enabled(enabled)
            for response_type, response_mode in [
                (ResponseTypes.CODE, ResponseMode.QUERY),
                (ResponseTypes.CODE, ResponseMode.FRAGMENT),
                (ResponseTypes.ID_TOKEN, ResponseMode.FRAGMENT),
            ]:
                with self.subTest(
                    enabled=enabled, response_type=response_type, response_mode=response_mode
                ):
                    # prompt=consent adds a consent stage, after which prompt=none fails
                    self.client.get(
                        reverse("authentik_providers_oauth2:authorize"),
                        data={
                            "client_id": self.provider.client_id,
                            "redirect_uri": REDIRECT_URI,
                            "response_type": response_type,
                            "response_mode": response_mode,
                            "state": self.state,
                            "scope": "openid",
                            "nonce": generate_id(),
                            "prompt": "none consent",
                        },
                    )
                    challenge = self.client.get(executor).json()
                    self.assertEqual(challenge["component"], "ak-stage-consent")
                    response = self.client.post(
                        executor,
                        data={"component": "ak-stage-consent", "token": challenge["token"]},
                        content_type="application/json",
                    )
                    # The executor continues with the final stage on the next request
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    response = self.client.get(executor).json()
                    self.assertEqual(response["component"], "xak-flow-redirect")
                    uri = urlsplit(response["to"])
                    encoded = uri.fragment if response_mode == ResponseMode.FRAGMENT else uri.query
                    params = {key: values[-1] for key, values in parse_qs(encoded).items()}
                    self.assertEqual(params["error"], "consent_required")
                    self.assertEqual(params["state"], self.state)
                    self.assert_issuer(params, enabled)

    def test_error_response_encoding(self):
        """The issuer is encoded like every other parameter, in every response mode"""
        request = self.factory.get("/")
        issuer = self.provider.get_issuer(request)
        for response_mode in [ResponseMode.QUERY, ResponseMode.FRAGMENT, ResponseMode.FORM_POST]:
            with self.subTest(response_mode=response_mode):
                error = AuthorizeError(
                    REDIRECT_URI,
                    "invalid_request",
                    GrantType.AUTHORIZATION_CODE,
                    self.state,
                    response_mode=response_mode,
                    provider=self.provider,
                )
                response = error.get_response(request)
                if response_mode == ResponseMode.FORM_POST:
                    params = response.context_data["attrs"]
                else:
                    uri = urlsplit(response.url)
                    encoded = uri.fragment or uri.query
                    # The `iss` in the state stays part of the state
                    self.assertIn("&iss=http%3A%2F%2Ftestserver%2Fapplication%2Fo%2F", encoded)
                    params = {
                        key: values[-1]
                        for key, values in parse_qs(encoded, keep_blank_values=True).items()
                    }
                self.assertEqual(params["iss"], issuer)
                self.assertEqual(params["state"], self.state)

    def test_error_without_provider(self):
        """Errors that aren't attributed to a provider don't include `iss`"""
        error = AuthorizeError(REDIRECT_URI, "invalid_request", GrantType.AUTHORIZATION_CODE, None)
        self.assertNotIn(
            "iss", parse_qs(urlsplit(error.get_response(self.factory.get("/")).url).query)
        )


class TestAuthorizationResponseIssuerSettings(OAuthTestCase):
    """Defaults and persistence of the setting"""

    def setUp(self):
        super().setUp()
        self.admin = create_test_admin_user()
        self.flow = create_test_flow()

    def test_model_default(self):
        """New providers include the issuer"""
        provider = OAuth2Provider.objects.create(name=generate_id(), authorization_flow=self.flow)
        self.assertTrue(provider.include_issuer_in_authorization_response)

    def test_api(self):
        """Created through the API, the setting is enabled by default, and updates that omit
        it keep the stored value"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": str(self.flow.pk),
                "invalidation_flow": str(self.flow.pk),
                "redirect_uris": [],
                "grant_types": [GrantType.AUTHORIZATION_CODE],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertTrue(body["include_issuer_in_authorization_response"])
        provider = OAuth2Provider.objects.get(pk=body["pk"])
        self.assertTrue(provider.include_issuer_in_authorization_response)
        url = reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider.pk})

        # Disable it explicitly
        response = self.client.patch(
            url,
            data={"include_issuer_in_authorization_response": False},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        provider.refresh_from_db()
        self.assertFalse(provider.include_issuer_in_authorization_response)

        # Partial update without the field
        response = self.client.patch(
            url, data={"name": generate_id()}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        provider.refresh_from_db()
        self.assertFalse(provider.include_issuer_in_authorization_response)

        # Full update without the field
        data = self.client.get(url).json()
        del data["include_issuer_in_authorization_response"]
        response = self.client.put(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        provider.refresh_from_db()
        self.assertFalse(provider.include_issuer_in_authorization_response)

    def test_blueprint(self):
        """Created by a blueprint, the setting is enabled by default, and a blueprint that
        doesn't set it keeps the stored value when applied again"""
        name = generate_id()
        blueprint = f"""
version: 1
entries:
  - model: authentik_providers_oauth2.oauth2provider
    identifiers:
      name: {name}
    attrs:
      authorization_flow: {self.flow.pk}
      invalidation_flow: {self.flow.pk}
      client_type: public
      redirect_uris: []
"""
        importer = Importer.from_string(blueprint)
        self.assertTrue(importer.apply())
        provider = OAuth2Provider.objects.get(name=name)
        self.assertTrue(provider.include_issuer_in_authorization_response)

        provider.include_issuer_in_authorization_response = False
        provider.save()
        importer = Importer.from_string(blueprint)
        self.assertTrue(importer.apply())
        provider.refresh_from_db()
        self.assertFalse(provider.include_issuer_in_authorization_response)

        # Setting it explicitly still applies
        importer = Importer.from_string(
            blueprint + "      include_issuer_in_authorization_response: true\n"
        )
        self.assertTrue(importer.apply())
        provider.refresh_from_db()
        self.assertTrue(provider.include_issuer_in_authorization_response)

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_dynamic_client_registration(self):
        """Registered clients copy the registration provider's setting when they're created"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        OAuth2DynamicClientRegistration.objects.create(provider=provider)
        token = AccessToken.objects.create(
            user=self.admin,
            provider=provider,
            token=generate_id(),
            auth_time=now(),
            _scope=SCOPE_AUTHENTIK_DCR,
            _id_token=dumps({}),
        )

        def register() -> OAuth2Provider:
            response = self.client.post(
                reverse(
                    "authentik_providers_oauth2:dynamic-client-registration",
                    kwargs={"application_slug": app.slug},
                ),
                dumps({"redirect_uris": ["https://example.com/callback"]}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {token.token}",
            )
            self.assertEqual(response.status_code, 201, response.content)
            return OAuth2Provider.objects.get(client_id=loads(response.content)["client_id"])

        for enabled in [False, True]:
            with self.subTest(enabled=enabled):
                provider.include_issuer_in_authorization_response = enabled
                provider.save()
                self.assertIs(register().include_issuer_in_authorization_response, enabled)

        # Later changes to the registration provider don't affect registered clients
        registered = register()
        provider.include_issuer_in_authorization_response = False
        provider.save()
        registered.refresh_from_db()
        self.assertTrue(registered.include_issuer_in_authorization_response)


class TestAuthorizationResponseIssuerMigration(TransactionTestCase):
    """Existing providers keep omitting `iss` after upgrading"""

    app = "authentik_providers_oauth2"
    migrate_from = "0038_oauth2sessionlogin"
    migrate_to = "0039_oauth2provider_include_issuer_in_authorization_response"

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_providers(self):
        executor = MigrationExecutor(connection)
        executor.migrate([(self.app, self.migrate_from)])
        old_apps = executor.loader.project_state([(self.app, self.migrate_from)]).apps
        old_provider = old_apps.get_model(self.app, "OAuth2Provider").objects.create(
            name=generate_id(), client_id=generate_id()
        )

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate([(self.app, self.migrate_to)])
        new_apps = executor.loader.project_state([(self.app, self.migrate_to)]).apps
        new_model = new_apps.get_model(self.app, "OAuth2Provider")

        self.assertFalse(
            new_model.objects.get(pk=old_provider.pk).include_issuer_in_authorization_response
        )
        new_provider = new_model.objects.create(name=generate_id(), client_id=generate_id())
        self.assertTrue(new_provider.include_issuer_in_authorization_response)
