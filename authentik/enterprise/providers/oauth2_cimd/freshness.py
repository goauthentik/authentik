"""HTTP freshness lifetime (RFC 9111 section 4.2), clamped to local bounds"""

from collections.abc import Mapping
from dataclasses import dataclass
from email.utils import parsedate_to_datetime

from authentik.enterprise.providers.oauth2_cimd.constants import DEFAULT_TTL, MAX_TTL, MIN_TTL

MAX_DELTA_DIGITS = 10


@dataclass(frozen=True)
class Freshness:
    """How long a response may be cached, and which header decided it"""

    ttl: int
    # One of: no_store, no_cache, invalid_age, max_age, expires, default. Safe as a log field.
    source: str


def _directives(header: str) -> dict[str, str | None]:
    directives: dict[str, str | None] = {}
    for part in header.split(","):
        name, sep, arg = part.strip().partition("=")
        name = name.strip().lower()
        if not name:
            continue
        value = arg.strip().strip('"') if sep else None
        if name in directives and directives[name] != value:
            # Conflicting duplicates make the response stale (RFC 9111 section 4.2.1)
            directives[name] = ""
        else:
            directives[name] = value
    return directives


def _delta_seconds(value: str | None) -> int | None:
    """Accept at most ten ASCII decimal digits, without unbounded integer conversion."""
    if not value or len(value) > MAX_DELTA_DIGITS or not value.isascii() or not value.isdecimal():
        return None
    return int(value)


def _http_date(value: str | None) -> float | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except TypeError, ValueError, IndexError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.timestamp()


def freshness(
    headers: Mapping[str, str],
    now: float,
    *,
    response_delay: float = 0,
    minimum: int = MIN_TTL,
    maximum: int = MAX_TTL,
    default: int = DEFAULT_TTL,
) -> Freshness:
    """Freshness lifetime of a response from its (lowercase-keyed) headers.

    `no-store` and `no-cache` still get `minimum`: the document was validated
    and caching it briefly bounds the fetch rate. Without any cache policy,
    `default` applies. The result is always within [minimum, maximum]."""

    def clamp(seconds: float, source: str) -> Freshness:
        return Freshness(ttl=int(min(max(seconds, minimum), maximum)), source=source)

    directives = _directives(headers.get("cache-control", ""))
    if "no-store" in directives:
        return clamp(0, "no_store")
    if "no-cache" in directives:
        # We never revalidate, so no-cache is treated like no-store
        return clamp(0, "no_cache")
    age = _delta_seconds(headers.get("age", "0"))
    if age is None:
        return clamp(0, "invalid_age")
    date = _http_date(headers.get("date"))
    current_age = max(0, now - date if date is not None else 0, age + max(0, response_delay))
    if "max-age" in directives:
        return clamp((_delta_seconds(directives["max-age"]) or 0) - current_age, "max_age")
    if "expires" in headers:
        expires = _http_date(headers["expires"])
        if expires is None:
            # Invalid Expires values mean "already expired"
            return clamp(0, "expires")
        return clamp(expires - (date if date is not None else now) - current_age, "expires")
    return clamp(default - current_age, "default")
