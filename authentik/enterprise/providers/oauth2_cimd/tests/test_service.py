"""Metadata and key cache service"""

import json
import threading
from time import monotonic
from time import sleep as real_sleep

from django.core.cache import cache
from django.test import TestCase
from structlog.testing import capture_logs

from authentik.enterprise.providers.oauth2_cimd.errors import (
    ClientDisabled,
    InvalidClientID,
    InvalidClientKeys,
    InvalidClientMetadata,
    MetadataRejected,
    MetadataUnavailable,
    UnknownSigningKey,
    UnsupportedClient,
)
from authentik.enterprise.providers.oauth2_cimd.negotiation import MANAGED_PROFILE, PUBLIC_PROFILE
from authentik.enterprise.providers.oauth2_cimd.service import (
    CACHE_PREFIX,
    ClientMetadataService,
    Kind,
)
from authentik.enterprise.providers.oauth2_cimd.tests.utils import (
    CLIENT_ID,
    JWKS_URI,
    START,
    json_response,
    make_service,
    managed_document,
    new_cache,
    public_document,
    public_jwk,
    requested_paths,
)
from authentik.lib.utils.untrusted_fetch import ConnectError, DeadlineExceeded
from authentik.lib.utils.untrusted_fetch.fetcher import UntrustedURLFetcher
from authentik.lib.utils.untrusted_fetch.testing import (
    FakeClock,
    MockResponse,
    MockTransport,
    StaticResolver,
    mock_fetcher,
)

METADATA_PATH = "/oauth/client.json"
JWKS_PATH = "/oauth/jwks.json"


def jwks(*keys):
    return {"keys": list(keys)}


