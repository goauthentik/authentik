"""Enterprise models"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
from dacite import from_dict

from django.db import models
from jwt import decode


@lru_cache()
def get_licensing_key() -> str:
    with open("todo", "r", encoding="utf-8") as _key:
        return _key.read()


def is_licensed() -> Optional["License"]:
    """"""
    # license = License.objects.filter


@dataclass
class LicenseBody:

    install_id: str
    users: int
    external_users: int
    exp: int

class License(models.Model):
    """An authentik enterprise license"""

    license_uuid = models.UUIDField(primary_key=True)

    name = models.TextField()
    key = models.TextField()
    expiry = models.DateTimeField()
    users = models.BigIntegerField()
    external_users = models.BigIntegerField()

    @property
    def status(self) -> LicenseBody:
        return from_dict(LicenseBody, decode(
            self.key,
            get_licensing_key(),
            algorithms=["RS256"],
            options={
                "verify_aud": False,
            },
        ))
