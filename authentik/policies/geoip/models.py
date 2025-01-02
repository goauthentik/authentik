"""GeoIP policy"""

from itertools import chain

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django_countries.fields import CountryField
from geopy import distance
from rest_framework.serializers import BaseSerializer

from authentik.events.context_processors.geoip import GeoIPDict
from authentik.events.models import Event, EventAction
from authentik.policies.exceptions import PolicyException
from authentik.policies.geoip.exceptions import GeoIPNotFoundException
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult

MAX_DISTANCE_HOUR_KM = 1000


class GeoIPPolicy(Policy):
    """Ensure the user satisfies requirements of geography or network topology, based on IP
    address."""

    asns = ArrayField(models.IntegerField(), blank=True, default=list)
    countries = CountryField(multiple=True, blank=True)

    distance_tolerance_km = models.PositiveIntegerField(default=50)
    check_history = models.BooleanField(default=False)
    history_max_distance_km = models.PositiveBigIntegerField(default=100)
    history_login_count = models.PositiveIntegerField(default=5)

    check_impossible_travel = models.BooleanField(default=False)
    impossible_tolerance_km = models.PositiveIntegerField(default=100)

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
        static_results: list[PolicyResult] = []
        dynamic_results: list[PolicyResult] = []

        if self.asns:
            static_results.append(self.passes_asn(request))
        if self.countries:
            static_results.append(self.passes_country(request))

        if self.check_history or self.check_impossible_travel:
            dynamic_results.append(self.passes_distance(request))

        if not static_results and not dynamic_results:
            return PolicyResult(True)

        passing = any(r.passing for r in static_results) and all(r.passing for r in dynamic_results)
        messages = chain(
            *[r.messages for r in static_results], *[r.messages for r in dynamic_results]
        )

        result = PolicyResult(passing, *messages)
        result.source_results = list(chain(static_results, dynamic_results))

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
        geoip_data: GeoIPDict | None = request.context.get("geoip")
        country = geoip_data.get("country") if geoip_data else None

        if not country:
            raise PolicyException(
                GeoIPNotFoundException(_("GeoIP: client IP address not found in City database."))
            )

        if country not in self.countries:
            message = _("Client IP is not in an allowed country.")
            return PolicyResult(False, message)

        return PolicyResult(True)

    def passes_distance(self, request: PolicyRequest) -> PolicyResult:
        """Check if current policy execution is out of distance range compared
        to previous authentication requests"""
        # Get previous login event and GeoIP data
        previous_logins = Event.objects.filter(
            action=EventAction.LOGIN, user__pk=request.user.pk, context__geo__isnull=False
        ).order_by("-created")[: self.history_login_count]
        _now = now()
        geoip_data: GeoIPDict | None = request.context.get("geoip")
        if not geoip_data:
            return PolicyResult(False)
        for previous_login in previous_logins:
            previous_login_geoip: GeoIPDict = previous_login.context.get("geo")

            # Figure out distance
            dist = distance.geodesic(
                (previous_login_geoip["lat"], previous_login_geoip["long"]),
                (geoip_data["lat"], geoip_data["long"]),
            )
            if self.check_history and dist.km >= (
                self.history_max_distance_km - self.distance_tolerance_km
            ):
                return PolicyResult(
                    False, _("Distance from previous authentication is larger than threshold.")
                )
            # Check if distance between `previous_login` and now is more
            # than max distance per hour times the amount of hours since the previous login
            # (round down to the lowest closest time of hours)
            # clamped to be at least 1 hour
            rel_time_hours = max(int((_now - previous_login.created).total_seconds() / 86400), 1)
            if self.check_impossible_travel and dist.km >= (
                (MAX_DISTANCE_HOUR_KM * rel_time_hours) - self.distance_tolerance_km
            ):
                return PolicyResult(False, _("Distance is further than possible."))
        return PolicyResult(True)

    class Meta(Policy.PolicyMeta):
        verbose_name = _("GeoIP Policy")
        verbose_name_plural = _("GeoIP Policies")
