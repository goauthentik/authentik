"""Enterprise models"""
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
from uuid import uuid4

from dacite import from_dict
from django.db import models
from django.utils.timezone import datetime
from jwt import decode

from authentik.core.models import User, UserTypes


@lru_cache()
def get_licensing_key() -> str:
    with open("authentik/enterprise/public.pem", "r", encoding="utf-8") as _key:
        return _key.read()


@dataclass
class LicenseBody:
    """License JWT claims"""

    name: str
    install_id: str
    users: int
    external_users: int
    exp: int


class License(models.Model):
    """An authentik enterprise license"""

    license_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    key = models.TextField(unique=True)

    name = models.TextField()
    expiry = models.DateTimeField()
    users = models.BigIntegerField()
    external_users = models.BigIntegerField()

    @property
    def status(self) -> LicenseBody:
        return from_dict(
            LicenseBody,
            decode(
                self.key,
                get_licensing_key(),
                algorithms=["ES521"],
                options={
                    "verify_aud": False,
                },
            ),
        )

    def is_valid(self) -> bool:
        """Check if license is valid"""
        status = self.status
        default_users = User.objects.filter(type=UserTypes.DEFAULT).count()
        if default_users > status.users:
            return False
        last_month = datetime().now() - timedelta(days=30)
        active_users = User.objects.filter(last_login__gte=last_month).count()
        if active_users > status.external_users:
            return False
        if self.expiry < datetime().now():
            return False
        return True
