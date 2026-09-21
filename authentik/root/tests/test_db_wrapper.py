"""Tests for authentik.root.db.base.DatabaseWrapper.get_connection_params."""

from unittest import TestCase, mock

from django_tenants.postgresql_backend.base import (
    DatabaseWrapper as BaseDatabaseWrapper,
)

from authentik.lib.config import DIRECT_DB_ALIAS
from authentik.root.db.base import DatabaseWrapper


def _call_get_connection_params(alias: str, refresh_table: dict):
    """Construct a minimal DatabaseWrapper and call get_connection_params.

    ``refresh_table`` maps ``"postgresql.direct.host"`` etc. to the value that
    ``CONFIG.refresh`` should return for that key. Unmapped keys return ``None``.
    ``super().get_connection_params()`` is mocked to return a stable baseline
    dict so the test focuses on what our override does to it.
    """
    wrapper = DatabaseWrapper.__new__(DatabaseWrapper)
    wrapper.alias = alias

    baseline = {
        "host": "BASELINE_HOST",
        "port": 0,
        "user": "BASELINE_USER",
        "password": "BASELINE_PW",
        "dbname": "authentik",
        "sslmode": "BASELINE_SSLMODE",
    }

    with mock.patch.object(
        BaseDatabaseWrapper, "get_connection_params", return_value=dict(baseline)
    ):
        with mock.patch("authentik.root.db.base.CONFIG") as mock_config:
            mock_config.refresh.side_effect = refresh_table.get
            params = wrapper.get_connection_params()
            calls = [c.args[0] for c in mock_config.refresh.call_args_list]
            return params, calls


class TestDatabaseWrapperGetConnectionParams(TestCase):
    """Verify per-alias config prefix routing in get_connection_params."""

    def test_default_alias_reads_top_level_postgresql_prefix(self):
        """The ``default`` alias pulls host/port/user/password from
        ``postgresql.*`` and ignores any ``postgresql.direct.*`` keys."""
        refresh_table = {
            "postgresql.host": "127.0.0.1",
            "postgresql.port": 5432,
            "postgresql.user": "ak",
            "postgresql.password": "secret",
            # Direct keys must not influence the default alias.
            "postgresql.direct.host": "10.0.0.1",
            "postgresql.direct.sslmode": "verify-ca",
        }
        params, calls = _call_get_connection_params("default", refresh_table)
        self.assertEqual(params["host"], "127.0.0.1")
        self.assertEqual(params["port"], 5432)
        self.assertEqual(params["user"], "ak")
        self.assertEqual(params["password"], "secret")
        # OPTIONS untouched by our override
        self.assertEqual(params["sslmode"], "BASELINE_SSLMODE")
        self.assertIn("postgresql.host", calls)
        self.assertNotIn("postgresql.direct.host", calls)

    def test_direct_alias_reads_direct_prefix_then_falls_back(self):
        """``direct`` alias pulls host from ``postgresql.direct.*`` and falls
        back to ``postgresql.*`` for unset keys. Regression guard: without the
        alias-specific prefix, the HOST was overwritten with the default
        endpoint's host while ``OPTIONS`` (sslmode=verify-ca) stayed — producing
        ``connection to server at "<default-host>"... SSL was required``.
        """
        refresh_table = {
            "postgresql.direct.host": "10.114.0.29",
            "postgresql.direct.user": "direct_user",
            "postgresql.host": "127.0.0.1",
            "postgresql.port": 5432,
            "postgresql.user": "default_user",
            "postgresql.password": "default_pw",
        }
        params, calls = _call_get_connection_params(DIRECT_DB_ALIAS, refresh_table)
        self.assertEqual(params["host"], "10.114.0.29")
        self.assertEqual(params["user"], "direct_user")
        self.assertEqual(params["port"], 5432)
        self.assertEqual(params["password"], "default_pw")
        self.assertIn("postgresql.direct.host", calls)
        self.assertIn("postgresql.direct.port", calls)
        self.assertIn("postgresql.port", calls)

    def test_direct_alias_does_not_get_clobbered_with_default_host(self):
        """Regression for the original failure: direct alias ending up with
        HOST=default_host because the override didn't know about the prefix."""
        refresh_table = {
            "postgresql.direct.host": "10.114.0.29",
            "postgresql.host": "127.0.0.1",
        }
        params, _ = _call_get_connection_params(DIRECT_DB_ALIAS, refresh_table)
        self.assertNotEqual(
            params["host"],
            "127.0.0.1",
            "direct alias must not be clobbered with the default postgresql.host",
        )
        self.assertEqual(params["host"], "10.114.0.29")

    def test_replica_alias_reads_replica_prefix(self):
        """The ``replica_*`` aliases should continue to read from
        ``postgresql.read_replicas.<name>.*`` (the existing behavior pre-fix
        must not regress)."""
        refresh_table = {
            "postgresql.read_replicas.eu1.host": "replica-eu1.example",
            "postgresql.read_replicas.eu1.port": 5433,
            "postgresql.host": "127.0.0.1",
            "postgresql.port": 5432,
            "postgresql.user": "ak",
            "postgresql.password": "secret",
        }
        params, calls = _call_get_connection_params("replica_eu1", refresh_table)
        self.assertEqual(params["host"], "replica-eu1.example")
        self.assertEqual(params["port"], 5433)
        # Replica didn't override user/password — should fall back to postgresql.*
        self.assertEqual(params["user"], "ak")
        self.assertEqual(params["password"], "secret")
        self.assertIn("postgresql.read_replicas.eu1.host", calls)
        self.assertIn("postgresql.user", calls)  # the fallback happened
