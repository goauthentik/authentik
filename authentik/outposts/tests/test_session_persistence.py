"""Test session persistence across outpost restarts"""
import os
import tempfile
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from authentik.core.tests.utils import create_test_flow
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.proxy.models import ProxyProvider

from internal.config import Config, SQLiteConfig
from internal.outpost.proxyv2.application.application import Application
from internal.outpost.proxyv2.sqlitestore.sqlitestore import SQLiteStore


class TestSessionPersistence(TestCase):
    """Test session persistence across outpost restarts"""

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
        
        # Create a temporary SQLite file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_session.sqlite")

    def tearDown(self):
        """Clean up after test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        os.rmdir(self.temp_dir)

    def test_session_persistence(self):
        """Test that sessions persist across outpost restarts when using a configured SQLite path"""
        # Create a SQLite store with our test path
        store = SQLiteStore(self.db_path, "test-provider-1")
        
        # Add a test session
        session_key = "test-session-key"
        session_data = b"test-session-data"
        
        # Insert directly to simulate a session
        store.db.execute(
            """
            INSERT INTO authentik_outposts_proxysession (
                uuid, session_key, data, expires, expiring, provider_id, claims, redirect
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "test-uuid",
                session_key,
                session_data,
                timezone.now() + timedelta(hours=1),
                True,
                "test-provider-1",
                "{}",
                "",
            )
        )
        store.Close()
        
        # Verify the file exists
        self.assertTrue(os.path.exists(self.db_path))
        
        # Create a new store instance (simulating a restart)
        new_store = SQLiteStore(self.db_path, "test-provider-1")
        
        # Check if our session data is still there
        cursor = new_store.db.execute(
            "SELECT data FROM authentik_outposts_proxysession WHERE session_key = ?",
            (session_key,)
        )
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], session_data)
        
        new_store.Close() 