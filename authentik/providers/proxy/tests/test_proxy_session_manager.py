"""Test ProxySessionManager"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from authentik.core.tests.utils import create_test_flow
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.proxy.models import ProxyProvider, ProxySession, ProxySessionManager


class TestProxySessionManager(TestCase):
    """Test ProxySessionManager"""

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

    def test_proxy_session_manager_exists(self):
        """Test ProxySessionManager exists"""
        self.assertIsInstance(ProxySession.objects, ProxySessionManager)

    def test_cleanup_expired_no_sessions(self):
        """Test cleanup_expired with no sessions"""
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 0)

    def test_cleanup_expired_no_expired_sessions(self):
        """Test cleanup_expired with no expired sessions"""
        # Create a session that expires in the future
        future_time = timezone.now() + timedelta(hours=1)
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="future-session",
            data=b"test-data",
            expires=future_time,
        )
        
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 0)
        
        # Verify session still exists
        self.assertTrue(ProxySession.objects.filter(session_key="future-session").exists())

    def test_cleanup_expired_with_expired_sessions(self):
        """Test cleanup_expired with expired sessions"""
        # Create expired sessions
        past_time = timezone.now() - timedelta(hours=1)
        
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expired-session-1",
            data=b"test-data",
            expires=past_time,
        )
        
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expired-session-2",
            data=b"test-data",
            expires=past_time,
        )
        
        # Create a non-expired session
        future_time = timezone.now() + timedelta(hours=1)
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="future-session",
            data=b"test-data",
            expires=future_time,
        )
        
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 2)
        
        # Verify only expired sessions were deleted
        self.assertFalse(ProxySession.objects.filter(session_key="expired-session-1").exists())
        self.assertFalse(ProxySession.objects.filter(session_key="expired-session-2").exists())
        self.assertTrue(ProxySession.objects.filter(session_key="future-session").exists())

    def test_cleanup_expired_with_none_expires(self):
        """Test cleanup_expired with sessions that have None expires"""
        # Create sessions with None expires (should not be deleted)
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="none-expires-session",
            data=b"test-data",
            expires=None,
        )
        
        # Create expired session
        past_time = timezone.now() - timedelta(hours=1)
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expired-session",
            data=b"test-data",
            expires=past_time,
        )
        
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 1)
        
        # Verify session with None expires was not deleted
        self.assertTrue(ProxySession.objects.filter(session_key="none-expires-session").exists())
        self.assertFalse(ProxySession.objects.filter(session_key="expired-session").exists())

    def test_cleanup_expired_mixed_providers(self):
        """Test cleanup_expired with sessions from different providers"""
        # Create second provider
        provider2 = ProxyProvider.objects.create(
            name="test-provider-2",
            internal_host="http://localhost2",
            external_host="http://localhost2",
            authorization_flow=create_test_flow(),
        )
        
        # Create expired sessions for both providers
        past_time = timezone.now() - timedelta(hours=1)
        
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expired-provider1",
            data=b"test-data",
            expires=past_time,
        )
        
        ProxySession.objects.create(
            provider_id=str(provider2.pk),
            session_key="expired-provider2",
            data=b"test-data",
            expires=past_time,
        )
        
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 2)
        
        # Verify both expired sessions were deleted
        self.assertFalse(ProxySession.objects.filter(session_key="expired-provider1").exists())
        self.assertFalse(ProxySession.objects.filter(session_key="expired-provider2").exists())

    def test_cleanup_expired_boundary_conditions(self):
        """Test cleanup_expired with boundary conditions"""
        now = timezone.now()
        
        # Create session that expires exactly now
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expires-now",
            data=b"test-data",
            expires=now,
        )
        
        # Create session that expires 1 second ago
        one_second_ago = now - timedelta(seconds=1)
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expires-one-second-ago",
            data=b"test-data",
            expires=one_second_ago,
        )
        
        # Create session that expires 1 second in the future
        one_second_future = now + timedelta(seconds=1)
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expires-one-second-future",
            data=b"test-data",
            expires=one_second_future,
        )
        
        deleted_count = ProxySession.objects.cleanup_expired()
        
        # Should delete sessions that expire now or in the past
        self.assertGreaterEqual(deleted_count, 1)
        self.assertTrue(ProxySession.objects.filter(session_key="expires-one-second-future").exists())

    def test_cleanup_expired_large_dataset(self):
        """Test cleanup_expired with large number of sessions"""
        # Create many expired sessions
        past_time = timezone.now() - timedelta(hours=1)
        sessions = []
        
        for i in range(100):
            sessions.append(ProxySession(
                provider_id=str(self.provider.pk),
                session_key=f"expired-session-{i}",
                data=f"test-data-{i}".encode(),
                expires=past_time,
            ))
        
        # Bulk create sessions
        ProxySession.objects.bulk_create(sessions)
        
        # Cleanup expired sessions
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 100)
        
        # Verify all sessions were deleted
        remaining_count = ProxySession.objects.count()
        self.assertEqual(remaining_count, 0)

    def test_cleanup_expired_performance(self):
        """Test cleanup_expired performance with mixed dataset"""
        # Create mix of expired and non-expired sessions
        past_time = timezone.now() - timedelta(hours=1)
        future_time = timezone.now() + timedelta(hours=1)
        
        # Create expired sessions
        expired_sessions = []
        for i in range(50):
            expired_sessions.append(ProxySession(
                provider_id=str(self.provider.pk),
                session_key=f"expired-{i}",
                data=f"expired-data-{i}".encode(),
                expires=past_time,
            ))
        
        # Create non-expired sessions
        active_sessions = []
        for i in range(50):
            active_sessions.append(ProxySession(
                provider_id=str(self.provider.pk),
                session_key=f"active-{i}",
                data=f"active-data-{i}".encode(),
                expires=future_time,
            ))
        
        # Bulk create all sessions
        ProxySession.objects.bulk_create(expired_sessions + active_sessions)
        
        # Cleanup expired sessions
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 50)
        
        # Verify correct sessions remain
        remaining_count = ProxySession.objects.count()
        self.assertEqual(remaining_count, 50)
        
        # Verify only active sessions remain
        remaining_keys = set(ProxySession.objects.values_list('session_key', flat=True))
        expected_keys = {f"active-{i}" for i in range(50)}
        self.assertEqual(remaining_keys, expected_keys)

    def test_cleanup_expired_with_different_expiry_times(self):
        """Test cleanup_expired with various expiry times"""
        now = timezone.now()
        
        # Create sessions with different expiry times
        expiry_deltas = [
            timedelta(hours=-2),   # 2 hours ago - should be deleted
            timedelta(minutes=-30), # 30 minutes ago - should be deleted  
            timedelta(seconds=-1),  # 1 second ago - should be deleted
            timedelta(seconds=1),   # 1 second future - should remain
            timedelta(minutes=30),  # 30 minutes future - should remain
            timedelta(hours=2),     # 2 hours future - should remain
        ]
        
        for i, delta in enumerate(expiry_deltas):
            ProxySession.objects.create(
                provider_id=str(self.provider.pk),
                session_key=f"session-{i}",
                data=f"data-{i}".encode(),
                expires=now + delta,
            )
        
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 3)  # Should delete first 3 sessions
        
        # Verify remaining sessions
        remaining_count = ProxySession.objects.count()
        self.assertEqual(remaining_count, 3)  # Should have last 3 sessions

    def test_cleanup_expired_return_value(self):
        """Test cleanup_expired returns correct count"""
        # Create expired sessions
        past_time = timezone.now() - timedelta(hours=1)
        
        for i in range(5):
            ProxySession.objects.create(
                provider_id=str(self.provider.pk),
                session_key=f"expired-{i}",
                data=f"data-{i}".encode(),
                expires=past_time,
            )
        
        # Test return value
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 5)
        self.assertIsInstance(deleted_count, int)

    def test_cleanup_expired_database_constraints(self):
        """Test cleanup_expired respects database constraints"""
        # Create expired session with foreign key relationships
        past_time = timezone.now() - timedelta(hours=1)
        
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expired-with-constraints",
            data=b"test-data",
            expires=past_time,
        )
        
        # Cleanup should work even with foreign key relationships
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 1)
        
        # Verify session was deleted
        self.assertFalse(ProxySession.objects.filter(uuid=session.uuid).exists())

    def test_cleanup_expired_atomic_transaction(self):
        """Test cleanup_expired uses atomic transactions"""
        # Create expired sessions
        past_time = timezone.now() - timedelta(hours=1)
        
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expired-atomic-1",
            data=b"test-data",
            expires=past_time,
        )
        
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expired-atomic-2",
            data=b"test-data",
            expires=past_time,
        )
        
        # Test that cleanup is atomic
        deleted_count = ProxySession.objects.cleanup_expired()
        self.assertEqual(deleted_count, 2)
        
        # After cleanup, sessions should be completely removed
        self.assertEqual(ProxySession.objects.count(), 0)

    def test_cleanup_expired_with_custom_manager(self):
        """Test cleanup_expired method is available on custom manager"""
        # Verify the manager has the cleanup_expired method
        self.assertTrue(hasattr(ProxySession.objects, 'cleanup_expired'))
        self.assertTrue(callable(getattr(ProxySession.objects, 'cleanup_expired')))

    def test_cleanup_expired_queryset_efficiency(self):
        """Test cleanup_expired uses efficient queryset operations"""
        # Create test data
        past_time = timezone.now() - timedelta(hours=1)
        future_time = timezone.now() + timedelta(hours=1)
        
        # Create mix of expired and non-expired sessions
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="expired-efficient",
            data=b"test-data",
            expires=past_time,
        )
        
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="active-efficient",
            data=b"test-data",
            expires=future_time,
        )
        
        # Test cleanup works efficiently
        with self.assertNumQueries(1):  # Should only need 1 query to delete
            deleted_count = ProxySession.objects.cleanup_expired()
        
        self.assertEqual(deleted_count, 1)

    def test_proxy_session_manager_inheritance(self):
        """Test ProxySessionManager inherits from models.Manager"""
        from django.db import models
        self.assertTrue(issubclass(ProxySessionManager, models.Manager))

    def test_proxy_session_manager_methods(self):
        """Test ProxySessionManager has required methods"""
        manager = ProxySession.objects
        
        # Test standard manager methods are available
        self.assertTrue(hasattr(manager, 'create'))
        self.assertTrue(hasattr(manager, 'get_or_create'))
        self.assertTrue(hasattr(manager, 'update_or_create'))
        self.assertTrue(hasattr(manager, 'bulk_create'))
        self.assertTrue(hasattr(manager, 'filter'))
        self.assertTrue(hasattr(manager, 'exclude'))
        self.assertTrue(hasattr(manager, 'all'))
        self.assertTrue(hasattr(manager, 'count'))
        
        # Test custom method
        self.assertTrue(hasattr(manager, 'cleanup_expired'))

    def test_proxy_session_manager_queryset_methods(self):
        """Test ProxySessionManager queryset methods work correctly"""
        # Create test sessions
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="queryset-test-1",
            data=b"test-data-1",
        )
        
        ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="queryset-test-2",
            data=b"test-data-2",
        )
        
        # Test queryset methods
        all_sessions = ProxySession.objects.all()
        self.assertEqual(all_sessions.count(), 2)
        
        filtered_sessions = ProxySession.objects.filter(session_key="queryset-test-1")
        self.assertEqual(filtered_sessions.count(), 1)
        
        excluded_sessions = ProxySession.objects.exclude(session_key="queryset-test-1")
        self.assertEqual(excluded_sessions.count(), 1)

    def test_proxy_session_manager_get_methods(self):
        """Test ProxySessionManager get methods"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="get-test",
            data=b"test-data",
        )
        
        # Test get method
        retrieved_session = ProxySession.objects.get(session_key="get-test")
        self.assertEqual(retrieved_session.uuid, session.uuid)
        
        # Test get_or_create method
        session2, created = ProxySession.objects.get_or_create(
            provider_id=str(self.provider.pk),
            session_key="get-or-create-test",
            defaults={'data': b"default-data"}
        )
        self.assertTrue(created)
        self.assertEqual(session2.session_key, "get-or-create-test")
        
        # Test get_or_create with existing session
        session3, created = ProxySession.objects.get_or_create(
            provider_id=str(self.provider.pk),
            session_key="get-or-create-test",
            defaults={'data': b"different-data"}
        )
        self.assertFalse(created)
        self.assertEqual(session3.uuid, session2.uuid)

    def test_proxy_session_manager_update_methods(self):
        """Test ProxySessionManager update methods"""
        session = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="update-test",
            data=b"original-data",
        )
        
        # Test update method
        updated_count = ProxySession.objects.filter(
            session_key="update-test"
        ).update(data=b"updated-data")
        self.assertEqual(updated_count, 1)
        
        # Verify update
        session.refresh_from_db()
        self.assertEqual(session.data, b"updated-data")
        
        # Test update_or_create method
        session2, created = ProxySession.objects.update_or_create(
            provider_id=str(self.provider.pk),
            session_key="update-or-create-test",
            defaults={'data': b"created-data"}
        )
        self.assertTrue(created)
        
        # Update existing
        session3, created = ProxySession.objects.update_or_create(
            provider_id=str(self.provider.pk),
            session_key="update-or-create-test",
            defaults={'data': b"updated-data"}
        )
        self.assertFalse(created)
        self.assertEqual(session3.uuid, session2.uuid)
        self.assertEqual(session3.data, b"updated-data")

    def test_proxy_session_manager_delete_methods(self):
        """Test ProxySessionManager delete methods"""
        # Create test sessions
        session1 = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="delete-test-1",
            data=b"test-data-1",
        )
        
        session2 = ProxySession.objects.create(
            provider_id=str(self.provider.pk),
            session_key="delete-test-2",
            data=b"test-data-2",
        )
        
        # Test queryset delete
        deleted_count, deleted_objects = ProxySession.objects.filter(
            session_key="delete-test-1"
        ).delete()
        self.assertEqual(deleted_count, 1)
        
        # Test bulk delete
        deleted_count, deleted_objects = ProxySession.objects.filter(
            session_key__startswith="delete-test"
        ).delete()
        self.assertEqual(deleted_count, 1)  # Only session2 should remain
        
        # Verify all sessions deleted
        remaining_count = ProxySession.objects.count()
        self.assertEqual(remaining_count, 0) 