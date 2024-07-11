"""GeoIP policy"""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer

from authentik.policies.geoip.countries import COUNTRIES
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult


class GeoIPPolicyMode(models.TextChoices):
    """Block or only allow connections from entities"""

    ALLOW = "allow", _("Only allow connections from entities")
    BLOCK = "block", _("Block connections from entities")


class GeoIPPolicy(Policy):
    """Ensure the user satisfies requirements of geography or network topology, based on IP
    address."""

    asn_mode = models.TextField(choices=GeoIPPolicyMode.choices)
    country_mode = models.TextField(choices=GeoIPPolicyMode.choices)
    asn_list = ArrayField(models.IntegerField())
    country_list = ArrayField(models.CharField(choices=COUNTRIES, max_length=2))

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.geoip.api import GeoIPPolicySerializer

        return GeoIPPolicySerializer

    @property
    def component(self) -> str:  # pragma: no cover
        return "ak-policy-geoip-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """TODO"""

        asn = request.context["asn"]["asn"]
        country = request.context["geoip"]["country"]

        if self.asn_mode == GeoIPPolicyMode.ALLOW and asn not in self.asn_list:
            message = _("Client IP is not part of an allowed autonomous system.")
            return PolicyResult(False, message)

        if self.asn_mode == GeoIPPolicyMode.BLOCK and asn in self.asn_list:
            message = _("Client IP is part of a blocked autonomous system.")
            return PolicyResult(False, message)

        if self.country_mode == GeoIPPolicyMode.ALLOW and country not in self.country_list:
            message = _("Client IP is not in an allowed country.")
            return PolicyResult(False, message)

        if self.country_mode == GeoIPPolicyMode.BLOCK and country in self.country_list:
            message = _("Client IP is in a blocked country.")
            return PolicyResult(False, message)

        return PolicyResult(True)

    class Meta(Policy.PolicyMeta):
        verbose_name = _("GeoIP Policy")
        verbose_name_plural = _("GeoIP Policies")
