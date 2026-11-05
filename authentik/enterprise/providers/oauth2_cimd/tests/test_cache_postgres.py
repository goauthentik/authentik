"""Production PostgreSQL cache capacity and cross-process coalescing."""

import os
import subprocess
import sys
from datetime import timedelta
from time import monotonic, sleep
from uuid import uuid4

from django.db import connection
from django.test import TransactionTestCase
from django.utils.timezone import now
from django_postgres_cache.backend import DatabaseCache
from django_postgres_cache.models import CacheEntry

from authentik.enterprise.providers.oauth2_cimd.negotiation import PUBLIC_PROFILE
from authentik.enterprise.providers.oauth2_cimd.service import CACHE_PREFIX, Kind
from authentik.enterprise.providers.oauth2_cimd.tests.utils import (
    CLIENT_ID,
    json_response,
    make_service,
    public_document,
)


def wait_for(predicate, timeout=20):
    """Bound every worker rendezvous even when another process fails."""
    deadline = monotonic() + timeout
    while not predicate():
        if monotonic() >= deadline:
            raise AssertionError("Cache worker rendezvous timed out")
        sleep(0.01)


def cache_worker(namespace: str, index: str, mode: str) -> None:
    """Run in a fresh interpreter with its own Django/PostgreSQL connections."""
    if connection.settings_dict["NAME"] != os.environ["AUTHENTIK_POSTGRESQL__TEST__NAME"]:
        raise AssertionError("Worker must use the explicitly selected test database")
    backend = DatabaseCache("cimd-production-test", {"KEY_PREFIX": namespace})
    url = CLIENT_ID if mode == "coalesce" else f"https://client{index}.example.com/client.json"
    service, transport, _ = make_service(
        {url: json_response(public_document(client_id=url))},
        shared_cache=backend,
        max_entries=2,
    )
    service._sleep = sleep
    original_add = service._add
    original_fetch = service._fetcher.fetch

    def add(*args, **kwargs):
        result = original_add(*args, **kwargs)
        backend.set(f"attempt:{index}", True, 30)
        return result

    def fetch(*args, **kwargs):
        backend.set(f"network:{index}", True, 30)
        if mode == "coalesce":
            wait_for(lambda: backend.get("release-fetch"))
        return original_fetch(*args, **kwargs)

    service._add = add
    service._fetcher.fetch = fetch
    backend.set(f"ready:{index}", True, 30)
    wait_for(lambda: backend.get("go"))
    service.resolve(url, PUBLIC_PROFILE)
    backend.set(f"done:{index}", len(transport.requests), 30)


class TestPostgresCache(TransactionTestCase):
    """Use the real backend and committed transactions, not an in-memory substitute."""

    def setUp(self):
        super().setUp()
        self.namespace = f"cimd-review-{uuid4().hex}"
        self.backend = DatabaseCache("cimd-production-test", {"KEY_PREFIX": self.namespace})
        self.entries = CacheEntry.objects.filter(cache_key__startswith=self.backend.make_key(""))
        self.addCleanup(self.entries.delete)

    def test_expired_capacity_is_reclaimed(self):
        for replace_same in (False, True):
            with self.subTest(replace_same=replace_same):
                self.entries.delete()
                new_id = CLIENT_ID if replace_same else "https://new.example.com/client.json"
                service, transport, _ = make_service(
                    {
                        CLIENT_ID: json_response(public_document()),
                        new_id: json_response(public_document(client_id=new_id)),
                    },
                    shared_cache=self.backend,
                    max_entries=1,
                )
                service.resolve(CLIENT_ID, PUBLIC_PROFILE)
                key = service._entry_key(Kind.METADATA, CLIENT_ID)
                self.entries.filter(cache_key=self.backend.make_key(key)).update(
                    expires=now() - timedelta(seconds=1)
                )
                self.assertEqual(self.backend.keys_count(f"{CACHE_PREFIX}:metadata:*"), 1)
                self.assertFalse(self.backend.has_key(key))
                service.resolve(new_id, PUBLIC_PROFILE)
                service.resolve(new_id, PUBLIC_PROFILE)
                self.assertEqual(len(transport.requests), 2)
                self.assertEqual(self.backend.keys_count(f"{CACHE_PREFIX}:metadata:*"), 1)
                self.assertTrue(self.backend.has_key(service._entry_key(Kind.METADATA, new_id)))

    def run_workers(self, mode, count):
        test_database = os.environ.get("AUTHENTIK_POSTGRESQL__TEST__NAME")
        if not test_database:
            self.skipTest("Subprocess tests require an explicit AUTHENTIK_POSTGRESQL__TEST__NAME")
        self.assertEqual(connection.settings_dict["NAME"], test_database)
        script = """
import sys
from authentik.root.setup import setup
setup()
import django
django.setup()
from authentik.enterprise.providers.oauth2_cimd.tests.test_cache_postgres import cache_worker
cache_worker(*sys.argv[1:])
"""
        environment = os.environ | {
            "AUTHENTIK_POSTGRESQL__NAME": test_database,
            "AUTHENTIK_POSTGRESQL__TEST__NAME": test_database,
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        processes = [
            subprocess.Popen(
                [sys.executable, "-c", script, self.namespace, str(index), mode],
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for index in range(count)
        ]
        try:
            wait_for(lambda: all(self.backend.get(f"ready:{index}") for index in range(count)))
            self.backend.set("go", True, 30)
            if mode == "coalesce":
                wait_for(
                    lambda: all(self.backend.get(f"attempt:{index}") for index in range(count))
                )
                self.backend.set("release-fetch", True, 30)
            for process in processes:
                stdout, stderr = process.communicate(timeout=30)
                self.assertEqual(process.returncode, 0, stdout + stderr)
            self.assertEqual(
                len(self.backend.get_many([f"done:{index}" for index in range(count)])), count
            )
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=5)

    def test_atomic_capacity_across_processes(self):
        self.run_workers("capacity", 6)
        self.assertEqual(self.backend.keys_count(f"{CACHE_PREFIX}:metadata:*"), 2)
        self.assertEqual(self.backend.keys_count("network:*"), 6)

    def test_fetch_coalesces_across_processes(self):
        self.run_workers("coalesce", 4)
        self.assertEqual(self.backend.keys_count(f"{CACHE_PREFIX}:metadata:*"), 1)
        self.assertEqual(self.backend.keys_count("network:*"), 1)

    def test_expired_full_cache_coalesces_across_processes(self):
        for index in range(2):
            self.backend.set(f"{CACHE_PREFIX}:metadata:expired{index}", {}, 300)
        self.entries.update(expires=now() - timedelta(seconds=1))
        self.run_workers("coalesce", 4)
        self.assertEqual(self.backend.keys_count(f"{CACHE_PREFIX}:metadata:*"), 1)
        self.assertEqual(self.backend.keys_count("network:*"), 1)

    def test_generation_is_shared_across_processes(self):
        service, _, _ = make_service(
            {CLIENT_ID: json_response(public_document())}, shared_cache=self.backend
        )
        before = service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        service.invalidate(CLIENT_ID)
        self.run_workers("coalesce", 2)
        after = service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertNotEqual(before.generation, after.generation)
        self.assertEqual(self.backend.keys_count("network:*"), 1)
