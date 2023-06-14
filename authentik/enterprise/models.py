"""Enterprise models"""
from base64 import b64decode
from binascii import Error
from dataclasses import dataclass
from datetime import timedelta
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


@dataclass
class LicenseBody:
    """License JWT claims"""

    aud: str
    exp: int

    name: str
    users: int
    external_users: int


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
