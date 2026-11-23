"""Test tokens being issued for a session while that session is cleaned up"""

from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from json import dumps

from django.db import IntegrityError, connections
from django.db.models.signals import pre_delete, pre_save
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils.timezone import now

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import GRANT_TYPE_REFRESH_TOKEN
from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.lib.utils.db import delete_in_batches
from authentik.providers.oauth2.models import (
    AccessToken,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class SessionCleanupMixin:
    """Helpers to create sessions and the tokens bound to them"""

    def create_provider(self) -> OAuth2Provider:
        return OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.REFRESH_TOKEN],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
        )

    def create_session(self, expires) -> AuthenticatedSession:
        return AuthenticatedSession.objects.create(
            session=Session.objects.create(
                session_key=generate_id(),
                last_ip="255.255.255.255",
                last_user_agent="",
                expires=expires,
            ),
            user=self.user,
        )

    def create_token(self, model, session_id: str | None):
        return model.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=now(),
            _scope="offline_access",
            session_id=session_id,
        )


class TestSessionCleanupRace(SessionCleanupMixin, TransactionTestCase):
    """Committed rows and separate connections, as the foreign keys from tokens to their
    session are only checked when the transaction deleting the session is committed."""

    def setUp(self):
        self.user = create_test_admin_user()
        self.provider = self.create_provider()
        self.sessions = [
            self.create_session(now() - timedelta(minutes=5)).session_id for _ in range(6)
        ]
        for session_id in self.sessions:
            self.create_token(RefreshToken, session_id)
            self.create_token(AccessToken, session_id)
        self.live = self.create_session(now() + timedelta(hours=1)).session_id
        self.create_token(RefreshToken, self.live)

    def expired(self):
        return Session.objects.including_expired().filter(expiring=True, expires__lt=now())

    def issue_while_deleting(self, model, session_ids: set[str], once: bool):
        """Issue a token bound to a session while that session is being deleted, after the
        objects referencing it have been collected."""
        issued = set()

        def issue(session_id: str):
            try:
                self.create_token(model, session_id)
            finally:
                connections.close_all()

        def receiver(sender, instance: AuthenticatedSession, **_):
            if instance.session_id not in session_ids:
                return
            if once and instance.session_id in issued:
                return
            issued.add(instance.session_id)
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(issue, instance.session_id).result(timeout=10)

        pre_delete.connect(receiver, sender=AuthenticatedSession)
        self.addCleanup(pre_delete.disconnect, receiver, sender=AuthenticatedSession)
        return receiver

    def test_refresh_token_issued_while_deleting(self):
        """A refresh token issued while its session is deleted does not fail the cleanup"""
        self.issue_while_deleting(RefreshToken, {self.sessions[2]}, once=True)
        self.assertEqual(delete_in_batches(self.expired()), len(self.sessions))
        self.assertFalse(self.expired().exists())
        self.assertTrue(Session.objects.filter(pk=self.live).exists())
        # Refresh tokens outlive their session
        self.assertEqual(RefreshToken.objects.filter(session=None).count(), len(self.sessions) + 1)
        self.assertEqual(RefreshToken.objects.filter(session_id=self.live).count(), 1)

    def test_access_token_issued_while_deleting(self):
        """An access token issued while its session is deleted does not fail the cleanup"""
        self.issue_while_deleting(AccessToken, {self.sessions[2]}, once=True)
        self.assertEqual(delete_in_batches(self.expired()), len(self.sessions))
        self.assertFalse(self.expired().exists())
        self.assertTrue(Session.objects.filter(pk=self.live).exists())
        # Access tokens do not outlive their session
        self.assertFalse(AccessToken.objects.exists())

    def test_token_issued_while_deleting_single_row(self):
        """A batch of a single session is attempted again as well"""
        self.issue_while_deleting(AccessToken, {self.sessions[2]}, once=True)
        self.assertEqual(delete_in_batches(self.expired(), batch_size=1), len(self.sessions))
        self.assertFalse(self.expired().exists())

    def test_token_issued_on_every_attempt(self):
        """A session that tokens keep being issued for is left for the next cleanup, without
        preventing the cleanup of the other sessions"""
        victim = self.sessions[2]
        receiver = self.issue_while_deleting(AccessToken, {victim}, once=False)
        self.assertEqual(delete_in_batches(self.expired()), len(self.sessions) - 1)
        self.assertEqual(list(self.expired().values_list("pk", flat=True)), [victim])
        pre_delete.disconnect(receiver, sender=AuthenticatedSession)
        self.assertEqual(delete_in_batches(self.expired()), 1)
        self.assertFalse(AccessToken.objects.exists())

    def test_nothing_can_be_deleted(self):
        """When no row of a batch can be deleted the error is not hidden"""
        self.issue_while_deleting(AccessToken, set(self.sessions), once=False)
        with self.assertRaises(IntegrityError):
            delete_in_batches(self.expired())
        self.assertEqual(self.expired().count(), len(self.sessions))


class TestTokenExpiredSession(SessionCleanupMixin, OAuthTestCase):
    """Test that tokens are only bound to a session that is still valid"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.provider = self.create_provider()
        self.provider.signing_key = self.keypair
        self.provider.save()
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-offline_access",
                ]
            )
        )
        # Needs to be assigned to an application for iss to be set
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=self.provider)

    def refresh(
        self, session: AuthenticatedSession, token: RefreshToken | None = None
    ) -> tuple[AccessToken, RefreshToken]:
        token = token or self.create_token(RefreshToken, session.session_id)
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        return (
            AccessToken.objects.get(token=body["access_token"]),
            RefreshToken.objects.get(token=body["refresh_token"]),
        )

    def test_refresh_valid_session(self):
        """Tokens issued from a refresh token stay bound to its session"""
        self.client.force_login(self.user)
        session = AuthenticatedSession.objects.get(session_id=self.client.session.session_key)
        access, refresh = self.refresh(session)
        self.assertEqual(access.session_id, session.session_id)
        self.assertEqual(refresh.session_id, session.session_id)

    def test_refresh_expired_session(self):
        """Tokens issued after the session expired are not bound to it, and are not removed
        when the session is cleaned up"""
        session = self.create_session(now() - timedelta(minutes=1))
        access, refresh = self.refresh(session)
        self.assertIsNone(access.session_id)
        self.assertIsNone(refresh.session_id)
        delete_in_batches(
            Session.objects.including_expired().filter(expiring=True, expires__lt=now())
        )
        self.assertFalse(AuthenticatedSession.objects.filter(pk=session.pk).exists())
        self.assertTrue(AccessToken.objects.filter(pk=access.pk).exists())
        self.assertTrue(RefreshToken.objects.filter(pk=refresh.pk).exists())

    def test_refresh_session_cleaned_up_during_request(self):
        """Revoking the previous refresh token does not bind it to its session again when the
        session has been cleaned up since the token was loaded"""
        session = self.create_session(now() - timedelta(minutes=1))
        token = self.create_token(RefreshToken, session.session_id)

        def cleanup(sender, **_):
            delete_in_batches(
                Session.objects.including_expired().filter(expiring=True, expires__lt=now())
            )

        pre_save.connect(cleanup, sender=AccessToken)
        self.addCleanup(pre_save.disconnect, cleanup, sender=AccessToken)
        self.refresh(session, token)
        self.assertFalse(AuthenticatedSession.objects.filter(pk=session.pk).exists())
        token.refresh_from_db()
        self.assertTrue(token.revoked)
        self.assertIsNone(token.session_id)
