"""Enterprise models"""

from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

from django.contrib.postgres.indexes import HashIndex
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from authentik.core.models import ExpiringModel
from authentik.lib.models import SerializerModel

if TYPE_CHECKING:
    from authentik.enterprise.license import LicenseKey


class License(SerializerModel):
    """An authentik enterprise license"""

    license_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    key = models.TextField()

    name = models.TextField()
    expiry = models.DateTimeField()
    internal_users = models.BigIntegerField()
    external_users = models.BigIntegerField()

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.api import LicenseSerializer

        return LicenseSerializer

    @property
    def status(self) -> "LicenseKey":
        """Get parsed license status"""
        from authentik.enterprise.license import LicenseKey

        return LicenseKey.validate(self.key)

    class Meta:
        indexes = (HashIndex(fields=("key",)),)
        verbose_name = _("License")
        verbose_name_plural = _("Licenses")


def usage_expiry():
    """Keep license usage records for 3 months"""
    return now() + timedelta(days=30 * 3)


class LicenseUsage(ExpiringModel):
    """a single license usage record"""

    expires = models.DateTimeField(default=usage_expiry)

    usage_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    user_count = models.BigIntegerField()
    external_user_count = models.BigIntegerField()
    within_limits = models.BooleanField()

    record_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("License Usage")
        verbose_name_plural = _("License Usage Records")
