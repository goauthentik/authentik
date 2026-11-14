"""Tests for the untrusted URL fetcher (policy and fetcher logic, no network)"""

import gzip
import socket
import threading
from concurrent.futures import Future
from ipaddress import ip_address
from time import monotonic
from unittest import TestCase
from unittest.mock import patch

from authentik.lib.config import CONFIG
from authentik.lib.utils.untrusted_fetch import (
    BlockedDestination,
    ConcurrencyLimitExceeded,
    ConnectError,
    DeadlineExceeded,
    DestinationPolicy,
    InvalidURL,
    ProtocolError,
    RedirectNotAllowed,
    ResolutionError,
    ResponseTooLarge,
    TLSError,
    UnexpectedStatus,
    UnsupportedContentEncoding,
    UntrustedURLFetcher,
    get_untrusted_fetcher,
    parse_untrusted_url,
)
from authentik.lib.utils.untrusted_fetch.testing import (
    DEFAULT_PUBLIC_ADDRESS,
    FakeClock,
    MockResponse,
    MockTransport,
    StaticResolver,
    mock_fetcher,
    use_fetcher,
)
from authentik.lib.utils.untrusted_fetch.transport import (
    MAX_RESOLVED_ADDRESSES,
    Deadline,
    SystemResolver,
)

URL = "https://client.example.com/oauth/metadata.json"
PUBLIC_V4 = "93.184.215.14"
PUBLIC_V6 = "2606:2800:21f:cb07:6820:80da:af6b:8b2c"

ALWAYS_BLOCKED = [
    "127.0.0.1",
    "127.255.255.254",
    "0.0.0.0",
    "0.1.2.3",
    "169.254.169.254",
    "169.254.170.2",
    "169.254.1.1",
    "100.100.100.200",
    "168.63.129.16",
    "192.0.0.192",
    "224.0.0.1",
    "255.255.255.255",
    "240.0.0.1",
    "::",
    "::1",
    "fe80::1",
    "fec0::1",
    "ff02::1",
    "fd00:ec2::254",
    "fd20:ce::254",
    # IPv4-mapped / translated / compatible / NAT64 forms of blocked addresses
    "::ffff:127.0.0.1",
    "::ffff:169.254.169.254",
    "::ffff:0:127.0.0.1",
    "::127.0.0.1",
    "::a9fe:a9fe",
    "64:ff9b::7f00:1",
    "64:ff9b::a9fe:a9fe",
    # 6to4 / Teredo embedding loopback or metadata
    "2002:7f00:1::1",
    "2002:a9fe:a9fe::1",
    "2001:0:4136:e378:8000:63bf:80ff:fffe",  # Teredo client 127.0.0.1
]

PRIVATE = [
    "10.0.0.1",
    "172.16.5.4",
    "192.168.1.1",
    "100.64.0.1",
    "192.0.2.1",
    "198.18.0.1",
    "fc00::1",
    "fd12:3456::1",
    "2001:db8::1",
    "::ffff:10.0.0.1",
    "64:ff9b::a00:1",
    "2002:a00:1::1",
]


