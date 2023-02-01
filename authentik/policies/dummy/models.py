"""Dummy policy"""
from random import SystemRandom
from time import sleep

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()


class DummyPolicy(Policy):
    """Policy used for debugging the PolicyEngine. Returns a fixed result,
    but takes a random time to process."""

    __debug_only__ = True

    result = models.BooleanField(default=False)
    wait_min = models.IntegerField(default=5)
    wait_max = models.IntegerField(default=30)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.dummy.api import DummyPolicySerializer

        return DummyPolicySerializer

    @property
    def component(self) -> str:  # pragma: no cover
        return "ak-policy-dummy-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Wait random time then return result"""
        wait = SystemRandom().randrange(self.wait_min, self.wait_max)
        LOGGER.info("Policy waiting", policy=self, delay=wait)
        sleep(wait)
        return PolicyResult(self.result, "dummy")

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Dummy Policy")
        verbose_name_plural = _("Dummy Policies")
