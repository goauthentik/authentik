"""Network layer for fetches of untrusted URLs.

The fetcher resolves and validates addresses itself and hands the transport a
single, already-validated IP address. The transport connects to exactly that
address; it never resolves the hostname again, so DNS rebinding between the check
and the connection is impossible. TLS still verifies the certificate against the
original hostname and sends it as SNI.

This module deliberately uses `http.client` rather than `requests`/`urllib3`:
`http.client` never follows redirects, never consults proxy environment
variables, never stores cookies, and never decompresses response bodies.
"""

import socket
import ssl
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from contextlib import ExitStack
from dataclasses import dataclass
from http.client import HTTPException, HTTPResponse, HTTPSConnection, IncompleteRead
from ipaddress import IPv6Address, ip_address
from time import monotonic
from typing import Protocol

from authentik.lib.utils.untrusted_fetch.errors import (
    ConnectError,
    DeadlineExceeded,
    ProtocolError,
    ResolutionError,
    TLSError,
)
from authentik.lib.utils.untrusted_fetch.policy import IPAddress

# Upper bound on the number of addresses considered per hostname
MAX_RESOLVED_ADDRESSES = 16


class Deadline:
    """A monotonic total deadline"""

    def __init__(self, seconds: float, clock: Callable[[], float] = monotonic):
        self._clock = clock
        self.expires_at = clock() + seconds

    def remaining(self) -> float:
        """Seconds left; raises DeadlineExceeded when none are left"""
        left = self.expires_at - self._clock()
        if left <= 0:
            raise DeadlineExceeded("Deadline exceeded")
        return left

    def seconds_left(self) -> float:
        """Seconds left, never negative and never raising"""
        return max(self.expires_at - self._clock(), 0.0)

    def expired(self) -> bool:
        """Whether the deadline has passed"""
        return self._clock() >= self.expires_at


class Resolver(Protocol):
    """Resolves a hostname to candidate addresses"""

    def resolve(self, hostname: str, port: int, deadline: Deadline) -> list[IPAddress]: ...


@dataclass(frozen=True)
class ConnectTarget:
    """A request to send to one specific, already validated address"""

    address: IPAddress
    hostname: str
    port: int
    path: str
    headers: tuple[tuple[str, str], ...]


class TransportResponse(Protocol):
    """A streaming response as returned by a transport"""

    status: int
    headers: list[tuple[str, str]]

    def read_chunk(self, max_bytes: int, deadline: Deadline) -> bytes:
        """Read up to `max_bytes` of the raw (still content-encoded) body; b"" at EOF"""
        ...

    def close(self) -> None: ...


class Transport(Protocol):
    """Sends a GET request to a single validated address"""

    def open(self, target: ConnectTarget, deadline: Deadline) -> TransportResponse: ...


