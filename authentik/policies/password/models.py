"""password policy"""

import re
from hashlib import sha1

from django.contrib.auth.hashers import identify_hasher
from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger
from zxcvbn import zxcvbn

from authentik.lib.utils.http import get_http_session
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()
RE_LOWER = re.compile("[a-z]")
RE_UPPER = re.compile("[A-Z]")
RE_DIGITS = re.compile("[0-9]")


class PasswordPolicy(Policy):
    """Policy to make sure passwords have certain properties"""

    password_field = models.TextField(
        default="password",
        help_text=_("Field key to check, field keys defined in Prompt stages are available."),
    )

    check_static_rules = models.BooleanField(default=True)
    check_have_i_been_pwned = models.BooleanField(default=False)
    check_zxcvbn = models.BooleanField(default=False)

    amount_digits = models.PositiveIntegerField(default=0)
    amount_uppercase = models.PositiveIntegerField(default=0)
    amount_lowercase = models.PositiveIntegerField(default=0)
    amount_symbols = models.PositiveIntegerField(default=0)
    length_min = models.PositiveIntegerField(default=0)
    symbol_charset = models.TextField(default=r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ ")
    error_message = models.TextField(blank=True)

    hibp_allowed_count = models.PositiveIntegerField(
        default=0,
        help_text=_("How many times the password hash is allowed to be on haveibeenpwned"),
    )

    zxcvbn_score_threshold = models.PositiveIntegerField(
        default=2,
        help_text=_("If the zxcvbn score is equal or less than this value, the policy will fail."),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.password.api import PasswordPolicySerializer

        return PasswordPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-password-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        password = request.context.get(PLAN_CONTEXT_PROMPT, {}).get(
            self.password_field, request.context.get(self.password_field)
        )
        if not password:
            LOGGER.warning(
                "Password field not set in Policy Request",
                field=self.password_field,
                fields=request.context.keys(),
            )
            return PolicyResult(False, _("Password not set in context"))
        password = str(password)

        if self.check_static_rules:
            static_result = self.passes_static(password, request)
            if not static_result.passing:
                return static_result
        if self.check_have_i_been_pwned:
            hibp_result = self.passes_hibp(password, request)
            if not hibp_result.passing:
                return hibp_result
        if self.check_zxcvbn:
            zxcvbn_result = self.passes_zxcvbn(password, request)
            if not zxcvbn_result.passing:
                return zxcvbn_result
        return PolicyResult(True)

    def passes_static(self, password: str, request: PolicyRequest) -> PolicyResult:
        """Check static rules"""
        error_message = self.error_message
        if error_message == "":
            error_message = _("Invalid password.")

        if len(password) < self.length_min:
            LOGGER.debug("password failed", check="static", reason="length")
            return PolicyResult(False, self.error_message)

        if self.amount_digits > 0 and len(RE_DIGITS.findall(password)) < self.amount_digits:
            LOGGER.debug("password failed", check="static", reason="amount_digits")
            return PolicyResult(False, self.error_message)
        if self.amount_lowercase > 0 and len(RE_LOWER.findall(password)) < self.amount_lowercase:
            LOGGER.debug("password failed", check="static", reason="amount_lowercase")
            return PolicyResult(False, self.error_message)
        if self.amount_uppercase > 0 and len(RE_UPPER.findall(password)) < self.amount_lowercase:
            LOGGER.debug("password failed", check="static", reason="amount_uppercase")
            return PolicyResult(False, self.error_message)
        if self.amount_symbols > 0:
            count = 0
            for symbol in self.symbol_charset:
                count += password.count(symbol)
            if count < self.amount_symbols:
                LOGGER.debug("password failed", check="static", reason="amount_symbols")
                return PolicyResult(False, self.error_message)

        return PolicyResult(True)

    def check_hibp(self, short_hash: str) -> str:
        """Check the haveibeenpwned API"""
        url = f"https://api.pwnedpasswords.com/range/{short_hash}"
        return get_http_session().get(url).text

    def passes_hibp(self, password: str, request: PolicyRequest) -> PolicyResult:
        """Check if password is in HIBP DB. Hashes given Password with SHA1, uses the first 5
        characters of Password in request and checks if full hash is in response. Returns 0
        if Password is not in result otherwise the count of how many times it was used."""
        pw_hash = sha1(password.encode("utf-8")).hexdigest()  # nosec
        result = self.check_hibp(pw_hash[:5])
        final_count = 0
        for line in result.split("\r\n"):
            full_hash, count = line.split(":")
            if pw_hash[5:] == full_hash.lower():
                final_count = int(count)
        LOGGER.debug("got hibp result", count=final_count, hash=pw_hash[:5])
        if final_count > self.hibp_allowed_count:
            LOGGER.debug("password failed", check="hibp", count=final_count)
            message = _("Password exists on {count} online lists.".format(count=final_count))
            return PolicyResult(False, message)
        return PolicyResult(True)

    def passes_zxcvbn(self, password: str, request: PolicyRequest) -> PolicyResult:
        """Check Dropbox's zxcvbn password estimator"""
        user_inputs = []
        if request.user.is_authenticated:
            user_inputs.append(request.user.username)
            user_inputs.append(request.user.name)
            user_inputs.append(request.user.email)
        if request.http_request:
            user_inputs.append(request.http_request.brand.branding_title)
        # Only calculate result for the first 72 characters, as with over 100 char
        # long passwords we can be reasonably sure that they'll surpass the score anyways
        # See https://github.com/dropbox/zxcvbn#runtime-latency
        results = zxcvbn(password[:72], user_inputs)
        LOGGER.debug("password failed", check="zxcvbn", score=results["score"])
        result = PolicyResult(results["score"] > self.zxcvbn_score_threshold)
        if not result.passing:
            result.messages += tuple((_("Password is too weak."),))
        if isinstance(results["feedback"]["warning"], list):
            result.messages += tuple(results["feedback"]["warning"])
        if isinstance(results["feedback"]["suggestions"], list):
            result.messages += tuple(results["feedback"]["suggestions"])
        return result

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Password Policy")
        verbose_name_plural = _("Password Policies")
