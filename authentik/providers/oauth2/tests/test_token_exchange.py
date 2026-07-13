"""Test token exchange view"""

from datetime import datetime, timedelta
from json import loads

from django.test import RequestFactory
from django.urls import reverse
from django.utils.timezone import now
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_TOKEN_EXCHANGE,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
    TOKEN_TYPE,
    TOKEN_TYPE_URI_ACCESS_TOKEN,
    TOKEN_TYPE_URI_JWT,
)
from authentik.core.models import Application, User
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.enterprise.pam.models import Grant, Persona, PersonaTemplate
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase

SCOPES = f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}"


class TestTokenExchange(OAuthTestCase):
    """Test token exchange (RFC 8693) view"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.other_cert = create_test_cert()
        self.cert = create_test_cert()

        # The provider that issued the subject token
        self.other_provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=self.other_cert,
        )
        self.other_provider.property_mappings.set(ScopeMapping.objects.all())
        self.other_app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.other_provider
        )

        # The provider performing the exchange
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=self.cert,
            grant_types=[GrantType.TOKEN_EXCHANGE],
        )
        self.provider.jwt_federation_providers.add(self.other_provider)
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )

        self.user = create_test_user()
        self.subject_token = self.create_subject_token(self.user)

    def create_subject_token(self, user: User, expires_in: timedelta = timedelta(hours=2)) -> str:
        """Issue an access token from the federated provider, usable as a subject token"""
        token = self.other_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + expires_in,
            }
        )
        AccessToken.objects.create(
            provider=self.other_provider,
            token=token,
            user=user,
            auth_time=now(),
        )
        return token

    def create_actor_token(self, expires_in: timedelta = timedelta(hours=2)) -> str:
        """Issue an access token from the federated provider, usable as an actor token"""
        token = self.other_provider.encode(
            {
                "sub": "agent",
                "exp": datetime.now() + expires_in,
            }
        )
        AccessToken.objects.create(
            provider=self.other_provider,
            token=token,
            user=self.user,
            auth_time=now(),
        )
        return token

    def create_persona_template(self, authorize_other_provider: bool = True) -> PersonaTemplate:
        """Create a PersonaTemplate, optionally authorizing self.other_provider as an actor"""
        template = PersonaTemplate.objects.create(name=generate_id())
        if authorize_other_provider:
            template.actor_providers.add(self.other_provider)
        return template

    def test_missing_subject_token(self):
        """test request without a subject token"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_unsupported_subject_token_type(self):
        """test request with a subject token type that is not supported"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": "urn:ietf:params:oauth:token-type:saml2",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_unsupported_requested_token_type(self):
        """test request with a requested token type that is not supported"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "requested_token_type": "urn:ietf:params:oauth:token-type:refresh_token",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_actor_token_without_persona_rejected(self):
        """test that an actor_token without a persona to act as is refused"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": self.subject_token,
                "actor_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_persona_without_actor_token_rejected(self):
        """test that a persona without an actor_token is refused rather than trusted blindly"""
        template = self.create_persona_template()
        persona = Persona.create_for_user(generate_id(), self.user, template=template)
        Grant.objects.create(persona=persona, target=self.app)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "persona": persona.pk,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_audience_rejected(self):
        """test that a requested audience is refused rather than silently ignored"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "audience": "https://api.example.com",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_target")

    def test_resource_rejected(self):
        """test that a requested resource is refused rather than silently ignored"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "resource": "https://api.example.com/orders",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_target")

    def test_invalid_signature(self):
        """test subject token whose signature does not verify"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token + "foo",
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_untrusted_provider(self):
        """test subject token from a provider that is not federated with the requesting provider"""
        self.provider.jwt_federation_providers.clear()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_expired_subject_token(self):
        """test subject token that has expired"""
        expired = self.create_subject_token(self.user, expires_in=-timedelta(hours=2))
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": expired,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_grant_type_not_configured(self):
        """test provider that does not allow the token exchange grant"""
        self.provider.grant_types = [GrantType.CLIENT_CREDENTIALS]
        self.provider.save()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_confidential_client_without_secret(self):
        """test that a confidential client must authenticate"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_client")

    def test_public_client_without_secret(self):
        """test that a public client may exchange without a client secret"""
        self.provider.client_type = ClientType.PUBLIC
        self.provider.save()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_wrong_grant_type_rejects_subject_token(self):
        """test that a subject token is not accepted by another grant type"""
        self.provider.grant_types = [GrantType.CLIENT_CREDENTIALS]
        self.provider.save()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_successful(self):
        """test successful exchange, preserving the subject's identity"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        self.assertEqual(body["issued_token_type"], TOKEN_TYPE_URI_ACCESS_TOKEN)

        _, alg = self.provider.jwt_key
        jwt = decode(
            body["access_token"],
            key=self.provider.signing_key.public_key,
            algorithms=[alg],
            audience=self.provider.client_id,
        )
        # Impersonation: the exchanged token speaks for the subject, and carries no
        # delegation chain
        self.assertEqual(jwt["given_name"], self.user.name)
        self.assertEqual(jwt["preferred_username"], self.user.username)
        self.assertNotIn("act", jwt)

    def test_persona_delegation_success(self):
        """test exchanging for a token scoped to a Persona, with an authorized actor_token"""
        template = self.create_persona_template()
        persona = Persona.create_for_user(generate_id(), self.user, template=template)
        Grant.objects.create(persona=persona, target=self.app)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "persona": persona.pk,
                "actor_token": self.create_actor_token(),
                "actor_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        _, alg = self.provider.jwt_key
        jwt = decode(
            body["access_token"],
            key=self.provider.signing_key.public_key,
            algorithms=[alg],
            audience=self.provider.client_id,
        )
        # The resulting token speaks for the persona, with an `act` claim recording
        # the human subject it was exchanged on behalf of.
        self.assertEqual(jwt["preferred_username"], persona.username)
        self.assertEqual(jwt["act"]["sub"], self.user.uid)

    def test_persona_not_owned_rejected(self):
        """test that a persona belonging to another user cannot be requested"""
        other_user = create_test_user()
        template = self.create_persona_template()
        persona = Persona.create_for_user(generate_id(), other_user, template=template)
        Grant.objects.create(persona=persona, target=self.app)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "persona": persona.pk,
                "actor_token": self.create_actor_token(),
                "actor_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_persona_without_grant_rejected(self):
        """test that a persona without a Grant for the target application is refused"""
        template = self.create_persona_template()
        persona = Persona.create_for_user(generate_id(), self.user, template=template)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "persona": persona.pk,
                "actor_token": self.create_actor_token(),
                "actor_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_persona_without_template_rejected(self):
        """test that a persona created directly, with no template, cannot be delegated to"""
        persona = Persona.create_for_user(generate_id(), self.user)
        Grant.objects.create(persona=persona, target=self.app)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "persona": persona.pk,
                "actor_token": self.create_actor_token(),
                "actor_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_actor_not_authorized_rejected(self):
        """test that a verified actor_token not on the template's allowlist is refused"""
        template = self.create_persona_template(authorize_other_provider=False)
        persona = Persona.create_for_user(generate_id(), self.user, template=template)
        Grant.objects.create(persona=persona, target=self.app)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "persona": persona.pk,
                "actor_token": self.create_actor_token(),
                "actor_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_actor_token_unverified_rejected(self):
        """test that an actor_token which fails signature verification is refused"""
        template = self.create_persona_template()
        persona = Persona.create_for_user(generate_id(), self.user, template=template)
        Grant.objects.create(persona=persona, target=self.app)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "persona": persona.pk,
                "actor_token": self.create_actor_token() + "foo",
                "actor_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_successful_requested_jwt(self):
        """test that requesting a JWT yields the same artifact, reported as a JWT"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_JWT,
                "requested_token_type": TOKEN_TYPE_URI_JWT,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["issued_token_type"], TOKEN_TYPE_URI_JWT)
