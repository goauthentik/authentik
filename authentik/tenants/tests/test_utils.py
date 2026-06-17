"""Tests for `authentik.tenants.utils.get_current_tenant` memoization."""

from django.core.signals import request_started
from django.db import connection
from django.test import TestCase

from authentik.tenants.models import Tenant
from authentik.tenants.utils import _TENANT_CACHE_ATTR, get_current_tenant


class TestGetCurrentTenantMemoization(TestCase):
    """Per-connection memoization with ``(schema_name, frozenset(only))`` key."""

    def _clear_cache(self):
        if hasattr(connection, _TENANT_CACHE_ATTR):
            delattr(connection, _TENANT_CACHE_ATTR)

    def setUp(self):
        # Tests share a connection; clear cache to start from a known state.
        self._clear_cache()

    def test_first_call_hits_db_subsequent_calls_with_same_only_do_not(self):
        """First call: 1 query. Subsequent calls with same ``only``: 0."""
        with self.assertNumQueries(1):
            t1 = get_current_tenant()
        with self.assertNumQueries(0):
            t2 = get_current_tenant()
            t3 = get_current_tenant()
        self.assertIs(t1, t2)
        self.assertIs(t2, t3)

    def test_calls_with_different_only_are_separate_cache_entries(self):
        """``only`` is part of the cache key. Calls during migrations may
        pass narrow ``only`` sets when the schema doesn't yet have all
        columns; respecting the key keeps each SELECT scoped correctly."""
        with self.assertNumQueries(1):
            t1 = get_current_tenant()  # only=[]
        with self.assertNumQueries(1):
            t2 = get_current_tenant(["flags"])
        with self.assertNumQueries(0):
            t3 = get_current_tenant(["flags"])
        self.assertIs(t2, t3)
        self.assertIsNot(t1, t2)

    def test_cache_cleared_on_request_start(self):
        """The ``request_started`` signal handler clears the cache so stale
        data can't survive a request boundary on persistent-connection
        deployments. Calls the handler directly (the real signal would
        also fire ``close_old_connections``, closing our test connection)."""
        from authentik.tenants.utils import _clear_current_tenant_cache

        get_current_tenant()
        self.assertTrue(hasattr(connection, _TENANT_CACHE_ATTR))
        _clear_current_tenant_cache(sender=None)
        self.assertFalse(hasattr(connection, _TENANT_CACHE_ATTR))

    def test_cache_clear_handler_registered_for_request_started(self):
        """The cache-clear handler is connected to ``request_started``."""
        receivers = request_started._live_receivers(sender=None)
        all_repr = "\n".join(str(r) for r in receivers)
        self.assertIn("_clear_current_tenant_cache", all_repr)

    def test_cache_keyed_on_schema_name(self):
        """Schema change mid-request invalidates the cache and forces a
        refetch. Simulates ``set_tenant`` to a non-existent schema; the
        refetch raises ``Tenant.DoesNotExist`` as expected."""
        tenant_public = get_current_tenant()
        original = connection.schema_name
        try:
            connection.schema_name = "_test_other_schema_does_not_exist"
            with self.assertRaises(Tenant.DoesNotExist):
                get_current_tenant()
        finally:
            connection.schema_name = original
        tenant_again = get_current_tenant()
        self.assertEqual(tenant_again.schema_name, tenant_public.schema_name)
