"""Test config loader"""
from os import chmod, environ, unlink, write
from tempfile import mkstemp

from django.conf import ImproperlyConfigured
from django.test import TestCase

from authentik.lib.config import ENV_PREFIX, UNSET, ConfigLoader


class TestConfig(TestCase):
    """Test config loader"""

    def test_env(self):
        """Test simple instance"""
        config = ConfigLoader()
        environ[ENV_PREFIX + "_test__test"] = "bar"
        config.update_from_env()
        self.assertEqual(config.y("test.test"), "bar")

    def test_patch(self):
        """Test patch decorator"""
        config = ConfigLoader()
        config.y_set("foo.bar", "bar")
        self.assertEqual(config.y("foo.bar"), "bar")
        with config.patch("foo.bar", "baz"):
            self.assertEqual(config.y("foo.bar"), "baz")
        self.assertEqual(config.y("foo.bar"), "bar")

    def test_uri_env(self):
        """Test URI parsing (environment)"""
        config = ConfigLoader()
        environ["foo"] = "bar"
        self.assertEqual(config.parse_uri("env://foo"), "bar")
        self.assertEqual(config.parse_uri("env://foo?bar"), "bar")

    def test_uri_file(self):
        """Test URI parsing (file load)"""
        config = ConfigLoader()
        file, file_name = mkstemp()
        write(file, "foo".encode())
        _, file2_name = mkstemp()
        chmod(file2_name, 0o000)  # Remove all permissions so we can't read the file
        self.assertEqual(config.parse_uri(f"file://{file_name}"), "foo")
        self.assertEqual(config.parse_uri(f"file://{file2_name}?def"), "def")
        unlink(file_name)
        unlink(file2_name)

    def test_file_update(self):
        """Test update_from_file"""
        config = ConfigLoader()
        file, file_name = mkstemp()
        write(file, "{".encode())
        file2, file2_name = mkstemp()
        write(file2, "{".encode())
        chmod(file2_name, 0o000)  # Remove all permissions so we can't read the file
        with self.assertRaises(ImproperlyConfigured):
            config.update_from_file(file_name)
        config.update_from_file(file2_name)
        unlink(file_name)
        unlink(file2_name)

    def test_check_deprecations(self):
        """Test config key re-write for deprecated env vars"""
        config = ConfigLoader()
        environ[ENV_PREFIX + "_REDIS__BROKER_URL"] = "redis://myredis:8327/43"
        environ[ENV_PREFIX + "_REDIS__BROKER_TRANSPORT_OPTIONS"] = "bWFzdGVybmFtZT1teW1hc3Rlcg=="
        environ[ENV_PREFIX + "_REDIS__CACHE_TIMEOUT"] = "124s"
        environ[ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_FLOWS"] = "32m"
        environ[ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_POLICIES"] = "3920ns"
        environ[ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_REPUTATION"] = "298382us"
        config.update_from_env()
        config.check_deprecations()
        self.assertEqual(config.y("redis.broker_url", UNSET), UNSET)
        self.assertEqual(config.y("redis.broker_transport_options", UNSET), UNSET)
        self.assertEqual(config.y("redis.cache_timeout", UNSET), UNSET)
        self.assertEqual(config.y("redis.cache_timeout_flows", UNSET), UNSET)
        self.assertEqual(config.y("redis.cache_timeout_policies", UNSET), UNSET)
        self.assertEqual(config.y("redis.cache_timeout_reputation", UNSET), UNSET)
        self.assertEqual(config.y("broker.url"), "redis://myredis:8327/43")
        self.assertEqual(config.y("broker.transport_options"), "bWFzdGVybmFtZT1teW1hc3Rlcg==")
        self.assertEqual(config.y("cache.timeout"), "124s")
        self.assertEqual(config.y("cache.timeout_flows"), "32m")
        self.assertEqual(config.y("cache.timeout_policies"), "3920ns")
        self.assertEqual(config.y("cache.timeout_reputation"), "298382us")

    def test_update_redis_url_from_env(self):
        """Test generating Redis URL from environment"""
        config = ConfigLoader()
        environ[ENV_PREFIX + "_REDIS__URL"] = (
            "redis://oldredis:2493/2"
            + "?idletimeout=20s&skipverify=true"
            + "&password=pass&username=redis"
        )
        environ[ENV_PREFIX + "_REDIS__HOST"] = "myredis"
        environ[ENV_PREFIX + "_REDIS__PORT"] = "9637"
        environ[ENV_PREFIX + "_REDIS__DB"] = "56"
        environ[ENV_PREFIX + "_REDIS__USERNAME"] = "default"
        environ[ENV_PREFIX + "_REDIS__PASSWORD"] = "\"'% !.;.°"
        environ[ENV_PREFIX + "_REDIS__TLS"] = "true"
        environ[ENV_PREFIX + "_REDIS__TLS_REQS"] = "none"
        config.update_from_env()
        config.update_redis_url_from_env()
        self.assertEqual(
            config.y("redis.url"),
            "rediss://myredis:9637/56?idletimeout=20s&insecureskipverify=true"
            + "&password=%22%27%25+%21.%3B.%C2%B0&username=default",
        )