class TestPublicResolution(TestCase):
    """Public client resolution and metadata caching"""

    def test_resolve_keyless_public(self):
        service, transport, _ = make_service({CLIENT_ID: json_response(public_document())})
        resolved = service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(resolved.metadata.client_id, CLIENT_ID)
        self.assertEqual(resolved.capabilities.token_endpoint_auth_method, "none")
        self.assertFalse(resolved.capabilities.confidential)
        self.assertIsNone(resolved.keys)
        self.assertEqual(resolved.expires_at, START + 120)
        self.assertEqual(requested_paths(transport), [METADATA_PATH])
        self.assertEqual(dict(transport.requests[0].headers)["Accept"], "application/json")

    def test_public_does_not_fetch_jwks(self):
        service, transport, _ = make_service(
            {CLIENT_ID: json_response(public_document(jwks_uri=JWKS_URI))}
        )
        resolved = service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertIsNone(resolved.keys)
        self.assertFalse(resolved.capabilities.confidential)
        self.assertEqual(requested_paths(transport), [METADATA_PATH])

    def test_cache_hit(self):
        service, transport, clock = make_service(
            {CLIENT_ID: json_response(public_document(), cache_control="max-age=300")}
        )
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        clock.advance(299)
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 1)
        clock.advance(1)
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 2)

    def test_maximum_ttl(self):
        service, transport, clock = make_service(
            {CLIENT_ID: json_response(public_document(), cache_control="max-age=31536000")}
        )
        self.assertEqual(service.resolve(CLIENT_ID, PUBLIC_PROFILE).expires_at, START + 300)
        clock.advance(300)
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 2)

    def test_no_store_minimum(self):
        """The 60-second minimum holds under no-store"""
        service, transport, clock = make_service(
            {CLIENT_ID: json_response(public_document(), cache_control="no-store")}
        )
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        clock.advance(59)
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 1)
        clock.advance(1)
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 2)

    def test_outage_after_expiry(self):
        """Expired metadata is never served when the refetch fails"""
        service, transport, clock = make_service(
            {CLIENT_ID: json_response(public_document(), cache_control="max-age=60")}
        )
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        transport.add(CLIENT_ID, ConnectError("down"))
        clock.advance(60)
        with self.assertRaises(MetadataUnavailable) as ctx:
            service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertTrue(ctx.exception.transient)
        self.assertEqual(ctx.exception.oauth_error, "temporarily_unavailable")
        for status, error in ((503, MetadataUnavailable), (404, MetadataRejected)):
            with self.subTest(status=status):
                transport.add(CLIENT_ID, MockResponse(status=status))
                with self.assertRaises(error):
                    service.resolve(CLIENT_ID, PUBLIC_PROFILE)

    def test_invalid_after_expiry(self):
        """A document that turns invalid is never replaced by the expired copy"""
        service, transport, clock = make_service({CLIENT_ID: json_response(public_document())})
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        transport.add(CLIENT_ID, json_response(public_document(client_secret="x")))
        clock.advance(120)
        with self.assertRaises(InvalidClientMetadata):
            service.resolve(CLIENT_ID, PUBLIC_PROFILE)

    def test_no_negative_caching(self):
        service, transport, _ = make_service({CLIENT_ID: ConnectError("down")})
        with self.assertRaises(MetadataUnavailable):
            service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        transport.add(CLIENT_ID, json_response(public_document()))
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 2)

    def test_invalid_document_not_cached(self):
        service, transport, _ = make_service(
            {CLIENT_ID: json_response(public_document(client_id="https://other.example.com/c"))}
        )
        for _ in range(2):
            with self.assertRaises(InvalidClientMetadata):
                service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 2)

    def test_fetch_failures(self):
        cases = {
            "redirect": (MockResponse(status=302, headers={"Location": "/x"}), MetadataRejected),
            "not found": (MockResponse(status=404), MetadataRejected),
            "server error": (MockResponse(status=500), MetadataUnavailable),
            "timeout": (DeadlineExceeded("slow"), MetadataUnavailable),
            "too large": (json_response(b"{" + b" " * 70000 + b"}"), MetadataRejected),
            "content type": (
                json_response(public_document(), content_type="text/html"),
                InvalidClientMetadata,
            ),
            "no content type": (
                MockResponse(status=200, body=json.dumps(public_document()).encode()),
                InvalidClientMetadata,
            ),
            "not json": (json_response(b"<html>"), InvalidClientMetadata),
        }
        for name, (response, error) in cases.items():
            with self.subTest(name=name):
                service, _, _ = make_service({CLIENT_ID: response})
                with self.assertRaises(error):
                    service.resolve(CLIENT_ID, PUBLIC_PROFILE)

    def test_blocked_destination(self):
        """Fetches go through the hardened fetcher's address policy"""
        clock = FakeClock(START)
        transport = MockTransport({CLIENT_ID: json_response(public_document())}, clock=clock)
        fetcher = UntrustedURLFetcher(
            resolver=StaticResolver({"client.example.com": ["10.0.0.1"]}),
            transport=transport,
            clock=clock,
        )
        service = ClientMetadataService(
            local_check=lambda _: True, cache_backend=new_cache(), fetcher=fetcher, clock=clock
        )
        with self.assertRaises(MetadataRejected) as ctx:
            service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(ctx.exception.code, "fetch_blocked_destination")
        self.assertEqual(transport.requests, [])

    def test_invalid_client_id_not_fetched(self):
        service, transport, _ = make_service()
        with self.assertRaises(InvalidClientID):
            service.resolve("https://client.example.com/", PUBLIC_PROFILE)
        self.assertEqual(transport.requests, [])

    def test_unsupported_not_cached_as_failure(self):
        """Negotiation failures don't affect the cached, valid metadata"""
        service, transport, _ = make_service({CLIENT_ID: json_response(public_document())})
        with self.assertRaises(UnsupportedClient):
            service.resolve(CLIENT_ID, MANAGED_PROFILE)
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 1)

    def test_local_check_on_cache_hit(self):
        allowed = {"value": True}
        service, transport, _ = make_service(
            {CLIENT_ID: json_response(public_document())},
            local_check=lambda client_id: allowed["value"],
        )
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        allowed["value"] = False
        with self.assertRaises(ClientDisabled):
            service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 1)

    def test_local_check_before_fetch(self):
        service, transport, _ = make_service(
            {CLIENT_ID: json_response(public_document())}, local_check=lambda _: False
        )
        with self.assertRaises(ClientDisabled):
            service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(transport.requests, [])

    def test_logs_exclude_bodies(self):
        marker = "very-secret-marker-value"
        service, _, _ = make_service(
            {CLIENT_ID: json_response(public_document(client_secret=marker, client_name=marker))}
        )
        with capture_logs() as logs, self.assertRaises(InvalidClientMetadata):
            service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertTrue(logs)
        self.assertNotIn(marker, repr(logs))
        failure = next(log for log in logs if log["event"] == "CIMD document fetch failed")
        self.assertEqual(failure["reason"], "invalid_metadata")
        self.assertEqual(failure["code"], "shared_secret")
        self.assertIn("duration_ms", failure)

    def test_success_log(self):
        service, _, _ = make_service(
            {CLIENT_ID: json_response(public_document(), cache_control="no-store")}
        )
        with capture_logs() as logs:
            service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        fetched = next(log for log in logs if log["event"] == "CIMD document fetched")
        self.assertEqual(fetched["ttl"], 60)
        self.assertEqual(fetched["freshness"], "no_store")
        self.assertEqual(fetched["kind"], Kind.METADATA)


