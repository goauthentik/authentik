"""Test grants bound to a client within a provider, and access token audiences"""

from base64 import b64encode
from dataclasses import dataclass
from datetime import timedelta
from json import dumps, loads
from unittest.mock import patch

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.client import (
    ClientAdapter,
    ClientAuthMethod,
    LegacyClientAdapter,
    OAuthClientContext,
    OAuthClientResolver,
    ProviderSelector,
)
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientBoundModel,
    ClientGrantBinding,
    ClientType,
    DeviceToken,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
    hash_client_id,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.utils import find_client_token
from authentik.providers.oauth2.views.token import TokenView

CLIENT_A = "https://a.example.com/oauth/client.json"
CLIENT_B = "https://b.example.com/oauth/client.json"
REDIRECT_A = "http://127.0.0.1:1234/a/callback"
REDIRECT_B = "http://127.0.0.1:1234/b/callback"
RESOURCE = "https://mcp.example.com/mcp"


@dataclass(frozen=True, slots=True)
class SyntheticClientContext(OAuthClientContext):
    """Client of a registration kind core does not know, optionally bound to a
    credential managed elsewhere"""

    credential: str | None = None
    credential_version: str | None = None
    auth_method: str = ClientAuthMethod.NONE

    @property
    def token_endpoint_auth_method(self) -> str:
        return self.auth_method

    @property
    def grant_binding(self) -> ClientGrantBinding:
        return ClientGrantBinding(
            client_id=self.client_id,
            auth_method=self.token_endpoint_auth_method,
            external_binding=self.credential,
            external_binding_version=self.credential_version,
        )


def synthetic_client(provider: OAuth2Provider, client_id: str, **kwargs) -> SyntheticClientContext:
    """Public synthetic client on `provider`"""
    return SyntheticClientContext(
        provider=provider,
        client_id=client_id,
        registration_kind="synthetic",
        client_type=ClientType.PUBLIC,
        redirect_uris=(
            RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_A),
            RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_B),
        ),
        grant_types=frozenset(
            [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN, GrantType.DEVICE_CODE]
        ),
        **kwargs,
    )


class SyntheticAdapter(ClientAdapter):
    """Resolves the synthetic clients A and B on any provider"""

    def resolve(self, request, provider, client_id):
        if client_id in (CLIENT_A, CLIENT_B):
            return synthetic_client(provider, client_id)
        return None


class FixedSelector(ProviderSelector):
    """Always selects the same provider"""

    def __init__(self, provider: OAuth2Provider):
        self.provider = provider

    def select(self, request, client_id):
        return self.provider


