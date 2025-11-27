from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from time import mktime
from unittest.mock import MagicMock, patch

from django.utils.timezone import now

from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import THRESHOLD_READ_ONLY_WEEKS, License
from authentik.lib.generators import generate_id

# Valid license expiry
expiry_valid = int(mktime((now() + timedelta(days=3000)).timetuple()))
# Valid license expiry, expires soon
expiry_soon = int(mktime((now() + timedelta(hours=10)).timetuple()))
# Invalid license expiry, recently expired
expiry_expired = int(mktime((now() - timedelta(hours=10)).timetuple()))
# Invalid license expiry, expired longer ago
expiry_expired_read_only = int(
    mktime((now() - timedelta(weeks=THRESHOLD_READ_ONLY_WEEKS + 1)).timetuple())
)


def enterprise_test(
    expiry: int = expiry_valid,
    internal_users: int = 100,
    external_users: int = 100,
    create_key=True,
):
    """Install testing enterprise license"""

    def wrapper_outer(func: Callable):

        @wraps(func)
        def wrapper(*args, **kwargs):
            with patch(
                "authentik.enterprise.license.LicenseKey.validate",
                MagicMock(
                    return_value=LicenseKey(
                        aud="",
                        exp=expiry,
                        name=generate_id(),
                        internal_users=internal_users,
                        external_users=external_users,
                    )
                ),
            ):
                if create_key:
                    License.objects.create(key=generate_id())
                return func(*args, **kwargs)

        return wrapper

    return wrapper_outer
