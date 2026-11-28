"""Test refresh token hashing, rotation and reuse detection"""

from base64 import b64encode
from datetime import timedelta
from json import dumps, loads

from django.http import HttpResponse
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
)
from authentik.core.models import Application, User
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
    hash_refresh_token,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestRefreshTokenRotation(OAuthTestCase):
    """Test refresh token hashing, rotation and reuse detection"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.user = create_test_admin_user()

    def _create_refresh_token_provider(self, **kwargs) -> tuple[OAuth2Provider, str]:
        """Create a provider with the refresh token grant, returns the provider and its
        basic auth header"""
        kwargs.setdefault("grant_types", [GrantType.REFRESH_TOKEN])
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            client_type=ClientType.CONFIDENTIAL,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=self.keypair,
            **kwargs,
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-offline_access",
                ]
            )
        )
        # Needs to be assigned to an application for iss to be set
        self.app.provider = provider
        self.app.save()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        return provider, header

    def _create_refresh_token(
        self, provider: OAuth2Provider, user: User | None = None
    ) -> RefreshToken:
        return RefreshToken.objects.create(
            provider=provider,
            user=user or self.user,
            _id_token=dumps({}),
            auth_time=now(),
            _scope="offline_access",
            expires=now() + timedelta(days=30),
        )

    def _refresh(self, header: str, refresh_token: str) -> HttpResponse:
        """Send a refresh token grant request"""
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": refresh_token,
                "redirect_uri": "http://testserver",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )

    def _rotate(self, header: str, refresh_token: str) -> str:
        """Refresh successfully, returns the new refresh token"""
        response = self._refresh(header, refresh_token)
        self.assertEqual(response.status_code, 200, response.content)
        return loads(response.content.decode())["refresh_token"]

    def _suspicious_events(self):
        return Event.objects.filter(action=EventAction.SUSPICIOUS_REQUEST)

    def _exchange_code(self, provider: OAuth2Provider, header: str) -> dict:
        """Run the authorization code grant with offline_access, returns the token response"""
        code = AuthorizationCode.objects.create(
            code=generate_id(),
            provider=provider,
            user=self.user,
            auth_time=now(),
            _scope="openid offline_access",
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "redirect_uri": "http://testserver",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 200, response.content)
        return loads(response.content.decode())

    def _userinfo(self, access_token: str) -> HttpResponse:
        return self.client.get(
            reverse("authentik_providers_oauth2:userinfo"),
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

    def test_new_provider_defaults(self):
        """New providers revoke the family on reuse"""
        provider, _ = self._create_refresh_token_provider()
        self.assertTrue(provider.refresh_token_revoke_family_on_reuse)
        self.assertEqual(provider.refresh_token_reuse_grace_period, "seconds=30")

    def test_token_hashed_at_rest(self):
        """Only the hash of a refresh token is stored"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        new_token = self._rotate(header, token.token)
        stored = RefreshToken.objects.get(revoked=False)
        self.assertIsNone(stored.legacy_token)
        self.assertIsNone(stored.token)
        self.assertEqual(stored.token_hash, hash_refresh_token(new_token))
        self.assertEqual(stored.family, token.family)
        token.refresh_from_db()
        self.assertTrue(token.revoked)
        self.assertIsNotNone(token.rotated_at)

    def test_legacy_plaintext_token(self):
        """A token issued by an older version (plaintext only, no hash or family) still works,
        is hashed when saved and starts a family"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        raw = generate_id()
        RefreshToken.objects.filter(pk=token.pk).update(
            legacy_token=raw, token_hash=None, family=None
        )
        new_token = self._rotate(header, raw)
        token.refresh_from_db()
        self.assertTrue(token.revoked)
        self.assertEqual(token.token_hash, hash_refresh_token(raw))
        self.assertIsNotNone(token.family)
        new = RefreshToken.objects.get(RefreshToken.token_query(new_token))
        self.assertEqual(new.family, token.family)
        self.assertEqual(AccessToken.objects.get().family, token.family)

    def test_reuse_revokes_family(self):
        """Reuse of a rotated token outside the grace period revokes the whole family"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        first = self._rotate(header, token.token)
        second = self._rotate(header, first)
        with freeze_time(now() + timedelta(minutes=1)):
            response = self._refresh(header, first)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(loads(response.content.decode())["error"], "invalid_grant")
            self.assertTrue(self._suspicious_events().get().context["family_revoked"])
            # The newest token of the family is revoked too
            self.assertEqual(self._refresh(header, second).status_code, 400)
        self.assertFalse(RefreshToken.objects.filter(revoked=False).exists())

    def test_reuse_revokes_access_tokens(self):
        """Reuse revokes the access tokens of the family too, from both the initial grant and
        later refreshes, and leaves other families alone"""
        provider, header = self._create_refresh_token_provider(
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN]
        )
        initial = self._exchange_code(provider, header)
        other = self._exchange_code(provider, header)
        refreshed = loads(self._refresh(header, initial["refresh_token"]).content.decode())
        family = RefreshToken.objects.get(RefreshToken.token_query(initial["refresh_token"])).family
        self.assertEqual(
            set(AccessToken.objects.filter(family=family).values_list("token", flat=True)),
            {initial["access_token"], refreshed["access_token"]},
        )
        self.assertEqual(self._userinfo(refreshed["access_token"]).status_code, 200)
        with freeze_time(now() + timedelta(minutes=1)):
            self.assertEqual(self._refresh(header, initial["refresh_token"]).status_code, 400)
            for access_token in (initial["access_token"], refreshed["access_token"]):
                self.assertEqual(self._userinfo(access_token).status_code, 401)
            self.assertTrue(
                self._suspicious_events()
                .filter(context__message="Revoked access token was used")
                .exists()
            )
            self.assertEqual(self._userinfo(other["access_token"]).status_code, 200)
        self.assertFalse(AccessToken.objects.filter(family=family, revoked=False).exists())
        self.assertFalse(
            AccessToken.objects.filter(token=other["access_token"], revoked=True).exists()
        )

    def test_reuse_revokes_only_own_family(self):
        """Revoking a family leaves other families of the same user alone"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        other = self._rotate(header, self._create_refresh_token(provider).token)
        self._rotate(header, token.token)
        with freeze_time(now() + timedelta(minutes=1)):
            self.assertEqual(self._refresh(header, token.token).status_code, 400)
            self._rotate(header, other)

    def test_reuse_within_grace_period(self):
        """The most recently rotated token may be reused within the grace period"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        first = self._rotate(header, token.token)
        # e.g. the client didn't receive the response and retries
        retried = self._rotate(header, token.token)
        self.assertFalse(self._suspicious_events().exists())
        self._rotate(header, first)
        self._rotate(header, retried)

    def test_reuse_within_grace_period_keeps_rotation_time(self):
        """Reusing a token within the grace period doesn't extend the grace period"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        self._rotate(header, token.token)
        token.refresh_from_db()
        rotated_at = token.rotated_at
        with freeze_time(now() + timedelta(seconds=20)):
            self._rotate(header, token.token)
        token.refresh_from_db()
        self.assertEqual(token.rotated_at, rotated_at)
        with freeze_time(now() + timedelta(seconds=40)):
            self.assertEqual(self._refresh(header, token.token).status_code, 400)

    def test_reuse_grace_period_only_most_recent(self):
        """The grace period only applies to the most recently rotated token"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        first = self._rotate(header, token.token)
        with freeze_time(now() + timedelta(seconds=1)):
            second = self._rotate(header, first)
            self.assertEqual(self._refresh(header, token.token).status_code, 400)
            self.assertEqual(self._refresh(header, second).status_code, 400)

    def test_reuse_grace_period_revoked_family(self):
        """The grace period doesn't apply when the family has no active token anymore"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        first = self._rotate(header, token.token)
        # The active token was revoked by the client (RFC 7009 deletes it)
        RefreshToken.objects.filter(RefreshToken.token_query(first)).delete()
        self.assertEqual(self._refresh(header, token.token).status_code, 400)
        self.assertTrue(self._suspicious_events().exists())

    def test_reuse_grace_period_disabled(self):
        """With a grace period of 0, any reuse revokes the family"""
        provider, header = self._create_refresh_token_provider(
            refresh_token_reuse_grace_period="seconds=0"  # nosec
        )
        token = self._create_refresh_token(provider)
        first = self._rotate(header, token.token)
        self.assertEqual(self._refresh(header, token.token).status_code, 400)
        self.assertEqual(self._refresh(header, first).status_code, 400)

    def test_reuse_family_revocation_disabled(self):
        """With family revocation disabled, reuse is rejected and logged, there is no grace
        period, and the newest token of the family stays valid"""
        provider, header = self._create_refresh_token_provider(
            refresh_token_revoke_family_on_reuse=False
        )
        token = self._create_refresh_token(provider)
        first = self._rotate(header, token.token)
        self.assertEqual(self._refresh(header, token.token).status_code, 400)
        self.assertFalse(self._suspicious_events().get().context["family_revoked"])
        self.assertFalse(AccessToken.objects.filter(revoked=True).exists())
        self._rotate(header, first)

    def test_reuse_without_family(self):
        """Reuse of a token without a family (issued by an older version) only revokes that
        token, not every other token without a family"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        other_user = create_test_admin_user()
        other = self._create_refresh_token(provider, other_user)
        RefreshToken.objects.filter(pk__in=[token.pk, other.pk]).update(family=None)
        RefreshToken.objects.filter(pk=token.pk).update(revoked=True)
        self.assertEqual(self._refresh(header, token.token).status_code, 400)
        self._rotate(header, other.token)

    def test_token_query_empty(self):
        """An empty token never matches tokens without a plaintext value"""
        provider, _ = self._create_refresh_token_provider()
        self._create_refresh_token(provider)
        for raw in (None, ""):
            self.assertFalse(RefreshToken.objects.filter(RefreshToken.token_query(raw)).exists())

    def test_revoke_endpoint(self):
        """RFC 7009 revocation finds hashed tokens, and a request without a token revokes
        nothing"""
        provider, header = self._create_refresh_token_provider()
        token = self._create_refresh_token(provider)
        other = self._create_refresh_token(provider)
        response = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RefreshToken.objects.count(), 2)
        response = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            data={"token": token.token},
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(RefreshToken.objects.all()), [other])

    def test_legacy_token_refreshed_without_rotation(self):
        """A token issued by an older version (existing tokens aren't backfilled by the
        migration) is hashed and starts a family when it is first refreshed, even when it isn't
        rotated, and the access token issued from it joins that family"""
        provider, header = self._create_refresh_token_provider(
            refresh_token_threshold="seconds=1"  # nosec
        )
        token = self._create_refresh_token(provider)
        raw = generate_id()
        RefreshToken.objects.filter(pk=token.pk).update(
            legacy_token=raw, token_hash=None, family=None
        )
        response = self._refresh(header, raw)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotIn("refresh_token", loads(response.content.decode()))
        token.refresh_from_db()
        self.assertFalse(token.revoked)
        self.assertEqual(token.token_hash, hash_refresh_token(raw))
        self.assertIsNotNone(token.family)
        # The plaintext is kept until a future release
        self.assertEqual(token.legacy_token, raw)
        self.assertEqual(AccessToken.objects.get().family, token.family)
        # Found by its hash from now on
        self._refresh(header, raw)
        self.assertEqual(RefreshToken.objects.get(token_hash=hash_refresh_token(raw)).pk, token.pk)
