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
from authentik.lib.models import SerializerModel, internal_model

if TYPE_CHECKING:
    from authentik.enterprise.license import LicenseKey


def usage_expiry():
    """Keep license usage records for 3 months"""
    return now() + timedelta(days=30 * 3)


THRESHOLD_WARNING_ADMIN_WEEKS = 2
THRESHOLD_WARNING_USER_WEEKS = 4
THRESHOLD_WARNING_EXPIRY_WEEKS = 2
THRESHOLD_READ_ONLY_WEEKS = 6


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

        return LicenseKey.validate(self.key, check_expiry=False)

    class Meta:
        indexes = (HashIndex(fields=("key",)),)
        verbose_name = _("License")
        verbose_name_plural = _("Licenses")


class LicenseUsageStatus(models.TextChoices):
    """License states an instance/tenant can be in"""

    UNLICENSED = "unlicensed"
    VALID = "valid"
    EXPIRED = "expired"
    EXPIRY_SOON = "expiry_soon"
    # User limit exceeded, 2 week threshold, show message in admin interface
    LIMIT_EXCEEDED_ADMIN = "limit_exceeded_admin"
    # User limit exceeded, 4 week threshold, show message in user interface
    LIMIT_EXCEEDED_USER = "limit_exceeded_user"
    READ_ONLY = "read_only"

    @property
    def is_valid(self) -> bool:
        """Quickly check if a license is valid"""
        return self in [LicenseUsageStatus.VALID, LicenseUsageStatus.EXPIRY_SOON]


@internal_model
class LicenseUsage(ExpiringModel):
    """a single license usage record"""

    expires = models.DateTimeField(default=usage_expiry)

    usage_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    internal_user_count = models.BigIntegerField()
    external_user_count = models.BigIntegerField()
    status = models.TextField(choices=LicenseUsageStatus.choices)

    record_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("License Usage")
        verbose_name_plural = _("License Usage Records")
        indexes = ExpiringModel.Meta.indexes