class TestManagedResolution(TestCase):
    """Managed clients and keys"""

    def setUp(self):
        self.key_a = public_jwk("EC", 0, kid="a")
        self.key_b = public_jwk("EC", 1, kid="b")

    def test_jwks_uri(self):
        service, transport, _ = make_service(
            {
                CLIENT_ID: json_response(managed_document(), cache_control="max-age=300"),
                JWKS_URI: json_response(jwks(self.key_a), cache_control="max-age=100"),
            }
        )
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        self.assertTrue(resolved.capabilities.confidential)
        self.assertEqual(resolved.keys.kids, frozenset(("a",)))
        self.assertEqual(resolved.expires_at, START + 100)
        self.assertEqual(requested_paths(transport), [METADATA_PATH, JWKS_PATH])
        self.assertEqual(
            dict(transport.requests[1].headers)["Accept"],
            "application/jwk-set+json, application/json",
        )
        self.assertEqual(service.find_signing_key(resolved, "a").kid, "a")

    def test_jwk_set_content_type(self):
        service, _, _ = make_service(
            {
                CLIENT_ID: json_response(managed_document()),
                JWKS_URI: json_response(jwks(self.key_a), content_type="application/jwk-set+json"),
            }
        )
        self.assertTrue(service.resolve(CLIENT_ID, MANAGED_PROFILE).keys)

    def test_without_usable_keys(self):
        cases = {
            "no keys declared": (managed_document(jwks_uri=None), None),
            "declares none": (
                public_document(jwks_uri=JWKS_URI),
                json_response(jwks(self.key_a)),
            ),
            "empty jwks": (managed_document(), json_response(jwks())),
            "encryption keys only": (
                managed_document(),
                json_response(jwks(public_jwk("RSA", use="enc"))),
            ),
        }
        for name, (document, keys) in cases.items():
            with self.subTest(name=name):
                responses = {CLIENT_ID: json_response(document)}
                if keys:
                    responses[JWKS_URI] = keys
                service, _, _ = make_service(responses)
                with self.assertRaises(UnsupportedClient):
                    service.resolve(CLIENT_ID, MANAGED_PROFILE)

    def test_private_and_malformed_keys(self):
        for name, keyset in {
            "private": jwks(self.key_a | {"d": "AAAA"}),
            "symmetric": jwks({"kty": "oct", "kid": "s"}),
            "malformed": jwks({"kty": "EC", "crv": "P-256", "x": "AA", "y": "AA"}),
        }.items():
            with self.subTest(name=name):
                service, transport, _ = make_service(
                    {CLIENT_ID: json_response(managed_document()), JWKS_URI: json_response(keyset)}
                )
                with self.assertRaises(InvalidClientKeys):
                    service.resolve(CLIENT_ID, MANAGED_PROFILE)
                with self.assertRaises(InvalidClientKeys):
                    service.resolve(CLIENT_ID, MANAGED_PROFILE)
                # Invalid key sets aren't cached
                self.assertEqual(requested_paths(transport), [METADATA_PATH, JWKS_PATH, JWKS_PATH])

    def test_jwks_outage_after_expiry(self):
        """Expired keys are never used, even with metadata still fresh"""
        service, transport, clock = make_service(
            {
                CLIENT_ID: json_response(managed_document(), cache_control="max-age=300"),
                JWKS_URI: json_response(jwks(self.key_a), cache_control="max-age=60"),
            }
        )
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        transport.add(JWKS_URI, ConnectError("down"))
        clock.advance(60)
        self.assertFalse(resolved.is_fresh(clock()))
        with self.assertRaises(MetadataUnavailable):
            service.resolve(CLIENT_ID, MANAGED_PROFILE)
        # An expired resolution can't be used to look up keys either
        with self.assertRaises(MetadataUnavailable):
            service.find_signing_key(resolved, "a")

    def test_rotation_within_freshness(self):
        """Rotated keys are picked up once the cached JWKS expires"""
        service, transport, clock = make_service(
            {
                CLIENT_ID: json_response(managed_document(), cache_control="max-age=300"),
                JWKS_URI: json_response(jwks(self.key_a), cache_control="no-store"),
            }
        )
        self.assertEqual(service.resolve(CLIENT_ID, MANAGED_PROFILE).keys.kids, {"a"})
        transport.add(JWKS_URI, json_response(jwks(self.key_b), cache_control="no-store"))
        clock.advance(59)
        self.assertEqual(service.resolve(CLIENT_ID, MANAGED_PROFILE).keys.kids, {"a"})
        clock.advance(1)
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        self.assertEqual(resolved.keys.kids, {"b"})
        self.assertEqual(requested_paths(transport), [METADATA_PATH, JWKS_PATH, JWKS_PATH])

    def test_unknown_kid_refresh(self):
        """An unknown kid refreshes keys at most once per interval"""
        service, transport, _ = make_service(
            {
                CLIENT_ID: json_response(managed_document(), cache_control="max-age=300"),
                JWKS_URI: json_response(jwks(self.key_a), cache_control="max-age=300"),
            }
        )
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        transport.add(JWKS_URI, json_response(jwks(self.key_a, self.key_b)))
        self.assertEqual(service.find_signing_key(resolved, "b").kid, "b")
        self.assertEqual(requested_paths(transport), [METADATA_PATH, JWKS_PATH, JWKS_PATH])
        # The refreshed set is cached for everyone
        self.assertEqual(service.resolve(CLIENT_ID, MANAGED_PROFILE).keys.kids, {"a", "b"})
        # Further unknown kids don't trigger more fetches
        for kid in ("c", "d", "e"):
            with self.assertRaises(UnknownSigningKey) as ctx:
                service.find_signing_key(resolved, kid)
            self.assertEqual(ctx.exception.code, "refresh_rate_limited")
        self.assertEqual(len(transport.requests), 3)

    def test_unknown_kid_rate_limit_shared(self):
        """The refresh rate limit applies across workers"""
        shared = new_cache()
        responses = {
            CLIENT_ID: json_response(managed_document(), cache_control="max-age=300"),
            JWKS_URI: json_response(jwks(self.key_a), cache_control="max-age=300"),
        }
        worker_a, transport_a, _ = make_service(responses, shared_cache=shared)
        worker_b, transport_b, _ = make_service(responses, shared_cache=shared)
        with self.assertRaises(UnknownSigningKey) as ctx:
            worker_a.find_signing_key(worker_a.resolve(CLIENT_ID, MANAGED_PROFILE), "x")
        self.assertEqual(ctx.exception.code, "unknown_kid")
        with self.assertRaises(UnknownSigningKey) as ctx:
            worker_b.find_signing_key(worker_b.resolve(CLIENT_ID, MANAGED_PROFILE), "x")
        self.assertEqual(ctx.exception.code, "refresh_rate_limited")
        self.assertEqual(transport_b.requests, [])
        self.assertEqual(requested_paths(transport_a), [METADATA_PATH, JWKS_PATH, JWKS_PATH])

    def test_unknown_kid_invalid_refresh(self):
        """A refresh that returns an invalid set drops the cached keys"""
        service, transport, _ = make_service(
            {
                CLIENT_ID: json_response(managed_document(), cache_control="max-age=300"),
                JWKS_URI: json_response(jwks(self.key_a), cache_control="max-age=300"),
            }
        )
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        transport.add(JWKS_URI, json_response(jwks(self.key_a | {"d": "AAAA"})))
        with self.assertRaises(InvalidClientKeys):
            service.find_signing_key(resolved, "b")
        with self.assertRaises(InvalidClientKeys):
            service.resolve(CLIENT_ID, MANAGED_PROFILE)

    def test_inline_keys_rotate_with_document(self):
        document_a = managed_document(jwks_uri=None, jwks=jwks(self.key_a))
        document_b = managed_document(jwks_uri=None, jwks=jwks(self.key_b))
        service, transport, _ = make_service(
            {CLIENT_ID: json_response(document_a, cache_control="max-age=300")}
        )
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        self.assertEqual(resolved.keys.kids, {"a"})
        transport.add(CLIENT_ID, json_response(document_b, cache_control="max-age=300"))
        self.assertEqual(service.find_signing_key(resolved, "b").kid, "b")
        self.assertEqual(requested_paths(transport), [METADATA_PATH, METADATA_PATH])

    def test_key_without_kid(self):
        service, _, _ = make_service(
            {
                CLIENT_ID: json_response(managed_document()),
                JWKS_URI: json_response(jwks(self.key_a, self.key_b)),
            }
        )
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        with self.assertRaises(UnknownSigningKey) as ctx:
            service.find_signing_key(resolved, None)
        self.assertEqual(ctx.exception.code, "ambiguous_key")


