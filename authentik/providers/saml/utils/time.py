"""Time utilities"""

import datetime


def get_time_string(delta: datetime.timedelta | None = None) -> str:
    """Get Data formatted in SAML format"""
    if delta is None:
        delta = datetime.timedelta()
    now = datetime.datetime.now()
    final = now + delta
    return final.strftime("%Y-%m-%dT%H:%M:%SZ")
