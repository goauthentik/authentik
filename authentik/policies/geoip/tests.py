"""geoip policy tests"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest import mock

from django.test import TestCase

from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.events.utils import get_user
from authentik.policies.engine import PolicyRequest, PolicyResult
from authentik.policies.exceptions import PolicyException
from authentik.policies.geoip.exceptions import GeoIPNotFoundException
from authentik.policies.geoip.models import GeoIPPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.process import PolicyProcess


class TestGeoIPPolicy(TestCase):
    """Test GeoIP Policy"""

    def setUp(self):
        super().setUp()
        self.user = create_test_user()
        self.request = PolicyRequest(self.user)

        self.context_disabled_geoip = {}
        self.context_unknown_ip = {"asn": None, "geoip": None}
        # 8.8.8.8
        self.context = {
            "asn": {"asn": 15169, "as_org": "GOOGLE", "network": "8.8.8.0/24"},
            "geoip": {
                "continent": "NA",
                "country": "US",
                "lat": 37.751,
                "long": -97.822,
                "city": "",
            },
        }

        self.matching_asns = [13335, 15169]
        self.matching_countries = ["US", "CA"]
        self.mismatching_asns = [1, 2]
        self.mismatching_countries = ["MX", "UA"]

    def enrich_context_disabled_geoip(self):
        pass

    def enrich_context_unknown_ip(self):
        self.request.context["asn"] = self.context_unknown_ip["asn"]
        self.request.context["geoip"] = self.context_unknown_ip["geoip"]

    def enrich_context(self):
        self.request.context["asn"] = self.context["asn"]
        self.request.context["geoip"] = self.context["geoip"]

    def create_login(self, geo: object, created: datetime) -> Event:
        """Create a login event at an explicit timestamp."""
        event = Event.objects.create(
            action=EventAction.LOGIN,
            user=get_user(self.user),
            context={"geo": geo},
        )
        Event.objects.filter(pk=event.pk).update(created=created)
        event.refresh_from_db()
        return event

    def test_disabled_geoip(self):
        """Test that disabled GeoIP raises PolicyException with GeoIPNotFoundException"""
        self.enrich_context_disabled_geoip()
        policy = GeoIPPolicy.objects.create(
            asns=self.matching_asns, countries=self.matching_countries
        )

        with self.assertRaises(PolicyException) as cm:
            policy.passes(self.request)

        self.assertIsInstance(cm.exception.src_exc, GeoIPNotFoundException)

    def test_unknown_ip(self):
        """Test that unknown IP raises PolicyException with GeoIPNotFoundException"""
        self.enrich_context_unknown_ip()
        policy = GeoIPPolicy.objects.create(
            asns=self.matching_asns, countries=self.matching_countries
        )

        with self.assertRaises(PolicyException) as cm:
            policy.passes(self.request)

        self.assertIsInstance(cm.exception.src_exc, GeoIPNotFoundException)

    def test_empty_policy(self):
        """Test that empty policy passes"""
        self.enrich_context()
        policy = GeoIPPolicy.objects.create()

        result: PolicyResult = policy.passes(self.request)

        self.assertTrue(result.passing)

    def test_policy_with_matching_asns(self):
        """Test that a policy with matching ASNs passes"""
        self.enrich_context()
        policy = GeoIPPolicy.objects.create(asns=self.matching_asns)

        result: PolicyResult = policy.passes(self.request)

        self.assertTrue(result.passing)

    def test_policy_with_mismatching_asns(self):
        """Test that a policy with mismatching ASNs fails"""
        self.enrich_context()
        policy = GeoIPPolicy.objects.create(asns=self.mismatching_asns)

        result: PolicyResult = policy.passes(self.request)

        self.assertFalse(result.passing)

    def test_policy_with_matching_countries(self):
        """Test that a policy with matching countries passes"""
        self.enrich_context()
        policy = GeoIPPolicy.objects.create(countries=self.matching_countries)

        result: PolicyResult = policy.passes(self.request)

        self.assertTrue(result.passing)

    def test_policy_with_mismatching_countries(self):
        """Test that a policy with mismatching countries fails"""
        self.enrich_context()
        policy = GeoIPPolicy.objects.create(countries=self.mismatching_countries)

        result: PolicyResult = policy.passes(self.request)

        self.assertFalse(result.passing)

    def test_policy_requires_only_one_match(self):
        """Test that a policy with one matching value passes"""
        self.enrich_context()
        policy = GeoIPPolicy.objects.create(
            asns=self.mismatching_asns, countries=self.matching_countries
        )

        result: PolicyResult = policy.passes(self.request)

        self.assertTrue(result.passing)

    def test_distance_missing_or_invalid_current_geoip(self):
        """Missing and invalid current coordinates pass as not evaluable."""
        policy = GeoIPPolicy.objects.create(check_impossible_travel=True)
        invalid_geoip = (
            None,
            {},
            {"lat": 0},
            {"lat": "0", "long": 0},
            {"lat": 0, "long": "0"},
            {"lat": True, "long": 0},
            {"lat": 91, "long": 0},
            {"lat": 0, "long": -181},
            {"lat": 10**1000, "long": 0},
            {"lat": 0, "long": 10**1000},
            {"lat": float("nan"), "long": 0},
            {"lat": 0, "long": float("inf")},
        )

        for geoip_data in invalid_geoip:
            with self.subTest(geoip_data=geoip_data):
                self.request.context["geoip"] = geoip_data
                self.assertTrue(policy.passes(self.request).passing)

    def test_distance_no_history(self):
        """A distance policy passes when there is no login history."""
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        policy = GeoIPPolicy.objects.create(check_impossible_travel=True)

        self.assertTrue(policy.passes(self.request).passing)

    def test_distance_only_invalid_history(self):
        """A distance policy passes when no historical coordinates are usable."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        for geo in (None, {}, {"lat": 0}, {"lat": 100, "long": 0}):
            self.create_login(geo, current_time - timedelta(minutes=30))
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        policy = GeoIPPolicy.objects.create(check_impossible_travel=True)

        with mock.patch("authentik.policies.geoip.models.now", return_value=current_time):
            self.assertTrue(policy.passes(self.request).passing)

    def test_distance_invalid_history_is_skipped(self):
        """Invalid recent history does not hide an older impossible login."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        violating_login = self.create_login(
            {"lat": 0, "long": 20}, current_time - timedelta(minutes=30)
        )
        self.create_login({"lat": "invalid", "long": 0}, current_time - timedelta(minutes=10))
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        policy = GeoIPPolicy.objects.create(check_impossible_travel=True)

        with mock.patch("authentik.policies.geoip.models.now", return_value=current_time):
            result = policy.passes(self.request)

        self.assertFalse(result.passing)
        self.assertEqual(result.raw_result["previous_login_event"], violating_login.event_uuid)

    def test_distance_checks_every_usable_login(self):
        """A passing recent login does not hide an older impossible login."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        violating_login = self.create_login(
            {"lat": 0, "long": 20}, current_time - timedelta(minutes=30)
        )
        self.create_login({"lat": 0, "long": 0}, current_time - timedelta(minutes=10))
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        policy = GeoIPPolicy.objects.create(check_impossible_travel=True)

        with mock.patch("authentik.policies.geoip.models.now", return_value=current_time):
            result = policy.passes(self.request)

        self.assertFalse(result.passing)
        self.assertEqual(result.raw_result["previous_login_event"], violating_login.event_uuid)

    def test_impossible_travel_same_location(self):
        """Travel from the same location passes."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        self.create_login({"lat": 10, "long": 10}, current_time - timedelta(minutes=5))
        self.request.context["geoip"] = {"lat": 10, "long": 10}
        policy = GeoIPPolicy.objects.create(check_impossible_travel=True)

        with mock.patch("authentik.policies.geoip.models.now", return_value=current_time):
            self.assertTrue(policy.passes(self.request).passing)

    def test_impossible_travel_uses_fractional_hours(self):
        """An interval just below two hours is not floored to one hour."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        self.create_login({"lat": 0, "long": 18}, current_time - timedelta(minutes=119))
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        policy = GeoIPPolicy.objects.create(
            check_impossible_travel=True, impossible_tolerance_km=100
        )

        with mock.patch("authentik.policies.geoip.models.now", return_value=current_time):
            self.assertTrue(policy.passes(self.request).passing)

    def test_impossible_travel_one_hour_minimum_and_boundary(self):
        """Short intervals use one hour and equality rejects travel."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        self.create_login({"lat": 0, "long": 10}, current_time - timedelta(minutes=30))
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        policy = GeoIPPolicy.objects.create(
            check_impossible_travel=True, impossible_tolerance_km=100
        )

        with (
            mock.patch("authentik.policies.geoip.models.now", return_value=current_time),
            mock.patch(
                "authentik.policies.geoip.models.distance.geodesic",
                return_value=SimpleNamespace(km=1100),
            ),
        ):
            result = policy.passes(self.request)

        self.assertFalse(result.passing)
        self.assertEqual(result.raw_result["elapsed_hours"], 1.0)
        self.assertEqual(result.raw_result["allowed_distance_km"], 1100)

    def test_distance_checks_use_separate_tolerances(self):
        """History and impossible-travel checks use their dedicated tolerances."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        self.create_login({"lat": 0, "long": 10}, current_time - timedelta(minutes=30))
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        history_policy = GeoIPPolicy.objects.create(
            name="history-distance-tolerance",
            check_history_distance=True,
            history_max_distance_km=1000,
            distance_tolerance_km=200,
        )
        impossible_policy = GeoIPPolicy.objects.create(
            name="impossible-travel-tolerance",
            check_impossible_travel=True,
            distance_tolerance_km=500,
            impossible_tolerance_km=0,
        )

        with mock.patch("authentik.policies.geoip.models.now", return_value=current_time):
            self.assertTrue(history_policy.passes(self.request).passing)
            self.assertFalse(impossible_policy.passes(self.request).passing)

    def test_impossible_travel_diagnostics(self):
        """A rejection identifies the historical event and threshold."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        previous_login = self.create_login(
            {"lat": 0, "long": 20}, current_time - timedelta(minutes=30)
        )
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        policy = GeoIPPolicy.objects.create(
            check_impossible_travel=True, impossible_tolerance_km=100
        )

        with mock.patch("authentik.policies.geoip.models.now", return_value=current_time):
            result = policy.passes(self.request)

        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("Distance is further than possible.",))
        self.assertEqual(result.raw_result["reason"], "impossible_travel_threshold_exceeded")
        self.assertGreater(result.raw_result["distance_km"], 2200)
        self.assertEqual(result.raw_result["allowed_distance_km"], 1100)
        self.assertEqual(result.raw_result["elapsed_hours"], 1.0)
        self.assertEqual(result.raw_result["max_speed_km_per_hour"], 1000)
        self.assertEqual(result.raw_result["impossible_tolerance_km"], 100)
        self.assertEqual(result.raw_result["previous_login_at"], previous_login.created)
        self.assertEqual(result.raw_result["previous_login_event"], previous_login.event_uuid)
        self.assertEqual(result.raw_result["current_geo"], {"lat": 0.0, "long": 0.0})
        self.assertEqual(result.raw_result["previous_geo"], {"lat": 0.0, "long": 20.0})

    def test_impossible_travel_diagnostics_in_execution_event(self):
        """Execution logging retains sanitized impossible-travel diagnostics."""
        current_time = datetime(2026, 1, 1, tzinfo=UTC)
        previous_login = self.create_login(
            {"lat": 0, "long": 20}, current_time - timedelta(minutes=30)
        )
        self.request.context["geoip"] = {"lat": 0, "long": 0}
        policy = GeoIPPolicy.objects.create(
            check_impossible_travel=True,
            impossible_tolerance_km=100,
            execution_logging=True,
        )

        with mock.patch("authentik.policies.geoip.models.now", return_value=current_time):
            result = PolicyProcess(
                PolicyBinding(policy=policy), self.request, connection=None
            ).execute()

        event = Event.objects.get(
            action=EventAction.POLICY_EXECUTION,
            context__policy_uuid=policy.policy_uuid.hex,
        )
        diagnostics = event.context["result"]["raw_result"]
        self.assertFalse(result.passing)
        self.assertEqual(diagnostics["reason"], "impossible_travel_threshold_exceeded")
        self.assertEqual(diagnostics["previous_login_event"], previous_login.event_uuid.hex)
        self.assertEqual(diagnostics["previous_login_at"], "2025-12-31T23:30:00Z")
        self.assertEqual(diagnostics["allowed_distance_km"], 1100)