class TestSystemResolver(TestCase):
    """Real executor lifecycle with deterministic, event-blocked DNS work"""

    def setUp(self):
        self.resolver = SystemResolver(max_workers=1)
        self.entered = threading.Event()
        self.release = threading.Event()
        self.addCleanup(self.shutdown)
        self.addCleanup(self.release.set)

    def shutdown(self):
        self.resolver._executor.shutdown(wait=True)
        self.assertTrue(all(not worker.is_alive() for worker in self.resolver._executor._threads))

    def answer(self, addresses=(PUBLIC_V4,)):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, 443))
            for address in addresses
        ]

    def blocked_lookup(self, *args, **kwargs):
        self.entered.set()
        if not self.release.wait(5):
            raise AssertionError("Blocked resolver was not released")
        return self.answer()

    def assert_capacity_recovers(self):
        self.release.set()
        self.assertTrue(self.resolver._slots.acquire(timeout=2))
        self.resolver._slots.release()
        self.assertEqual(
            self.resolver.resolve("client.example.com", 443, Deadline(2)),
            [ip_address(PUBLIC_V4)],
        )

    def assert_no_new_submissions(self, submit, queued):
        start = monotonic()
        for _ in range(5):
            with self.assertRaises(DeadlineExceeded):
                self.resolver.resolve("client.example.com", 443, Deadline(0.01))
        self.assertLess(monotonic() - start, 2)
        self.assertEqual(submit.call_count, 1)
        self.assertEqual(self.resolver._executor._work_queue.qsize(), queued)
        self.assertFalse(self.resolver._slots.acquire(blocking=False))

    def test_running_timeout_retains_capacity(self):
        with (
            patch("socket.getaddrinfo", side_effect=self.blocked_lookup) as lookup,
            patch.object(
                self.resolver._executor, "submit", wraps=self.resolver._executor.submit
            ) as submit,
        ):
            with self.assertRaises(DeadlineExceeded):
                self.resolver.resolve("client.example.com", 443, Deadline(0.05))
            self.assertTrue(self.entered.wait(2))
            self.assert_no_new_submissions(submit, queued=0)
            self.assertEqual(lookup.call_count, 1)
            self.assert_capacity_recovers()

    def test_queued_timeout_does_not_accumulate_cancelled_work(self):
        blocker = self.resolver._executor.submit(self.blocked_lookup)
        self.assertTrue(self.entered.wait(2))
        with (
            patch("socket.getaddrinfo", return_value=self.answer()) as lookup,
            patch.object(
                self.resolver._executor, "submit", wraps=self.resolver._executor.submit
            ) as submit,
        ):
            with self.assertRaises(DeadlineExceeded):
                self.resolver.resolve("client.example.com", 443, Deadline(0.01))
            self.assert_no_new_submissions(submit, queued=1)
            lookup.assert_not_called()
            self.assert_capacity_recovers()
            blocker.result(timeout=2)
            self.assertEqual(lookup.call_count, 2)

    def test_running_interruption_retains_capacity_and_fetch_slot_recovers(self):
        interruption = KeyboardInterrupt("cancelled fetch")
        fetcher = UntrustedURLFetcher(
            resolver=self.resolver,
            transport=MockTransport({URL: MockResponse(body=b"{}")}),
            max_concurrency=1,
        )

        def interrupt_result(future, timeout=None):
            self.assertTrue(self.entered.wait(2))
            raise interruption

        with (
            patch("socket.getaddrinfo", side_effect=self.blocked_lookup),
            patch.object(
                self.resolver._executor, "submit", wraps=self.resolver._executor.submit
            ) as submit,
        ):
            with patch.object(Future, "result", new=interrupt_result):
                with self.assertRaises(KeyboardInterrupt) as raised:
                    fetcher.fetch(URL, max_bytes=1024)
            self.assertIs(raised.exception, interruption)
            self.assertTrue(fetcher._slots.acquire(blocking=False))
            fetcher._slots.release()
            self.assert_no_new_submissions(submit, queued=0)
            self.assert_capacity_recovers()
            self.assertEqual(fetcher.fetch(URL, max_bytes=1024).content, b"{}")

    def test_queued_interruption_retains_capacity(self):
        blocker = self.resolver._executor.submit(self.blocked_lookup)
        self.assertTrue(self.entered.wait(2))
        interruption = BaseException("cancelled queued lookup")
        with (
            patch("socket.getaddrinfo", return_value=self.answer()) as lookup,
            patch.object(
                self.resolver._executor, "submit", wraps=self.resolver._executor.submit
            ) as submit,
        ):
            with patch.object(Future, "result", side_effect=interruption):
                with self.assertRaises(BaseException) as raised:
                    self.resolver.resolve("client.example.com", 443, Deadline(2))
            self.assertIs(raised.exception, interruption)
            self.assert_no_new_submissions(submit, queued=1)
            lookup.assert_not_called()
            self.assert_capacity_recovers()
            blocker.result(timeout=2)
            self.assertEqual(lookup.call_count, 2)

    def test_submission_failure_releases_capacity(self):
        interruption = KeyboardInterrupt("interrupted submit")
        with patch.object(self.resolver._executor, "submit", side_effect=interruption):
            with self.assertRaises(KeyboardInterrupt) as raised:
                self.resolver.resolve("client.example.com", 443, Deadline(2))
        self.assertIs(raised.exception, interruption)
        with patch("socket.getaddrinfo", return_value=self.answer()):
            self.assert_capacity_recovers()

    def test_expired_deadline_never_submits(self):
        with patch.object(self.resolver._executor, "submit") as submit:
            with self.assertRaises(DeadlineExceeded):
                self.resolver.resolve("client.example.com", 443, Deadline(0))
        submit.assert_not_called()
        with patch("socket.getaddrinfo", return_value=self.answer()):
            self.assert_capacity_recovers()

    def test_lookup_failure_releases_capacity(self):
        with patch("socket.getaddrinfo", side_effect=socket.gaierror("no answer")):
            with self.assertRaises(ResolutionError):
                self.resolver.resolve("client.example.com", 443, Deadline(2))
        with patch("socket.getaddrinfo", return_value=self.answer()):
            self.assert_capacity_recovers()

    def test_oversized_answer_rejected_before_connect(self):
        public = [f"93.184.215.{index + 1}" for index in range(MAX_RESOLVED_ADDRESSES)]
        transport = MockTransport({URL: MockResponse(body=b"{}")})
        fetcher = UntrustedURLFetcher(resolver=self.resolver, transport=transport)
        for tail in ("127.0.0.1", "10.0.0.1", "93.184.215.100"):
            with self.subTest(tail=tail):
                with patch("socket.getaddrinfo", return_value=self.answer([*public, tail])):
                    with self.assertRaises(ResolutionError):
                        fetcher.fetch(URL, max_bytes=1024)
        self.assertEqual(transport.requests, [])

    def test_answer_limit_counts_distinct_addresses(self):
        public = [f"93.184.215.{index + 1}" for index in range(MAX_RESOLVED_ADDRESSES)]
        with patch("socket.getaddrinfo", return_value=self.answer(public * 2)):
            self.assertEqual(
                self.resolver.resolve("client.example.com", 443, Deadline(2)),
                [ip_address(address) for address in public],
            )

    def test_blocked_address_at_limit_rejects_whole_answer(self):
        public = [f"93.184.215.{index + 1}" for index in range(MAX_RESOLVED_ADDRESSES - 1)]
        transport = MockTransport({URL: MockResponse(body=b"{}")})
        fetcher = UntrustedURLFetcher(resolver=self.resolver, transport=transport)
        with patch("socket.getaddrinfo", return_value=self.answer([*public, "127.0.0.1"])):
            with self.assertRaises(BlockedDestination):
                fetcher.fetch(URL, max_bytes=1024)
        self.assertEqual(transport.requests, [])


