"""GeoIP policy"""

from itertools import chain
from math import isfinite

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
MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180


def valid_coordinates(geoip_data: object) -> tuple[float, float] | None:
    """Return valid latitude and longitude from GeoIP data."""
    if not isinstance(geoip_data, dict):
        return None
    latitude = geoip_data.get("lat")
    longitude = geoip_data.get("long")
    if (
        isinstance(latitude, bool)
        or not isinstance(latitude, int | float)
        or isinstance(longitude, bool)
        or not isinstance(longitude, int | float)
    ):
        return None
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except OverflowError:
        return None
    if not isfinite(latitude) or not isfinite(longitude):
        return None
    if not MIN_LATITUDE <= latitude <= MAX_LATITUDE or not (
        MIN_LONGITUDE <= longitude <= MAX_LONGITUDE
    ):
        return None
    return latitude, longitude


class GeoIPPolicy(Policy):
    """Ensure the user satisfies requirements of geography or network topology, based on IP
    address."""

    asns = ArrayField(models.IntegerField(), blank=True, default=list)
    countries = CountryField(multiple=True, blank=True)

    distance_tolerance_km = models.PositiveIntegerField(default=50)

    check_history_distance = models.BooleanField(default=False)
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

        if self.check_history_distance or self.check_impossible_travel:
            dynamic_results.append(self.passes_distance(request))

        if not static_results and not dynamic_results:
            return PolicyResult(True)

        static_passing = any(r.passing for r in static_results) if static_results else True
        dynamic_passing = all(r.passing for r in dynamic_results)
        passing = static_passing and dynamic_passing
        messages = chain(
            *[r.messages for r in static_results], *[r.messages for r in dynamic_results]
        )

        result = PolicyResult(passing, *messages)
        result.source_results = list(chain(static_results, dynamic_results))
        for source_result in dynamic_results:
            if source_result.raw_result is not None:
                result.raw_result = source_result.raw_result
                break

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
        previous_logins = Event.objects.filter(
            action=EventAction.LOGIN,
            user__pk=request.user.pk,
        ).order_by("-created")[: self.history_login_count]
        current_coordinates = valid_coordinates(request.context.get("geoip"))
        if current_coordinates is None:
            return PolicyResult(True)
        current_time = now()
        for previous_login in previous_logins:
            previous_coordinates = valid_coordinates(previous_login.context.get("geo"))
            if previous_coordinates is None:
                continue

            dist = distance.geodesic(previous_coordinates, current_coordinates)
            if self.check_history_distance and dist.km >= (
                self.history_max_distance_km + self.distance_tolerance_km
            ):
                return PolicyResult(
                    False, _("Distance from previous authentication is larger than threshold.")
                )
            elapsed_hours = max(
                (current_time - previous_login.created).total_seconds() / 3600,
                1.0,
            )
            allowed_distance_km = (
                MAX_DISTANCE_HOUR_KM * elapsed_hours
            ) + self.impossible_tolerance_km
            if self.check_impossible_travel and dist.km >= allowed_distance_km:
                result = PolicyResult(False, _("Distance is further than possible."))
                result.raw_result = {
                    "reason": "impossible_travel_threshold_exceeded",
                    "distance_km": dist.km,
                    "allowed_distance_km": allowed_distance_km,
                    "elapsed_hours": elapsed_hours,
                    "max_speed_km_per_hour": MAX_DISTANCE_HOUR_KM,
                    "impossible_tolerance_km": self.impossible_tolerance_km,
                    "previous_login_at": previous_login.created,
                    "previous_login_event": previous_login.event_uuid,
                    "current_geo": {
                        "lat": current_coordinates[0],
                        "long": current_coordinates[1],
                    },
                    "previous_geo": {
                        "lat": previous_coordinates[0],
                        "long": previous_coordinates[1],
                    },
                }
                return result
        return PolicyResult(True)

    class Meta(Policy.PolicyMeta):
        verbose_name = _("GeoIP Policy")
        verbose_name_plural = _("GeoIP Policies")
