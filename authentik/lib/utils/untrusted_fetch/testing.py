"""Deterministic resolver and transport for tests. Nothing here touches the network."""

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from ipaddress import ip_address

from authentik.lib.utils.untrusted_fetch import fetcher as fetcher_module
from authentik.lib.utils.untrusted_fetch.errors import (
    ConnectError,
    DeadlineExceeded,
    ResolutionError,
    UntrustedFetchError,
)
from authentik.lib.utils.untrusted_fetch.fetcher import UntrustedURLFetcher
from authentik.lib.utils.untrusted_fetch.policy import DestinationPolicy, IPAddress
from authentik.lib.utils.untrusted_fetch.transport import ConnectTarget, Deadline

# A globally routable address that mocks resolve to by default. It is never contacted.
DEFAULT_PUBLIC_ADDRESS = "93.184.215.14"


class FakeClock:
    """Manually advanced monotonic clock"""

    def __init__(self, start: float = 1000.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        """Move the clock forward"""
        self.now += seconds


class StaticResolver:
    """Resolve hostnames from a fixed table.

    Each value is either a list of addresses, or (via `sequence`) a list of
    answers returned on successive lookups, the last one repeating. Unknown
    hostnames resolve to `default` if set, else fail."""

    def __init__(
        self,
        records: Mapping[str, Sequence[str]] | None = None,
        *,
        default: Sequence[str] | None = None,
    ):
        self._answers: dict[str, list[list[str]]] = {
            host.lower(): [list(addrs)] for host, addrs in (records or {}).items()
        }
        self._default = list(default) if default is not None else None
        self.calls: list[str] = []

    @classmethod
    def sequence(cls, records: Mapping[str, Sequence[Sequence[str]]]) -> StaticResolver:
        """Resolver that returns a different answer on each lookup"""
        resolver = cls()
        resolver._answers = {
            host.lower(): [list(answer) for answer in answers] for host, answers in records.items()
        }
        return resolver

    def resolve(self, hostname: str, port: int, deadline: Deadline) -> list[IPAddress]:
        deadline.remaining()
        self.calls.append(hostname)
        answers = self._answers.get(hostname.lower())
        if answers is None:
            if self._default is None:
                raise ResolutionError("Hostname did not resolve")
            return [ip_address(a) for a in self._default]
        answer = answers.pop(0) if len(answers) > 1 else answers[0]
        if not answer:
            raise ResolutionError("Hostname did not resolve")
        return [ip_address(a) for a in answer]


@dataclass
class MockResponse:
    """A canned response. `body` may be bytes or a list of chunks.

    `chunk_delay` advances the transport's FakeClock before each chunk, to
    simulate slow responses without sleeping."""

    status: int = 200
    headers: Sequence[tuple[str, str]] | Mapping[str, str] = field(default_factory=dict)
    body: bytes | Sequence[bytes] = b""
    chunk_delay: float = 0.0
    header_delay: float = 0.0


class _MockStream:
    def __init__(self, response: MockResponse, clock: FakeClock | None):
        self.status = response.status
        raw_headers = response.headers
        self.headers = list(
            raw_headers.items() if isinstance(raw_headers, Mapping) else raw_headers
        )
        body = response.body
        self._chunks = [body] if isinstance(body, bytes) else list(body)
        self._delay = response.chunk_delay
        self._clock = clock
        self._buffer = b""
        self.closed = False

    def read_chunk(self, max_bytes: int, deadline: Deadline) -> bytes:
        if not self._buffer:
            if not self._chunks:
                return b""
            if self._clock is not None and self._delay:
                self._clock.advance(self._delay)
            if deadline.expired():
                raise DeadlineExceeded("Read timed out")
            self._buffer = self._chunks.pop(0)
        data, self._buffer = self._buffer[:max_bytes], self._buffer[max_bytes:]
        return data

    def close(self) -> None:
        self.closed = True


class MockTransport:
    """Serve canned responses keyed by URL ("https://host[:port]/path").

    Records every request in `requests`. Addresses in `unreachable` raise
    ConnectError, to exercise fallback across resolved addresses."""

    def __init__(
        self,
        responses: Mapping[str, MockResponse | UntrustedFetchError] | None = None,
        *,
        clock: FakeClock | None = None,
        unreachable: Sequence[str] = (),
    ):
        self.responses: dict[str, MockResponse | UntrustedFetchError] = dict(responses or {})
        self.clock = clock
        self.unreachable = {ip_address(a) for a in unreachable}
        self.requests: list[ConnectTarget] = []
        self.streams: list[_MockStream] = []

    def add(self, url: str, response: MockResponse | UntrustedFetchError) -> None:
        """Register a response"""
        self.responses[url] = response

    def open(self, target: ConnectTarget, deadline: Deadline) -> _MockStream:
        deadline.remaining()
        self.requests.append(target)
        if target.address in self.unreachable:
            raise ConnectError("Connection failed")
        host = dict(target.headers)["Host"]
        response = self.responses.get(f"https://{host}{target.path}")
        if response is None:
            response = MockResponse(status=404)
        if isinstance(response, UntrustedFetchError):
            raise response
        if self.clock is not None and response.header_delay:
            self.clock.advance(response.header_delay)
            deadline.remaining()
        stream = _MockStream(response, self.clock)
        self.streams.append(stream)
        return stream


def mock_fetcher(
    responses: Mapping[str, MockResponse | UntrustedFetchError] | None = None,
    *,
    records: Mapping[str, Sequence[str]] | None = None,
    policy: DestinationPolicy | None = None,
    **kwargs,
) -> tuple[UntrustedURLFetcher, MockTransport]:
    """A fetcher with a FakeClock, StaticResolver and MockTransport.

    Hostnames without a record resolve to DEFAULT_PUBLIC_ADDRESS."""
    clock = kwargs.pop("clock", None) or FakeClock()
    transport = MockTransport(responses, clock=clock)
    resolver = kwargs.pop("resolver", None) or StaticResolver(
        records, default=[DEFAULT_PUBLIC_ADDRESS]
    )
    fetcher = UntrustedURLFetcher(
        policy=policy, resolver=resolver, transport=transport, clock=clock, **kwargs
    )
    return fetcher, transport


@contextmanager
def use_fetcher(fetcher: UntrustedURLFetcher) -> Iterator[UntrustedURLFetcher]:
    """Make `get_untrusted_fetcher()` return `fetcher` within the block"""
    previous = fetcher_module._fetcher_override
    fetcher_module._fetcher_override = fetcher
    try:
        yield fetcher
    finally:
        fetcher_module._fetcher_override = previous


__all__ = [
    "DEFAULT_PUBLIC_ADDRESS",
    "FakeClock",
    "MockResponse",
    "MockTransport",
    "StaticResolver",
    "mock_fetcher",
    "use_fetcher",
]
