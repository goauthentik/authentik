"""Test core signals"""

from django.test import TestCase

from authentik.blueprints.v1.importer import Importer
from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.signals import deactivation_inhibit_cleanup
from authentik.core.tests.utils import create_test_session, create_test_user
from authentik.lib.generators import generate_id


class TestUserDeactivatedSignal(TestCase):
    """Test that deactivating a user always deletes their sessions"""

    def test_deactivate_deletes_sessions(self):
        """Saving a deactivated user deletes all their sessions"""
        user = create_test_user()
        sessions = [create_test_session(user) for _ in range(3)]
        other_user = create_test_user()
        other_session = create_test_session(other_user)
        self.assertEqual(AuthenticatedSession.objects.filter(user=user).count(), 3)

        user.is_active = False
        user.save()

        for session in sessions:
            self.assertFalse(
                Session.objects.filter(session_key=session.session.session_key).exists()
            )
        self.assertFalse(AuthenticatedSession.objects.filter(user=user).exists())
        # Other users' sessions are untouched
        self.assertTrue(
            Session.objects.filter(session_key=other_session.session.session_key).exists()
        )

    def test_create_inactive_user(self):
        """A user can be created as inactive and saved again without errors"""
        user = User.objects.create(username=generate_id(), name=generate_id(), is_active=False)
        user.name = generate_id()
        user.save()
        user.save(update_fields=["name"])
        self.assertFalse(user.is_active)
        self.assertFalse(AuthenticatedSession.objects.filter(user=user).exists())

    def test_deactivate_inhibited(self):
        """deactivation_inhibit_cleanup leaves the user's sessions alone"""
        user = create_test_user()
        session = create_test_session(user)

        user.is_active = False
        with deactivation_inhibit_cleanup():
            user.save()

        self.assertFalse(user.is_active)
        self.assertTrue(Session.objects.filter(session_key=session.session.session_key).exists())
        # Once the context manager exits, deactivating saves delete sessions again
        user.save()
        self.assertFalse(Session.objects.filter(session_key=session.session.session_key).exists())

    def test_deactivate_inhibit_tokens_only(self):
        """Inhibiting only token cleanup still deletes sessions"""
        user = create_test_user()
        session = create_test_session(user)

        user.is_active = False
        with deactivation_inhibit_cleanup(sessions=False, tokens=True):
            user.save()

        self.assertFalse(Session.objects.filter(session_key=session.session.session_key).exists())

    def test_deactivate_via_blueprint(self):
        """Deactivating a user via blueprint deletes their sessions"""
        user = create_test_user()
        session = create_test_session(user)

        importer = Importer.from_string(f"""version: 1
entries:
  - model: authentik_core.user
    state: present
    identifiers:
      username: {user.username}
    attrs:
      name: {user.name}
      is_active: false
""")
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(Session.objects.filter(session_key=session.session.session_key).exists())