class TestInvalidation(TestCase):
    """Cross-worker invalidation"""

    def test_invalidate_across_workers(self):
        shared = new_cache()
        responses = {CLIENT_ID: json_response(public_document(), cache_control="max-age=300")}
        worker_a, transport_a, _ = make_service(responses, shared_cache=shared)
        worker_b, transport_b, _ = make_service(responses, shared_cache=shared)
        worker_a.resolve(CLIENT_ID, PUBLIC_PROFILE)
        worker_b.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport_a.requests), 1)
        self.assertEqual(len(transport_b.requests), 0)
        worker_b.invalidate(CLIENT_ID)
        worker_a.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport_a.requests), 2)

    def test_invalidate_keys(self):
        shared = new_cache()
        key_a = public_jwk("EC", 0, kid="a")
        responses = {
            CLIENT_ID: json_response(managed_document(), cache_control="max-age=300"),
            JWKS_URI: json_response(jwks(key_a), cache_control="max-age=300"),
        }
        worker_a, transport_a, _ = make_service(responses, shared_cache=shared)
        worker_b, _, _ = make_service(responses, shared_cache=shared)
        worker_a.resolve(CLIENT_ID, MANAGED_PROFILE)
        worker_b.invalidate(CLIENT_ID)
        worker_a.resolve(CLIENT_ID, MANAGED_PROFILE)
        self.assertEqual(
            requested_paths(transport_a), [METADATA_PATH, JWKS_PATH, METADATA_PATH, JWKS_PATH]
        )

    def test_invalidate_during_fetch(self):
        """An entry written by a fetch that raced an invalidation isn't reused"""
        shared = new_cache()
        service, transport, _ = make_service(
            {CLIENT_ID: json_response(public_document(), cache_control="max-age=300")},
            shared_cache=shared,
        )
        original_fetch = service._fetch

        def fetch_then_invalidate(*args, **kwargs):
            entry = original_fetch(*args, **kwargs)
            service.invalidate(CLIENT_ID)
            # The in-flight fetch stores its result after the invalidation
            shared.set(args[3], entry, timeout=300)
            return entry

        service._fetch = fetch_then_invalidate
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        service._fetch = original_fetch
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 2)

    def test_default_cache_backend(self):
        """The default backend is the shared Django cache"""
        service, transport, _ = make_service({CLIENT_ID: json_response(public_document())})
        service = ClientMetadataService(
            local_check=lambda _: True, fetcher=service._fetcher, clock=service._clock
        )
        self.assertIs(service._cache, cache)
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(cache.keys_count(f"{CACHE_PREFIX}:{Kind.METADATA}:*"), 1)

    def test_entry_bound(self):
        """Once full, new documents are served but not cached"""
        responses = {
            f"https://client{i}.example.com/client.json": json_response(
                public_document(client_id=f"https://client{i}.example.com/client.json")
            )
            for i in range(3)
        }
        clock = FakeClock(START)
        fetcher, _ = mock_fetcher(responses, clock=clock)
        service = ClientMetadataService(
            local_check=lambda _: True, fetcher=fetcher, clock=clock, max_entries=2
        )
        for url in responses:
            service.resolve(url, PUBLIC_PROFILE)
        self.assertEqual(cache.keys_count(f"{CACHE_PREFIX}:{Kind.METADATA}:*"), 2)
        # The cached ones are still served, and refreshed in place when full
        clock.advance(120)
        for url in list(responses)[:2]:
            service.resolve(url, PUBLIC_PROFILE)
        self.assertEqual(cache.keys_count(f"{CACHE_PREFIX}:{Kind.METADATA}:*"), 2)


