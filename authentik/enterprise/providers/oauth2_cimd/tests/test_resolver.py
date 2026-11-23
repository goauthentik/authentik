"""Public client resolution: admission, caching, staleness and errors"""

import pickle  # nosec B403
import threading
from dataclasses import FrozenInstanceError
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase

from authentik.enterprise.providers.oauth2_cimd.client import CIMDClient
from authentik.enterprise.providers.oauth2_cimd.constants import STALE_IF_ERROR
from authentik.enterprise.providers.oauth2_cimd.errors import (
    CIMDError,
    ClientNotAdmitted,
    InvalidClientID,
    InvalidClientMetadata,
    MetadataRejected,
    MetadataUnavailable,
    UnsupportedClient,
)
from authentik.enterprise.providers.oauth2_cimd.resolver import (
    PublicClientResolver,
    invalidate,
    resolve_public_client,
)
from authentik.enterprise.providers.oauth2_cimd.tests.utils import (
    CLIENT_ID,
    REDIRECT_URI,
    START,
    admit_all,
    json_response,
    make_resolver,
    new_cache,
    public_document,
)
from authentik.lib.utils.untrusted_fetch import (
    BlockedDestination,
    ConcurrencyLimitExceeded,
    ConnectError,
    DeadlineExceeded,
    RedirectNotAllowed,
    ResolutionError,
    TLSError,
)
from authentik.lib.utils.untrusted_fetch.testing import MockResponse, mock_fetcher, use_fetcher

VALID = json_response(public_document(), cache_control="max-age=300")


class CountingAdmit:
    """An admission check that records its calls"""

    def __init__(self, result: bool = True):
        self.result = result
        self.calls: list[str] = []

    def __call__(self, client_id: str) -> bool:
        self.calls.append(client_id)
        return self.result


