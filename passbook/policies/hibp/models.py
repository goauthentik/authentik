"""passbook HIBP Models"""
from hashlib import sha1

from django.db import models
from django.utils.translation import gettext as _
from requests import get
from structlog import get_logger

from passbook.core.models import Policy, PolicyResult, User

LOGGER = get_logger()


class HaveIBeenPwendPolicy(Policy):
    """Check if password is on HaveIBeenPwned's list by upload the first
    5 characters of the SHA1 Hash."""

    allowed_count = models.IntegerField(default=0)

    form = "passbook.policies.hibp.forms.HaveIBeenPwnedPolicyForm"

    def passes(self, user: User) -> PolicyResult:
        """Check if password is in HIBP DB. Hashes given Password with SHA1, uses the first 5
        characters of Password in request and checks if full hash is in response. Returns 0
        if Password is not in result otherwise the count of how many times it was used."""
        # Only check if password is being set
        if not hasattr(user, "__password__"):
            return PolicyResult(True)
        password = getattr(user, "__password__")
        pw_hash = sha1(password.encode("utf-8")).hexdigest()  # nosec
        url = "https://api.pwnedpasswords.com/range/%s" % pw_hash[:5]
        result = get(url).text
        final_count = 0
        for line in result.split("\r\n"):
            full_hash, count = line.split(":")
            if pw_hash[5:] == full_hash.lower():
                final_count = int(count)
        LOGGER.debug("got hibp result", count=final_count, hash=pw_hash[:5])
        if final_count > self.allowed_count:
            message = _(
                "Password exists on %(count)d online lists." % {"count": final_count}
            )
            return PolicyResult(False, message)
        return PolicyResult(True)

    class Meta:

        verbose_name = _("Have I Been Pwned Policy")
        verbose_name_plural = _("Have I Been Pwned Policies")
