"""Test config loader"""
from os import chmod, environ, unlink, write
from tempfile import mkstemp
from unittest import mock

from django.conf import ImproperlyConfigured
from django.test import TestCase

from authentik.lib.config import ENV_PREFIX, UNSET, ConfigLoader


class TestConfig(TestCase):
    """Test config loader"""

    check_deprecations_env_vars = {
        ENV_PREFIX + "_REDIS__BROKER_URL": "redis://myredis:8327/43",
        ENV_PREFIX + "_REDIS__BROKER_TRANSPORT_OPTIONS": "bWFzdGVybmFtZT1teW1hc3Rlcg==",
        ENV_PREFIX + "_REDIS__CACHE_TIMEOUT": "124s",
        ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_FLOWS": "32m",
        ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_POLICIES": "3920ns",
        ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_REPUTATION": "298382us",
    }
    update_redis_url_from_env_env_vars = {
        ENV_PREFIX
        + "_REDIS__URL": "redis://oldredis:2493/2?idletimeout=20s&skipverify=true"
        + "&password=pass&username=redis",
        ENV_PREFIX + "_REDIS__HOST": "myredis",
        ENV_PREFIX + "_REDIS__PORT": "9637",
        ENV_PREFIX + "_REDIS__DB": "56",
        ENV_PREFIX + "_REDIS__USERNAME": "default",
        ENV_PREFIX + "_REDIS__PASSWORD": "\"'% !.;.°",
        ENV_PREFIX + "_REDIS__TLS": "true",
        ENV_PREFIX + "_REDIS__TLS_REQS": "none",
    }
    update_redis_url_from_env_tls_reqs_env_vars = {
        ENV_PREFIX + "_REDIS__URL": "redis://myredis:5132/8?insecureskipverify=notvalid",
        ENV_PREFIX + "_REDIS__TLS": "true",
        ENV_PREFIX + "_REDIS__TLS_REQS": "optional",
    }

    @mock.patch.dict(environ, {ENV_PREFIX + "_test__test": "bar"})
    def test_env(self):
        """Test simple instance"""
        config = ConfigLoader()
        config.update_from_env()
        self.assertEqual(config.get("test.test"), "bar")

    def test_patch(self):
        """Test patch decorator"""
        config = ConfigLoader()
        config.set("foo.bar", "bar")
        self.assertEqual(config.get("foo.bar"), "bar")
        with config.patch("foo.bar", "baz"):
            self.assertEqual(config.get("foo.bar"), "baz")
        self.assertEqual(config.get("foo.bar"), "bar")

    @mock.patch.dict(environ, {"foo": "bar"})
    def test_uri_env(self):
        """Test URI parsing (environment)"""
        config = ConfigLoader()
        self.assertEqual(config.parse_uri("env://foo"), "bar")
        self.assertEqual(config.parse_uri("env://foo?bar"), "bar")

    def test_uri_file(self):
        """Test URI parsing (file load)"""
        config = ConfigLoader()
        file, file_name = mkstemp()
        write(file, "foo".encode())
        _, file2_name = mkstemp()
        chmod(file2_name, 0o000)  # Remove all permissions so we can't read the file
        self.assertEqual(config.parse_uri(f"file://{file_name}").value, "foo")
        self.assertEqual(config.parse_uri(f"file://{file2_name}?def").value, "def")
        unlink(file_name)
        unlink(file2_name)

    def test_uri_file_update(self):
        """Test URI parsing (file load and update)"""
        file, file_name = mkstemp()
        write(file, "foo".encode())
        config = ConfigLoader(file_test=f"file://{file_name}")
        self.assertEqual(config.get("file_test"), "foo")

        # Update config file
        write(file, "bar".encode())
        config.refresh("file_test")
        self.assertEqual(config.get("file_test"), "foobar")

        unlink(file_name)

    def test_uri_env_full(self):
        """Test URI set as env variable"""
        environ["AUTHENTIK_TEST_VAR"] = "file:///foo?bar"
        config = ConfigLoader()
        self.assertEqual(config.get("test_var"), "bar")

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

    def test_get_int(self):
        """Test get_int"""
        config = ConfigLoader()
        config.set("foo", 1234)
        self.assertEqual(config.get_int("foo"), 1234)

    def test_get_int_invalid(self):
        """Test get_int"""
        config = ConfigLoader()
        config.set("foo", "bar")
        self.assertEqual(config.get_int("foo", 1234), 1234)

    @mock.patch.dict(environ, check_deprecations_env_vars)
    def test_check_deprecations(self):
        """Test config key re-write for deprecated env vars"""
        config = ConfigLoader()
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

    @mock.patch.dict(environ, update_redis_url_from_env_env_vars)
    def test_update_redis_url_from_env(self):
        """Test updating Redis URL from environment"""
        config = ConfigLoader()
        config.update_from_env()
        config.update_redis_url_from_env()
        self.assertEqual(
            config.y("redis.url"),
            "rediss://myredis:9637/56?idletimeout=20s&insecureskipverify=true"
            + "&password=%22%27%25+%21.%3B.%C2%B0&username=default",
        )

    @mock.patch.dict(environ, update_redis_url_from_env_tls_reqs_env_vars)
    def test_update_redis_url_from_env_tls_reqs(self):
        """Test updating Redis URL from environment with new TLS reqs"""
        config = ConfigLoader()
        config.update_from_env()
        config.update_redis_url_from_env()
        self.assertEqual(
            config.y("redis.url"),
            "rediss://myredis:5132/8?skipverify=true",
        )
