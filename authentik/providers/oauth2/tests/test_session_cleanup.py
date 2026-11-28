"""Test tokens being issued for a session while that session is cleaned up"""

from concurrent.futures import Future, ThreadPoolExecutor, wait
from datetime import timedelta
from json import dumps

from django.db import IntegrityError, connections
from django.db.models.signals import pre_delete
from django.test import TransactionTestCase
from django.utils.timezone import now

from authentik.core.models import AuthenticatedSession, Session
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
)


class TestSessionCleanupRace(TransactionTestCase):
    """Committed rows and separate connections, as the foreign keys from tokens to their
    session are only checked when the transaction deleting the session is committed."""

    def setUp(self):
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.REFRESH_TOKEN],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
        )
        self.sessions = [
            self.create_session(now() - timedelta(minutes=5)).session_id for _ in range(6)
        ]
        for session_id in self.sessions:
            self.create_token(RefreshToken, session_id)
            self.create_token(AccessToken, session_id)
        self.live = self.create_session(now() + timedelta(hours=1)).session_id
        self.create_token(RefreshToken, self.live)

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

    def expired(self):
        return Session.objects.including_expired().filter(expiring=True, expires__lt=now())

    def issue_while_deleting(self, model, session_id: str) -> list[Future]:
        """Issue a token bound to a session while that session is being deleted, after the
        objects referencing it have been collected."""
        executor = ThreadPoolExecutor(max_workers=1)
        self.addCleanup(executor.shutdown)
        issued: list[Future] = []

        def issue():
            try:
                self.create_token(model, session_id)
            finally:
                connections.close_all()

        def receiver(sender, instance: AuthenticatedSession, **_):
            if instance.session_id != session_id or issued:
                return
            issued.append(executor.submit(issue))
            # The token's foreign key check waits for the session to be deleted
            done, _ = wait(issued, timeout=1)
            self.assertFalse(done)

        pre_delete.connect(receiver, sender=AuthenticatedSession)
        self.addCleanup(pre_delete.disconnect, receiver, sender=AuthenticatedSession)
        return issued

    def test_refresh_token_issued_while_deleting(self):
        """A refresh token issued while its session is deleted does not fail the cleanup"""
        issued = self.issue_while_deleting(RefreshToken, self.sessions[2])
        self.assertEqual(delete_in_batches(self.expired()), len(self.sessions))
        with self.assertRaises(IntegrityError):
            issued[0].result(timeout=10)
        self.assertFalse(self.expired().exists())
        self.assertTrue(Session.objects.filter(pk=self.live).exists())
        # Refresh tokens outlive their session
        self.assertEqual(RefreshToken.objects.filter(session=None).count(), len(self.sessions))
        self.assertEqual(RefreshToken.objects.filter(session_id=self.live).count(), 1)

    def test_access_token_issued_while_deleting(self):
        """An access token issued while its session is deleted does not fail the cleanup"""
        issued = self.issue_while_deleting(AccessToken, self.sessions[2])
        self.assertEqual(delete_in_batches(self.expired(), batch_size=1), len(self.sessions))
        with self.assertRaises(IntegrityError):
            issued[0].result(timeout=10)
        self.assertFalse(self.expired().exists())
        self.assertTrue(Session.objects.filter(pk=self.live).exists())
        # Access tokens do not outlive their session
        self.assertFalse(AccessToken.objects.exists())
