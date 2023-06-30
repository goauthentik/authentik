"""FreeIPA specific"""
from datetime import datetime
from typing import Any, Generator

from pytz import UTC

from authentik.core.models import User
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer


class FreeIPA(BaseLDAPSynchronizer):
    """FreeIPA-specific LDAP"""

    @staticmethod
    def name() -> str:
        return "freeipa"

    def get_objects(self, **kwargs) -> Generator:
        yield None

    def sync(self, attributes: dict[str, Any], user: User, created: bool):
        self.check_pwd_last_set(attributes, user, created)

    def check_pwd_last_set(self, attributes: dict[str, Any], user: User, created: bool):
        """Check krbLastPwdChange"""
        if "krbLastPwdChange" not in attributes:
            return
        pwd_last_set: datetime = attributes.get("krbLastPwdChange", datetime.now())
        pwd_last_set = pwd_last_set.replace(tzinfo=UTC)
        if created or pwd_last_set >= user.password_change_date:
            self.message(f"'{user.username}': Reset user's password")
            self._logger.debug(
                "Reset user's password",
                user=user.username,
                created=created,
                pwd_last_set=pwd_last_set,
            )
            user.set_unusable_password()
            user.save()
