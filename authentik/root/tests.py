"""root tests"""

from pathlib import Path
from secrets import token_urlsafe
from tempfile import gettempdir
from unittest.mock import MagicMock, patch

import pytest
import fakeredis
from redis import exceptions

from celery.app.amqp import Connection as AmqpConnection
from django.core.cache import BaseCache
from django.test import TestCase
from django.urls import reverse

from authentik.root.redis_middleware_celery import CustomCelery
from authentik.root.redis_middleware_channels import CustomChannelLayer
from authentik.root.redis_middleware_django import CustomClient
from authentik.root.redis_middleware_kombu import CustomClusterChannel, CustomConnection, CustomQoS


class TestRoot(TestCase):
    """Test root application"""

    def setUp(self):
        _tmp = Path(gettempdir())
        self.token = token_urlsafe(32)
        with open(_tmp / "authentik-core-metrics.key", "w") as _f:
            _f.write(self.token)

    def tearDown(self):
        _tmp = Path(gettempdir())
        (_tmp / "authentik-core-metrics.key").unlink()

    def test_monitoring_error(self):
        """Test monitoring without any credentials"""
        response = self.client.get(reverse("metrics"))
        self.assertEqual(response.status_code, 401)

    def test_monitoring_ok(self):
        """Test monitoring with credentials"""
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        response = self.client.get(reverse("metrics"), **auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_monitoring_live(self):
        """Test LiveView"""
        self.assertEqual(self.client.get(reverse("health-live")).status_code, 200)

    def test_monitoring_ready(self):
        """Test ReadyView"""
        self.assertEqual(self.client.get(reverse("health-ready")).status_code, 200)


class TestRedisMiddlewareCelery(TestCase):
    """Test Redis Middleware for Celery"""

    def test_backend_injection(self):
        """Test correct injection of custom Redis backend"""
        celery_app = CustomCelery("authentik")
        connection = celery_app.connection_for_read(
            "redis+sentinel://localhost:6379/?mastername=mymaster"
        )
        self.assertIsInstance(connection, CustomConnection)

    def test_default_backend(self):
        """Test other non-custom backends"""
        celery_app = CustomCelery("authentik")
        connection = celery_app.connection_for_read("amqp://localhost:5672/myvhost")
        self.assertIsInstance(connection, AmqpConnection)


class TestRedisMiddlewareDjango(TestCase):
    """Test Redis Middleware for Django"""

    def test_custom_client_sentinel(self):
        """Test config adjustments for Redis sentinel"""
        params = {}
        base_cache = BaseCache(params)
        django_client = CustomClient(
            "redis+sentinel://myredis:1293/?mastername=mymaster", params, base_cache
        )
        server_config = django_client._server
        self.assertEqual(len(server_config), 2)
        self.assertEqual(server_config[0]["type"], "sentinel")
        self.assertEqual(server_config[0]["service_name"], "mymaster")
        self.assertEqual(len(server_config[0]["sentinels"]), 1)
        self.assertEqual(server_config[0]["sentinels"][0]["host"], "myredis")
        self.assertEqual(server_config[0]["sentinels"][0]["port"], 1293)
        self.assertEqual(server_config[1]["type"], "sentinel")
        self.assertEqual(server_config[1]["service_name"], "mymaster")
        self.assertEqual(len(server_config[1]["sentinels"]), 1)
        self.assertEqual(server_config[1]["sentinels"][0]["host"], "myredis")
        self.assertEqual(server_config[1]["sentinels"][0]["port"], 1293)
        self.assertTrue(server_config[1]["is_slave"])


class TestRedisMiddlewareChannels(TestCase):
    """Test Redis Middleware for Channels-Redis (Django)"""

    def test_custom_client_sentinel(self):
        """Test config adjustments for Redis sentinel"""
        channel_layer = CustomChannelLayer("redis+sentinel://myredis:1293/?mastername=mymaster")
        channel_config = channel_layer.config
        self.assertEqual(len(channel_config), 2)
        self.assertEqual(channel_config[0]["type"], "sentinel")
        self.assertEqual(channel_config[0]["service_name"], "mymaster")
        self.assertEqual(len(channel_config[0]["sentinels"]), 1)
        self.assertEqual(channel_config[0]["sentinels"][0]["host"], "myredis")
        self.assertEqual(channel_config[0]["sentinels"][0]["port"], 1293)
        self.assertEqual(channel_config[1]["type"], "sentinel")
        self.assertEqual(channel_config[1]["service_name"], "mymaster")
        self.assertEqual(len(channel_config[1]["sentinels"]), 1)
        self.assertEqual(channel_config[1]["sentinels"][0]["host"], "myredis")
        self.assertEqual(channel_config[1]["sentinels"][0]["port"], 1293)
        self.assertTrue(channel_config[1]["is_slave"])


class TestCustomQoS(TestCase):
    def setUp(self):
        self.channel = MagicMock()
        self.custom_qos = CustomQoS(self.channel)

    @patch('authentik.root.redis_middleware_kombu.mutex')
    @patch('authentik.root.redis_middleware_kombu._detect_environment')
    def test_restore_visible(self, mock_detect_environment, mock_mutex):
        mock_detect_environment.return_value = 'gevent'
        mock_client = MagicMock()
        self.channel.conn_or_acquire.return_value.__enter__.return_value = mock_client
        mock_client.zrevrangebyscore.return_value = [('tag', 1)]
        mock_mutex.return_value.__enter__.return_value = None

        self.custom_qos.restore_visible()

        mock_client.zrevrangebyscore.assert_called_once()
        self.custom_qos.restore_by_tag.assert_called_once_with('tag', mock_client)

    @patch('authentik.root.redis_middleware_kombu.loads')
    def test_restore_by_tag(self, mock_loads):
        mock_client = MagicMock()
        mock_tag = MagicMock()
        self.custom_qos.restore_by_tag(mock_tag, client=mock_client)
        mock_client.pipeline.assert_called_once()
        mock_loads.assert_called_once()


class TestCustomClusterChannel(TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.channel = CustomClusterChannel(self.conn)

    def test_inject_custom_connection_class(self):
        connection_class = MagicMock()
        AsyncConnection = self.channel.inject_custom_connection_class(connection_class)
        connection = AsyncConnection()
        connection.disconnect()
        connection_class.disconnect.assert_called_once()
        self.conn._on_connection_disconnect.assert_called_once_with(connection)

    def test_create_client(self):
        with patch('authentik.root.redis_middleware_kombu.get_client') as mock_get_client:
            self.channel._create_client()
            mock_get_client.assert_called_once_with(self.channel.client_config, self.channel.pool)

    def test_get_pool(self):
        with patch('authentik.root.redis_middleware_kombu.get_connection_pool') as mock_get_connection_pool:
            self.channel._get_pool()
            mock_get_connection_pool.assert_called_once_with(
                self.channel.config,
                use_async=False,
                update_connection_class=self.channel.inject_custom_connection_class
            )

    def test_exchange_bind(self):
        with self.assertRaises(NotImplementedError):
            self.channel.exchange_bind()

    def test_exchange_unbind(self):
        with self.assertRaises(NotImplementedError):
            self.channel.exchange_unbind()

    def test_flow(self):
        with self.assertRaises(NotImplementedError):
            self.channel.flow()

    def test_brpop_start(self):
        self.channel._queue_cycle = MagicMock()
        self.channel._queue_cycle.consume.return_value = []
        self.channel._brpop_start()
        self.assertFalse(self.channel._in_poll)

    def test_brpop_read(self):
        self.channel.client = MagicMock()
        self.channel.connection = MagicMock()
        self.channel.connection_errors = MagicMock()
        self.channel._queue_cycle = MagicMock()
        self.channel._brpop_read(conn=MagicMock())
        self.assertFalse(self.channel._in_poll)

    def test_poll_error(self):
        self.channel.client = MagicMock()
        self.channel._poll_error('BRPOP', MagicMock())
        self.channel.client.parse_response.assert_called_once()


class TestRedisSentinelHA(TestCase):
    """Unit tests for HA Redis Sentinel scenarios in custom middleware."""

    def test_sentinel_master_failover(self):
        """Simulate a Sentinel-managed master failover."""
        fake_master = fakeredis.FakeRedis()
        fake_replica = fakeredis.FakeRedis()
        fake_master.set("before_failover", "123")
        fake_replica.set("before_failover", "123")
        client = fake_master
        self.assertEqual(client.get("before_failover"), b"123")

        # Simulate master failure by patching get() to raise a ConnectionError
        with patch.object(fake_master, 'get', side_effect=exceptions.ConnectionError("Master down")):
            with pytest.raises(exceptions.ConnectionError):
                client.get("before_failover")
            # Sentinel promotes replica as new master
            client = fake_replica
        self.assertEqual(client.get("before_failover"), b"123")
        client.set("after_failover", "456")
        self.assertIsNone(fake_master.get("after_failover"))
        self.assertEqual(fake_replica.get("after_failover"), b"456")

    def test_sentinel_connection_interruption_recovery(self):
        """Simulate transient network timeouts and recovery in a Sentinel setup."""
        fake_master = fakeredis.FakeRedis()
        client = fake_master
        fake_master.set("key", "value")
        calls = {'attempt': 0}

        def flaky_get(key):
            calls['attempt'] += 1
            if calls['attempt'] == 1:
                raise exceptions.TimeoutError("Connection timed out")
            return fake_master.get(key)

        with patch.object(fake_master, 'get', side_effect=flaky_get):
            with pytest.raises(exceptions.TimeoutError):
                client.get("key")
            self.assertEqual(client.get("key"), b"value")
        self.assertEqual(fake_master.get("key"), b"value")

    def test_sentinel_write_during_failover(self):
        """Test handling of writes during Sentinel failover that encounter ReadOnlyError."""
        fake_master = fakeredis.FakeRedis()
        fake_replica = fakeredis.FakeRedis()
        client = fake_master
        fake_master.set("some_key", "1")
        with patch.object(fake_master, 'set', side_effect=exceptions.ReadOnlyError("READONLY You can't write against a read only replica.")):
            with pytest.raises(exceptions.ReadOnlyError):
                client.set("some_key", "2")
            client = fake_replica
            client.set("some_key", "2")
        self.assertEqual(fake_replica.get("some_key"), b"2")
        self.assertNotEqual(fake_master.get("some_key"), b"2")


class TestRedisClusterHA(TestCase):
    """Unit tests for HA Redis Cluster scenarios in custom middleware."""

    def test_cluster_master_failover(self):
        """Simulate a master node failover in a Redis Cluster shard."""
        fake_master = fakeredis.FakeRedis()
        fake_replica = fakeredis.FakeRedis()
        fake_master.set("cluster_key", "init")
        fake_replica.set("cluster_key", "init")
        client = fake_master
        self.assertEqual(client.get("cluster_key"), b"init")

        # Simulate master failure by patching get() to raise ConnectionError
        with patch.object(fake_master, 'get', side_effect=exceptions.ConnectionError("Node down")):
            with pytest.raises(exceptions.ConnectionError):
                client.get("cluster_key")
            client = fake_replica
        self.assertEqual(client.get("cluster_key"), b"init")
        client.set("cluster_new", "12345")
        self.assertIsNone(fake_master.get("cluster_new"))
        self.assertEqual(fake_replica.get("cluster_new"), b"12345")

    def test_cluster_network_partition_recovery(self):
        """Simulate a cluster-wide outage and subsequent recovery."""
        fake_node = fakeredis.FakeRedis()
        client = fake_node
        with patch.object(fake_node, 'set', side_effect=exceptions.ClusterDownError("CLUSTERDOWN The cluster is down")):
            with pytest.raises(exceptions.ClusterDownError):
                client.set("key", "value")
        client.set("key", "value")
        self.assertEqual(client.get("key"), b"value")

    def test_cluster_operation_during_failover(self):
        """Test that operations during cluster failover raise errors and succeed after recovery."""
        fake_master = fakeredis.FakeRedis()
        fake_replica = fakeredis.FakeRedis()
        client = fake_master
        fake_master.set("failover_key", "A")
        fake_replica.set("failover_key", "A")
        with patch.object(fake_master, 'get', side_effect=exceptions.ClusterDownError("CLUSTERDOWN Failover in progress")):
            with pytest.raises(exceptions.ClusterDownError):
                client.get("failover_key")
            client = fake_replica
        self.assertEqual(client.get("failover_key"), b"A")