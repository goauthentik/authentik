"""Time utilities"""

import datetime
from hashlib import sha256
from random import randrange, seed
from socket import getfqdn

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ALLOWED_KEYS = (
    "microseconds",
    "milliseconds",
    "seconds",
    "minutes",
    "hours",
    "days",
    "weeks",
)


def timedelta_string_validator(value: str):
    """Validator for Django that checks if value can be parsed with `timedelta_from_string`"""
    try:
        timedelta_from_string(value)
    except ValueError as exc:
        raise ValidationError(
            _("%(value)s is not in the correct format of 'hours=3;minutes=1'."),
            params={"value": value},
        ) from exc


def timedelta_from_string(expr: str) -> datetime.timedelta:
    """Convert a string with the format of 'hours=1;minute=3;seconds=5' to a
    `datetime.timedelta` Object with hours = 1, minutes = 3, seconds = 5"""
    kwargs = {}
    for duration_pair in expr.split(";"):
        key, value = duration_pair.split("=")
        if key.lower() not in ALLOWED_KEYS:
            continue
        kwargs[key.lower()] = float(value.strip())
    if len(kwargs) < 1:
        raise ValueError("No valid keys to pass to timedelta")
    return datetime.timedelta(**kwargs)


def fqdn_rand(task: str, stop: int = 60) -> int:
    """Get a random number within max based on the FQDN and task name"""
    entropy = f"{getfqdn()}:{task}"
    hasher = sha256()
    hasher.update(entropy.encode("utf-8"))
    seed(hasher.hexdigest())
    return randrange(0, stop)  # nosec