class TestClientBoundGrants(OAuthTestCase):
    """Grants bound to a client within a provider"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            grant_types=[
                GrantType.AUTHORIZATION_CODE,
                GrantType.REFRESH_TOKEN,
                GrantType.DEVICE_CODE,
            ],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_A)],
            signing_key=self.keypair,
        )
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-offline_access",
                ]
            )
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.registered = OAuthClientContext.for_provider(self.provider)
        self.client_a = synthetic_client(self.provider, CLIENT_A)
        self.client_b = synthetic_client(self.provider, CLIENT_B)

    def token_request(self, client_id: str, **data):
        """POST to the token endpoint as `client_id`; synthetic clients are public"""
        kwargs = {}
        if client_id == self.provider.client_id:
            header = b64encode(f"{client_id}:{self.provider.client_secret}".encode()).decode()
            kwargs["HTTP_AUTHORIZATION"] = f"Basic {header}"
        else:
            data["client_id"] = client_id
        resolver = OAuthClientResolver(
            FixedSelector(self.provider), [LegacyClientAdapter(), SyntheticAdapter()]
        )
        with patch.object(TokenView, "get_client_resolver", return_value=resolver):
            return self.client.post(reverse("authentik_providers_oauth2:token"), data, **kwargs)

    def create_code(self, client: OAuthClientContext | None, **kwargs) -> AuthorizationCode:
        """Authorization code, bound to `client` unless it is None"""
        code = AuthorizationCode(
            provider=self.provider,
            user=self.user,
            code=generate_id(),
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(minutes=1),
            scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS],
        )
        if client:
            code.bind_client(client, redirect_uri=REDIRECT_A, **kwargs)
        code.save()
        return code

    def create_refresh_token(self, client: OAuthClientContext | None, **kwargs) -> RefreshToken:
        """Refresh token, bound to `client` unless it is None"""
        token = RefreshToken(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(days=1),
            _scope=f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
        )
        if client:
            token.bind_client(client, **kwargs)
        token.save()
        return token

    def redeem_code(self, client_id: str, code: AuthorizationCode, redirect_uri=REDIRECT_A):
        return self.token_request(
            client_id,
            grant_type=GRANT_TYPE_AUTHORIZATION_CODE,
            code=code.code,
            redirect_uri=redirect_uri,
        )

    def refresh(self, client_id: str, token: RefreshToken):
        return self.token_request(
            client_id,
            grant_type=GRANT_TYPE_REFRESH_TOKEN,
            refresh_token=token.token,
            scope=f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
        )

    def test_bind_client(self):
        """Binding records the exact client and its hash"""
        code = self.create_code(self.client_a, resource=RESOURCE)
        code.refresh_from_db()
        self.assertEqual(code.client_id, CLIENT_A)
        self.assertEqual(code.client_id_hash, hash_client_id(CLIENT_A))
        self.assertEqual(code.client_auth_method, ClientAuthMethod.NONE)
        self.assertEqual(code.redirect_uri, REDIRECT_A)
        self.assertEqual(code.resource, RESOURCE)
        self.assertIsNone(code.external_binding)
        self.assertEqual(code.bound_client_id, CLIENT_A)

    def test_bind_client_registered(self):
        """Grants of the registered client record it explicitly"""
        code = self.create_code(self.registered)
        self.assertEqual(code.client_id, self.provider.client_id)
        self.assertEqual(code.client_auth_method, ClientAuthMethod.CLIENT_SECRET_BASIC)
        self.assertTrue(code.is_bound_to(self.registered))
        self.assertTrue(code.is_bound_to_registered_client())
        self.assertFalse(code.is_bound_to(self.client_a))

    def test_bind_client_other_provider(self):
        """A grant cannot be bound to a client of another provider"""
        other = OAuth2Provider.objects.create(name=generate_id(), authorization_flow=None)
        code = AuthorizationCode(provider=other, user=self.user)
        with self.assertRaises(ValueError):
            code.bind_client(self.client_a)

    def test_save_keeps_hash(self):
        """The hash follows the client identifier"""
        code = self.create_code(self.client_a)
        code.client_id = CLIENT_B
        code.save()
        code.refresh_from_db()
        self.assertEqual(code.client_id_hash, hash_client_id(CLIENT_B))

    def test_unbound_grant(self):
        """Grants without a binding belong to the registered client only"""
        code = self.create_code(None)
        self.assertFalse(code.is_client_bound)
        self.assertIsNone(code.client_id_hash)
        self.assertEqual(code.bound_client_id, self.provider.client_id)
        self.assertTrue(code.is_bound_to(self.registered))
        self.assertTrue(code.is_bound_to_registered_client())
        self.assertFalse(code.is_bound_to(self.client_a))
        # A synthetic client using the registered client_id is still not the registered client
        self.assertFalse(code.is_bound_to(synthetic_client(self.provider, self.provider.client_id)))

    def test_binding_attributes(self):
        """Method and external binding are compared for non-legacy clients"""
        code = self.create_code(self.client_a)
        self.assertTrue(code.is_bound_to(self.client_a))
        self.assertFalse(code.is_bound_to(self.client_b))
        self.assertFalse(
            code.is_bound_to(synthetic_client(self.provider, CLIENT_A, auth_method="other"))
        )
        self.assertFalse(
            code.is_bound_to(synthetic_client(self.provider, CLIENT_A, credential="1"))
        )

        managed = synthetic_client(
            self.provider, CLIENT_A, credential="cred", credential_version="1"
        )
        code = self.create_code(managed)
        self.assertEqual(code.external_binding, "cred")
        self.assertEqual(code.external_binding_version, "1")
        self.assertTrue(code.is_bound_to(managed))
        self.assertFalse(code.is_bound_to(self.client_a))
        self.assertFalse(
            code.is_bound_to(
                synthetic_client(self.provider, CLIENT_A, credential="cred", credential_version="2")
            )
        )
        self.assertFalse(code.is_bound_to_registered_client())

    def test_registered_client_ignores_method(self):
        """Registered clients follow their provider's current client type"""
        code = self.create_code(self.registered)
        self.provider.client_type = ClientType.PUBLIC
        self.provider.save()
        self.assertTrue(code.is_bound_to(OAuthClientContext.for_provider(self.provider)))

    def test_bound_to_q(self):
        """Lookups by client narrow to the client's grants and unbound grants"""
        unbound = self.create_code(None)
        registered = self.create_code(self.registered)
        code_a = self.create_code(self.client_a)
        code_b = self.create_code(self.client_b)
        lookup = AuthorizationCode.objects.filter
        self.assertEqual(
            set(lookup(ClientBoundModel.bound_to_q(self.registered))), {unbound, registered}
        )
        self.assertEqual(set(lookup(ClientBoundModel.bound_to_q(self.client_a))), {code_a})
        self.assertEqual(set(lookup(ClientBoundModel.bound_to_q(self.client_b))), {code_b})
        self.assertEqual(
            set(lookup(ClientBoundModel.registered_client_q(), provider=self.provider)),
            {unbound, registered},
        )

    def test_bound_to_q_hash_collision(self):
        """A row whose hash matches but whose client identifier differs is not returned"""
        code = self.create_code(self.client_b)
        AuthorizationCode.objects.filter(pk=code.pk).update(client_id_hash=hash_client_id(CLIENT_A))
        self.assertFalse(
            AuthorizationCode.objects.filter(ClientBoundModel.bound_to_q(self.client_a)).exists()
        )

    def test_code_cross_client(self):
        """A code issued to client A cannot be redeemed by client B"""
        code = self.create_code(self.client_a)
        response = self.redeem_code(CLIENT_B, code)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_grant")
        self.assertTrue(AuthorizationCode.objects.filter(pk=code.pk).exists())
        # Nor by the provider's registered client
        response = self.redeem_code(self.provider.client_id, code)
        self.assertEqual(response.status_code, 400)

    def test_code_unbound_synthetic(self):
        """A code without a binding cannot be redeemed by a synthetic client"""
        code = self.create_code(None)
        response = self.redeem_code(CLIENT_A, code)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_grant")

    def test_code_redirect_uri(self):
        """Non-legacy clients must redeem with the exact authorized redirect URI"""
        code = self.create_code(self.client_a)
        response = self.redeem_code(CLIENT_A, code, redirect_uri=REDIRECT_B)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_grant")

    def test_code_flow(self):
        """Client A redeems its code and refreshes; tokens stay bound to A"""
        code = self.create_code(self.client_a, resource=RESOURCE)
        response = self.redeem_code(CLIENT_A, code)
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content)
        access = AccessToken.objects.get(token=body["access_token"])
        refresh = RefreshToken.objects.get(token=body["refresh_token"])
        for token in (access, refresh):
            self.assertEqual(token.client_id, CLIENT_A)
            self.assertEqual(token.redirect_uri, REDIRECT_A)
            self.assertEqual(token.resource, RESOURCE)
        self.assertIsNotNone(refresh.family_id)

        # Client B cannot use A's refresh token, and doing so does not revoke it
        response = self.refresh(CLIENT_B, refresh)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_grant")
        refresh.refresh_from_db()
        self.assertFalse(refresh.revoked)

        response = self.refresh(CLIENT_A, refresh)
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content)
        successor = RefreshToken.objects.get(token=body["refresh_token"])
        self.assertEqual(successor.family_id, refresh.family_id)
        self.assertEqual(successor.client_id, CLIENT_A)
        self.assertEqual(successor.redirect_uri, REDIRECT_A)
        self.assertEqual(successor.resource, RESOURCE)
        self.assertEqual(AccessToken.objects.get(token=body["access_token"]).resource, RESOURCE)

    def test_refresh_new_family(self):
        """Separate grants start separate families"""
        first = self.create_refresh_token(self.client_a)
        second = self.create_refresh_token(self.client_a)
        self.assertNotEqual(first.family_id, second.family_id)

    def test_refresh_unbound(self):
        """Refresh tokens without a binding keep working for the registered client, and
        their successors are bound to it explicitly and start a family"""
        token = self.create_refresh_token(None)
        RefreshToken.objects.filter(pk=token.pk).update(family_id=None)
        response = self.refresh(CLIENT_A, token)
        self.assertEqual(response.status_code, 400)

        response = self.refresh(self.provider.client_id, token)
        self.assertEqual(response.status_code, 200, response.content)
        successor = RefreshToken.objects.get(token=loads(response.content)["refresh_token"])
        self.assertEqual(successor.client_id, self.provider.client_id)
        self.assertEqual(successor.client_auth_method, ClientAuthMethod.CLIENT_SECRET_BASIC)
        self.assertIsNotNone(successor.family_id)

    def test_refresh_cross_client_revoked(self):
        """Another client presenting a revoked token is rejected before revocation is
        considered"""
        token = self.create_refresh_token(self.client_a)
        token.revoked = True
        token.save()
        response = self.refresh(CLIENT_B, token)
        self.assertEqual(response.status_code, 400)

    def test_device_code_cross_client(self):
        """A device code issued to client A cannot be redeemed by client B"""
        device = DeviceToken(
            provider=self.provider,
            user=self.user,
            expires=timezone.now() + timedelta(minutes=5),
            _scope=SCOPE_OPENID,
        )
        device.bind_client(self.client_a, resource=RESOURCE)
        device.save()
        self.assertEqual(device.client_id_hash, hash_client_id(CLIENT_A))
        response = self.token_request(
            CLIENT_B, grant_type=GRANT_TYPE_DEVICE_CODE, device_code=device.device_code
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_grant")

        response = self.token_request(
            CLIENT_A, grant_type=GRANT_TYPE_DEVICE_CODE, device_code=device.device_code
        )
        self.assertEqual(response.status_code, 200, response.content)
        access = AccessToken.objects.get(token=loads(response.content)["access_token"])
        self.assertEqual(access.client_id, CLIENT_A)
        self.assertEqual(access.resource, RESOURCE)

    def test_device_backchannel_binds(self):
        """Device authorization binds the device code to the registered client"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={"client_id": self.provider.client_id, "scope": SCOPE_OPENID},
        )
        self.assertEqual(response.status_code, 200)
        device = DeviceToken.objects.get(device_code=loads(response.content)["device_code"])
        self.assertEqual(device.client_id, self.provider.client_id)
        self.assertTrue(device.is_bound_to(self.registered))

    def test_find_client_token(self):
        """Introspection and revocation only find the presenting client's tokens"""
        token_a = self.create_refresh_token(self.client_a)
        unbound = self.create_refresh_token(None)
        self.assertEqual(find_client_token(token_a.token, self.client_a), token_a)
        self.assertIsNone(find_client_token(token_a.token, self.client_b))
        self.assertIsNone(find_client_token(token_a.token, self.registered))
        self.assertEqual(find_client_token(unbound.token, self.registered), unbound)
        self.assertIsNone(find_client_token(unbound.token, self.client_a))

    def test_find_client_token_federated(self):
        """Federation reaches only the registered client's tokens of the other provider"""
        other = OAuth2Provider.objects.create(name=generate_id(), authorization_flow=None)
        other.jwt_federation_providers.add(self.provider)
        other_client = synthetic_client(other, CLIENT_A)
        registered_token = RefreshToken(
            provider=other,
            user=self.user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=timezone.now(),
        )
        registered_token.bind_client(OAuthClientContext.for_provider(other))
        registered_token.save()
        synthetic_token = RefreshToken(
            provider=other,
            user=self.user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=timezone.now(),
        )
        synthetic_token.bind_client(other_client)
        synthetic_token.save()
        self.assertEqual(
            find_client_token(registered_token.token, self.registered, include_federated=True),
            registered_token,
        )
        self.assertIsNone(find_client_token(registered_token.token, self.registered))
        self.assertIsNone(
            find_client_token(synthetic_token.token, self.registered, include_federated=True)
        )

    def test_introspect_cross_client(self):
        """The registered client cannot introspect or revoke a synthetic client's token"""
        token = self.create_refresh_token(self.client_a)
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            data={"token": token.token},
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertJSONEqual(response.content, {"active": False})
        response = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            data={"token": token.token},
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(RefreshToken.objects.filter(pk=token.pk).exists())


class TestTokenAudiences(OAuthTestCase):
    """Client and resource audiences"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=self.keypair,
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )

    def issue(self, client: OAuthClientContext | None, resource: str | None = None):
        """Issue an access token, returning it with its ID token and access claims"""
        token = AccessToken(
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(minutes=5),
            scope=[SCOPE_OPENID],
        )
        if client:
            token.bind_client(client, resource=resource)
        id_token = IDToken.new(self.provider, token, self.factory.get("/"))
        token.id_token = id_token
        token.save()
        key = self.provider.signing_key.public_key
        claims = decode(token.token, key, algorithms=["RS256"], options={"verify_aud": False})
        return token, id_token, claims

    def test_registered_unchanged(self):
        """Without a resource, access tokens keep the client audience and claim layout"""
        _, unbound_id, unbound = self.issue(None)
        _, bound_id, bound = self.issue(OAuthClientContext.for_provider(self.provider))
        for id_token, claims in ((unbound_id, unbound), (bound_id, bound)):
            self.assertEqual(id_token.aud, self.provider.client_id)
            self.assertEqual(claims["aud"], self.provider.client_id)
            self.assertEqual(claims["azp"], self.provider.client_id)
            self.assertNotIn("client_id", claims)
        # Same claims in the same order, apart from per-token random values
        for claims in (unbound, bound):
            for key in ("jti", "uid", "iat", "exp"):
                claims.pop(key)
        self.assertEqual(list(unbound.items()), list(bound.items()))

    def test_resource_audience(self):
        """With a resource, the access token targets it; the ID token targets the client"""
        client = synthetic_client(self.provider, CLIENT_A)
        token, id_token, claims = self.issue(client, RESOURCE)
        self.assertEqual(id_token.aud, CLIENT_A)
        self.assertEqual(id_token.to_dict()["aud"], CLIENT_A)
        self.assertEqual(claims["aud"], RESOURCE)
        self.assertEqual(claims["client_id"], CLIENT_A)
        self.assertEqual(claims["azp"], CLIENT_A)
        self.assertNotEqual(id_token.aud, claims["aud"])
        # The stored ID token keeps the client audience
        self.assertEqual(AccessToken.objects.get(pk=token.pk).id_token.aud, CLIENT_A)

    def test_synthetic_without_resource(self):
        """Without a resource, a synthetic client is the audience of both tokens"""
        _, id_token, claims = self.issue(synthetic_client(self.provider, CLIENT_A))
        self.assertEqual(id_token.aud, CLIENT_A)
        self.assertEqual(claims["aud"], CLIENT_A)
        self.assertEqual(claims["azp"], CLIENT_A)

    def test_resource_overrides_claim_overlay(self):
        """Custom claims cannot override the enforced resource audience"""
        client = synthetic_client(self.provider, CLIENT_A)
        token = AccessToken(
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(minutes=5),
        )
        token.bind_client(client, resource=RESOURCE)
        id_token = IDToken.new(self.provider, token, self.factory.get("/"))
        id_token.claims = {"aud": "https://evil.example.com", "azp": "evil"}
        token.id_token = id_token
        key = self.provider.signing_key.public_key
        claims = decode(token.token, key, algorithms=["RS256"], options={"verify_aud": False})
        self.assertEqual(claims["aud"], RESOURCE)
        self.assertEqual(claims["azp"], CLIENT_A)

    def test_introspection_audience(self):
        """Introspection reports the bound client and the resource audience"""
        self.provider.client_type = ClientType.CONFIDENTIAL
        self.provider.save()
        token, _, _ = self.issue(OAuthClientContext.for_provider(self.provider), RESOURCE)
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            data={"token": token.token},
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        body = loads(response.content)
        self.assertTrue(body["active"])
        self.assertEqual(body["aud"], RESOURCE)
        self.assertEqual(body["client_id"], self.provider.client_id)
