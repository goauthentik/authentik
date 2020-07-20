"""passbook reputation request policy"""
from typing import Type

from django.core.cache import cache
from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext as _

from passbook.core.models import User
from passbook.lib.utils.http import get_client_ip
from passbook.policies.models import Policy
from passbook.policies.types import PolicyRequest, PolicyResult

CACHE_KEY_IP_PREFIX = "passbook_reputation_ip_"
CACHE_KEY_USER_PREFIX = "passbook_reputation_user_"


class ReputationPolicy(Policy):
    """Return true if request IP/target username's score is below a certain threshold"""

    check_ip = models.BooleanField(default=True)
    check_username = models.BooleanField(default=True)
    threshold = models.IntegerField(default=-5)

    def form(self) -> Type[ModelForm]:
        from passbook.policies.reputation.forms import ReputationPolicyForm

        return ReputationPolicyForm

    def passes(self, request: PolicyRequest) -> PolicyResult:
        remote_ip = get_client_ip(request.http_request) or "255.255.255.255"
        passing = True
        if self.check_ip:
            score = cache.get_or_set(CACHE_KEY_IP_PREFIX + remote_ip, 0)
            passing = passing and score <= self.threshold
        if self.check_username:
            score = cache.get_or_set(CACHE_KEY_USER_PREFIX + request.user.username, 0)
            passing = passing and score <= self.threshold
        return PolicyResult(passing)

    class Meta:

        verbose_name = _("Reputation Policy")
        verbose_name_plural = _("Reputation Policies")


class IPReputation(models.Model):
    """Store score coming from the same IP"""

    ip = models.GenericIPAddressField(unique=True)
    score = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"IPReputation for {self.ip} @ {self.score}"


class UserReputation(models.Model):
    """Store score attempting to log in as the same username"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"UserReputation for {self.user} @ {self.score}"
