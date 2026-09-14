"""Active Directory specific"""

from collections.abc import Generator
from datetime import UTC, datetime
from enum import IntFlag
from typing import Any

from django.utils.timezone import now

from authentik.core.models import User
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.sources.ldap.models import flatten
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer

FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=UTC)
FILETIME_NEVER = 9223372036854775807


def account_expired(value: Any) -> bool:
    """Interpret accountExpires with or without ldap3's schema-aware formatting."""
    value = flatten(value)
    if value is None:
        return False
    current_time = now()
    if isinstance(value, datetime):
        # ldap3 formats zero as the FILETIME epoch and the maximum integer as datetime.max.
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        else:
            value = value.astimezone(UTC)
        if value in (FILETIME_EPOCH, datetime.max.replace(tzinfo=UTC)):
            return False
        return value <= current_time
    if isinstance(value, bool) or not isinstance(value, int | str | bytes):
        raise ValueError("Invalid accountExpires: expected an AD timestamp")
    try:
        timestamp = int(value)
    except ValueError as exc:
        raise ValueError("Invalid accountExpires: expected an AD timestamp") from exc
    if not 0 <= timestamp <= FILETIME_NEVER:
        raise ValueError("Invalid accountExpires: timestamp is outside the AD range")
    if timestamp in (0, FILETIME_NEVER):
        return False
    # Compare integers to avoid floating-point rounding and datetime overflow.
    elapsed = current_time - FILETIME_EPOCH
    current_timestamp = (elapsed.days * 86400 + elapsed.seconds) * 10000000
    current_timestamp += elapsed.microseconds * 10
    return timestamp <= current_timestamp


class UserAccountControl(IntFlag):
    """UserAccountControl attribute for Active directory users"""

    # https://docs.microsoft.com/en-us/troubleshoot/windows-server/identity
    #   /useraccountcontrol-manipulate-account-properties

    SCRIPT = 1
    ACCOUNTDISABLE = 2
    HOMEDIR_REQUIRED = 8
    LOCKOUT = 16
    PASSWD_NOTREQD = 32
    PASSWD_CANT_CHANGE = 64
    ENCRYPTED_TEXT_PWD_ALLOWED = 128
    TEMP_DUPLICATE_ACCOUNT = 256
    NORMAL_ACCOUNT = 512
    INTERDOMAIN_TRUST_ACCOUNT = 2048
    WORKSTATION_TRUST_ACCOUNT = 4096
    SERVER_TRUST_ACCOUNT = 8192
    DONT_EXPIRE_PASSWORD = 65536
    MNS_LOGON_ACCOUNT = 131072
    SMARTCARD_REQUIRED = 262144
    TRUSTED_FOR_DELEGATION = 524288
    NOT_DELEGATED = 1048576
    USE_DES_KEY_ONLY = 2097152
    DONT_REQ_PREAUTH = 4194304
    PASSWORD_EXPIRED = 8388608
    TRUSTED_TO_AUTH_FOR_DELEGATION = 16777216
    PARTIAL_SECRETS_ACCOUNT = 67108864


class MicrosoftActiveDirectory(BaseLDAPSynchronizer):
    """Microsoft-specific LDAP"""

    @staticmethod
    def name() -> str:
        return "microsoft_ad"

    def get_objects(self, **kwargs) -> Generator:
        yield None

    def sync(self, attributes: dict[str, Any], user: User, created: bool):
        self.ms_check_pwd_last_set(attributes, user, created)

    def ms_check_pwd_last_set(self, attributes: dict[str, Any], user: User, created: bool):
        """Check pwdLastSet"""
        if "pwdLastSet" not in attributes:
            return
        pwd_last_set: datetime = attributes.get("pwdLastSet", datetime.now())
        pwd_last_set = pwd_last_set.replace(tzinfo=UTC)
        if created or pwd_last_set >= user.password_change_date:
            self._task.info(f"'{user.username}': Reset user's password")
            self._logger.debug(
                "Reset user's password",
                user=user.username,
                created=created,
                pwd_last_set=pwd_last_set,
            )
            user.set_unusable_password()
            user.save()

    def get_account_active(self, attributes: dict[str, Any]) -> bool | None:
        """Combine AD restrictions before saving, preserving state when UAC is unavailable."""
        try:
            expired = account_expired(attributes.get("accountExpires"))
        except ValueError as exc:
            raise StopSync(exc) from exc
        if expired:
            return False
        uac_bit = flatten(attributes.get("userAccountControl"))
        if uac_bit is None:
            return None
        uac = UserAccountControl(int(uac_bit))
        return (
            UserAccountControl.ACCOUNTDISABLE not in uac and UserAccountControl.LOCKOUT not in uac
        )
