"""root tests"""

from base64 import b64encode

from celery.app.amqp import Connection as AmqpConnection
from django.conf import settings
from django.core.cache import BaseCache
from django.test import TestCase
from django.urls import reverse

from authentik.root.redis_middleware_celery import CustomCelery
from authentik.root.redis_middleware_channels import CustomChannelLayer
from authentik.root.redis_middleware_django import CustomClient
from authentik.root.redis_middleware_kombu import CustomConnection


class TestRoot(TestCase):
    """Test root application"""

    def test_monitoring_error(self):
        """Test monitoring without any credentials"""
        response = self.client.get(reverse("metrics"))
        self.assertEqual(response.status_code, 401)

    def test_monitoring_ok(self):
        """Test monitoring with credentials"""
        creds = "Basic " + b64encode(f"monitor:{settings.SECRET_KEY}".encode()).decode("utf-8")
        auth_headers = {"HTTP_AUTHORIZATION": creds}
        response = self.client.get(reverse("metrics"), **auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_monitoring_live(self):
        """Test LiveView"""
        self.assertEqual(self.client.get(reverse("health-live")).status_code, 204)

    def test_monitoring_ready(self):
        """Test ReadyView"""
        self.assertEqual(self.client.get(reverse("health-ready")).status_code, 204)


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
