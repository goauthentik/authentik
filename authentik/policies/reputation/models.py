"""authentik reputation request policy"""
from datetime import timedelta
from uuid import uuid4

from django.db import models
from django.db.models import Sum
from django.db.models.query_utils import Q
from django.utils.timezone import now
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog import get_logger

from authentik.core.models import ExpiringModel
from authentik.lib.config import CONFIG
from authentik.lib.models import SerializerModel
from authentik.lib.utils.http import get_client_ip
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()
CACHE_KEY_PREFIX = "goauthentik.io/policies/reputation/scores/"


def reputation_expiry():
    """Reputation expiry"""
    return now() + timedelta(seconds=CONFIG.get_int("reputation.expiry"))


class ReputationPolicy(Policy):
    """Return true if request IP/target username's score is below a certain threshold"""

    check_ip = models.BooleanField(default=True)
    check_username = models.BooleanField(default=True)
    threshold = models.IntegerField(default=-5)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.reputation.api import ReputationPolicySerializer

        return ReputationPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-reputation-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        remote_ip = get_client_ip(request.http_request)
        query = Q()
        if self.check_ip:
            query |= Q(ip=remote_ip)
        if self.check_username:
            query |= Q(identifier=request.user.username)
        score = (
            Reputation.objects.filter(query).aggregate(total_score=Sum("score"))["total_score"] or 0
        )
        passing = score <= self.threshold
        LOGGER.debug(
            "Score for user",
            username=request.user.username,
            remote_ip=remote_ip,
            score=score,
            passing=passing,
        )
        return PolicyResult(bool(passing))

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Reputation Policy")
        verbose_name_plural = _("Reputation Policies")


class Reputation(ExpiringModel, SerializerModel):
    """Reputation for user and or IP."""

    reputation_uuid = models.UUIDField(primary_key=True, unique=True, default=uuid4)

    identifier = models.TextField()
    ip = models.GenericIPAddressField()
    ip_geo_data = models.JSONField(default=dict)
    score = models.BigIntegerField(default=0)

    expires = models.DateTimeField(default=reputation_expiry)

    updated = models.DateTimeField(auto_now_add=True)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.reputation.api import ReputationSerializer

        return ReputationSerializer

    def __str__(self) -> str:
        return f"Reputation {self.identifier}/{self.ip} @ {self.score}"

    class Meta:
        verbose_name = _("Reputation Score")
        verbose_name_plural = _("Reputation Scores")
        unique_together = ("identifier", "ip")
