"""Test SAMLSession Model"""

from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.tests.utils import create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.saml.api.sessions import SAMLSessionSerializer
from authentik.providers.saml.models import SAMLProvider, SAMLSession
from authentik.sources.saml.processors.constants import (
    SAML_NAME_ID_FORMAT_EMAIL,
)


class TestSAMLSessionModel(TestCase):
    """Test SAMLSession model functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
        )
        self.flow = create_test_flow()

        # Create a provider
        self.provider = SAMLProvider.objects.create(
            name="test-provider",
            authorization_flow=self.flow,
            acs_url="https://sp.example.com/acs",
            issuer="https://idp.example.com",
        )

        # Create another provider for testing
        self.provider2 = SAMLProvider.objects.create(
            name="test-provider-2",
            authorization_flow=self.flow,
            acs_url="https://sp2.example.com/acs",
            issuer="https://idp2.example.com",
        )

        # Create a session first (using authentik's custom Session model)
        self.django_session = Session.objects.create(
            session_key=generate_id(),
            last_ip="127.0.0.1",
        )

        # Create an authenticated session
        self.auth_session = AuthenticatedSession.objects.create(
            session=self.django_session,
            user=self.user,
        )

        # Session data
        self.session_index = generate_id()
        self.name_id = "test@example.com"
        self.name_id_format = SAML_NAME_ID_FORMAT_EMAIL
        self.expires = timezone.now() + timedelta(hours=8)

    def test_session_creation(self):
        """Test creating a SAML session"""
        saml_session = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=self.session_index,
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Verify the session was created
        self.assertIsNotNone(saml_session.pk)
        self.assertEqual(saml_session.provider, self.provider)
        self.assertEqual(saml_session.user, self.user)
        self.assertEqual(saml_session.session, self.auth_session)
        self.assertEqual(saml_session.session_index, self.session_index)
        self.assertEqual(saml_session.name_id, self.name_id)
        self.assertEqual(saml_session.name_id_format, self.name_id_format)
        self.assertIsNotNone(saml_session.created)

        # Test string representation
        expected_str = f"SAML Session for provider {self.provider.pk} and user {self.user.pk}"
        self.assertEqual(str(saml_session), expected_str)

    def test_unique_constraint_session_index_provider(self):
        """Test that session_index must be unique per provider"""
        # Create first session
        SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=self.session_index,
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Try to create another session with same session_index and provider
        with self.assertRaises(IntegrityError):
            SAMLSession.objects.create(
                provider=self.provider,
                user=self.user,
                session=self.auth_session,
                session_index=self.session_index,  # Same session_index
                name_id="different@example.com",
                name_id_format=self.name_id_format,
                expires=self.expires,
                expiring=True,
            )

    def test_cascade_deletion_user(self):
        """Test that deleting a user deletes associated SAML sessions"""
        # Create SAML session
        saml_session = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=self.session_index,
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Verify session exists
        self.assertTrue(SAMLSession.objects.filter(pk=saml_session.pk).exists())

        # Delete the user
        self.user.delete()

        # Verify SAML session was deleted
        self.assertFalse(SAMLSession.objects.filter(pk=saml_session.pk).exists())

    def test_cascade_deletion_provider(self):
        """Test that deleting a provider deletes associated SAML sessions"""
        # Create SAML session
        saml_session = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=self.session_index,
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Verify session exists
        self.assertTrue(SAMLSession.objects.filter(pk=saml_session.pk).exists())

        # Delete the provider
        self.provider.delete()

        # Verify SAML session was deleted
        self.assertFalse(SAMLSession.objects.filter(pk=saml_session.pk).exists())

    def test_cascade_deletion_authenticated_session(self):
        """Test that deleting an AuthenticatedSession deletes associated SAML sessions"""
        # Create SAML session
        saml_session = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=self.session_index,
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Verify session exists
        self.assertTrue(SAMLSession.objects.filter(pk=saml_session.pk).exists())

        # Delete the authenticated session
        self.auth_session.delete()

        # Verify SAML session was deleted
        self.assertFalse(SAMLSession.objects.filter(pk=saml_session.pk).exists())

    def test_multiple_sessions_per_user(self):
        """Test that a user can have multiple SAML sessions with different providers"""
        # Create first session
        session1 = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=generate_id(),
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Create second session with different provider
        session2 = SAMLSession.objects.create(
            provider=self.provider2,
            user=self.user,
            session=self.auth_session,
            session_index=generate_id(),
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Verify both sessions exist
        user_sessions = SAMLSession.objects.filter(user=self.user)
        self.assertEqual(user_sessions.count(), 2)
        self.assertIn(session1, user_sessions)
        self.assertIn(session2, user_sessions)

    def test_session_expiry_tracking(self):
        """Test that session expiry time is properly stored"""
        # Create session with specific expiry
        future_time = timezone.now() + timedelta(hours=24)
        saml_session = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=self.session_index,
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=future_time,
            expiring=True,
        )

        # Verify expiry time
        self.assertEqual(saml_session.expires, future_time)

        # Check if session is expired (ExpiringModel behavior)
        self.assertFalse(saml_session.is_expired)

        # Create an expired session
        past_time = timezone.now() - timedelta(hours=1)
        expired_session = SAMLSession.objects.create(
            provider=self.provider2,
            user=self.user,
            session=self.auth_session,
            session_index=generate_id(),
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=past_time,
            expiring=True,
        )

        # Check if marked as expired
        self.assertTrue(expired_session.is_expired)

    def test_name_id_format_optional(self):
        """Test that name_id_format is optional (can be blank)"""
        # Create session without name_id_format
        saml_session = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=self.session_index,
            name_id=self.name_id,
            name_id_format="",  # Blank format
            expires=self.expires,
            expiring=True,
        )

        # Verify it was created successfully
        self.assertIsNotNone(saml_session.pk)
        self.assertEqual(saml_session.name_id_format, "")

    def test_query_sessions_by_provider(self):
        """Test querying sessions by provider"""
        # Create sessions for different providers
        session1 = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=generate_id(),
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        session2 = SAMLSession.objects.create(
            provider=self.provider2,
            user=self.user,
            session=self.auth_session,
            session_index=generate_id(),
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Query by provider
        provider1_sessions = SAMLSession.objects.filter(provider=self.provider)
        self.assertEqual(provider1_sessions.count(), 1)
        self.assertEqual(provider1_sessions.first(), session1)

        provider2_sessions = SAMLSession.objects.filter(provider=self.provider2)
        self.assertEqual(provider2_sessions.count(), 1)
        self.assertEqual(provider2_sessions.first(), session2)

    def test_serializer_property(self):
        """Test that the serializer property returns the correct serializer"""
        saml_session = SAMLSession.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.auth_session,
            session_index=self.session_index,
            name_id=self.name_id,
            name_id_format=self.name_id_format,
            expires=self.expires,
            expiring=True,
        )

        # Check serializer property
        self.assertEqual(saml_session.serializer, SAMLSessionSerializer)

    def test_bulk_delete_sessions_for_user(self):
        """Test bulk deletion of all SAML sessions for a user"""
        # Create multiple sessions
        for i in range(3):
            SAMLSession.objects.create(
                provider=self.provider if i % 2 == 0 else self.provider2,
                user=self.user,
                session=self.auth_session,
                session_index=generate_id(),
                name_id=self.name_id,
                name_id_format=self.name_id_format,
                expires=self.expires,
                expiring=True,
            )

        # Verify sessions exist
        self.assertEqual(SAMLSession.objects.filter(user=self.user).count(), 3)

        # Delete all sessions for the user
        deleted_count, _ = SAMLSession.objects.filter(user=self.user).delete()

        # Verify all were deleted
        self.assertEqual(deleted_count, 3)
        self.assertEqual(SAMLSession.objects.filter(user=self.user).count(), 0)