class TestDestinationPolicy(TestCase):
    """Address policy"""

    def test_public_allowed(self):
        policy = DestinationPolicy()
        for addr in (PUBLIC_V4, PUBLIC_V6, "8.8.8.8", "::ffff:8.8.8.8", "64:ff9b::808:808"):
            with self.subTest(addr=addr):
                self.assertTrue(policy.check_str(addr).allowed)

    def test_always_blocked(self):
        policy = DestinationPolicy()
        for addr in ALWAYS_BLOCKED:
            with self.subTest(addr=addr):
                self.assertFalse(policy.check_str(addr).allowed)

    def test_private_blocked_by_default(self):
        policy = DestinationPolicy()
        for addr in PRIVATE:
            with self.subTest(addr=addr):
                decision = policy.check_str(addr)
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.reason, "private")

    def test_scoped_ipv6_blocked(self):
        self.assertFalse(DestinationPolicy().check_str("fd12::1%eth0").allowed)
        self.assertFalse(
            DestinationPolicy.from_entries(["fd12::/16"]).check_str("fd12::1%2").allowed
        )

    def test_invalid_address(self):
        self.assertFalse(DestinationPolicy().check_str("not-an-ip").allowed)

    def test_allowlist_only_listed_ranges(self):
        policy = DestinationPolicy.from_entries(["10.0.0.0/8", "fd12:3456::/32", "192.168.1.5"])
        self.assertTrue(policy.check_str("10.1.2.3").allowed)
        self.assertTrue(policy.check_str("::ffff:10.1.2.3").allowed)
        self.assertTrue(policy.check_str("fd12:3456::1").allowed)
        self.assertTrue(policy.check_str("192.168.1.5").allowed)
        self.assertFalse(policy.check_str("192.168.1.6").allowed)
        self.assertFalse(policy.check_str("172.16.0.1").allowed)
        self.assertFalse(policy.check_str("fd12:3457::1").allowed)

    def test_allowlist_never_permits_always_blocked(self):
        policy = DestinationPolicy.from_entries(
            [
                "0.0.0.0/0",
                "::/0",
                "127.0.0.0/8",
                "169.254.0.0/16",
                "fe80::/10",
                "fd00::/8",
                "::1",
                "localhost",
                "metadata.google.internal",
            ]
        )
        for addr in ALWAYS_BLOCKED:
            with self.subTest(addr=addr):
                self.assertFalse(policy.check_str(addr).allowed)
                self.assertFalse(policy.check_str(addr, "metadata.google.internal").allowed)
        # But the broad entries do permit ordinary private ranges
        self.assertTrue(policy.check_str("10.0.0.1").allowed)

    def test_ipv4_address_does_not_match_ipv6_network(self):
        # ipaddress would report 0.0.0.10 as inside ::/96 without a version check
        policy = DestinationPolicy.from_entries(["::/96"])
        self.assertFalse(policy.check_str("10.0.0.1").allowed)

    def test_hostname_allowlist(self):
        policy = DestinationPolicy.from_entries(["Internal.Example.", "10.0.0.0/8"])
        self.assertTrue(policy.check_str("192.168.1.1", "internal.example").allowed)
        self.assertTrue(policy.check_str("192.168.1.1", "INTERNAL.example.").allowed)
        self.assertFalse(policy.check_str("192.168.1.1", "other.example").allowed)
        self.assertFalse(policy.check_str("192.168.1.1", "sub.internal.example").allowed)
        self.assertFalse(policy.check_str("127.0.0.1", "internal.example").allowed)
        self.assertFalse(policy.check_str("169.254.169.254", "internal.example").allowed)

    def test_from_config_value(self):
        policy = DestinationPolicy.from_config_value("10.0.0.0/8, internal.example ,, 10.0.0.0/33")
        self.assertEqual(len(policy.allowed_networks), 1)
        self.assertEqual(policy.allowed_hostnames, frozenset({"internal.example"}))
        policy = DestinationPolicy.from_config_value(["192.168.0.0/16", "bad/entry", "a:b"])
        self.assertEqual(len(policy.allowed_networks), 1)
        self.assertEqual(policy.allowed_hostnames, frozenset())
        self.assertEqual(DestinationPolicy.from_config_value(None), DestinationPolicy())


