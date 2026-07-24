"""Session user switching tests."""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.crypto import get_random_string

from authentik.core import user_switching
from authentik.core.models import UserSwitchingSession
from authentik.core.tests.utils import create_test_session, create_test_user


class TestUserSwitchingSessions(TestCase):
    """Test binding and invalidation of browser login sessions."""

    def test_existing_session_is_bound_to_browser(self):
        """An existing login gets a switching group and signed browser cookie."""
        target = create_test_session(create_test_user())
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session_id

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertTrue(target.is_current)
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
        target.refresh_from_db()
        self.assertFalse(target.is_current)
        self.client.cookies[settings.SESSION_COOKIE_NAME] = target.session_id

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 403)

    def test_activation_requires_existing_switching_session(self):
        """Activating an unknown switching group fails instead of creating it."""
        target = create_test_session(create_test_user())

        with self.assertRaises(UserSwitchingSession.DoesNotExist):
            user_switching.activate_session(
                target.session_id,
                get_random_string(user_switching.TOKEN_LENGTH),
            )

        target.refresh_from_db()
        self.assertIsNone(target.user_switching_session_id)

    def test_cookie_validation(self):
        """Only signed, well-formed switching tokens are accepted."""
        valid = get_random_string(user_switching.TOKEN_LENGTH)
        UserSwitchingSession.objects.create(token=valid)
        self.assertEqual(user_switching.decode_cookie(user_switching.encode_cookie(valid)), valid)
        orphaned = get_random_string(user_switching.TOKEN_LENGTH)
        self.assertIsNone(user_switching.decode_cookie(user_switching.encode_cookie(orphaned)))
        for invalid in (None, "", valid, "too-short", "!" * user_switching.TOKEN_LENGTH):
            self.assertIsNone(user_switching.decode_cookie(invalid))
