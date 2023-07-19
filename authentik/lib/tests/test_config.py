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
        self.assertEqual(config.get("test.test"), "bar")

    def test_patch(self):
        """Test patch decorator"""
        config = ConfigLoader()
        config.set("foo.bar", "bar")
        self.assertEqual(config.get("foo.bar"), "bar")
        with config.patch("foo.bar", "baz"):
            self.assertEqual(config.get("foo.bar"), "baz")
        self.assertEqual(config.get("foo.bar"), "bar")

    def test_uri_env(self):
        """Test URI parsing (environment)"""
        config = ConfigLoader()
        environ["foo"] = "bar"
        self.assertEqual(config.parse_uri("env://foo").value, "bar")
        self.assertEqual(config.parse_uri("env://foo?bar").value, "bar")

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