class TestParseURL(TestCase):
    """URL validation"""

    def test_valid(self):
        parsed = parse_untrusted_url(URL)
        self.assertEqual(parsed.hostname, "client.example.com")
        self.assertEqual(parsed.port, 443)
        self.assertEqual(parsed.path, "/oauth/metadata.json")
        self.assertEqual(parsed.host_header, "client.example.com")
        self.assertEqual(parse_untrusted_url("https://Example.COM:8443").path, "/")
        self.assertEqual(
            parse_untrusted_url("https://Example.COM:8443").host_header, "example.com:8443"
        )
        self.assertEqual(
            parse_untrusted_url("https://[2606:2800::1]/x").host_header, "[2606:2800::1]"
        )
        self.assertEqual(parse_untrusted_url("https://example.com./x").hostname, "example.com")

    def test_invalid(self):
        for url in [
            "",
            "http://client.example.com/m",
            "HTTPS://client.example.com/m",
            "ftp://client.example.com/m",
            "https://user:pass@client.example.com/m",
            "https://user@client.example.com/m",
            "https://client.example.com/m?x=1",
            "https://client.example.com/m?",
            "https://client.example.com/m#frag",
            "https://client.example.com/m#",
            "https://client.example.com/a/../m",
            "https://client.example.com/a/./m",
            "https://client.example.com/a/%2e%2e/m",
            "https://client.example.com/a%2Fb",
            "https://client.example.com/a%5cb",
            "https://client.example.com/a%00",
            "https://client.example.com/a%zz",
            "https://client.example.com\\@evil.example/",
            "https://client.example.com/a b",
            "https://client.example.com/\n",
            "https://clïent.example.com/",
            "https:///nohost",
            "https://client.example.com:0/",
            "https://client.example.com:99999/",
            "https://client.example.com:abc/",
            "https://[fe80::1%25eth0]/",
            "https://[not-ipv6]/",
            "https://127.1/",
            "https://2130706433/",
            "https://under_score.example/",
            "https://-leading.example/",
            "https://" + "a" * 64 + ".example/",
            "https://example.com/" + "a" * 2100,
        ]:
            with self.subTest(url=url):
                with self.assertRaises(InvalidURL):
                    parse_untrusted_url(url)

    def test_ip_literal(self):
        self.assertEqual(
            parse_untrusted_url("https://93.184.215.14/").ip_literal, ip_address(PUBLIC_V4)
        )


