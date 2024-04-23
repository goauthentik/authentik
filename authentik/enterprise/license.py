"""Enterprise license"""

from base64 import b64decode
from binascii import Error
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from time import mktime

from cryptography.exceptions import InvalidSignature
from cryptography.x509 import Certificate, load_der_x509_certificate, load_pem_x509_certificate
from dacite import from_dict
from django.core.cache import cache
from django.db.models.query import QuerySet
from django.utils.timezone import now
from jwt import PyJWTError, decode, get_unverified_header
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, DateTimeField, IntegerField

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User, UserTypes
from authentik.enterprise.models import License, LicenseUsage
from authentik.tenants.utils import get_unique_identifier

CACHE_KEY_ENTERPRISE_LICENSE = "goauthentik.io/enterprise/license"
CACHE_EXPIRY_ENTERPRISE_LICENSE = 3 * 60 * 60  # 2 Hours


@lru_cache
def get_licensing_key() -> Certificate:
    """Get Root CA PEM"""
    with open("authentik/enterprise/public.pem", "rb") as _key:
        return load_pem_x509_certificate(_key.read())


def get_license_aud() -> str:
    """Get the JWT audience field"""
    return f"enterprise.goauthentik.io/license/{get_unique_identifier()}"


class LicenseFlags(Enum):
    """License flags"""


@dataclass
class LicenseSummary:
    """Internal representation of a license summary"""

    internal_users: int
    external_users: int
    valid: bool
    show_admin_warning: bool
    show_user_warning: bool
    read_only: bool
    latest_valid: datetime
    has_license: bool


class LicenseSummarySerializer(PassiveSerializer):
    """Serializer for license status"""

    internal_users = IntegerField(required=True)
    external_users = IntegerField(required=True)
    valid = BooleanField()
    show_admin_warning = BooleanField()
    show_user_warning = BooleanField()
    read_only = BooleanField()
    latest_valid = DateTimeField()
    has_license = BooleanField()


@dataclass
class LicenseKey:
    """License JWT claims"""

    aud: str
    exp: int

    name: str
    internal_users: int = 0
    external_users: int = 0
    flags: list[LicenseFlags] = field(default_factory=list)

    @staticmethod
    def validate(jwt: str) -> "LicenseKey":
        """Validate the license from a given JWT"""
        try:
            headers = get_unverified_header(jwt)
        except PyJWTError:
            raise ValidationError("Unable to verify license") from None
        x5c: list[str] = headers.get("x5c", [])
        if len(x5c) < 1:
            raise ValidationError("Unable to verify license")
        try:
            our_cert = load_der_x509_certificate(b64decode(x5c[0]))
            intermediate = load_der_x509_certificate(b64decode(x5c[1]))
            our_cert.verify_directly_issued_by(intermediate)
            intermediate.verify_directly_issued_by(get_licensing_key())
        except (InvalidSignature, TypeError, ValueError, Error):
            raise ValidationError("Unable to verify license") from None
        try:
            body = from_dict(
                LicenseKey,
                decode(
                    jwt,
                    our_cert.public_key(),
                    algorithms=["ES512"],
                    audience=get_license_aud(),
                ),
            )
        except PyJWTError:
            raise ValidationError("Unable to verify license") from None
        return body

    @staticmethod
    def get_total() -> "LicenseKey":
        """Get a summarized version of all (not expired) licenses"""
        active_licenses = License.objects.filter(expiry__gte=now())
        total = LicenseKey(get_license_aud(), 0, "Summarized license", 0, 0)
        for lic in active_licenses:
            total.internal_users += lic.internal_users
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
        return User.objects.all().exclude(is_active=False)

    @staticmethod
    def get_default_user_count():
        """Get current default user count"""
        return LicenseKey.base_user_qs().filter(type=UserTypes.INTERNAL).count()

    @staticmethod
    def get_external_user_count():
        """Get current external user count"""
        return LicenseKey.base_user_qs().filter(type=UserTypes.EXTERNAL).count()

    def is_valid(self) -> bool:
        """Check if the given license body covers all users

        Only checks the current count, no historical data is checked"""
        default_users = self.get_default_user_count()
        if default_users > self.internal_users:
            return False
        active_users = self.get_external_user_count()
        if active_users > self.external_users:
            return False
        return True

    def record_usage(self):
        """Capture the current validity status and metrics and save them"""
        threshold = now() - timedelta(hours=8)
        if not LicenseUsage.objects.filter(record_date__gte=threshold).exists():
            LicenseUsage.objects.create(
                user_count=self.get_default_user_count(),
                external_user_count=self.get_external_user_count(),
                within_limits=self.is_valid(),
            )
        summary = asdict(self.summary())
        # Also cache the latest summary for the middleware
        cache.set(CACHE_KEY_ENTERPRISE_LICENSE, summary, timeout=CACHE_EXPIRY_ENTERPRISE_LICENSE)
        return summary

    @staticmethod
    def last_valid_date() -> datetime:
        """Get the last date the license was valid"""
        usage: LicenseUsage = (
            LicenseUsage.filter_not_expired(within_limits=True).order_by("-record_date").first()
        )
        if not usage:
            return now()
        return usage.record_date

    def summary(self) -> LicenseSummary:
        """Summary of license status"""
        has_license = License.objects.all().count() > 0
        last_valid = LicenseKey.last_valid_date()
        show_admin_warning = last_valid < now() - timedelta(weeks=2)
        show_user_warning = last_valid < now() - timedelta(weeks=4)
        read_only = last_valid < now() - timedelta(weeks=6)
        latest_valid = datetime.fromtimestamp(self.exp)
        return LicenseSummary(
            show_admin_warning=show_admin_warning and has_license,
            show_user_warning=show_user_warning and has_license,
            read_only=read_only and has_license,
            latest_valid=latest_valid,
            internal_users=self.internal_users,
            external_users=self.external_users,
            valid=self.is_valid(),
            has_license=has_license,
        )

    @staticmethod
    def cached_summary() -> LicenseSummary:
        """Helper method which looks up the last summary"""
        summary = cache.get(CACHE_KEY_ENTERPRISE_LICENSE)
        if not summary:
            return LicenseKey.get_total().summary()
        return from_dict(LicenseSummary, summary)