class TestResolve(SimpleTestCase):
    """Resolution and the result record"""

    def test_resolve(self):
        resolver, transport, _ = make_resolver({CLIENT_ID: VALID})
        client = resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(
            client,
            CIMDClient(
                client_id=CLIENT_ID,
                client_name="Example MCP client",
                client_name_declared=True,
                client_uri=None,
                policy_uri=None,
                tos_uri=None,
                redirect_uris=(REDIRECT_URI,),
                grant_types=("authorization_code", "refresh_token"),
                token_endpoint_auth_method="none",
                scopes=None,
                expires_at=START + 300,
                stale=False,
            ),
        )
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(transport.requests[0].path, "/oauth/client.json")
        self.assertEqual(dict(transport.requests[0].headers)["Accept"], "application/json")

    def test_picklable(self):
        """The record is stored in flow plans"""
        resolver, _, _ = make_resolver(
            {CLIENT_ID: json_response(public_document(scope="openid mcp"))}
        )
        client = resolver.resolve(CLIENT_ID, admit=admit_all)
        restored = pickle.loads(pickle.dumps(client))  # nosec B301
        self.assertEqual(restored, client)
        self.assertIsInstance(restored, CIMDClient)
        self.assertEqual(restored.scopes, ("openid", "mcp"))
        self.assertFalse(hasattr(client, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            client.client_id = "x"  # type: ignore[misc]
        for value in (
            client.client_id,
            client.client_name,
            client.client_name_declared,
            client.redirect_uris,
            client.grant_types,
            client.token_endpoint_auth_method,
            client.scopes,
            client.expires_at,
            client.stale,
        ):
            self.assertIsInstance(value, str | bool | float | tuple)

    def test_crypto_free_keys(self):
        """A public document with keys a crypto library would reject still resolves"""
        keys = [
            {"kty": "RSA", "e": "AQAB", "n": "x" * 171},
            {"kty": "OKP", "crv": "Ed25519", "x": "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo"},
            {"kty": "EC", "crv": "secp256k1", "x": "AAAA", "y": "AAAA"},
        ]
        for key in keys:
            with self.subTest(key=key["kty"]):
                resolver, transport, _ = make_resolver(
                    {CLIENT_ID: json_response(public_document(jwks={"keys": [key]}))}
                )
                resolver.resolve(CLIENT_ID, admit=admit_all)
                self.assertEqual(len(transport.requests), 1)

    def test_jwks_uri_not_fetched(self):
        resolver, transport, _ = make_resolver(
            {CLIENT_ID: json_response(public_document(jwks_uri="https://client.example.com/j"))}
        )
        resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual([r.path for r in transport.requests], ["/oauth/client.json"])

    def test_content_type(self):
        resolver, _, _ = make_resolver(
            {CLIENT_ID: json_response(public_document(), content_type="text/html")}
        )
        with self.assertRaises(InvalidClientMetadata) as ctx:
            resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(ctx.exception.code, "content_type")

    def test_unsupported(self):
        resolver, _, _ = make_resolver(
            {
                CLIENT_ID: json_response(
                    public_document(token_endpoint_auth_method="private_key_jwt")
                )
            }
        )
        with self.assertRaises(UnsupportedClient) as ctx:
            resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(ctx.exception.oauth_error, "invalid_client")
        self.assertFalse(ctx.exception.transient)


class TestAdmission(SimpleTestCase):
    """`admit` runs on every call, before anything is fetched"""

    def test_refused_no_fetch(self):
        resolver, transport, _ = make_resolver({CLIENT_ID: VALID})
        admit = CountingAdmit(False)
        with self.assertRaises(ClientNotAdmitted) as ctx:
            resolver.resolve(CLIENT_ID, admit=admit)
        self.assertEqual(admit.calls, [CLIENT_ID])
        self.assertEqual(transport.requests, [])
        self.assertEqual(ctx.exception.reason, "not_admitted")
        self.assertEqual(ctx.exception.oauth_error, "invalid_client")
        self.assertFalse(ctx.exception.transient)

    def test_cache_hit_still_admits(self):
        resolver, transport, _ = make_resolver({CLIENT_ID: VALID})
        admit = CountingAdmit()
        resolver.resolve(CLIENT_ID, admit=admit)
        resolver.resolve(CLIENT_ID, admit=admit)
        self.assertEqual(len(admit.calls), 2)
        self.assertEqual(len(transport.requests), 1)
        admit.result = False
        with self.assertRaises(ClientNotAdmitted):
            resolver.resolve(CLIENT_ID, admit=admit)
        self.assertEqual(len(admit.calls), 3)

    def test_invalid_client_id_not_admitted_or_fetched(self):
        resolver, transport, _ = make_resolver()
        admit = CountingAdmit()
        for client_id in (CLIENT_ID + "?x=1", "https://client.example.com/a/../b", 1):
            with self.subTest(client_id=client_id), self.assertRaises(InvalidClientID):
                resolver.resolve(client_id, admit=admit)  # type: ignore[arg-type]
        self.assertEqual(admit.calls, [])
        self.assertEqual(transport.requests, [])

    def test_rejection_logged_truncated_at_debug(self):
        resolver, _, _ = make_resolver()
        client_id = "https://client.example.com/" + "a" * 2000
        # Patch the logger rather than capture output: the configured log level filters debug
        with patch("authentik.enterprise.providers.oauth2_cimd.resolver.LOGGER") as logger:
            with self.assertRaises(ClientNotAdmitted):
                resolver.resolve(client_id, admit=CountingAdmit(False))
        logger.debug.assert_called_once()
        self.assertEqual(logger.debug.call_args.args, ("CIMD client rejected",))
        logged = logger.debug.call_args.kwargs
        self.assertEqual(logged["reason"], "not_admitted")
        self.assertLessEqual(len(logged["client_id"]), 131)
        self.assertTrue(client_id.startswith(logged["client_id"].removesuffix("...")))


class TestCaching(SimpleTestCase):
    """Freshness, sharing and invalidation"""

    def test_freshness(self):
        for cache_control, ttl in (
            ("max-age=300", 300),
            ("max-age=86400", 300),
            ("max-age=90", 90),
            ("no-store", 60),
            (None, 120),
        ):
            with self.subTest(cache_control=cache_control):
                resolver, transport, clock = make_resolver(
                    {CLIENT_ID: json_response(public_document(), cache_control=cache_control)}
                )
                self.assertEqual(
                    resolver.resolve(CLIENT_ID, admit=admit_all).expires_at, START + ttl
                )
                clock.advance(ttl - 1)
                resolver.resolve(CLIENT_ID, admit=admit_all)
                self.assertEqual(len(transport.requests), 1)
                clock.advance(1)
                client = resolver.resolve(CLIENT_ID, admit=admit_all)
                self.assertEqual(len(transport.requests), 2)
                self.assertFalse(client.stale)
                self.assertEqual(client.expires_at, START + 2 * ttl)

    def test_shared_between_workers(self):
        shared = new_cache()
        first, first_transport, clock = make_resolver({CLIENT_ID: VALID}, shared_cache=shared)
        second, second_transport, _ = make_resolver(
            {CLIENT_ID: VALID}, shared_cache=shared, clock=clock
        )
        first.resolve(CLIENT_ID, admit=admit_all)
        second.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(len(first_transport.requests), 1)
        self.assertEqual(len(second_transport.requests), 0)

    def test_invalidate(self):
        shared = new_cache()
        first, first_transport, clock = make_resolver({CLIENT_ID: VALID}, shared_cache=shared)
        second, second_transport, _ = make_resolver(
            {CLIENT_ID: VALID}, shared_cache=shared, clock=clock
        )
        first.resolve(CLIENT_ID, admit=admit_all)
        second.invalidate(CLIENT_ID)
        first.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(len(first_transport.requests), 2)
        self.assertEqual(len(second_transport.requests), 0)

    def test_failures_not_cached(self):
        resolver, transport, _ = make_resolver({CLIENT_ID: MockResponse(status=503)})
        with self.assertRaises(MetadataUnavailable):
            resolver.resolve(CLIENT_ID, admit=admit_all)
        transport.add(CLIENT_ID, VALID)
        resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(len(transport.requests), 2)

    def test_invalid_document_not_cached(self):
        resolver, transport, _ = make_resolver(
            {CLIENT_ID: json_response(public_document(client_secret="x"))}
        )
        with self.assertRaises(InvalidClientMetadata):
            resolver.resolve(CLIENT_ID, admit=admit_all)
        with self.assertRaises(InvalidClientMetadata):
            resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(len(transport.requests), 2)

    def test_cached_entry_revalidated(self):
        """An entry that no longer passes validation is dropped and refetched"""
        shared = new_cache()
        resolver, transport, _ = make_resolver({CLIENT_ID: VALID}, shared_cache=shared)
        resolver.resolve(CLIENT_ID, admit=admit_all)
        key = resolver._key(CLIENT_ID)
        entry = shared.get(key)
        entry["document"] = public_document(client_secret="x")
        shared.set(key, entry)
        client = resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(client.client_name, "Example MCP client")
        self.assertEqual(len(transport.requests), 2)


class TestStaleIfError(SimpleTestCase):
    """Draft -03 section 6.1: transient failures don't discard valid metadata"""

    def expired(self, failure):
        resolver, transport, clock = make_resolver({CLIENT_ID: VALID})
        resolver.resolve(CLIENT_ID, admit=admit_all)
        clock.advance(300)
        transport.add(CLIENT_ID, failure)
        return resolver, transport, clock

    def test_transient_serves_stale(self):
        for failure in (
            MockResponse(status=500),
            MockResponse(status=503),
            MockResponse(status=429),
            MockResponse(status=408),
            ConnectError("down"),
            DeadlineExceeded("slow"),
            ResolutionError("dns"),
            TLSError("tls"),
            ConcurrencyLimitExceeded("busy"),
        ):
            with self.subTest(failure=failure):
                resolver, transport, clock = self.expired(failure)
                client = resolver.resolve(CLIENT_ID, admit=admit_all)
                self.assertTrue(client.stale)
                self.assertEqual(client.client_name, "Example MCP client")
                self.assertEqual(client.expires_at, clock() + 60)
                self.assertEqual(len(transport.requests), 2)

    def test_stale_retry_interval(self):
        resolver, transport, clock = self.expired(MockResponse(status=503))
        resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(len(transport.requests), 2)
        clock.advance(59)
        self.assertTrue(resolver.resolve(CLIENT_ID, admit=admit_all).stale)
        self.assertEqual(len(transport.requests), 2)
        clock.advance(1)
        self.assertTrue(resolver.resolve(CLIENT_ID, admit=admit_all).stale)
        self.assertEqual(len(transport.requests), 3)
        transport.add(CLIENT_ID, VALID)
        clock.advance(60)
        client = resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertFalse(client.stale)
        self.assertEqual(client.expires_at, clock() + 300)

    def test_stale_bounded(self):
        resolver, transport, clock = self.expired(MockResponse(status=503))
        self.assertTrue(resolver.resolve(CLIENT_ID, admit=admit_all).stale)
        clock.advance(STALE_IF_ERROR - 30)
        client = resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertTrue(client.stale)
        # The retry point never extends past the stale limit
        self.assertEqual(client.expires_at, START + 300 + STALE_IF_ERROR)
        clock.advance(30)
        with self.assertRaises(MetadataUnavailable) as ctx:
            resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertTrue(ctx.exception.transient)
        self.assertEqual(ctx.exception.oauth_error, "temporarily_unavailable")

    def test_stale_still_admits(self):
        resolver, transport, _ = self.expired(MockResponse(status=503))
        resolver.resolve(CLIENT_ID, admit=admit_all)
        with self.assertRaises(ClientNotAdmitted):
            resolver.resolve(CLIENT_ID, admit=CountingAdmit(False))
        self.assertEqual(len(transport.requests), 2)

    def test_transient_without_cache(self):
        resolver, _, _ = make_resolver({CLIENT_ID: ConnectError("down")})
        with self.assertRaises(MetadataUnavailable) as ctx:
            resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(ctx.exception.reason, "unavailable")
        self.assertEqual(ctx.exception.code, "fetch_connect_failed")

    def test_terminal_purges(self):
        for failure, error in (
            (MockResponse(status=404), MetadataRejected),
            (MockResponse(status=410), MetadataRejected),
            (MockResponse(status=302, headers={"Location": "https://x/"}), MetadataRejected),
            (RedirectNotAllowed(301), MetadataRejected),
            (BlockedDestination("blocked"), MetadataRejected),
            (json_response(b"not json"), InvalidClientMetadata),
            (json_response(public_document(client_secret="x")), InvalidClientMetadata),
            (
                json_response(public_document(token_endpoint_auth_method="private_key_jwt")),
                UnsupportedClient,
            ),
        ):
            with self.subTest(failure=failure):
                resolver, transport, _ = self.expired(failure)
                with self.assertRaises(error) as ctx:
                    resolver.resolve(CLIENT_ID, admit=admit_all)
                self.assertFalse(ctx.exception.transient)
                # Trust is gone: a later transient failure has nothing to fall back on
                transport.add(CLIENT_ID, MockResponse(status=503))
                with self.assertRaises(MetadataUnavailable):
                    resolver.resolve(CLIENT_ID, admit=admit_all)

    def test_client_id_mismatch_purges(self):
        mismatch = json_response(
            public_document(client_id="https://other.example.com/oauth/client.json")
        )
        resolver, transport, clock = self.expired(mismatch)
        with self.assertRaises(InvalidClientMetadata) as ctx:
            resolver.resolve(CLIENT_ID, admit=admit_all)
        self.assertEqual(ctx.exception.code, "client_id_mismatch")
        self.assertIsNone(resolver._cache.get(resolver._key(CLIENT_ID)))
        transport.add(CLIENT_ID, ConnectError("down"))
        with self.assertRaises(MetadataUnavailable):
            resolver.resolve(CLIENT_ID, admit=admit_all)

    def test_terminal_purges_before_expiry_too(self):
        """Within the freshness lifetime the cache is used, without fetching"""
        resolver, transport, clock = make_resolver({CLIENT_ID: VALID})
        resolver.resolve(CLIENT_ID, admit=admit_all)
        transport.add(CLIENT_ID, MockResponse(status=404))
        clock.advance(299)
        self.assertFalse(resolver.resolve(CLIENT_ID, admit=admit_all).stale)
        self.assertEqual(len(transport.requests), 1)


class TestConcurrency(SimpleTestCase):
    """Concurrent resolutions in one process share a fetch"""

    THREADS = 50

    def run_concurrently(self, resolver: PublicClientResolver, transport):
        """Hold the one fetch until every other thread waits on it"""
        original_open = transport.open
        all_waiting = threading.Event()

        def open_when_all_wait(target, deadline):
            flight = resolver._flights[CLIENT_ID]
            for _ in range(500):
                with resolver._flights_lock:
                    if flight.waiters == self.THREADS - 1:
                        all_waiting.set()
                        break
                threading.Event().wait(0.01)
            return original_open(target, deadline)

        results: list[CIMDClient] = []
        errors: list[BaseException] = []
        lock = threading.Lock()

        def worker():
            try:
                client = resolver.resolve(CLIENT_ID, admit=admit_all)
                with lock:
                    results.append(client)
            except BaseException as exc:  # noqa: BLE001
                with lock:
                    errors.append(exc)

        with patch.object(transport, "open", open_when_all_wait):
            threads = [threading.Thread(target=worker) for _ in range(self.THREADS)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)
        self.assertTrue(all_waiting.is_set())
        return results, errors

    def test_one_fetch_no_errors(self):
        resolver, transport, _ = make_resolver({CLIENT_ID: VALID})
        results, errors = self.run_concurrently(resolver, transport)
        self.assertEqual(errors, [])
        self.assertEqual(len(results), self.THREADS)
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(resolver._flights, {})

    def test_shared_failure(self):
        resolver, transport, _ = make_resolver({CLIENT_ID: MockResponse(status=404)})
        results, errors = self.run_concurrently(resolver, transport)
        self.assertEqual(results, [])
        self.assertEqual(len(errors), self.THREADS)
        self.assertTrue(all(isinstance(e, MetadataRejected) for e in errors))
        self.assertEqual(
            {e.code for e in errors if isinstance(e, CIMDError)}, {"fetch_http_status"}
        )
        self.assertEqual(len(transport.requests), 1)


class TestModuleAPI(TestCase):
    """The module-level resolver, on the default (PostgreSQL) cache"""

    def setUp(self):
        cache.clear()

    def test_resolve_and_invalidate(self):
        fetcher, transport = mock_fetcher({CLIENT_ID: VALID})
        admit = CountingAdmit()
        with use_fetcher(fetcher):
            first = resolve_public_client(CLIENT_ID, admit=admit)
            second = resolve_public_client(CLIENT_ID, admit=admit)
            self.assertEqual(first, second)
            self.assertEqual(len(transport.requests), 1)
            invalidate(CLIENT_ID)
            resolve_public_client(CLIENT_ID, admit=admit)
            self.assertEqual(len(transport.requests), 2)
        self.assertEqual(admit.calls, [CLIENT_ID] * 3)
        self.assertFalse(first.stale)

    def test_not_admitted(self):
        fetcher, transport = mock_fetcher({CLIENT_ID: VALID})
        with use_fetcher(fetcher), self.assertRaises(ClientNotAdmitted):
            resolve_public_client(CLIENT_ID, admit=lambda _: False)
        self.assertEqual(transport.requests, [])
