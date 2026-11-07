"""Destination policy for fetches of untrusted URLs"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network

from structlog.stdlib import get_logger

LOGGER = get_logger()

type IPAddress = IPv4Address | IPv6Address
type IPNetwork = IPv4Network | IPv6Network

# Destinations that are never reachable, not even when an operator lists them as
# permitted private destinations: loopback, unspecified, link-local, multicast,
# reserved/broadcast, deprecated IPv6 forms, and cloud metadata services.
ALWAYS_BLOCKED_NETWORKS: tuple[IPNetwork, ...] = tuple(
    ip_network(net)
    for net in (
        # IPv4
        "0.0.0.0/8",  # "this network", unspecified
        "127.0.0.0/8",  # loopback
        "169.254.0.0/16",  # link-local, incl. 169.254.169.254 (AWS/GCP/Azure/OCI metadata)
        "224.0.0.0/4",  # multicast
        "240.0.0.0/4",  # reserved, incl. 255.255.255.255 broadcast
        "100.100.100.200/32",  # Alibaba Cloud metadata
        "168.63.129.16/32",  # Azure WireServer
        "192.0.0.192/32",  # Oracle Cloud legacy metadata
        # IPv6
        "::/128",  # unspecified
        "::1/128",  # loopback
        "::/96",  # deprecated IPv4-compatible addresses (::a.b.c.d)
        "fe80::/10",  # link-local
        "fec0::/10",  # deprecated site-local
        "ff00::/8",  # multicast
        "fd00:ec2::/32",  # AWS IPv6 instance services (fd00:ec2::254 metadata)
        "fd20:ce::254/128",  # GCP IPv6 metadata
    )
)

# IPv6 prefixes whose last 32 bits are an embedded IPv4 address that the
# connection effectively reaches. These are judged by the embedded address.
_EMBEDDED_V4_TRANSLATION_NETWORKS: tuple[IPv6Network, ...] = (
    IPv6Network("::ffff:0:0/96"),  # IPv4-mapped
    IPv6Network("::ffff:0:0:0/96"),  # IPv4-translated (SIIT)
    IPv6Network("64:ff9b::/96"),  # NAT64 well-known prefix
)


class DestinationPolicyError(ValueError):
    """Raised when the configured private destination allowlist is malformed"""


def _in_any(address: IPAddress, networks: Iterable[IPNetwork]) -> bool:
    # ipaddress does not compare versions in `in`, so an IPv4 address could
    # otherwise match an IPv6 network such as ::/96.
    return any(address.version == net.version and address in net for net in networks)


def _normalize_hostname(hostname: str) -> str:
    return hostname.rstrip(".").lower()


def _embedded_ipv4(address: IPv6Address) -> IPv4Address | None:
    for network in _EMBEDDED_V4_TRANSLATION_NETWORKS:
        if address in network:
            return IPv4Address(int(address) & 0xFFFFFFFF)
    return None


def _tunnel_ipv4s(address: IPv6Address) -> list[IPv4Address]:
    """IPv4 addresses embedded in tunneling forms (6to4, Teredo)"""
    found: list[IPv4Address] = []
    if address.sixtofour:
        found.append(address.sixtofour)
    if address.teredo:
        found.extend(address.teredo)
    return found


@dataclass(frozen=True)
class AddressDecision:
    """Outcome of checking a single address"""

    allowed: bool
    reason: str


@dataclass(frozen=True)
class DestinationPolicy:
    """Decide whether a resolved address may be connected to.

    Public (globally routable) addresses are allowed. Non-public and special-use
    addresses are denied unless `allowed_networks` contains them or the requested
    hostname is listed in `allowed_hostnames`. Addresses in
    `ALWAYS_BLOCKED_NETWORKS` are denied regardless of the allowlist.
    """

    allowed_networks: tuple[IPNetwork, ...] = field(default_factory=tuple)
    allowed_hostnames: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_entries(cls, entries: Iterable[str]) -> DestinationPolicy:
        """Build a policy from a list of CIDRs, IP addresses, or hostnames"""
        networks: list[IPNetwork] = []
        hostnames: set[str] = set()
        for raw in entries:
            entry = str(raw).strip()
            if not entry:
                continue
            try:
                networks.append(ip_network(entry, strict=False))
                continue
            except ValueError:
                pass
            if "/" in entry or ":" in entry or not entry.isascii():
                raise DestinationPolicyError(f"Invalid private destination entry: {entry!r}")
            hostnames.add(_normalize_hostname(entry))
        return cls(allowed_networks=tuple(networks), allowed_hostnames=frozenset(hostnames))

    @classmethod
    def from_config_value(cls, value: object) -> DestinationPolicy:
        """Build a policy from a config value (a list, or a comma-separated string).

        Invalid entries are logged and skipped so that a typo never widens access."""
        if value is None:
            items: list[str] = []
        elif isinstance(value, str):
            items = value.split(",")
        elif isinstance(value, Iterable):
            items = [str(v) for v in value]
        else:
            items = [str(value)]
        valid: list[str] = []
        for item in items:
            try:
                cls.from_entries([item])
            except DestinationPolicyError as exc:
                LOGGER.warning("Ignoring invalid private destination entry", error=str(exc))
                continue
            valid.append(item)
        return cls.from_entries(valid)

    def hostname_allowed(self, hostname: str) -> bool:
        """Whether the hostname is listed as a permitted private destination"""
        return _normalize_hostname(hostname) in self.allowed_hostnames

    def check(self, address: IPAddress, hostname: str | None = None) -> AddressDecision:
        """Check whether `address` (resolved for `hostname`) may be connected to"""
        if isinstance(address, IPv6Address):
            if address.scope_id:
                return AddressDecision(False, "scoped_address")
            embedded = _embedded_ipv4(address)
            if embedded is not None:
                return self.check(embedded, hostname)
        if _in_any(address, ALWAYS_BLOCKED_NETWORKS):
            return AddressDecision(False, "always_blocked")
        if isinstance(address, IPv6Address):
            for tunneled in _tunnel_ipv4s(address):
                if _in_any(tunneled, ALWAYS_BLOCKED_NETWORKS):
                    return AddressDecision(False, "always_blocked")
        if address.is_global:
            return AddressDecision(True, "public")
        if hostname is not None and self.hostname_allowed(hostname):
            return AddressDecision(True, "allowed_hostname")
        if _in_any(address, self.allowed_networks):
            return AddressDecision(True, "allowed_network")
        return AddressDecision(False, "private")

    def check_str(self, address: str, hostname: str | None = None) -> AddressDecision:
        """Check an address given as a string"""
        try:
            parsed = ip_address(address)
        except ValueError:
            return AddressDecision(False, "invalid_address")
        return self.check(parsed, hostname)
