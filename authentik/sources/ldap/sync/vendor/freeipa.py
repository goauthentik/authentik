"""FreeIPA specific"""

from collections.abc import Generator
from typing import Any

from authentik.core.models import User
from authentik.sources.ldap.models import flatten
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer


class FreeIPA(BaseLDAPSynchronizer):
    """FreeIPA-specific LDAP"""

    @staticmethod
    def name() -> str:
        return "freeipa"

    def get_objects(self, **kwargs) -> Generator:
        yield None

    def sync(self, attributes: dict[str, Any], user: User, created: bool):
        self.check_pwd_last_set("krbLastPwdChange", attributes, user, created)
        self.check_nsaccountlock(attributes, user)

    def check_nsaccountlock(self, attributes: dict[str, Any], user: User):
        """https://www.port389.org/docs/389ds/howto/howto-account-inactivation.html"""
        # This is more of a 389-ds quirk rather than FreeIPA, but FreeIPA uses
        # 389-ds and this will trigger regardless
        if "nsaccountlock" not in attributes:
            return
        # For some reason, nsaccountlock is not defined properly in the schema as bool
        # hence we get it as a list of strings
        _is_locked = str(flatten(attributes.get("nsaccountlock", ["FALSE"])))
        # So we have to attempt to convert it to a bool
        is_locked = _is_locked.lower() == "true"
        # And then invert it since freeipa saves locked and we save active
        is_active = not is_locked
        if is_active != user.is_active:
            user.is_active = is_active
            user.save()
