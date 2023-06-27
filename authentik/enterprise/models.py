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
from django.db.models.functions import TruncDate
from django.db.models.query import QuerySet
from django.utils.timezone import get_current_timezone, now
from guardian.shortcuts import get_anonymous_user
from jwt import PyJWTError, decode, get_unverified_header
from rest_framework.exceptions import ValidationError

from authentik.core.models import User, UserTypes
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
            if exp_ts >= total.exp:
                total.exp = exp_ts
            total.flags.extend(lic.status.flags)
        return total

    @property
    def base_user_qs(self) -> QuerySet:
        return User.objects.all().exclude(pk=get_anonymous_user().pk)

    def is_valid(self) -> bool:
        """Check if the given license body covers all users

        Only checks the current count, no historical data is checked"""
        default_users = self.base_user_qs.filter(type=UserTypes.DEFAULT).count()
        if default_users > self.users:
            return False
        last_month = now() - timedelta(days=30)
        active_users = self.base_user_qs.filter(
            type=UserTypes.EXTERNAL, last_login__gte=last_month
        ).count()
        if active_users > self.external_users:
            return False
        return True

    def last_valid_date(self) -> datetime:
        exp = datetime.fromtimestamp(self.exp, tz=get_current_timezone())
        if self.is_valid() or exp < now():
            # License is valid, so we can just set the cache to that date
            # or license is invalid, but the expiry date is in the past
            return exp
        # Warning to admin after 2 weeks of overage
        # Warning to user after 4 weeks of overage
        # Read only after 6 weeks of overage
        default_users = self.check_default_users()
        external_users = self.check_external_users()
        last_valid = min(default_users, external_users)
        return last_valid

    def check_default_users(self):
        """Find the last time when the amount of users existent were within the license"""
        user_dates = (
            self.base_user_qs.filter(
                type=UserTypes.DEFAULT,
            )
            .annotate(date=TruncDate("date_joined"))
            .values_list("date", flat=True)
            .reverse()
        )
        last_valid_date = now()
        # Go through dates in reverse, starting from newest to oldest
        for date in user_dates:
            # Count how many users were created on a given date
            users = self.base_user_qs.filter(date_joined__date=date).count()
            # If that user count is more than the license has, we continue looking
            if users > self.users:
                continue
            # Once we've found the last date where the user count is less or equal than
            # what the license has, that's the date
            last_valid_date = date
            break
        return last_valid_date

    def check_external_users(self):
        """Find the last time monthly active external users were in the license limit"""
        user_dates = (
            self.base_user_qs.filter(
                type=UserTypes.EXTERNAL,
            )
            .annotate(date=TruncDate("last_login"))
            .values_list("date", flat=True)
            .reverse()
        )
        last_valid_date = now()
        # Go through dates in reverse, starting from newest to oldest
        for date in user_dates:
            # Count how many users were created on a given date
            users = self.base_user_qs.filter(last_login__date=date).count()
            # If that user count is more than the license has, we continue looking
            if users > self.external_users:
                continue
            # Once we've found the last date where the user count is less or equal than
            # what the license has, that's the date
            last_valid_date = date
            break
        return last_valid_date


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
