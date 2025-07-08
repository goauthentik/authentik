"""Test ProxySession model"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from authentik.core.tests.utils import create_test_flow
from authentik.outposts.models import ProxySession, ProxySessionManager, Outpost, OutpostType
from authentik.providers.proxy.models import ProxyProvider


class TestProxySessionModel(TestCase):
    """Test ProxySession model"""

    def setUp(self):
        """Set up test case"""
        self.provider = ProxyProvider.objects.create(
            name="test-provider",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=create_test_flow(),
        )
        self.outpost = Outpost.objects.create(
            name="test-outpost",
            type=OutpostType.PROXY,
        )
        self.outpost.providers.add(self.provider)

    def test_proxy_session_creation(self):
        """Test creating a ProxySession"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="test-session-key",
            data=b"test-data",
            claims='{"sub": "user123"}',
            redirect="/redirect/path",
        )
        
        self.assertIsNotNone(session.uuid)
        self.assertEqual(session.provider_id, str(self.provider.pk))
        self.assertEqual(session.session_key, "test-session-key")
        self.assertEqual(session.data, b"test-data")
        self.assertEqual(session.claims, '{"sub": "user123"}')
        self.assertEqual(session.redirect, "/redirect/path")
        self.assertIsNotNone(session.created_at)
        self.assertFalse(session.expiring)  # Should default to False

    def test_proxy_session_str_representation(self):
        """Test ProxySession string representation"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="test-session-key",
            data=b"test-data",
        )
        
        expected_str = f"ProxySession {session.uuid} (provider: {self.provider.pk}, key: test-session-key)"
        self.assertEqual(str(session), expected_str)

    def test_proxy_session_required_fields(self):
        """Test ProxySession with required fields only"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="minimal-session",
            data=b"minimal-data",
        )
        
        self.assertEqual(session.claims, "")
        self.assertEqual(session.redirect, "")
        self.assertFalse(session.expiring)

    def test_proxy_session_uuid_generation(self):
        """Test ProxySession UUID is automatically generated"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="uuid-test",
            data=b"test-data",
        )
        
        self.assertIsInstance(session.uuid, uuid.UUID)
        self.assertIsNotNone(session.uuid)

    def test_proxy_session_unique_constraint(self):
        """Test unique constraint on session_key and provider_id"""
        # Create first session
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="duplicate-key",
            data=b"test-data",
        )
        
        # Try to create duplicate - should fail
        with self.assertRaises(IntegrityError):
            ProxySession.objects.create(
                provider_id=str(self.provider.pk),
                session_key="duplicate-key",
                data=b"different-data",
            )

    def test_proxy_session_different_providers(self):
        """Test same session key with different providers is allowed"""
        # Create second provider
        provider2 = ProxyProvider.objects.create(
            name="test-provider-2",
            internal_host="http://localhost2",
            external_host="http://localhost2",
            authorization_flow=create_test_flow(),
        )
        
        # Create sessions with same key but different providers
        session1 = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="same-key",
            data=b"data1",
        )
        
        session2 = ProxySession.objects.create(
            provider_id=str(provider2.pk),
            session_key="same-key",
            data=b"data2",
        )
        
        self.assertEqual(session1.session_key, session2.session_key)
        self.assertNotEqual(session1.provider_id, session2.provider_id)

    def test_proxy_session_expiring_field(self):
        """Test expiring field behavior"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expiring-test",
            data=b"test-data",
            expiring=True,
        )
        
        self.assertTrue(session.expiring)

    def test_proxy_session_expires_field(self):
        """Test expires field with datetime"""
        future_time = timezone.now() + timedelta(hours=1)
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expires-test",
            data=b"test-data",
            expires=future_time,
        )
        
        self.assertEqual(session.expires, future_time)

    def test_proxy_session_large_data(self):
        """Test ProxySession with large data"""
        large_data = b"x" * 10000  # 10KB of data
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="large-data-test",
            data=large_data,
        )
        
        self.assertEqual(session.data, large_data)

    def test_proxy_session_empty_data(self):
        """Test ProxySession with empty data"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="empty-data-test",
            data=b"",
        )
        
        self.assertEqual(session.data, b"")

    def test_proxy_session_special_characters_in_key(self):
        """Test ProxySession with special characters in session key"""
        special_key = "session-key_with.special:chars@123"
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key=special_key,
            data=b"test-data",
        )
        
        self.assertEqual(session.session_key, special_key)

    def test_proxy_session_long_session_key(self):
        """Test ProxySession with maximum length session key"""
        # Assuming max length is 255 (standard CharField)
        long_key = "a" * 255
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key=long_key,
            data=b"test-data",
        )
        
        self.assertEqual(session.session_key, long_key)

    def test_proxy_session_json_claims(self):
        """Test ProxySession with JSON claims"""
        claims_json = '{"sub": "user123", "email": "user@example.com", "groups": ["admin", "user"]}'
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="json-claims-test",
            data=b"test-data",
            claims=claims_json,
        )
        
        self.assertEqual(session.claims, claims_json)

    def test_proxy_session_long_redirect(self):
        """Test ProxySession with long redirect URL"""
        long_redirect = "https://example.com/very/long/redirect/path/with/many/segments/" + "a" * 200
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="long-redirect-test",
            data=b"test-data",
            redirect=long_redirect,
        )
        
        self.assertEqual(session.redirect, long_redirect)

    def test_proxy_session_update(self):
        """Test updating ProxySession fields"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="update-test",
            data=b"original-data",
            claims='{"sub": "original"}',
        )
        
        # Update fields
        session.data = b"updated-data"
        session.claims = '{"sub": "updated"}'
        session.expiring = True
        session.save()
        
        # Reload from database
        session.refresh_from_db()
        
        self.assertEqual(session.data, b"updated-data")
        self.assertEqual(session.claims, '{"sub": "updated"}')
        self.assertTrue(session.expiring)

    def test_proxy_session_delete(self):
        """Test deleting ProxySession"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="delete-test",
            data=b"test-data",
        )
        
        session_id = session.uuid
        session.delete()
        
        # Verify deletion
        with self.assertRaises(ProxySession.DoesNotExist):
            ProxySession.objects.get(uuid=session_id)

    def test_proxy_session_save_override(self):
        """Test ProxySession save method override"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="save-override-test",
            data=b"test-data",
            expiring=True,  # This should be kept as True
        )
        
        # The save method should ensure expiring defaults to False for new instances
        # but keep existing values for updates
        self.assertTrue(session.expiring)

    def test_proxy_session_meta_verbose_names(self):
        """Test ProxySession meta verbose names"""
        self.assertEqual(ProxySession._meta.verbose_name, "Proxy Provider Session")
        self.assertEqual(ProxySession._meta.verbose_name_plural, "Proxy Provider Sessions")

    def test_proxy_session_indexes(self):
        """Test ProxySession has proper indexes"""
        # Get the model's indexes
        indexes = ProxySession._meta.indexes
        
        # Check that expected indexes exist
        index_fields = [list(index.fields) for index in indexes]
        
        # Should have index on session_key and provider_id
        self.assertIn(["session_key", "provider_id"], index_fields)
        # Should have index on provider_id alone
        self.assertIn(["provider_id"], index_fields)
        # Should have index on created_at
        self.assertIn(["created_at"], index_fields)

    def test_proxy_session_constraints(self):
        """Test ProxySession constraints"""
        # Get the model's constraints
        constraints = ProxySession._meta.constraints
        
        # Should have a unique constraint on session_key and provider_id
        constraint_fields = [list(constraint.fields) for constraint in constraints]
        self.assertIn(["session_key", "provider_id"], constraint_fields)

    def test_proxy_session_inheritance(self):
        """Test ProxySession inherits from ExpiringModel"""
        # ProxySession should inherit from ExpiringModel
        from authentik.core.models import ExpiringModel
        self.assertTrue(issubclass(ProxySession, ExpiringModel))

    def test_proxy_session_with_none_expires(self):
        """Test ProxySession with None expires value"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="none-expires-test",
            data=b"test-data",
            expires=None,
        )
        
        self.assertIsNone(session.expires)

    def test_proxy_session_bulk_create(self):
        """Test bulk creating ProxySession objects"""
        sessions = [
            ProxySession(
                provider_id=str(self.provider.pk),
                session_key=f"bulk-session-{i}",
                data=f"data-{i}".encode(),
            )
            for i in range(5)
        ]
        
        created_sessions = ProxySession.objects.bulk_create(sessions)
        self.assertEqual(len(created_sessions), 5)
        
        # Verify all were created
        self.assertEqual(ProxySession.objects.filter(session_key__startswith="bulk-session-").count(), 5)

    def test_proxy_session_queryset_filter(self):
        """Test filtering ProxySession queryset"""
        # Create sessions for different providers
        provider2 = ProxyProvider.objects.create(
            name="test-provider-2",
            internal_host="http://localhost2",
            external_host="http://localhost2",
            authorization_flow=create_test_flow(),
        )
        
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="filter-test-1",
            data=b"data1",
        )
        
        ProxySession.objects.create(
            provider_id=str(provider2.pk),
            session_key="filter-test-2",
            data=b"data2",
        )
        
        # Filter by provider
        provider1_sessions = ProxySession.objects.filter(provider_id=str(self.provider.pk))
        provider2_sessions = ProxySession.objects.filter(provider_id=str(provider2.pk))
        
        self.assertEqual(provider1_sessions.count(), 1)
        self.assertEqual(provider2_sessions.count(), 1)
        self.assertEqual(provider1_sessions.first().session_key, "filter-test-1")
        self.assertEqual(provider2_sessions.first().session_key, "filter-test-2")

    def test_proxy_session_ordering(self):
        """Test ProxySession default ordering"""
        # Create sessions with different timestamps
        session1 = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="order-test-1",
            data=b"data1",
        )
        
        session2 = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="order-test-2",
            data=b"data2",
        )
        
        # Get all sessions and check ordering
        sessions = list(ProxySession.objects.all())
        # Should be ordered by created_at (newest first, typically)
        self.assertGreaterEqual(sessions[0].created_at, sessions[1].created_at)

    def test_proxy_session_count_queries(self):
        """Test ProxySession count queries"""
        # Create several sessions
        for i in range(3):
            ProxySession.objects.create(
                provider_id=str(self.provider.pk),
                session_key=f"count-test-{i}",
                data=f"data-{i}".encode(),
            )
        
        # Test count
        count = ProxySession.objects.count()
        self.assertEqual(count, 3)
        
        # Test filter count
        provider_count = ProxySession.objects.filter(provider_id=str(self.provider.pk)).count()
        self.assertEqual(provider_count, 3)

    def test_proxy_session_exists_queries(self):
        """Test ProxySession exists queries"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="exists-test",
            data=b"test-data",
        )
        
        # Test exists
        exists = ProxySession.objects.filter(session_key="exists-test").exists()
        self.assertTrue(exists)
        
        # Test non-existent
        not_exists = ProxySession.objects.filter(session_key="non-existent").exists()
        self.assertFalse(not_exists)

    def test_proxy_session_values_queries(self):
        """Test ProxySession values queries"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="values-test",
            data=b"test-data",
            claims='{"sub": "user123"}',
        )
        
        # Test values query
        values = ProxySession.objects.values('session_key', 'provider_id').first()
        self.assertEqual(values['session_key'], "values-test")
        self.assertEqual(values['provider_id'], str(self.provider.pk))

    def test_proxy_session_values_list_queries(self):
        """Test ProxySession values_list queries"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="values-list-test",
            data=b"test-data",
        )
        
        # Test values_list query
        session_keys = ProxySession.objects.values_list('session_key', flat=True)
        self.assertIn("values-list-test", list(session_keys)) 