"""Enterprise models"""
from base64 import b64decode
from binascii import Error
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from functools import lru_cache
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.x509 import Certificate, load_pem_x509_certificate
from dacite import from_dict
from django.db import models
from django.utils.timezone import datetime
from jwt import PyJWTError, decode, get_unverified_header
from rest_framework.exceptions import ValidationError

from authentik.core.models import User, UserTypes
from authentik.root.install_id import get_install_id


@lru_cache()
def get_licensing_key() -> Certificate:
    """Get Root CA PEM"""
    with open("authentik/enterprise/public.pem", "rb") as _key:
        return load_pem_x509_certificate(_key.read())


def validate_license(jwt: str) -> dict:
    """Validate the license from a given JWT"""
    headers = get_unverified_header(jwt)
    x5c = headers.get("x5c")
    try:
        cert = load_pem_x509_certificate(b64decode(x5c))
    except (ValueError, Error) as exc:
        raise ValidationError("Unable to verify license") from exc
    try:
        cert.verify_directly_issued_by(get_licensing_key())
    except (InvalidSignature, TypeError, ValueError):
        raise ValidationError("Unable to verify license")
    try:
        body = from_dict(
            LicenseBody,
            decode(
                jwt,
                cert,
                algorithms=["ES521"],
                audience=get_license_aud(),
            ),
        )
    except PyJWTError:
        raise ValidationError("Unable to verify license")
    return body


def get_license_aud() -> str:
    """Get the JWT audience field"""
    return f"enterprise.goauthentik.io/license/{get_install_id()}"


class LicenseFlags(Enum):
    """License flags"""


@dataclass
class LicenseBody:
    """License JWT claims"""

    aud: str
    exp: int

    name: str
    users: int
    external_users: int
    flags: list[LicenseFlags]

    @staticmethod
    def get_total() -> "LicenseBody":
        """Get a summarized version of all (not expired) licenses"""
        active_licenses = License.objects.filter(expiry__lte=datetime().now())
        total = LicenseBody(
            get_license_aud("summary"), datetime().now(), "Summarized license", -1, -1
        )
        for license in active_licenses:
            total.users += license.users
            total.external_users += license.external_users
            exp_ts = datetime.fromtimestamp(license.expiry)
            if exp_ts >= total.exp:
                total.exp = exp_ts
            total.flags.extend(license.status.flags)
        return total

    def is_valid(self) -> bool:
        """Check if the given license body covers all users"""
        default_users = User.objects.filter(type=UserTypes.DEFAULT).count()
        if default_users > self.users:
            return False
        last_month = datetime().now() - timedelta(days=30)
        active_users = User.objects.filter(
            type=UserTypes.EXTERNAL, last_login__gte=last_month
        ).count()
        if active_users > self.external_users:
            return False
        return True


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
        """Get parsed license status"""
        return from_dict(LicenseBody, validate_license(self.key))
