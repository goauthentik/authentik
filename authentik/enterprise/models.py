"""Enterprise models"""
from base64 import b64decode
from binascii import Error
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from time import mktime
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.x509 import Certificate, load_pem_x509_certificate
from dacite import from_dict
from django.db import models
from django.db.models.query import QuerySet
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user
from jwt import PyJWTError, decode, get_unverified_header
from rest_framework.exceptions import ValidationError

from authentik.core.models import ExpiringModel, User, UserTypes
from authentik.root.install_id import get_install_id


@lru_cache()
def get_licensing_key() -> Certificate:
    """Get Root CA PEM"""
    with open("authentik/enterprise/public.pem", "rb") as _key:
        return load_pem_x509_certificate(_key.read())


def get_license_aud() -> str:
    """Get the JWT audience field"""
    return f"enterprise.goauthentik.io/license/{get_install_id()}"


class LicenseFlags(Enum):
    """License flags"""


@dataclass
class LicenseKey:
    """License JWT claims"""

    aud: str
    exp: int

    name: str
    users: int
    external_users: int
    flags: list[LicenseFlags] = field(default_factory=list)

    @staticmethod
    def validate(jwt: str) -> "LicenseKey":
        """Validate the license from a given JWT"""
        try:
            headers = get_unverified_header(jwt)
        except PyJWTError:
            raise ValidationError("Unable to verify license")
        x5c: list[str] = headers.get("x5c", [])
        if len(x5c) < 1:
            raise ValidationError("Unable to verify license")
        try:
            our_cert = load_pem_x509_certificate(b64decode(x5c[0]))
            intermediate = load_pem_x509_certificate(b64decode(x5c[1]))
            our_cert.verify_directly_issued_by(intermediate)
            intermediate.verify_directly_issued_by(get_licensing_key())
        except (InvalidSignature, TypeError, ValueError, Error):
            raise ValidationError("Unable to verify license")
        try:
            body = from_dict(
                LicenseKey,
                decode(
                    jwt,
                    our_cert.public_key(),
                    algorithms=["ES521"],
                    audience=get_license_aud(),
                ),
            )
        except PyJWTError:
            raise ValidationError("Unable to verify license")
        return body

    @staticmethod
    def get_total() -> "LicenseKey":
        """Get a summarized version of all (not expired) licenses"""
        active_licenses = License.objects.filter(expiry__gte=now())
        total = LicenseKey(get_license_aud(), 0, "Summarized license", 0, 0)
        for lic in active_licenses:
            total.users += lic.users
            total.external_users += lic.external_users
            exp_ts = int(mktime(lic.expiry.timetuple()))
            if total.exp == 0:
                total.exp = exp_ts
            if exp_ts <= total.exp:
                total.exp = exp_ts
            total.flags.extend(lic.status.flags)
        return total

    @staticmethod
    def base_user_qs() -> QuerySet:
        """Base query set for all users"""
        return User.objects.all().exclude(pk=get_anonymous_user().pk)

    @staticmethod
    def get_default_user_count():
        """Get current default user count"""
        return LicenseKey.base_user_qs().filter(type=UserTypes.DEFAULT).count()

    @staticmethod
    def get_external_user_count():
        """Get current external user count"""
        # Count since start of the month
        last_month = now().replace(day=1)
        return (
            LicenseKey.base_user_qs()
            .filter(type=UserTypes.EXTERNAL, last_login__gte=last_month)
            .count()
        )

    def is_valid(self) -> bool:
        """Check if the given license body covers all users

        Only checks the current count, no historical data is checked"""
        default_users = self.get_default_user_count()
        if default_users > self.users:
            return False
        active_users = self.get_external_user_count()
        if active_users > self.external_users:
            return False
        return True

    def record_usage(self):
        """Capture the current validity status and metrics and save them"""
        LicenseUsage.objects.create(
            user_count=self.get_default_user_count(),
            external_user_count=self.get_external_user_count(),
            within_limits=self.is_valid(),
        )

    @staticmethod
    def last_valid_date() -> datetime:
        """Get the last date the license was valid"""
        usage: LicenseUsage = (
            LicenseUsage.filter_not_expired(within_limits=True).order_by("-record_date").first()
        )
        if not usage:
            return now()
        return usage.record_date


class License(models.Model):
    """An authentik enterprise license"""

    license_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    key = models.TextField(unique=True)

    name = models.TextField()
    expiry = models.DateTimeField()
    users = models.BigIntegerField()
    external_users = models.BigIntegerField()

    @property
    def status(self) -> LicenseKey:
        """Get parsed license status"""
        return LicenseKey.validate(self.key)


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
