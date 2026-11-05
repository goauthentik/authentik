"""Tests for the untrusted URL fetcher's real transport against a local TLS server.

The server listens on 127.0.0.1 only; nothing leaves the machine. The fetcher's
destination policy (which always blocks loopback) is replaced by a test policy,
and DNS is replaced by a static resolver."""

import gzip
import socket
import ssl
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from authentik.lib.utils.untrusted_fetch import (
    AddressDecision,
    ConnectError,
    DeadlineExceeded,
    DestinationPolicy,
    ProtocolError,
    RedirectNotAllowed,
    ResponseTooLarge,
    TLSError,
    UntrustedURLFetcher,
)
from authentik.lib.utils.untrusted_fetch.testing import StaticResolver
from authentik.lib.utils.untrusted_fetch.transport import (
    ConnectTarget,
    Deadline,
    HTTPClientTransport,
    _PinnedHTTPSConnection,
    _Watchdog,
    default_ssl_context,
)

HOSTNAME = "metadata.test"
LOOPBACK = "127.0.0.1"


class _LoopbackTestPolicy(DestinationPolicy):
    """Test-only policy that permits the local test server"""

    def check(self, address, hostname=None) -> AddressDecision:
        if address == ip_address(LOOPBACK):
            return AddressDecision(True, "test")
        return super().check(address, hostname)


def _make_cert(directory: Path) -> tuple[Path, Path, Path]:
    """Create a CA and a leaf certificate for HOSTNAME"""
    now = datetime.now(UTC)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "untrusted-fetch test CA")])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False
        )
        .sign(ca_key, hashes.SHA256())
    )
    key = ec.generate_private_key(ec.SECP256R1())
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, HOSTNAME)]))
        .issuer_name(ca_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(HOSTNAME)]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    ca_path = directory / "ca.pem"
    cert_path = directory / "cert.pem"
    key_path = directory / "key.pem"
    ca_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return ca_path, cert_path, key_path


type Handler = Callable[[ssl.SSLSocket, bytes], None]


def respond(raw: bytes) -> Handler:
    """Handler that sends a fixed response"""

    def handler(conn: ssl.SSLSocket, _request: bytes) -> None:
        conn.sendall(raw)

    return handler


def drip(headers: bytes, interval: float, count: int = 1000) -> Handler:
    """Handler that sends headers, then one body byte per `interval`"""

    def handler(conn: ssl.SSLSocket, _request: bytes) -> None:
        conn.sendall(headers)
        for _ in range(count):
            time.sleep(interval)
            conn.sendall(b"a")

    return handler


def stall(conn: ssl.SSLSocket, _request: bytes) -> None:
    """Handler that never responds"""
    time.sleep(3)


class LocalTLSServer:
    """Minimal threaded HTTPS server on 127.0.0.1"""

    def __init__(self, cert_path: Path, key_path: Path):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(cert_path, key_path)
        self.context.sni_callback = self._sni
        self.sock = socket.create_server((LOOPBACK, 0))
        self.port = self.sock.getsockname()[1]
        self.handler: Handler = respond(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}")
        self.sni: list[str | None] = []
        self.requests: list[bytes] = []
        self.tls_failures = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _sni(self, _sslobj, server_name, _ctx):
        self.sni.append(server_name)

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                raw, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(raw,), daemon=True).start()

    def _handle(self, raw: socket.socket) -> None:
        raw.settimeout(5)
        try:
            conn = self.context.wrap_socket(raw, server_side=True)
        except ssl.SSLError, OSError:
            self.tls_failures += 1
            raw.close()
            return
        try:
            request = b""
            while b"\r\n\r\n" not in request:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                request += chunk
            self.requests.append(request)
            self.handler(conn, request)
        except OSError:
            pass
        finally:
            conn.close()

    def close(self) -> None:
        self._stop.set()
        self.sock.close()


