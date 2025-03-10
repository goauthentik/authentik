"""geoip policy tests"""

from django.test import TestCase

from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.events.utils import get_user
from authentik.policies.engine import PolicyRequest, PolicyResult
from authentik.policies.exceptions import PolicyException
from authentik.policies.geoip.exceptions import GeoIPNotFoundException
from authentik.policies.geoip.models import GeoIPPolicy


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

    def test_history(self):
        """Test history checks"""
        Event.objects.create(
            action=EventAction.LOGIN,
            user=get_user(self.user),
            context={
                # Random location in Canada
                "geo": {"lat": 55.868351, "long": -104.441011},
            },
        )
        # Random location in Poland
        self.request.context["geoip"] = {"lat": 50.950613, "long": 20.363679}

        policy = GeoIPPolicy.objects.create(check_history_distance=True)

        result: PolicyResult = policy.passes(self.request)
        self.assertFalse(result.passing)

    def test_history_no_data(self):
        """Test history checks (with no geoip data in context)"""
        Event.objects.create(
            action=EventAction.LOGIN,
            user=get_user(self.user),
            context={
                # Random location in Canada
                "geo": {"lat": 55.868351, "long": -104.441011},
            },
        )

        policy = GeoIPPolicy.objects.create(check_history_distance=True)

        result: PolicyResult = policy.passes(self.request)
        self.assertFalse(result.passing)

    def test_history_impossible_travel(self):
        """Test history checks"""
        Event.objects.create(
            action=EventAction.LOGIN,
            user=get_user(self.user),
            context={
                # Random location in Canada
                "geo": {"lat": 55.868351, "long": -104.441011},
            },
        )
        # Random location in Poland
        self.request.context["geoip"] = {"lat": 50.950613, "long": 20.363679}

        policy = GeoIPPolicy.objects.create(check_impossible_travel=True)

        result: PolicyResult = policy.passes(self.request)
        self.assertFalse(result.passing)

    def test_history_no_geoip(self):
        """Test history checks (previous login with no geoip data)"""
        Event.objects.create(
            action=EventAction.LOGIN,
            user=get_user(self.user),
            context={},
        )
        # Random location in Poland
        self.request.context["geoip"] = {"lat": 50.950613, "long": 20.363679}

        policy = GeoIPPolicy.objects.create(check_history_distance=True)

        result: PolicyResult = policy.passes(self.request)
        self.assertFalse(result.passing)
