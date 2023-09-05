"""test reputation signals and policy"""
from django.core.cache import cache
from django.test import RequestFactory, TestCase

from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.policies.reputation.api import ReputationPolicySerializer
from authentik.policies.reputation.models import CACHE_KEY_PREFIX, Reputation, ReputationPolicy
from authentik.policies.reputation.tasks import save_reputation
from authentik.policies.types import PolicyRequest
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import authenticate


class TestReputationPolicy(TestCase):
    """test reputation signals and policy"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get("/")
        self.test_ip = "127.0.0.1"
        self.test_username = "test"
        keys = cache.keys(CACHE_KEY_PREFIX + "*")
        cache.delete_many(keys)
        # We need a user for the one-to-one in userreputation
        self.user = User.objects.create(username=self.test_username)
        self.backends = [BACKEND_INBUILT]

    def test_ip_reputation(self):
        """test IP reputation"""
        # Trigger negative reputation
        authenticate(
            self.request, self.backends, username=self.test_username, password=self.test_username
        )
        # Test value in cache
        self.assertEqual(
            cache.get(CACHE_KEY_PREFIX + self.test_ip + "/" + self.test_username),
            {"ip": "127.0.0.1", "identifier": "test", "score": -1},
        )
        # Save cache and check db values
        save_reputation.delay().get()
        self.assertEqual(Reputation.objects.get(ip=self.test_ip).score, -1)

    def test_user_reputation(self):
        """test User reputation"""
        # Trigger negative reputation
        authenticate(
            self.request, self.backends, username=self.test_username, password=self.test_username
        )
        # Test value in cache
        self.assertEqual(
            cache.get(CACHE_KEY_PREFIX + self.test_ip + "/" + self.test_username),
            {"ip": "127.0.0.1", "identifier": "test", "score": -1},
        )
        # Save cache and check db values
        save_reputation.delay().get()
        self.assertEqual(Reputation.objects.get(identifier=self.test_username).score, -1)

    def test_policy(self):
        """Test Policy"""
        request = PolicyRequest(user=self.user)
        policy: ReputationPolicy = ReputationPolicy.objects.create(
            name="reputation-test", threshold=0
        )
        self.assertTrue(policy.passes(request).passing)

    def test_api(self):
        """Test API Validation"""
        no_toggle = ReputationPolicySerializer(data={"name": generate_id(), "threshold": -5})
        self.assertFalse(no_toggle.is_valid())
