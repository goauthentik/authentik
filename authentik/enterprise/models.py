"""Enterprise models"""
from functools import lru_cache
from typing import Optional

from django.db import models
from jwt import decode
from authentik.core.models import User


@lru_cache()
def get_licensing_key() -> str:
    with open("todo", "r", encoding="utf-8") as _key:
        return _key.read()


def is_licensed() -> Optional["License"]:
    """"""
    license = License.objects.filter

class License(models.Model):
    """An authentik enterprise license"""

    license_uuid = models.UUIDField(primary_key=True)

    name = models.TextField()
    key = models.TextField()
    expiry = models.DateTimeField()
    users = models.BigIntegerField()

    @property
    def status(self) -> dict:
        return decode(
            self.key,
            get_licensing_key(),
            algorithms=["RS256"],
            options={
                "verify_aud": False,
            },
        )