class SystemResolver:
    """Resolve within the deadline, with at most max_workers outstanding lookups.

    Timed-out or interrupted callers leave their lookup running, retaining its
    slot until completion. Never cancel queued futures: cancellation completes
    the future without removing its work item from the executor's queue.
    Answers with more than 16 distinct addresses are rejected, not truncated.
    """

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="untrusted-fetch-dns"
        )
        self._slots = threading.BoundedSemaphore(max_workers)

    def _lookup(self, hostname: str, port: int) -> list[IPAddress]:
        infos = socket.getaddrinfo(
            hostname, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        addresses: list[IPAddress] = []
        for family, _, _, _, sockaddr in infos:
            if family not in (socket.AF_INET, socket.AF_INET6):
                continue
            raw = str(sockaddr[0])
            if family == socket.AF_INET6 and sockaddr[3]:  # type: ignore[misc]
                # Keep the scope so that the policy rejects scoped addresses
                raw = f"{raw.split('%', maxsplit=1)[0]}%{sockaddr[3]}"  # type: ignore[misc]
            addr = ip_address(raw)
            if addr not in addresses:
                addresses.append(addr)
                if len(addresses) > MAX_RESOLVED_ADDRESSES:
                    raise ResolutionError("Hostname resolved to too many addresses")
        return addresses

    def resolve(self, hostname: str, port: int, deadline: Deadline) -> list[IPAddress]:
        if not self._slots.acquire(timeout=deadline.remaining()):
            raise DeadlineExceeded("Timed out waiting for DNS capacity")
        try:
            deadline.remaining()
            future = self._executor.submit(self._lookup, hostname, port)
        except BaseException:
            self._slots.release()
            raise
        future.add_done_callback(lambda completed: self._slots.release())
        try:
            addresses = future.result(timeout=deadline.remaining())
        except FutureTimeoutError as exc:
            raise DeadlineExceeded("DNS resolution timed out") from exc
        except (OSError, UnicodeError, ValueError) as exc:
            raise ResolutionError("DNS resolution failed") from exc
        if not addresses:
            raise ResolutionError("Hostname did not resolve")
        return addresses


def default_ssl_context() -> ssl.SSLContext:
    """TLS context with certificate and hostname verification"""
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context


class _PinnedHTTPSConnection(HTTPSConnection):
    """HTTPS connection to a fixed IP that verifies TLS against a separate hostname"""

    def __init__(
        self,
        address: IPAddress,
        hostname: str,
        port: int,
        context: ssl.SSLContext,
        timeout: float,
        watchdog: _Watchdog,
    ):
        super().__init__(str(address), port, timeout=timeout, context=context)
        self._watchdog = watchdog
        self._pinned_address = address
        self._tls_hostname = hostname
        self._tls_context = context

    def connect(self) -> None:
        family = (
            socket.AF_INET6 if isinstance(self._pinned_address, IPv6Address) else socket.AF_INET
        )
        sock = socket.socket(family, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        try:
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._watchdog.attach(sock)
            try:
                sock.connect((str(self._pinned_address), self.port))
            except TimeoutError as exc:
                raise DeadlineExceeded("Connection timed out") from exc
            except OSError as exc:
                raise ConnectError("Connection failed") from exc
            try:
                self.sock = self._tls_context.wrap_socket(sock, server_hostname=self._tls_hostname)
            except TimeoutError as exc:
                raise DeadlineExceeded("TLS handshake timed out") from exc
            except (ssl.SSLError, ssl.CertificateError) as exc:
                raise TLSError("TLS verification failed") from exc
            except OSError as exc:
                raise ConnectError("Connection failed during TLS handshake") from exc
        except BaseException:
            sock.close()
            raise


class _Watchdog:
    """Forcibly shuts down a connection when the deadline passes.

    Socket timeouts bound each blocking call, but a peer that trickles bytes can
    keep a sequence of calls alive indefinitely; this enforces the total deadline.
    It holds a duplicate of the socket so it keeps working after the TLS wrap
    detaches the original socket object."""

    def __init__(self, deadline: Deadline):
        self.fired = False
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()
        self._timer = threading.Timer(deadline.seconds_left(), self._fire)
        self._timer.daemon = True
        self._timer.start()

    def attach(self, sock: socket.socket) -> None:
        with self._lock:
            self._sock = sock.dup()
            if self.fired:
                self._shutdown()

    def _shutdown(self) -> None:
        if self._sock is None:
            return
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            self._sock.close()
            self._sock = None

    def _fire(self) -> None:
        with self._lock:
            self.fired = True
            self._shutdown()

    def cancel(self) -> None:
        self._timer.cancel()
        with self._lock:
            if self._sock is not None:
                self._sock.close()
                self._sock = None


class _HTTPClientResponse:
    def __init__(
        self,
        connection: _PinnedHTTPSConnection,
        response: HTTPResponse,
        watchdog: _Watchdog,
    ):
        self._connection = connection
        self._response = response
        self._watchdog = watchdog
        self.status = response.status
        self.headers = list(response.getheaders())

    def read_chunk(self, max_bytes: int, deadline: Deadline) -> bytes:
        sock = self._connection.sock
        if sock is not None:
            sock.settimeout(deadline.remaining())
        try:
            chunk = self._response.read1(max_bytes)
            if not chunk and self._response.length:
                raise IncompleteRead(b"", self._response.length)
            return chunk
        except TimeoutError as exc:
            raise DeadlineExceeded("Read timed out") from exc
        except (OSError, HTTPException, ValueError) as exc:
            if self._watchdog.fired or deadline.expired():
                raise DeadlineExceeded("Deadline exceeded while reading") from exc
            raise ProtocolError("Failed to read response body") from exc

    def close(self) -> None:
        self._watchdog.cancel()
        self._response.close()
        self._connection.close()


class HTTPClientTransport:
    """Real network transport: HTTPS to a pinned address via `http.client`"""

    def __init__(self, ssl_context: ssl.SSLContext | None = None):
        self._ssl_context = ssl_context or default_ssl_context()
        if (
            not self._ssl_context.check_hostname
            or self._ssl_context.verify_mode != ssl.CERT_REQUIRED
        ):
            raise ValueError("Untrusted fetches require certificate and hostname verification")

    def open(self, target: ConnectTarget, deadline: Deadline) -> TransportResponse:
        timeout = deadline.remaining()
        watchdog = _Watchdog(deadline)
        try:
            with ExitStack() as cleanup:
                cleanup.callback(watchdog.cancel)
                connection = _PinnedHTTPSConnection(
                    target.address,
                    target.hostname,
                    target.port,
                    self._ssl_context,
                    timeout=timeout,
                    watchdog=watchdog,
                )
                cleanup.callback(connection.close)
                connection.connect()
                connection.putrequest("GET", target.path, skip_host=True, skip_accept_encoding=True)
                for name, value in target.headers:
                    connection.putheader(name, value)
                connection.endheaders()
                connection.sock.settimeout(deadline.remaining())
                response = connection.getresponse()
                cleanup.callback(response.close)
                result = _HTTPClientResponse(connection, response, watchdog)
                cleanup.pop_all()
                return result
        except (ConnectError, TLSError) as exc:
            if watchdog.fired or deadline.expired():
                raise DeadlineExceeded("Deadline exceeded while connecting") from exc
            raise
        except TimeoutError as exc:
            raise DeadlineExceeded("Timed out waiting for response") from exc
        except (OSError, HTTPException, ValueError) as exc:
            if watchdog.fired or deadline.expired():
                raise DeadlineExceeded("Deadline exceeded waiting for response") from exc
            raise ProtocolError("Invalid HTTP response") from exc