class TestHTTPClientTransport(TestCase):
    """Real transport over TLS to a local server"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp = TemporaryDirectory()
        cls.ca_path, cert_path, key_path = _make_cert(Path(cls._tmp.name))
        cls.server = LocalTLSServer(cert_path, key_path)

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        cls._tmp.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.server.sni.clear()
        self.server.requests.clear()
        self.server.tls_failures = 0
        self.server.handler = respond(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 8\r\n\r\n"
            b'{"a": 1}'
        )

    def ssl_context(self) -> ssl.SSLContext:
        context = default_ssl_context()
        context.load_verify_locations(cafile=self.ca_path)
        return context

    def fetcher(self, *, timeout: float = 5, ssl_context: ssl.SSLContext | None = None):
        return UntrustedURLFetcher(
            policy=_LoopbackTestPolicy(),
            resolver=StaticResolver({HOSTNAME: [LOOPBACK]}),
            transport=HTTPClientTransport(ssl_context or self.ssl_context()),
            timeout=timeout,
        )

    @property
    def url(self) -> str:
        return f"https://{HOSTNAME}:{self.server.port}/client.json"

    def test_success_pins_address_and_preserves_sni(self):
        """Connects to the validated IP without a new DNS lookup; SNI and Host are the hostname"""
        with patch("socket.getaddrinfo", side_effect=AssertionError("DNS lookup")):
            response = self.fetcher().fetch(self.url, max_bytes=1024)
        self.assertEqual(response.content, b'{"a": 1}')
        self.assertEqual(response.address, LOOPBACK)
        self.assertEqual(self.server.sni, [HOSTNAME])
        (request,) = self.server.requests
        lines = request.decode().split("\r\n")
        self.assertEqual(lines[0], "GET /client.json HTTP/1.1")
        header_names = sorted(line.split(":", 1)[0].lower() for line in lines[1:] if line)
        self.assertEqual(
            header_names, ["accept", "accept-encoding", "connection", "host", "user-agent"]
        )
        self.assertIn(f"Host: {HOSTNAME}:{self.server.port}", lines)

    def test_untrusted_certificate(self):
        """The test CA is not trusted by default"""
        with self.assertRaises(TLSError):
            self.fetcher(ssl_context=default_ssl_context()).fetch(self.url, max_bytes=1024)
        self.assertEqual(self.server.requests, [])

    def test_premature_content_length_eof(self):
        for body, encoding in ((b"", b""), (b"{}", b""), (gzip.compress(b"{}"), b"gzip")):
            with self.subTest(body=body, encoding=encoding):
                self.server.handler = respond(
                    b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\nContent-Encoding: %s\r\n\r\n%s"
                    % (len(body) + 100, encoding, body)
                )
                with self.assertRaises(ProtocolError):
                    self.fetcher().fetch(self.url, max_bytes=1024)

    def test_complete_response_framing(self):
        for headers, body in (
            (b"Content-Length: 0\r\n", b""),
            (b"Content-Length: 2\r\nConnection: close\r\n", b"{}"),
            (b"Connection: close\r\n", b"{}"),
        ):
            with self.subTest(headers=headers):
                self.server.handler = respond(b"HTTP/1.1 200 OK\r\n" + headers + b"\r\n" + body)
                self.assertEqual(self.fetcher().fetch(self.url, max_bytes=1024).content, body)

    def test_premature_chunked_eof(self):
        for body in (b"2\r\n{", b"2\r\n{}\r\n"):
            with self.subTest(body=body):
                self.server.handler = respond(
                    b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" + body
                )
                with self.assertRaises(ProtocolError):
                    self.fetcher().fetch(self.url, max_bytes=1024)

    def assert_watchdog_closed(self, watchdog, duplicate):
        self.assertIsNone(watchdog._sock)
        self.assertEqual(duplicate.fileno(), -1)
        self.assertTrue(watchdog._timer.finished.is_set())
        watchdog._timer.join(timeout=2)
        self.assertFalse(watchdog._timer.is_alive())

    def test_interrupted_open_closes_real_tls_connection(self):
        for error_type in (KeyboardInterrupt, SystemExit, BaseException, RuntimeError):
            with self.subTest(error_type=error_type):
                interruption = error_type("interrupted response")
                captured = []

                def interrupt(connection, captured=captured, interruption=interruption):
                    self.addCleanup(connection._watchdog.cancel)
                    self.addCleanup(connection.close)
                    captured.append((connection, connection.sock, connection._watchdog._sock))
                    raise interruption

                fetcher = self.fetcher()
                with patch.object(_PinnedHTTPSConnection, "getresponse", new=interrupt):
                    with self.assertRaises(error_type) as raised:
                        fetcher.fetch(self.url, max_bytes=1024)
                self.assertIs(raised.exception, interruption)
                ((connection, sock, duplicate),) = captured
                self.assertIsNone(connection.sock)
                self.assertEqual(sock.fileno(), -1)
                self.assert_watchdog_closed(connection._watchdog, duplicate)
                self.assertTrue(fetcher._slots.acquire(blocking=False))
                fetcher._slots.release()
                self.assertEqual(fetcher.fetch(self.url, max_bytes=1024).content, b'{"a": 1}')

    def test_interrupted_response_wrapper_closes_detached_response(self):
        self.server.handler = respond(
            b"HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Length: 2\r\n\r\n{}"
        )
        interruption = KeyboardInterrupt("interrupted wrapper")
        captured = []

        def interrupt(connection, response, watchdog):
            self.addCleanup(watchdog.cancel)
            self.addCleanup(connection.close)
            self.addCleanup(response.close)
            captured.append((connection, response, response.fp, watchdog, watchdog._sock))
            raise interruption

        with patch(
            "authentik.lib.utils.untrusted_fetch.transport._HTTPClientResponse", new=interrupt
        ):
            with self.assertRaises(KeyboardInterrupt) as raised:
                self.fetcher().fetch(self.url, max_bytes=1024)
        self.assertIs(raised.exception, interruption)
        ((connection, response, reader, watchdog, duplicate),) = captured
        self.assertIsNone(connection.sock)
        self.assertTrue(response.isclosed())
        self.assertTrue(reader.closed)
        self.assert_watchdog_closed(watchdog, duplicate)

    def test_failed_connection_construction_cancels_watchdog(self):
        interruption = KeyboardInterrupt("interrupted constructor")
        captured = []

        def interrupt(*args, watchdog, **kwargs):
            self.addCleanup(watchdog.cancel)
            captured.append(watchdog)
            raise interruption

        with patch(
            "authentik.lib.utils.untrusted_fetch.transport._PinnedHTTPSConnection", new=interrupt
        ):
            with self.assertRaises(KeyboardInterrupt) as raised:
                self.fetcher().fetch(self.url, max_bytes=1024)
        self.assertIs(raised.exception, interruption)
        (watchdog,) = captured
        self.assertTrue(watchdog._timer.finished.is_set())
        watchdog._timer.join(timeout=2)
        self.assertFalse(watchdog._timer.is_alive())

    def test_fired_watchdog_closes_duplicate_without_cancellation(self):
        with socket.socket() as sock:
            watchdog = _Watchdog(Deadline(5))
            self.addCleanup(watchdog.cancel)
            watchdog.attach(sock)
            duplicate = watchdog._sock
            watchdog._fire()
            self.assertTrue(watchdog.fired)
            self.assertIsNone(watchdog._sock)
            self.assertEqual(duplicate.fileno(), -1)

    def test_attach_after_watchdog_fires_closes_duplicate(self):
        with socket.socket() as sock:
            watchdog = _Watchdog(Deadline(5))
            self.addCleanup(watchdog.cancel)
            watchdog._fire()
            duplicate = sock.dup()
            with patch.object(socket.socket, "dup", return_value=duplicate):
                watchdog.attach(sock)
            self.assertIsNone(watchdog._sock)
            self.assertEqual(duplicate.fileno(), -1)

    def test_hostname_mismatch(self):
        transport = HTTPClientTransport(self.ssl_context())
        target = ConnectTarget(
            address=ip_address(LOOPBACK),
            hostname="other.test",
            port=self.server.port,
            path="/",
            headers=(("Host", "other.test"),),
        )
        with self.assertRaises(TLSError):
            transport.open(target, Deadline(5))
        self.assertEqual(self.server.sni, ["other.test"])
        self.assertEqual(self.server.requests, [])

    def test_unverified_context_rejected(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        with self.assertRaises(ValueError):
            HTTPClientTransport(context)
        context.verify_mode = ssl.CERT_NONE
        with self.assertRaises(ValueError):
            HTTPClientTransport(context)

    def test_redirect_not_followed(self):
        self.server.handler = respond(
            b"HTTP/1.1 302 Found\r\nLocation: https://metadata.test/elsewhere\r\n"
            b"Content-Length: 0\r\n\r\n"
        )
        with self.assertRaises(RedirectNotAllowed):
            self.fetcher().fetch(self.url, max_bytes=1024)
        self.assertEqual(len(self.server.requests), 1)

    def test_proxy_environment_ignored(self):
        proxy = "http://192.0.2.1:3128"
        with patch.dict(
            environ,
            {
                "HTTPS_PROXY": proxy,
                "https_proxy": proxy,
                "ALL_PROXY": proxy,
                "all_proxy": proxy,
                "NO_PROXY": "",
                "no_proxy": "",
            },
        ):
            response = self.fetcher().fetch(self.url, max_bytes=1024)
        self.assertEqual(response.content, b'{"a": 1}')
        self.assertEqual(len(self.server.requests), 1)

    def test_size_overflow_without_content_length(self):
        self.server.handler = respond(
            b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n" + b"a" * (200 * 1024)
        )
        with self.assertRaises(ResponseTooLarge):
            self.fetcher().fetch(self.url, max_bytes=64 * 1024)

    def test_chunked_overflow(self):
        chunk = b"a" * 4096
        body = b"".join(b"%x\r\n%s\r\n" % (len(chunk), chunk) for _ in range(40)) + b"0\r\n\r\n"
        self.server.handler = respond(
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" + body
        )
        with self.assertRaises(ResponseTooLarge):
            self.fetcher().fetch(self.url, max_bytes=64 * 1024)

    def test_chunked_ok(self):
        body = b'4\r\n{"a"\r\n4\r\n: 1}\r\n0\r\n\r\n'
        self.server.handler = respond(
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" + body
        )
        self.assertEqual(self.fetcher().fetch(self.url, max_bytes=1024).content, b'{"a": 1}')

    def test_gzip_and_decompression_overflow(self):
        small = gzip.compress(b'{"a": 1}')
        self.server.handler = respond(
            b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Length: %d\r\n\r\n%s"
            % (len(small), small)
        )
        self.assertEqual(self.fetcher().fetch(self.url, max_bytes=1024).content, b'{"a": 1}')
        bomb = gzip.compress(b"\0" * (20 * 1024 * 1024))
        self.server.handler = respond(
            b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nConnection: close\r\n\r\n" + bomb
        )
        with self.assertRaises(ResponseTooLarge):
            self.fetcher().fetch(self.url, max_bytes=64 * 1024)

    def test_slow_body_deadline(self):
        """A server trickling bytes cannot extend the total deadline"""
        self.server.handler = drip(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n", 0.05)
        start = time.monotonic()
        with self.assertRaises(DeadlineExceeded):
            self.fetcher(timeout=0.5).fetch(self.url, max_bytes=64 * 1024)
        self.assertLess(time.monotonic() - start, 2)

    def test_slow_headers_deadline(self):
        """A server that trickles a header line forever cannot extend the deadline"""
        self.server.handler = drip(b"HTTP/1.1 200 OK\r\nX-Slow: ", 0.05)
        start = time.monotonic()
        with self.assertRaises(DeadlineExceeded):
            self.fetcher(timeout=0.5).fetch(self.url, max_bytes=64 * 1024)
        self.assertLess(time.monotonic() - start, 2)

    def test_no_response_deadline(self):
        self.server.handler = stall
        start = time.monotonic()
        with self.assertRaises(DeadlineExceeded):
            self.fetcher(timeout=0.5).fetch(self.url, max_bytes=1024)
        self.assertLess(time.monotonic() - start, 2)

    def test_connection_refused(self):
        closed = socket.create_server((LOOPBACK, 0))
        port = closed.getsockname()[1]
        closed.close()
        with self.assertRaises(ConnectError):
            self.fetcher().fetch(f"https://{HOSTNAME}:{port}/", max_bytes=1024)

    def test_protocol_error(self):
        self.server.handler = respond(b"garbage\r\n\r\n")
        with self.assertRaises(Exception) as ctx:
            self.fetcher().fetch(self.url, max_bytes=1024)
        self.assertEqual(getattr(ctx.exception, "reason", None), "protocol_error")
