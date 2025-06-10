"""Time utilities"""

from datetime import datetime, timedelta

from django.utils.timezone import now


def get_time_string(delta: timedelta | datetime | None = None) -> str:
    """Get Data formatted in SAML format"""
    if delta is None:
        delta = timedelta()
    if isinstance(delta, timedelta):
        final = now() + delta
    else:
        final = delta
    return final.strftime("%Y-%m-%dT%H:%M:%SZ")
