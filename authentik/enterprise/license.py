"""Enterprise license"""

from base64 import b64decode
from binascii import Error
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from functools import lru_cache
from time import mktime

from cryptography.exceptions import InvalidSignature
from cryptography.x509 import Certificate, load_der_x509_certificate, load_pem_x509_certificate
from dacite import DaciteError, from_dict
from django.core.cache import cache
from django.db.models.query import QuerySet
from django.utils.timezone import now
from jwt import PyJWTError, decode, get_unverified_header
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    BooleanField,
    ChoiceField,
    DateTimeField,
    IntegerField,
)

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User, UserTypes
from authentik.enterprise.models import (
    THRESHOLD_READ_ONLY_WEEKS,
    THRESHOLD_WARNING_ADMIN_WEEKS,
    THRESHOLD_WARNING_EXPIRY_WEEKS,
    THRESHOLD_WARNING_USER_WEEKS,
    License,
    LicenseUsage,
    LicenseUsageStatus,
)
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

    TRIAL = "trial"


@dataclass
class LicenseSummary:
    """Internal representation of a license summary"""

    internal_users: int
    external_users: int
    status: LicenseUsageStatus
    latest_valid: datetime
    has_license: bool


class LicenseSummarySerializer(PassiveSerializer):
    """Serializer for license status"""

    internal_users = IntegerField(required=True)
    external_users = IntegerField(required=True)
    status = ChoiceField(choices=LicenseUsageStatus.choices)
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
        return User.objects.all().exclude_anonymous().exclude(is_active=False)

    @staticmethod
    def get_default_user_count():
        """Get current default user count"""
        return LicenseKey.base_user_qs().filter(type=UserTypes.INTERNAL).count()

    @staticmethod
    def get_external_user_count():
        """Get current external user count"""
        return LicenseKey.base_user_qs().filter(type=UserTypes.EXTERNAL).count()

    def _last_valid_date(self):
        last_valid_date = (
            LicenseUsage.objects.order_by("-record_date")
            .filter(status=LicenseUsageStatus.VALID)
            .first()
        )
        if not last_valid_date:
            return datetime.fromtimestamp(0, UTC)
        return last_valid_date.record_date

    def is_valid(self) -> LicenseUsageStatus:
        """Check if the given license body covers all users, and is valid."""
        last_valid = self._last_valid_date()
        _now = now()
        # Check limit-exceeded  based status
        default_users = self.get_default_user_count()
        active_users = self.get_external_user_count()
        if default_users > self.internal_users or active_users > self.external_users:
            if last_valid < _now - timedelta(weeks=THRESHOLD_READ_ONLY_WEEKS):
                return LicenseUsageStatus.READ_ONLY
            if last_valid < _now - timedelta(weeks=THRESHOLD_WARNING_USER_WEEKS):
                return LicenseUsageStatus.LIMIT_EXCEEDED_USER
            if last_valid < _now - timedelta(weeks=THRESHOLD_WARNING_ADMIN_WEEKS):
                return LicenseUsageStatus.LIMIT_EXCEEDED_ADMIN
        # Check expiry based status
        if self.exp < _now:
            if self.exp < _now - timedelta(weeks=THRESHOLD_WARNING_EXPIRY_WEEKS):
                return LicenseUsageStatus.EXPIRY_SOON
            if self.exp < _now - timedelta(weeks=THRESHOLD_READ_ONLY_WEEKS):
                return LicenseUsageStatus.READ_ONLY
            return LicenseUsageStatus.EXPIRED
        return LicenseUsageStatus.VALID

    def record_usage(self):
        """Capture the current validity status and metrics and save them"""
        threshold = now() - timedelta(hours=8)
        usage = (
            LicenseUsage.objects.order_by("-record_date").filter(record_date__gte=threshold).first()
        )
        if not usage:
            usage = LicenseUsage.objects.create(
                user_count=self.get_default_user_count(),
                external_user_count=self.get_external_user_count(),
                status=self.is_valid(),
            )
        summary = asdict(self.summary())
        # Also cache the latest summary for the middleware
        cache.set(CACHE_KEY_ENTERPRISE_LICENSE, summary, timeout=CACHE_EXPIRY_ENTERPRISE_LICENSE)
        return usage

    def summary(self) -> LicenseSummary:
        """Summary of license status"""
        has_license = License.objects.all().count() > 0
        status = self.is_valid()
        latest_valid = datetime.fromtimestamp(self.exp)
        return LicenseSummary(
            latest_valid=latest_valid,
            internal_users=self.internal_users,
            external_users=self.external_users,
            status=status if has_license else LicenseUsageStatus.VALID,
            has_license=has_license,
        )

    @staticmethod
    def cached_summary() -> LicenseSummary:
        """Helper method which looks up the last summary"""
        summary = cache.get(CACHE_KEY_ENTERPRISE_LICENSE)
        if not summary:
            return LicenseKey.get_total().summary()
        try:
            return from_dict(LicenseSummary, summary)
        except DaciteError:
            cache.delete(CACHE_KEY_ENTERPRISE_LICENSE)
            return LicenseKey.get_total().summary()
