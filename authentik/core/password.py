"""Django user password APIs backed by a password device."""

from datetime import datetime

from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, check_password
from django.contrib.auth.models import AbstractUser
from django.db import router, transaction
from django.utils.timezone import now


class PasswordUser(AbstractUser):
    """Keep Django's set-then-save contract while storing credentials on a device."""

    _pending_password: tuple[str, datetime] | None = None

    class Meta:
        abstract = True

    @property
    def password(self) -> str:
        if self._pending_password is not None:
            return self._pending_password[0]
        device = getattr(self, "password_device", None)
        return device.password if device else UNUSABLE_PASSWORD_PREFIX

    @password.setter
    def password(self, password_hash: str):
        self._pending_password = (password_hash, now())

    @property
    def password_change_date(self) -> datetime:
        if self._pending_password is not None:
            return self._pending_password[1]
        device = getattr(self, "password_device", None)
        return device.password_change_date if device else self.date_joined

    def save(self, *args, **kwargs):
        from authentik.stages.password.models import PasswordDevice

        update_fields = kwargs.get("update_fields")
        save_password = self._pending_password is not None and (
            update_fields is None or "password" in update_fields
        )
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) - {"password", "password_change_date"}
        if not save_password:
            return super().save(*args, **kwargs)
        using = kwargs.get("using") or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=using):
            super().save(*args, **kwargs)
            password, changed_at = self._pending_password
            self.password_device = PasswordDevice.save_password_hash(
                self, password, changed_at, using
            )
        self._pending_password = None
        return None

    def refresh_from_db(self, using=None, fields=None, from_queryset=None):
        super().refresh_from_db(using=using, fields=fields, from_queryset=from_queryset)
        if fields is None:
            self._pending_password = None
            self._password = None

    def set_password(self, raw_password, signal=True, sender=None, request=None):
        if self.pk and signal:
            from authentik.core.signals import password_changed

            if not sender:
                sender = self
            password_changed.send(sender=sender, user=self, password=raw_password, request=request)
        super().set_password(raw_password)

    def set_password_from_hash(self, password_hash: str, signal=True, sender=None, request=None):
        """Set password directly from a pre-hashed value.

        Unlike set_password(), this does not hash the input again. The provided value
        must already be validated by the caller, and it is stored as-is.

        Because no raw password is available, downstream password sync integrations
        such as LDAP and Kerberos cannot be updated from this code path.
        """
        if self.pk and signal:
            from authentik.core.signals import password_hash_changed

            if not sender:
                sender = self
            password_hash_changed.send(sender=sender, user=self, request=request)
        self.password = password_hash

    def check_password(self, raw_password: str) -> bool:
        if self._pending_password is not None:
            return check_password(raw_password, self.password)
        device = getattr(self, "password_device", None)
        if device is None:
            return check_password(raw_password, UNUSABLE_PASSWORD_PREFIX)
        return device.check_password(raw_password)

    async def acheck_password(self, raw_password: str) -> bool:
        return await sync_to_async(self.check_password)(raw_password)
