"""Test token exchange view"""

from datetime import datetime, timedelta
from json import loads
from uuid import uuid4

from django.http import HttpResponse
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
    TOKEN_TYPE_URI_AUTHENTIK_TOKEN,
    TOKEN_TYPE_URI_JWT,
)
from authentik.core.models import (
    Actor,
    ActorPolicyInheritance,
    Application,
    Group,
    Token,
    TokenIntents,
    User,
)
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
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

        # The provider a token can be requested for via `audience`
        self.target_cert = create_test_cert()
        self.target_provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=self.target_cert,
        )
        self.target_provider.jwt_federation_providers.add(self.provider)
        self.target_provider.property_mappings.set(ScopeMapping.objects.all())
        self.target_app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.target_provider
        )

        self.user = create_test_user()
        self.subject_token = self.create_subject_token(self.user)

    def create_subject_token(
        self,
        user: User,
        expires_in: timedelta = timedelta(hours=2),
        provider: OAuth2Provider | None = None,
    ) -> str:
        """Issue an access token from the federated provider, usable as a subject token"""
        provider = provider or self.other_provider
        token = provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + expires_in,
            }
        )
        AccessToken.objects.create(
            provider=provider,
            token=token,
            user=user,
            auth_time=now(),
        )
        return token

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

    def test_actor_token_unsupported_type_rejected(self):
        """test that an actor_token of an unsupported type is refused rather than
        silently ignored"""
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
                "actor_token_type": "urn:ietf:params:oauth:token-type:saml2",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def _exchange(self, **extra) -> HttpResponse:
        """Run an otherwise-valid exchange, with `extra` merged into the request"""
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                **extra,
            },
        )

    def _decode_for(self, provider: OAuth2Provider, access_token: str) -> dict:
        _, alg = provider.jwt_key
        return decode(
            access_token,
            key=provider.signing_key.public_key,
            algorithms=[alg],
            audience=provider.client_id,
        )

    def test_audience_client_id(self):
        """test that an audience naming a provider's client_id issues on that provider"""
        response = self._exchange(audience=self.target_provider.client_id)
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        jwt = self._decode_for(self.target_provider, body["access_token"])
        self.assertEqual(jwt["aud"], self.target_provider.client_id)
        self.assertEqual(jwt["azp"], self.target_provider.client_id)
        self.assertIn(self.target_app.slug, jwt["iss"])
        self.assertEqual(jwt["preferred_username"], self.user.username)

        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertEqual(access_token.provider_id, self.target_provider.pk)
        self.assertEqual(access_token.user_id, self.user.pk)

    def test_audience_pbm_uuid(self):
        """test that an audience naming an application's pbm_uuid issues on its provider"""
        response = self._exchange(audience=str(self.target_app.pbm_uuid))
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        jwt = self._decode_for(self.target_provider, body["access_token"])
        self.assertEqual(jwt["aud"], self.target_provider.client_id)
        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertEqual(access_token.provider_id, self.target_provider.pk)

    def test_audience_self(self):
        """test that naming the requesting provider still issues on it"""
        response = self._exchange(audience=self.provider.client_id)
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertEqual(access_token.provider_id, self.provider.pk)

    def test_audience_unknown(self):
        """test an audience that matches no provider, both as a URI and as a UUID"""
        for audience in ["https://api.example.com", str(uuid4())]:
            with self.subTest(audience=audience):
                response = self._exchange(audience=audience)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(loads(response.content.decode())["error"], "invalid_target")

    def test_audience_multiple(self):
        """test that multi-provider tokens are refused rather than silently narrowed"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "audience": [self.provider.client_id, self.target_provider.client_id],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content.decode())["error"], "invalid_target")

    def test_audience_not_federated(self):
        """test an audience that does not federate with the requesting provider"""
        self.target_provider.jwt_federation_providers.clear()
        response = self._exchange(audience=self.target_provider.client_id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content.decode())["error"], "invalid_target")

    def test_audience_without_application(self):
        """test an audience whose provider has no application"""
        self.target_app.delete()
        response = self._exchange(audience=self.target_provider.client_id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content.decode())["error"], "invalid_target")

    def test_audience_policy_denied(self):
        """test that the target application's policies gate the exchange"""
        PolicyBinding.objects.create(
            group=Group.objects.create(name=generate_id()),
            target=self.target_app,
            order=0,
        )
        response = self._exchange(audience=self.target_provider.client_id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content.decode())["error"], "invalid_grant")
        self.assertFalse(AccessToken.objects.filter(provider=self.target_provider).exists())

    def test_audience_scopes_from_target(self):
        """test that scopes are clamped to the target provider's mappings, not the client's"""
        self.target_provider.property_mappings.set(
            ScopeMapping.objects.filter(scope_name=SCOPE_OPENID)
        )
        response = self._exchange(audience=self.target_provider.client_id)
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())
        self.assertEqual(body["scope"], SCOPE_OPENID)

    def test_audience_subject_token_from_self(self):
        """test that a token the requesting provider issued for itself is a valid subject
        token when `audience` targets another provider -- the target has already opted into
        the requesting provider, which is what authorizes the exchange"""
        subject_token = self.create_subject_token(self.user, provider=self.provider)
        response = self._exchange(
            subject_token=subject_token, audience=self.target_provider.client_id
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        jwt = self._decode_for(self.target_provider, body["access_token"])
        self.assertEqual(jwt["aud"], self.target_provider.client_id)
        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertEqual(access_token.provider_id, self.target_provider.pk)
        self.assertEqual(access_token.user_id, self.user.pk)

    def test_subject_token_from_self_without_audience(self):
        """test that a self-issued subject token is only accepted when `audience` targets
        another provider -- naming the requesting provider itself does not widen the trust,
        since that is the default behavior and no target opted in"""
        subject_token = self.create_subject_token(self.user, provider=self.provider)
        for audience in [None, self.provider.client_id]:
            with self.subTest(audience=audience):
                extra = {"audience": audience} if audience else {}
                response = self._exchange(subject_token=subject_token, **extra)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(loads(response.content.decode())["error"], "invalid_grant")

    def test_audience_subject_token_from_self_not_federated(self):
        """test that a self-issued subject token does not bypass the target's opt-in"""
        self.target_provider.jwt_federation_providers.clear()
        subject_token = self.create_subject_token(self.user, provider=self.provider)
        response = self._exchange(
            subject_token=subject_token, audience=self.target_provider.client_id
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content.decode())["error"], "invalid_target")

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

    def test_successful_with_group_binding(self):
        """test that policies are evaluated as the subject, not anonymously"""
        group = Group.objects.create(name=generate_id())
        group.users.add(self.user)
        PolicyBinding.objects.create(group=group, target=self.app, order=0)

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

    def test_denied_with_group_binding(self):
        """test that a subject outside the bound group is still denied"""
        group = Group.objects.create(name=generate_id())
        PolicyBinding.objects.create(group=group, target=self.app, order=0)

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

    def _decode(self, access_token: str) -> dict:
        return self._decode_for(self.provider, access_token)

    def _actor_token_jwt(self, actor: Actor, provider: OAuth2Provider | None = None) -> str:
        """Issue an access token for `actor` from the federated provider, usable as a
        JWT actor_token"""
        provider = provider or self.other_provider
        token = provider.encode(
            {
                "sub": "actor",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        AccessToken.objects.create(
            provider=provider,
            token=token,
            user=actor,
            auth_time=now(),
        )
        return token

    def _actor_token_builtin(self, actor: Actor) -> str:
        """Issue an authentik built-in API token for `actor`, usable as an actor_token"""
        token = Token.objects.create(
            identifier=generate_id(),
            user=actor,
            intent=TokenIntents.INTENT_API,
        )
        return token.key

    def test_actor_token_successful_delegation(self):
        """test RFC 8693 §4.1 delegation: subject_token identifies the human, actor_token
        identifies an Actor the human controls -- the issued token's `sub` stays the
        human (unchanged), and `act` records the actor"""
        actor = Actor.for_user(self.user, ActorPolicyInheritance.NONE)
        actor_token = self._actor_token_jwt(actor)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": actor_token,
                "actor_token_type": TOKEN_TYPE_URI_JWT,
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        jwt = self._decode(body["access_token"])
        # sub is unchanged -- still the human, exactly like plain (non-delegated) exchange
        self.assertEqual(jwt["preferred_username"], self.user.username)
        self.assertIn("act", jwt)
        self.assertEqual(jwt["act"]["sub"], actor.uid)

        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertEqual(access_token.user_id, self.user.pk)
        self.assertEqual(access_token.actor_id, actor.pk)

    def test_actor_token_builtin_successful_delegation(self):
        """test RFC 8693 §4.1 delegation via an authentik built-in Token, for an actor
        that has an owner"""
        actor = Actor.for_user(self.user, ActorPolicyInheritance.NONE)
        actor_token = self._actor_token_builtin(actor)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": actor_token,
                "actor_token_type": TOKEN_TYPE_URI_AUTHENTIK_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        jwt = self._decode(body["access_token"])
        self.assertIn("act", jwt)
        self.assertEqual(jwt["act"]["sub"], actor.uid)

        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertEqual(access_token.actor_id, actor.pk)

    def test_actor_token_unowned_jwt_allowed(self):
        """test that an actor with no owner can be delegated to via a JWT actor_token"""
        actor = Actor.for_user(None, ActorPolicyInheritance.NONE)
        actor_token = self._actor_token_jwt(actor)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": actor_token,
                "actor_token_type": TOKEN_TYPE_URI_JWT,
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        jwt = self._decode(body["access_token"])
        self.assertIn("act", jwt)
        self.assertEqual(jwt["act"]["sub"], actor.uid)

        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertEqual(access_token.actor_id, actor.pk)

    def test_actor_token_jwt_from_self_with_audience(self):
        """test that an actor_token issued by the requesting provider itself is accepted
        when `audience` targets another provider, matching the subject_token trust set"""
        actor = Actor.for_user(self.user, ActorPolicyInheritance.NONE)
        actor_token = self._actor_token_jwt(actor, provider=self.provider)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": actor_token,
                "actor_token_type": TOKEN_TYPE_URI_JWT,
                "audience": self.target_provider.client_id,
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content.decode())

        jwt = self._decode_for(self.target_provider, body["access_token"])
        self.assertIn("act", jwt)
        self.assertEqual(jwt["act"]["sub"], actor.uid)

        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertEqual(access_token.provider_id, self.target_provider.pk)
        self.assertEqual(access_token.actor_id, actor.pk)

    def test_actor_token_jwt_from_self_without_audience(self):
        """test that an actor_token issued by the requesting provider itself is rejected
        without an `audience` targeting another provider"""
        actor = Actor.for_user(self.user, ActorPolicyInheritance.NONE)
        actor_token = self._actor_token_jwt(actor, provider=self.provider)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": actor_token,
                "actor_token_type": TOKEN_TYPE_URI_JWT,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content.decode())["error"], "invalid_grant")

    def test_actor_token_unowned_builtin_rejected(self):
        """test that an actor with no owner cannot be delegated to via a built-in Token
        actor_token -- only JWTs are supported for ownerless actors"""
        actor = Actor.for_user(None, ActorPolicyInheritance.NONE)
        actor_token = self._actor_token_builtin(actor)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": actor_token,
                "actor_token_type": TOKEN_TYPE_URI_AUTHENTIK_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")
        self.assertFalse(AccessToken.objects.filter(actor=actor).exists())

    def test_actor_token_rejects_unowned_actor(self):
        """test that a human cannot use as actor one they don't control"""
        other_user = create_test_user()
        someone_elses_actor = Actor.for_user(other_user, ActorPolicyInheritance.NONE)
        actor_token = self._actor_token_jwt(someone_elses_actor)

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": actor_token,
                "actor_token_type": TOKEN_TYPE_URI_JWT,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")
        self.assertFalse(AccessToken.objects.filter(actor=someone_elses_actor).exists())

    def test_actor_token_rejects_non_actor(self):
        """test that an access token belonging to an ordinary (non-Actor) user is
        not accepted as an actor -- only Actors may be delegated to"""
        other_user = create_test_user()
        actor_token = self.other_provider.encode(
            {
                "sub": "not-an-actor",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        AccessToken.objects.create(
            provider=self.other_provider,
            token=actor_token,
            user=other_user,
            auth_time=now(),
        )

        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": actor_token,
                "actor_token_type": TOKEN_TYPE_URI_JWT,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_actor_token_rejects_unknown_token(self):
        """test an actor_token value that doesn't match any real access token"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": "not-a-real-token",
                "actor_token_type": TOKEN_TYPE_URI_JWT,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_actor_token_rejects_unknown_builtin_token(self):
        """test a built-in actor_token value that doesn't match any real Token"""
        actor = Actor.for_user(self.user, ActorPolicyInheritance.NONE)
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_TOKEN_EXCHANGE,
                "scope": SCOPES,
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "subject_token": self.subject_token,
                "subject_token_type": TOKEN_TYPE_URI_ACCESS_TOKEN,
                "actor_token": "not-a-real-token",
                "actor_token_type": TOKEN_TYPE_URI_AUTHENTIK_TOKEN,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")
        self.assertFalse(AccessToken.objects.filter(actor=actor).exists())

    def test_actor_token_absent_is_unaffected(self):
        """test that plain token exchange (no actor_token) is completely unaffected --
        no actor recorded, no act claim, no enterprise license even required"""
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
        jwt = self._decode(body["access_token"])
        self.assertNotIn("act", jwt)
        access_token = AccessToken.objects.get(token=body["access_token"])
        self.assertIsNone(access_token.actor_id)
        self.assertEqual(access_token.user_id, self.user.pk)
