"""Test config loader"""

import base64
from json import dumps
from os import chmod, environ, unlink, write
from tempfile import mkstemp
from unittest import mock

from django.conf import ImproperlyConfigured
from django.test import TestCase

from authentik.lib.config import (
    ENV_PREFIX,
    UNSET,
    Attr,
    AttrEncoder,
    ConfigLoader,
    django_db_config,
)


class TestConfig(TestCase):
    """Test config loader"""

    check_deprecations_env_vars = {
        ENV_PREFIX + "_WORKER__CONCURRENCY": "2",
        ENV_PREFIX + "_REDIS__CACHE_TIMEOUT": "124s",
        ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_FLOWS": "32m",
        ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_POLICIES": "3920ns",
        ENV_PREFIX + "_REDIS__CACHE_TIMEOUT_REPUTATION": "298382us",
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
        foo_uri = "env://foo"
        foo_parsed = config.parse_uri(foo_uri)
        self.assertEqual(foo_parsed.value, "bar")
        self.assertEqual(foo_parsed.source_type, Attr.Source.URI)
        self.assertEqual(foo_parsed.source, foo_uri)
        foo_bar_uri = "env://foo?bar"
        foo_bar_parsed = config.parse_uri(foo_bar_uri)
        self.assertEqual(foo_bar_parsed.value, "bar")
        self.assertEqual(foo_bar_parsed.source_type, Attr.Source.URI)
        self.assertEqual(foo_bar_parsed.source, foo_bar_uri)

    def test_uri_file(self):
        """Test URI parsing (file load)"""
        config = ConfigLoader()
        file, file_name = mkstemp()
        write(file, b"foo")
        _, file2_name = mkstemp()
        chmod(file2_name, 0o000)  # Remove all permissions so we can't read the file
        self.assertEqual(config.parse_uri(f"file://{file_name}").value, "foo")
        self.assertEqual(config.parse_uri(f"file://{file2_name}?def").value, "def")
        unlink(file_name)
        unlink(file2_name)

    def test_uri_file_update(self):
        """Test URI parsing (file load and update)"""
        file, file_name = mkstemp()
        write(file, b"foo")
        config = ConfigLoader(file_test=f"file://{file_name}")
        self.assertEqual(config.get("file_test"), "foo")

        # Update config file
        write(file, b"bar")
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
        write(file, b"{")
        file2, file2_name = mkstemp()
        write(file2, b"{")
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

    def test_get_dict_from_b64_json(self):
        """Test get_dict_from_b64_json"""
        config = ConfigLoader()
        test_value = b'  { "foo": "bar"   }   '
        b64_value = base64.b64encode(test_value)
        config.set("foo", b64_value)
        self.assertEqual(config.get_dict_from_b64_json("foo"), {"foo": "bar"})

    def test_get_dict_from_b64_json_missing_brackets(self):
        """Test get_dict_from_b64_json with missing brackets"""
        config = ConfigLoader()
        test_value = b' "foo": "bar"     '
        b64_value = base64.b64encode(test_value)
        config.set("foo", b64_value)
        self.assertEqual(config.get_dict_from_b64_json("foo"), {"foo": "bar"})

    def test_get_dict_from_b64_json_invalid(self):
        """Test get_dict_from_b64_json with invalid value"""
        config = ConfigLoader()
        config.set("foo", "bar")
        self.assertEqual(config.get_dict_from_b64_json("foo"), {})

    def test_attr_json_encoder(self):
        """Test AttrEncoder"""
        test_attr = Attr("foo", Attr.Source.ENV, "AUTHENTIK_REDIS__USERNAME")
        json_attr = dumps(test_attr, indent=4, cls=AttrEncoder)
        self.assertEqual(json_attr, '"foo"')

    def test_attr_json_encoder_no_attr(self):
        """Test AttrEncoder if no Attr is passed"""

        class Test:
            """Non Attr class"""

        with self.assertRaises(TypeError):
            test_obj = Test()
            dumps(test_obj, indent=4, cls=AttrEncoder)

    def test_get_optional_int(self):
        config = ConfigLoader()
        self.assertEqual(config.get_optional_int("foo", 21), 21)
        self.assertEqual(config.get_optional_int("foo"), None)
        config.set("foo", "21")
        self.assertEqual(config.get_optional_int("foo"), 21)
        self.assertEqual(config.get_optional_int("foo", 0), 21)
        self.assertEqual(config.get_optional_int("foo", "null"), 21)
        config.set("foo", "null")
        self.assertEqual(config.get_optional_int("foo"), None)
        self.assertEqual(config.get_optional_int("foo", 21), None)

    @mock.patch.dict(environ, check_deprecations_env_vars)
    def test_check_deprecations(self):
        """Test config key re-write for deprecated env vars"""
        config = ConfigLoader()
        config.update_from_env()
        config.check_deprecations()
        self.assertEqual(config.get("worker.concurrency", UNSET), UNSET)
        self.assertEqual(config.get("redis.cache_timeout", UNSET), UNSET)
        self.assertEqual(config.get("redis.cache_timeout_flows", UNSET), UNSET)
        self.assertEqual(config.get("redis.cache_timeout_policies", UNSET), UNSET)
        self.assertEqual(config.get("redis.cache_timeout_reputation", UNSET), UNSET)
        self.assertEqual(config.get("worker.threads"), 2)
        self.assertEqual(config.get("cache.timeout"), "124s")
        self.assertEqual(config.get("cache.timeout_flows"), "32m")
        self.assertEqual(config.get("cache.timeout_policies"), "3920ns")
        self.assertEqual(config.get("cache.timeout_reputation"), "298382us")

    def test_get_keys(self):
        """Test get_keys"""
        config = ConfigLoader()
        config.set("foo.bar", "baz")
        self.assertEqual(list(config.get_keys("foo")), ["bar"])

    def test_db_default(self):
        """Test default DB Config"""
        config = ConfigLoader()
        config.set("postgresql.host", "foo")
        config.set("postgresql.name", "foo")
        config.set("postgresql.user", "foo")
        config.set("postgresql.password", "foo")
        config.set("postgresql.port", "foo")
        config.set("postgresql.sslmode", "foo")
        config.set("postgresql.sslrootcert", "foo")
        config.set("postgresql.sslcert", "foo")
        config.set("postgresql.sslkey", "foo")
        config.set("postgresql.test.name", "foo")
        conf = django_db_config(config)
        self.assertEqual(
            conf,
            {
                "default": {
                    "ENGINE": "authentik.root.db",
                    "HOST": "foo",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "foo",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                    "CONN_MAX_AGE": 0,
                    "CONN_HEALTH_CHECKS": False,
                    "DISABLE_SERVER_SIDE_CURSORS": False,
                }
            },
        )

    def test_db_conn_max_age(self):
        """Test DB conn_max_age Config"""
        config = ConfigLoader()
        config.set("postgresql.conn_max_age", "null")
        conf = django_db_config(config)
        self.assertEqual(
            conf["default"]["CONN_MAX_AGE"],
            None,
        )

    def test_db_read_replicas(self):
        """Test read replicas"""
        config = ConfigLoader()
        config.set("postgresql.host", "foo")
        config.set("postgresql.name", "foo")
        config.set("postgresql.user", "foo")
        config.set("postgresql.password", "foo")
        config.set("postgresql.port", "foo")
        config.set("postgresql.sslmode", "foo")
        config.set("postgresql.sslrootcert", "foo")
        config.set("postgresql.sslcert", "foo")
        config.set("postgresql.sslkey", "foo")
        config.set("postgresql.test.name", "foo")
        # Read replica
        config.set("postgresql.read_replicas.0.host", "bar")
        conf = django_db_config(config)
        self.assertEqual(
            conf,
            {
                "default": {
                    "ENGINE": "authentik.root.db",
                    "HOST": "foo",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "foo",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                    "CONN_MAX_AGE": 0,
                    "CONN_HEALTH_CHECKS": False,
                    "DISABLE_SERVER_SIDE_CURSORS": False,
                },
                "replica_0": {
                    "ENGINE": "authentik.root.db",
                    "HOST": "bar",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "foo",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                    "CONN_MAX_AGE": 0,
                    "CONN_HEALTH_CHECKS": False,
                    "DISABLE_SERVER_SIDE_CURSORS": False,
                },
            },
        )

    def test_db_read_replicas_pgbouncer(self):
        """Test read replicas"""
        config = ConfigLoader()
        config.set("postgresql.host", "foo")
        config.set("postgresql.name", "foo")
        config.set("postgresql.user", "foo")
        config.set("postgresql.password", "foo")
        config.set("postgresql.port", "foo")
        config.set("postgresql.sslmode", "foo")
        config.set("postgresql.sslrootcert", "foo")
        config.set("postgresql.sslcert", "foo")
        config.set("postgresql.sslkey", "foo")
        config.set("postgresql.test.name", "foo")
        config.set("postgresql.use_pgbouncer", True)
        # Read replica
        config.set("postgresql.read_replicas.0.host", "bar")
        # Override conn_max_age
        config.set("postgresql.read_replicas.0.conn_max_age", 10)
        # This isn't supported
        config.set("postgresql.read_replicas.0.use_pgbouncer", False)
        conf = django_db_config(config)
        self.assertEqual(
            conf,
            {
                "default": {
                    "DISABLE_SERVER_SIDE_CURSORS": True,
                    "CONN_MAX_AGE": None,
                    "CONN_HEALTH_CHECKS": False,
                    "ENGINE": "authentik.root.db",
                    "HOST": "foo",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "foo",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                },
                "replica_0": {
                    "DISABLE_SERVER_SIDE_CURSORS": True,
                    "CONN_MAX_AGE": 10,
                    "CONN_HEALTH_CHECKS": False,
                    "ENGINE": "authentik.root.db",
                    "HOST": "bar",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "foo",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                },
            },
        )

    def test_db_read_replicas_pgpool(self):
        """Test read replicas"""
        config = ConfigLoader()
        config.set("postgresql.host", "foo")
        config.set("postgresql.name", "foo")
        config.set("postgresql.user", "foo")
        config.set("postgresql.password", "foo")
        config.set("postgresql.port", "foo")
        config.set("postgresql.sslmode", "foo")
        config.set("postgresql.sslrootcert", "foo")
        config.set("postgresql.sslcert", "foo")
        config.set("postgresql.sslkey", "foo")
        config.set("postgresql.test.name", "foo")
        config.set("postgresql.use_pgpool", True)
        # Read replica
        config.set("postgresql.read_replicas.0.host", "bar")
        # This isn't supported
        config.set("postgresql.read_replicas.0.use_pgpool", False)
        conf = django_db_config(config)
        self.assertEqual(
            conf,
            {
                "default": {
                    "DISABLE_SERVER_SIDE_CURSORS": True,
                    "CONN_MAX_AGE": 0,
                    "CONN_HEALTH_CHECKS": False,
                    "ENGINE": "authentik.root.db",
                    "HOST": "foo",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "foo",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                },
                "replica_0": {
                    "DISABLE_SERVER_SIDE_CURSORS": True,
                    "CONN_MAX_AGE": 0,
                    "CONN_HEALTH_CHECKS": False,
                    "ENGINE": "authentik.root.db",
                    "HOST": "bar",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "foo",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                },
            },
        )

    def test_db_read_replicas_diff_ssl(self):
        """Test read replicas (with different SSL Settings)"""
        """Test read replicas"""
        config = ConfigLoader()
        config.set("postgresql.host", "foo")
        config.set("postgresql.name", "foo")
        config.set("postgresql.user", "foo")
        config.set("postgresql.password", "foo")
        config.set("postgresql.port", "foo")
        config.set("postgresql.sslmode", "foo")
        config.set("postgresql.sslrootcert", "foo")
        config.set("postgresql.sslcert", "foo")
        config.set("postgresql.sslkey", "foo")
        config.set("postgresql.test.name", "foo")
        # Read replica
        config.set("postgresql.read_replicas.0.host", "bar")
        config.set("postgresql.read_replicas.0.sslcert", "bar")
        conf = django_db_config(config)
        self.assertEqual(
            conf,
            {
                "default": {
                    "ENGINE": "authentik.root.db",
                    "HOST": "foo",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "foo",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                    "DISABLE_SERVER_SIDE_CURSORS": False,
                    "CONN_MAX_AGE": 0,
                    "CONN_HEALTH_CHECKS": False,
                },
                "replica_0": {
                    "ENGINE": "authentik.root.db",
                    "HOST": "bar",
                    "NAME": "foo",
                    "OPTIONS": {
                        "pool": False,
                        "sslcert": "bar",
                        "sslkey": "foo",
                        "sslmode": "foo",
                        "sslrootcert": "foo",
                    },
                    "PASSWORD": "foo",
                    "PORT": "foo",
                    "TEST": {"NAME": "foo"},
                    "USER": "foo",
                    "DISABLE_SERVER_SIDE_CURSORS": False,
                    "CONN_MAX_AGE": 0,
                    "CONN_HEALTH_CHECKS": False,
                },
            },
        )

    def test_db_conn_options(self):
        config = ConfigLoader()
        config.set(
            "postgresql.conn_options",
            base64.b64encode(
                dumps(
                    {
                        "connect_timeout": "10",
                    }
                ).encode()
            ).decode(),
        )
        config.set("postgresql.read_replicas.0.host", "bar")

        conf = django_db_config(config)

        self.assertEqual(
            conf["default"]["OPTIONS"]["connect_timeout"],
            "10",
        )
        self.assertNotIn("connect_timeout", conf["replica_0"]["OPTIONS"])

    def test_db_conn_options_read_replicas(self):
        config = ConfigLoader()
        config.set(
            "postgresql.replica_conn_options",
            base64.b64encode(
                dumps(
                    {
                        "connect_timeout": "10",
                    }
                ).encode()
            ).decode(),
        )
        config.set("postgresql.read_replicas.0.host", "bar")
        config.set("postgresql.read_replicas.1.host", "bar")
        config.set(
            "postgresql.read_replicas.1.conn_options",
            base64.b64encode(
                dumps(
                    {
                        "connect_timeout": "20",
                    }
                ).encode()
            ).decode(),
        )

        conf = django_db_config(config)

        self.assertNotIn("connect_timeout", conf["default"]["OPTIONS"])
        self.assertEqual(
            conf["replica_0"]["OPTIONS"]["connect_timeout"],
            "10",
        )
        self.assertEqual(
            conf["replica_1"]["OPTIONS"]["connect_timeout"],
            "20",
        )

    # FIXME: Temporarily force pool to be deactivated.
    # See https://github.com/goauthentik/authentik/issues/14320
    # def test_db_pool(self):
    #     """Test DB Config with pool"""
    #     config = ConfigLoader()
    #     config.set("postgresql.host", "foo")
    #     config.set("postgresql.name", "foo")
    #     config.set("postgresql.user", "foo")
    #     config.set("postgresql.password", "foo")
    #     config.set("postgresql.port", "foo")
    #     config.set("postgresql.test.name", "foo")
    #     config.set("postgresql.use_pool", True)
    #     conf = django_db_config(config)
    #     self.assertEqual(
    #         conf,
    #         {
    #             "default": {
    #                 "ENGINE": "authentik.root.db",
    #                 "HOST": "foo",
    #                 "NAME": "foo",
    #                 "OPTIONS": {
    #                     "pool": True,
    #                     "sslcert": None,
    #                     "sslkey": None,
    #                     "sslmode": None,
    #                     "sslrootcert": None,
    #                 },
    #                 "PASSWORD": "foo",
    #                 "PORT": "foo",
    #                 "TEST": {"NAME": "foo"},
    #                 "USER": "foo",
    #                 "CONN_MAX_AGE": 0,
    #                 "CONN_HEALTH_CHECKS": False,
    #                 "DISABLE_SERVER_SIDE_CURSORS": False,
    #             }
    #         },
    #     )

    # def test_db_pool_options(self):
    #     """Test DB Config with pool"""
    #     config = ConfigLoader()
    #     config.set("postgresql.host", "foo")
    #     config.set("postgresql.name", "foo")
    #     config.set("postgresql.user", "foo")
    #     config.set("postgresql.password", "foo")
    #     config.set("postgresql.port", "foo")
    #     config.set("postgresql.test.name", "foo")
    #     config.set("postgresql.use_pool", True)
    #     config.set(
    #         "postgresql.pool_options",
    #         base64.b64encode(
    #             dumps(
    #                 {
    #                     "max_size": 15,
    #                 }
    #             ).encode()
    #         ).decode(),
    #     )
    #     conf = django_db_config(config)
    #     self.assertEqual(
    #         conf,
    #         {
    #             "default": {
    #                 "ENGINE": "authentik.root.db",
    #                 "HOST": "foo",
    #                 "NAME": "foo",
    #                 "OPTIONS": {
    #                     "pool": {
    #                         "max_size": 15,
    #                     },
    #                     "sslcert": None,
    #                     "sslkey": None,
    #                     "sslmode": None,
    #                     "sslrootcert": None,
    #                 },
    #                 "PASSWORD": "foo",
    #                 "PORT": "foo",
    #                 "TEST": {"NAME": "foo"},
    #                 "USER": "foo",
    #                 "CONN_MAX_AGE": 0,
    #                 "CONN_HEALTH_CHECKS": False,
    #                 "DISABLE_SERVER_SIDE_CURSORS": False,
    #             }
    #         },
    #     )
