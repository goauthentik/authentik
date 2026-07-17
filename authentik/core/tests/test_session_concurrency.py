"""Concurrent session user switching tests."""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier

from django.db import close_old_connections
from django.test import TransactionTestCase
from django.utils.crypto import get_random_string

from authentik.core import user_switching
from authentik.core.models import AuthenticatedSession
from authentik.core.tests.utils import create_test_session, create_test_user
from authentik.core.user_switching import UserSwitchingSession


def activate_session(session_key: str, token: str, barrier: Barrier) -> None:
    """Activate a session from an independent database connection."""
    close_old_connections()
    try:
        barrier.wait()
        user_switching.activate_session(session_key, token)
    finally:
        close_old_connections()


class TestUserSwitchingConcurrency(TransactionTestCase):
    """Test concurrent activation of sessions in one browser."""

    def test_concurrent_activation_has_one_current_session(self):
        token = get_random_string(user_switching.TOKEN_LENGTH)
        sessions = [create_test_session(create_test_user()) for _ in range(2)]
        barrier = Barrier(len(sessions))

        with ThreadPoolExecutor(max_workers=len(sessions)) as executor:
            list(
                executor.map(
                    partial(activate_session, token=token, barrier=barrier),
                    [session.session_id for session in sessions],
                )
            )

        switching_session = UserSwitchingSession.objects.get(token=token)
        self.assertIn(switching_session.current_session_id, {session.pk for session in sessions})
        self.assertEqual(
            AuthenticatedSession.objects.filter(user_switching_session_id=token).count(),
            len(sessions),
        )
