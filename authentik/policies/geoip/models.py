"""GeoIP policy"""

from itertools import chain

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext as _
from django_countries.fields import CountryField
from rest_framework.serializers import BaseSerializer

from authentik.policies.exceptions import PolicyException
from authentik.policies.geoip.exceptions import GeoIPNotFoundException
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult


class GeoIPPolicy(Policy):
    """Ensure the user satisfies requirements of geography or network topology, based on IP
    address."""

    asns = ArrayField(models.IntegerField(), blank=True, default=list)
    countries = CountryField(multiple=True, blank=True)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.geoip.api import GeoIPPolicySerializer

        return GeoIPPolicySerializer

    @property
    def component(self) -> str:  # pragma: no cover
        return "ak-policy-geoip-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """
        Passes if any of the following is true:
        - the client IP is advertised by an autonomous system with ASN in the `asns`
        - the client IP is geolocated in a country of `countries`
        """
        results: list[PolicyResult] = []

        if self.asns:
            results.append(self.passes_asn(request))
        if self.countries:
            results.append(self.passes_country(request))

        if not results:
            return PolicyResult(True)

        passing = any(r.passing for r in results)
        messages = chain(*[r.messages for r in results])

        result = PolicyResult(passing, *messages)
        result.source_results = results

        return result

    def passes_asn(self, request: PolicyRequest) -> PolicyResult:
        # This is not a single get chain because `request.context` can contain `{ "asn": None }`.
        asn_data = request.context.get("asn")
        asn = asn_data.get("asn") if asn_data else None

        if not asn:
            raise PolicyException(
                GeoIPNotFoundException(_("GeoIP: client IP not found in ASN database."))
            )

        if asn not in self.asns:
            message = _("Client IP is not part of an allowed autonomous system.")
            return PolicyResult(False, message)

        return PolicyResult(True)

    def passes_country(self, request: PolicyRequest) -> PolicyResult:
        # This is not a single get chain because `request.context` can contain `{ "geoip": None }`.
        geoip_data = request.context.get("geoip")
        country = geoip_data.get("country") if geoip_data else None

        if not country:
            raise PolicyException(
                GeoIPNotFoundException(_("GeoIP: client IP address not found in City database."))
            )

        if country not in self.countries:
            message = _("Client IP is not in an allowed country.")
            return PolicyResult(False, message)

        return PolicyResult(True)

    class Meta(Policy.PolicyMeta):
        verbose_name = _("GeoIP Policy")
        verbose_name_plural = _("GeoIP Policies")