class BlockingTransport(MockTransport):
    """Blocks every request until `release` is set"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.release = threading.Event()
        self.started = threading.Event()

    def open(self, target, deadline):
        self.started.set()
        self.release.wait(10)
        return super().open(target, deadline)


def wait_until(condition, timeout=5.0):
    end = monotonic() + timeout
    while not condition():
        if monotonic() > end:
            raise AssertionError("Condition not met")
        real_sleep(0.01)


def wait_for_waiters(service: ClientMetadataService, count: int):
    """Wait until `count` callers are waiting on the in-flight metadata fetch"""
    entry_key = service._entry_key(Kind.METADATA, CLIENT_ID)

    def ready():
        flight = service._flights.get(entry_key)
        return flight is not None and flight.waiters >= count

    wait_until(ready)


class TestCoalescing(TestCase):
    """Concurrent fetches of one URL are coalesced"""

    def make_blocking(self, responses, shared=None):
        clock = FakeClock(START)
        transport = BlockingTransport(responses, clock=clock)
        fetcher = UntrustedURLFetcher(
            resolver=StaticResolver(default=["93.184.215.14"]), transport=transport, clock=clock
        )
        service = ClientMetadataService(
            local_check=lambda _: True,
            cache_backend=shared or new_cache(),
            fetcher=fetcher,
            clock=clock,
        )
        return service, transport

    def run_threads(self, count, target):
        results, errors = [], []

        def run():
            try:
                results.append(target())
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=run) for _ in range(count)]
        for thread in threads:
            thread.start()
        return threads, results, errors

    def test_in_process(self):
        service, transport = self.make_blocking({CLIENT_ID: json_response(public_document())})
        threads, results, errors = self.run_threads(
            5, lambda: service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        )
        wait_for_waiters(service, 4)
        transport.release.set()
        for thread in threads:
            thread.join(10)
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 5)
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual({r.metadata for r in results}, {results[0].metadata})

    def test_in_process_failure_shared(self):
        """Waiters get the leader's failure; nothing is cached and nobody retries"""
        service, transport = self.make_blocking({CLIENT_ID: MockResponse(status=503)})
        threads, results, errors = self.run_threads(
            3, lambda: service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        )
        wait_for_waiters(service, 2)
        transport.release.set()
        for thread in threads:
            thread.join(10)
        self.assertEqual(results, [])
        self.assertEqual(len(errors), 3)
        self.assertTrue(all(isinstance(e, MetadataUnavailable) for e in errors))
        self.assertEqual(len(transport.requests), 1)
        transport.add(CLIENT_ID, json_response(public_document()))
        service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 2)

    def test_across_workers(self):
        """A worker waits for another worker's fetch instead of fetching itself"""
        shared = new_cache()
        responses = {CLIENT_ID: json_response(public_document(), cache_control="max-age=300")}
        leader, leader_transport = self.make_blocking(responses, shared)
        follower, follower_transport, _ = make_service(responses, shared_cache=shared)
        thread = threading.Thread(target=lambda: leader.resolve(CLIENT_ID, PUBLIC_PROFILE))
        thread.start()
        leader_transport.started.wait(5)

        def poll(seconds):
            follower._clock.advance(seconds)
            leader_transport.release.set()
            thread.join(10)

        follower._sleep = poll
        resolved = follower.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(resolved.metadata.client_id, CLIENT_ID)
        self.assertEqual(len(leader_transport.requests), 1)
        self.assertEqual(follower_transport.requests, [])

    def test_across_workers_leader_fails(self):
        shared = new_cache()
        follower, transport, _ = make_service(
            {CLIENT_ID: json_response(public_document())}, shared_cache=shared
        )
        lock_key = follower._lock_key(follower._entry_key(Kind.METADATA, CLIENT_ID))
        shared.add(lock_key, "other-worker", timeout=30)
        follower._sleep = lambda seconds: shared.delete(lock_key)
        with self.assertRaises(MetadataUnavailable) as ctx:
            follower.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(ctx.exception.code, "coalesced_fetch_failed")
        self.assertEqual(transport.requests, [])
        # Not cached: the next request fetches
        follower.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 1)

    def test_across_workers_timeout(self):
        shared = new_cache()
        follower, transport, _ = make_service(
            {CLIENT_ID: json_response(public_document())}, shared_cache=shared
        )
        lock_key = follower._lock_key(follower._entry_key(Kind.METADATA, CLIENT_ID))
        shared.add(lock_key, "stuck-worker", timeout=30)
        with self.assertRaises(MetadataUnavailable) as ctx:
            follower.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(ctx.exception.code, "coalesce_timeout")
        self.assertEqual(transport.requests, [])
