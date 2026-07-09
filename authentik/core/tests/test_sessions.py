"""Session user switching tests."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.conf import settings
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils.crypto import get_random_string

from authentik.core import user_switching
from authentik.core.models import AuthenticatedSession
from authentik.core.tests.utils import create_test_session, create_test_user
from authentik.core.user_switching import UserSwitchingSession


class TestUserSwitchingSessions(TestCase):
    """Test binding and invalidation of browser login sessions."""

    def test_existing_session_is_bound_to_browser(self):
        """An existing login gets a switching group and signed browser cookie."""
        target = create_test_session(create_test_user())
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session_id

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        print(f"session superseded={target.is_superseded}")
        cookie = response.cookies[user_switching.COOKIE_NAME]
        self.assertEqual(
            user_switching.decode_cookie(cookie.value),
            target.user_switching_session_id,
        )

    def test_superseded_session_is_rejected(self):
        """A recorded session cookie cannot be replayed after a switch."""
        token = get_random_string(user_switching.TOKEN_LENGTH)
        target = create_test_session(create_test_user(), token)
        create_test_session(create_test_user(), token)
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session_id

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 403)

    def test_cookie_validation(self):
        """Only signed, well-formed switching tokens are accepted."""
        valid = get_random_string(user_switching.TOKEN_LENGTH)
        self.assertEqual(user_switching.decode_cookie(user_switching.encode_cookie(valid)), valid)
        for invalid in (None, "", valid, "too-short", "!" * user_switching.TOKEN_LENGTH):
            self.assertIsNone(user_switching.decode_cookie(invalid))


class TestUserSwitchingConcurrency(TransactionTestCase):
    """Test concurrent activation of sessions in one browser."""

    def test_concurrent_activation_has_one_current_session(self):
        token = get_random_string(user_switching.TOKEN_LENGTH)
        sessions = [create_test_session(create_test_user()) for _ in range(2)]
        barrier = Barrier(len(sessions))

        def activate(session_key: str) -> None:
            close_old_connections()
            try:
                barrier.wait()
                user_switching.activate_session(session_key, token)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(sessions)) as executor:
            list(executor.map(activate, [session.session_id for session in sessions]))

        switching_session = UserSwitchingSession.objects.get(token=token)
        self.assertIn(switching_session.current_session_id, {session.pk for session in sessions})
        self.assertEqual(
            AuthenticatedSession.objects.filter(user_switching_session_id=token).count(),
            len(sessions),
        )
