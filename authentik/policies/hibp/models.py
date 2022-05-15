"""authentik HIBP Models"""
from hashlib import sha1

from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.lib.utils.http import get_http_session
from authentik.policies.models import Policy, PolicyResult
from authentik.policies.types import PolicyRequest
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()


class HaveIBeenPwendPolicy(Policy):
    """Check if password is on HaveIBeenPwned's list by uploading the first
    5 characters of the SHA1 Hash."""

    password_field = models.TextField(
        default="password",
        help_text=_("Field key to check, field keys defined in Prompt stages are available."),
    )

    allowed_count = models.IntegerField(default=0)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.policies.hibp.api import HaveIBeenPwendPolicySerializer

        return HaveIBeenPwendPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-hibp-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Check if password is in HIBP DB. Hashes given Password with SHA1, uses the first 5
        characters of Password in request and checks if full hash is in response. Returns 0
        if Password is not in result otherwise the count of how many times it was used."""
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

        pw_hash = sha1(password.encode("utf-8")).hexdigest()  # nosec
        url = f"https://api.pwnedpasswords.com/range/{pw_hash[:5]}"
        result = get_http_session().get(url).text
        final_count = 0
        for line in result.split("\r\n"):
            full_hash, count = line.split(":")
            if pw_hash[5:] == full_hash.lower():
                final_count = int(count)
        LOGGER.debug("got hibp result", count=final_count, hash=pw_hash[:5])
        if final_count > self.allowed_count:
            message = _("Password exists on %(count)d online lists." % {"count": final_count})
            return PolicyResult(False, message)
        return PolicyResult(True)

    class Meta:

        verbose_name = _("Have I Been Pwned Policy")
        verbose_name_plural = _("Have I Been Pwned Policies")
