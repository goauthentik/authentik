"""Test config loader"""
from os import chmod, environ, unlink, write
from tempfile import mkstemp

from django.conf import ImproperlyConfigured
from django.test import TestCase

from authentik.lib.config import ENV_PREFIX, ConfigLoader


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

    def test_update_redis_url_from_env(self):
        """Test generating Redis URL from environment"""
        config = ConfigLoader()
        environ["AUTHENTIK_REDIS__HOST"] = "myredis"
        environ["AUTHENTIK_REDIS__PORT"] = "9637"
        environ["AUTHENTIK_REDIS__DB"] = "56"
        environ["AUTHENTIK_REDIS__USERNAME"] = "default"
        environ["AUTHENTIK_REDIS__PASSWORD"] = "\"'% !.;.°"
        environ["AUTHENTIK_REDIS__TLS"] = "true"
        environ["AUTHENTIK_REDIS__TLS_REQS"] = "none"
        config.update_from_env()
        config.check_deprecations()
        self.assertEqual(
            config.y("redis.url"),
            "rediss://myredis:9637/56?insecureskipverify=true&password=%22%27%25+%21.%3B.%C2%B0&username=default",
        )
