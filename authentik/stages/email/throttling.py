"""Shared email attempt rate limiting."""

import math
from datetime import UTC, datetime
from hashlib import sha256

from django.core.cache import cache
from django.utils.timezone import now

from authentik.lib.utils.time import timedelta_from_string

EMAIL_RECOVERY_MAX_ATTEMPTS = 5
EMAIL_RECOVERY_CACHE_TIMEOUT = "minutes=5"
EMAIL_RECOVERY_CACHE_KEY = "goauthentik.io/stages/email/stage/"


def email_cache_key(email: str) -> str:
    """Use the same case-insensitive address key for all email stages."""
    return EMAIL_RECOVERY_CACHE_KEY + sha256(email.lower().encode("utf-8")).hexdigest()


def email_is_rate_limited(
    email: str,
    max_attempts: int = EMAIL_RECOVERY_MAX_ATTEMPTS,
    cache_timeout: str = EMAIL_RECOVERY_CACHE_TIMEOUT,
) -> int | None:
    """Record an attempt, or return the remaining wait in minutes.

    OTP sends use the email stage's default policy. Recovery stages can pass
    their configured limits. Both paths share the existing attempt history.
    """
    cache_key = email_cache_key(email)
    attempts = cache.get(cache_key, [])
    cache_timeout_delta = timedelta_from_string(cache_timeout)

    # Keep enough history for every policy that has used this address. A caller
    # with a short window must not erase attempts needed by a longer window.
    retention_key = cache_key + "/retention"
    retention_seconds = max(cache.get(retention_key, 0), int(cache_timeout_delta.total_seconds()))
    _now = now()
    start_window = _now - cache_timeout_delta

    # Convert unix timestamps to datetime objects for comparison
    recent_attempts_in_window = [
        datetime.fromtimestamp(attempt, UTC)
        for attempt in attempts
        if datetime.fromtimestamp(attempt, UTC) > start_window
    ]

    retained_attempts = [
        attempt for attempt in attempts if attempt > _now.timestamp() - retention_seconds
    ]
    minutes_left = None
    if len(recent_attempts_in_window) >= max_attempts:
        retry_after = (min(recent_attempts_in_window) + cache_timeout_delta) - _now
        minutes_left = max(1, math.ceil(retry_after.total_seconds() / 60))
    else:
        retained_attempts.append(_now.timestamp())

    cache.set(retention_key, retention_seconds, retention_seconds)
    cache.set(cache_key, retained_attempts, retention_seconds)
    return minutes_left
