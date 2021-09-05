"""authentik reputation request policy"""
from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog import get_logger

from authentik.lib.utils.http import get_client_ip
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()
CACHE_KEY_IP_PREFIX = "authentik_reputation_ip_"
CACHE_KEY_USER_PREFIX = "authentik_reputation_user_"


class ReputationPolicy(Policy):
    """Return true if request IP/target username's score is below a certain threshold"""

    check_ip = models.BooleanField(default=True)
    check_username = models.BooleanField(default=True)
    threshold = models.IntegerField(default=-5)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.policies.reputation.api import ReputationPolicySerializer

        return ReputationPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-reputation-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        remote_ip = get_client_ip(request.http_request)
        passing = False
        if self.check_ip:
            score = cache.get_or_set(CACHE_KEY_IP_PREFIX + remote_ip, 0)
            passing += passing or score <= self.threshold
            LOGGER.debug("Score for IP", ip=remote_ip, score=score, passing=passing)
        if self.check_username:
            score = cache.get_or_set(CACHE_KEY_USER_PREFIX + request.user.username, 0)
            passing += passing or score <= self.threshold
            LOGGER.debug(
                "Score for Username",
                username=request.user.username,
                score=score,
                passing=passing,
            )
        return PolicyResult(bool(passing))

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

    username = models.TextField()
    score = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"UserReputation for {self.username} @ {self.score}"
