"""Tests for the FailoverRouter and the direct database alias."""

from unittest.mock import patch

from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase

from authentik.lib.config import DIRECT_DB_ALIAS
from authentik.tenants.db import FailoverRouter


class TestFailoverRouter(TestCase):
    """The ``direct`` alias is wired up by ``django_db_config`` and used
    directly by the broker / channel layer. The router must not pull it into
    the read-replica pool, must not route ORM reads/writes to it, and must
    block migrations against it (the same database is migrated via
    ``default``)."""

    def _router_with_databases(self, *aliases: str) -> FailoverRouter:
        databases = {alias: {"ENGINE": "django.db.backends.postgresql"} for alias in aliases}
        with patch("authentik.tenants.db.settings") as mock_settings:
            mock_settings.DATABASES = databases
            return FailoverRouter()

    def test_direct_alias_excluded_from_replica_pool(self):
        """The direct alias must never be treated as a read replica."""
        router = self._router_with_databases(DEFAULT_DB_ALIAS, DIRECT_DB_ALIAS, "replica_0")
        self.assertNotIn(DIRECT_DB_ALIAS, router.read_replica_aliases)
        self.assertIn("replica_0", router.read_replica_aliases)
        self.assertTrue(router.replica_enabled)

    def test_direct_alias_only_does_not_enable_replicas(self):
        """A deployment with only ``default`` + ``direct`` (no real replicas)
        must report ``replica_enabled = False`` so ``db_for_read`` keeps
        returning ``default`` instead of picking from an empty list."""
        router = self._router_with_databases(DEFAULT_DB_ALIAS, DIRECT_DB_ALIAS)
        self.assertEqual(router.read_replica_aliases, [])
        self.assertFalse(router.replica_enabled)

    def test_allow_migrate_blocks_direct_alias(self):
        """Migrations against the direct alias must be blocked — they would
        otherwise run twice (once via default, once via direct, both pointing
        at the same database) or try to acquire the migration advisory lock
        against a transaction pooler that can't hold it."""
        router = self._router_with_databases(DEFAULT_DB_ALIAS, DIRECT_DB_ALIAS)
        self.assertIs(router.allow_migrate(DIRECT_DB_ALIAS, "authentik_core"), False)

    def test_allow_migrate_passes_through_for_other_aliases(self):
        """Migrations against ``default`` and replicas defer to the downstream
        ``TenantSyncRouter`` (return None to indicate no opinion)."""
        router = self._router_with_databases(DEFAULT_DB_ALIAS, DIRECT_DB_ALIAS, "replica_0")
        self.assertIsNone(router.allow_migrate(DEFAULT_DB_ALIAS, "authentik_core"))
        self.assertIsNone(router.allow_migrate("replica_0", "authentik_core"))

    def test_db_for_write_is_always_default(self):
        """Writes never go to the direct alias even when it's configured."""
        router = self._router_with_databases(DEFAULT_DB_ALIAS, DIRECT_DB_ALIAS, "replica_0")
        self.assertEqual(router.db_for_write(None), DEFAULT_DB_ALIAS)