def _gzip(data: bytes) -> bytes:
    return gzip.compress(data)


class TestFetcher(TestCase):
    """Fetcher behavior with the deterministic transport"""

    def test_success(self):
        fetcher, transport = mock_fetcher(
            {URL: MockResponse(headers={"Content-Type": "application/json"}, body=b'{"a": 1}')}
        )
        response = fetcher.fetch(URL, max_bytes=64 * 1024)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.content, b'{"a": 1}')
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.address, DEFAULT_PUBLIC_ADDRESS)
        self.assertTrue(transport.streams[0].closed)

    def test_request_headers(self):
        """Only fixed headers are sent: no cookies, credentials or caller headers"""
        fetcher, transport = mock_fetcher({URL: MockResponse(body=b"{}")})
        fetcher.fetch(URL, max_bytes=1024, accept="application/jwk-set+json")
        (request,) = transport.requests
        names = [name.lower() for name, _ in request.headers]
        self.assertEqual(names, ["host", "user-agent", "accept", "accept-encoding", "connection"])
        headers = dict(request.headers)
        self.assertEqual(headers["Host"], "client.example.com")
        self.assertEqual(headers["Accept"], "application/jwk-set+json")
        self.assertEqual(headers["Accept-Encoding"], "gzip")
        self.assertEqual(request.hostname, "client.example.com")
        self.assertEqual(request.path, "/oauth/metadata.json")

    def test_accept_header_injection(self):
        fetcher, _ = mock_fetcher()
        with self.assertRaises(ValueError):
            fetcher.fetch(URL, max_bytes=1024, accept="application/json\r\nCookie: a=b")

    def test_max_bytes_bounds(self):
        fetcher, _ = mock_fetcher()
        for value in (0, -1, 1024 * 1024 + 1):
            with self.assertRaises(ValueError):
                fetcher.fetch(URL, max_bytes=value)

    def test_invalid_url_never_resolves(self):
        resolver = StaticResolver(default=[PUBLIC_V4])
        fetcher, transport = mock_fetcher(resolver=resolver)
        with self.assertRaises(InvalidURL):
            fetcher.fetch("http://client.example.com/m", max_bytes=1024)
        self.assertEqual(resolver.calls, [])
        self.assertEqual(transport.requests, [])

    def test_blocked_resolved_addresses(self):
        for addr in ALWAYS_BLOCKED + PRIVATE:
            with self.subTest(addr=addr):
                fetcher, transport = mock_fetcher(
                    {URL: MockResponse(body=b"{}")}, records={"client.example.com": [addr]}
                )
                with self.assertRaises(BlockedDestination):
                    fetcher.fetch(URL, max_bytes=1024)
                self.assertEqual(transport.requests, [])

    def test_blocked_ip_literals(self):
        for url in (
            "https://127.0.0.1/m",
            "https://169.254.169.254/latest/meta-data",
            "https://[::1]/m",
            "https://[::ffff:127.0.0.1]/m",
            "https://[::ffff:7f00:1]/m",
            "https://[fd00:ec2::254]/m",
            "https://10.0.0.1/m",
        ):
            with self.subTest(url=url):
                fetcher, transport = mock_fetcher()
                with self.assertRaises(BlockedDestination):
                    fetcher.fetch(url, max_bytes=1024)
                self.assertEqual(transport.requests, [])

    def test_any_blocked_address_rejects(self):
        """A single bad address in the answer blocks the fetch, even if listed later"""
        fetcher, transport = mock_fetcher(
            {URL: MockResponse(body=b"{}")},
            records={"client.example.com": [PUBLIC_V4, PUBLIC_V6, "127.0.0.1"]},
        )
        with self.assertRaises(BlockedDestination):
            fetcher.fetch(URL, max_bytes=1024)
        self.assertEqual(transport.requests, [])

    def test_dns_rebinding(self):
        """The connection goes to the validated address; DNS is consulted once per fetch"""
        resolver = StaticResolver.sequence(
            {"client.example.com": [[PUBLIC_V4], ["127.0.0.1"], ["169.254.169.254"]]}
        )
        fetcher, transport = mock_fetcher({URL: MockResponse(body=b"{}")}, resolver=resolver)
        response = fetcher.fetch(URL, max_bytes=1024)
        self.assertEqual(response.address, PUBLIC_V4)
        self.assertEqual(resolver.calls, ["client.example.com"])
        self.assertEqual([r.address for r in transport.requests], [ip_address(PUBLIC_V4)])
        # The rebound answer is checked again on the next fetch and blocked
        with self.assertRaises(BlockedDestination):
            fetcher.fetch(URL, max_bytes=1024)
        self.assertEqual(len(transport.requests), 1)

    def test_fallback_to_next_address(self):
        fetcher, transport = mock_fetcher(
            {URL: MockResponse(body=b"{}")},
            records={"client.example.com": [PUBLIC_V6, PUBLIC_V4]},
        )
        transport.unreachable = {ip_address(PUBLIC_V6)}
        response = fetcher.fetch(URL, max_bytes=1024)
        self.assertEqual(response.address, PUBLIC_V4)
        self.assertEqual(len(transport.requests), 2)

    def test_all_addresses_unreachable(self):
        fetcher, transport = mock_fetcher(records={"client.example.com": [PUBLIC_V4]})
        transport.unreachable = {ip_address(PUBLIC_V4)}
        with self.assertRaises(ConnectError):
            fetcher.fetch(URL, max_bytes=1024)

    def test_tls_error_does_not_fall_back(self):
        fetcher, transport = mock_fetcher(
            {URL: TLSError("bad certificate")},
            records={"client.example.com": [PUBLIC_V4, PUBLIC_V6]},
        )
        with self.assertRaises(TLSError):
            fetcher.fetch(URL, max_bytes=1024)
        self.assertEqual(len(transport.requests), 1)

    def test_resolution_failure(self):
        fetcher, _ = mock_fetcher(resolver=StaticResolver())
        with self.assertRaises(ResolutionError):
            fetcher.fetch(URL, max_bytes=1024)

    def test_redirects_not_followed(self):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                fetcher, transport = mock_fetcher(
                    {
                        URL: MockResponse(
                            status=status, headers={"Location": "https://other.example/m"}
                        )
                    }
                )
                with self.assertRaises(RedirectNotAllowed) as ctx:
                    fetcher.fetch(URL, max_bytes=1024)
                self.assertEqual(ctx.exception.status, status)
                self.assertEqual(len(transport.requests), 1)

    def test_unexpected_status(self):
        for status in (204, 304, 404, 500):
            with self.subTest(status=status):
                fetcher, _ = mock_fetcher({URL: MockResponse(status=status, body=b"nope")})
                with self.assertRaises(UnexpectedStatus) as ctx:
                    fetcher.fetch(URL, max_bytes=1024)
                self.assertEqual(ctx.exception.status, status)

    def test_size_limit_exact(self):
        fetcher, _ = mock_fetcher({URL: MockResponse(body=b"a" * 1024)})
        self.assertEqual(len(fetcher.fetch(URL, max_bytes=1024).content), 1024)

    def test_size_overflow_declared(self):
        fetcher, transport = mock_fetcher(
            {URL: MockResponse(headers={"Content-Length": "2048"}, body=b"a" * 2048)}
        )
        with self.assertRaises(ResponseTooLarge):
            fetcher.fetch(URL, max_bytes=1024)
        self.assertTrue(transport.streams[0].closed)

    def test_size_overflow_without_content_length(self):
        fetcher, _ = mock_fetcher({URL: MockResponse(body=[b"a" * 1000] * 100)})
        with self.assertRaises(ResponseTooLarge):
            fetcher.fetch(URL, max_bytes=64 * 1024)

    def test_size_overflow_lying_content_length(self):
        fetcher, _ = mock_fetcher(
            {URL: MockResponse(headers={"Content-Length": "10"}, body=b"a" * 4096)}
        )
        with self.assertRaises(ResponseTooLarge):
            fetcher.fetch(URL, max_bytes=1024)

    def test_invalid_content_length(self):
        for value in ("abc", "-1"):
            with self.subTest(value=value):
                fetcher, _ = mock_fetcher(
                    {URL: MockResponse(headers={"Content-Length": value}, body=b"{}")}
                )
                with self.assertRaises(ProtocolError):
                    fetcher.fetch(URL, max_bytes=1024)

    def test_gzip(self):
        fetcher, _ = mock_fetcher(
            {URL: MockResponse(headers={"Content-Encoding": "gzip"}, body=_gzip(b'{"a": 1}'))}
        )
        self.assertEqual(fetcher.fetch(URL, max_bytes=1024).content, b'{"a": 1}')

    def test_decompression_overflow(self):
        bomb = _gzip(b"\0" * (50 * 1024 * 1024))
        self.assertLess(len(bomb), 64 * 1024)
        fetcher, _ = mock_fetcher(
            {URL: MockResponse(headers={"Content-Encoding": "gzip"}, body=bomb)}
        )
        with self.assertRaises(ResponseTooLarge):
            fetcher.fetch(URL, max_bytes=64 * 1024)

    def test_decompression_limit_exact(self):
        fetcher, _ = mock_fetcher(
            {URL: MockResponse(headers={"Content-Encoding": "gzip"}, body=_gzip(b"a" * 1024))}
        )
        self.assertEqual(len(fetcher.fetch(URL, max_bytes=1024).content), 1024)
        fetcher, _ = mock_fetcher(
            {URL: MockResponse(headers={"Content-Encoding": "gzip"}, body=_gzip(b"a" * 1025))}
        )
        with self.assertRaises(ResponseTooLarge):
            fetcher.fetch(URL, max_bytes=1024)

    def test_bad_gzip(self):
        payload = _gzip(b'{"a": 1}' * 100)
        for body in (b"not gzip", payload[: len(payload) // 2], payload + b"trailing", payload * 2):
            with self.subTest(body=body[:10]):
                fetcher, _ = mock_fetcher(
                    {URL: MockResponse(headers={"Content-Encoding": "gzip"}, body=body)}
                )
                with self.assertRaises(UnsupportedContentEncoding):
                    fetcher.fetch(URL, max_bytes=64 * 1024)

    def test_unsupported_encodings(self):
        for encoding in ("br", "zstd", "deflate", "gzip, gzip", "compress"):
            with self.subTest(encoding=encoding):
                fetcher, _ = mock_fetcher(
                    {URL: MockResponse(headers={"Content-Encoding": encoding}, body=b"{}")}
                )
                with self.assertRaises(UnsupportedContentEncoding):
                    fetcher.fetch(URL, max_bytes=1024)

    def test_identity_encoding(self):
        fetcher, _ = mock_fetcher(
            {URL: MockResponse(headers={"Content-Encoding": "identity"}, body=b"{}")}
        )
        self.assertEqual(fetcher.fetch(URL, max_bytes=1024).content, b"{}")

    def test_slow_body(self):
        """A body that trickles in past the total deadline fails"""
        fetcher, _ = mock_fetcher(
            {URL: MockResponse(body=[b"a"] * 100, chunk_delay=0.1)}, timeout=5
        )
        with self.assertRaises(DeadlineExceeded):
            fetcher.fetch(URL, max_bytes=1024)

    def test_slow_headers(self):
        fetcher, _ = mock_fetcher({URL: MockResponse(body=b"{}", header_delay=6)}, timeout=5)
        with self.assertRaises(DeadlineExceeded):
            fetcher.fetch(URL, max_bytes=1024)

    def test_within_deadline(self):
        fetcher, _ = mock_fetcher({URL: MockResponse(body=[b"a"] * 10, chunk_delay=0.4)}, timeout=5)
        self.assertEqual(fetcher.fetch(URL, max_bytes=1024).content, b"a" * 10)

    def test_concurrency_limit(self):
        fetcher, transport = mock_fetcher({URL: MockResponse(body=b"{}")}, max_concurrency=1)
        # Use a real clock so the semaphore wait is bounded by the deadline
        fetcher._clock = __import__("time").monotonic
        fetcher.timeout = 0.2
        self.assertTrue(fetcher._slots.acquire(blocking=False))
        try:
            with self.assertRaises(ConcurrencyLimitExceeded):
                fetcher.fetch(URL, max_bytes=1024)
        finally:
            fetcher._slots.release()
        self.assertEqual(transport.requests, [])
        self.assertEqual(fetcher.fetch(URL, max_bytes=1024).content, b"{}")

    def test_bounds_clamped(self):
        fetcher = UntrustedURLFetcher(
            resolver=StaticResolver(), transport=MockTransport(), timeout=1000, max_concurrency=0
        )
        self.assertEqual(fetcher.timeout, 30)
        self.assertEqual(fetcher.max_concurrency, 1)

    def test_from_config(self):
        with (
            CONFIG.patch("untrusted_fetch.timeout", "2.5"),
            CONFIG.patch("untrusted_fetch.max_concurrency", 3),
            CONFIG.patch(
                "untrusted_fetch.allowed_private_destinations", "10.0.0.0/8,internal.example"
            ),
        ):
            fetcher = UntrustedURLFetcher.from_config(
                resolver=StaticResolver(), transport=MockTransport()
            )
        self.assertEqual(fetcher.timeout, 2.5)
        self.assertEqual(fetcher.max_concurrency, 3)
        self.assertTrue(fetcher.policy.check_str("10.2.3.4").allowed)
        self.assertTrue(fetcher.policy.check_str("192.168.1.1", "internal.example").allowed)
        self.assertFalse(fetcher.policy.check_str("127.0.0.1", "internal.example").allowed)

    def test_default_config(self):
        fetcher = UntrustedURLFetcher.from_config(
            resolver=StaticResolver(), transport=MockTransport()
        )
        self.assertEqual(fetcher.timeout, 5)
        self.assertEqual(fetcher.policy, DestinationPolicy())

    def test_private_allowlist_end_to_end(self):
        policy = DestinationPolicy.from_entries(["10.0.0.0/8"])
        fetcher, transport = mock_fetcher(
            {URL: MockResponse(body=b"{}")},
            records={"client.example.com": ["10.1.1.1"]},
            policy=policy,
        )
        self.assertEqual(fetcher.fetch(URL, max_bytes=1024).address, "10.1.1.1")
        for addr in ("192.168.1.1", "127.0.0.1", "169.254.169.254"):
            with self.subTest(addr=addr):
                fetcher, _ = mock_fetcher(
                    {URL: MockResponse(body=b"{}")},
                    records={"client.example.com": [addr]},
                    policy=policy,
                )
                with self.assertRaises(BlockedDestination):
                    fetcher.fetch(URL, max_bytes=1024)

    def test_use_fetcher(self):
        fetcher, _ = mock_fetcher({URL: MockResponse(body=b"{}")})
        with use_fetcher(fetcher):
            self.assertIs(get_untrusted_fetcher(), fetcher)
        self.assertIsNot(get_untrusted_fetcher(), fetcher)

    def test_fake_clock(self):
        clock = FakeClock(10)
        clock.advance(5)
        self.assertEqual(clock(), 15)
