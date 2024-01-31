"""Time utilities"""

import datetime
from typing import Optional


def get_time_string(delta: Optional[datetime.timedelta] = None) -> str:
    """Get Data formatted in SAML format"""
    if delta is None:
        delta = datetime.timedelta()
    now = datetime.datetime.now()
    final = now + delta
    return final.strftime("%Y-%m-%dT%H:%M:%SZ")
