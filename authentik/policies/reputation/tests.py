"""test reputation signals and policy"""

from django.test import RequestFactory, TestCase

from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.policies.reputation.api import ReputationPolicySerializer
from authentik.policies.reputation.models import Reputation, ReputationPolicy
from authentik.policies.reputation.signals import update_score
from authentik.policies.types import PolicyRequest
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import authenticate
from authentik.tenants.models import DEFAULT_REPUTATION_LOWER_LIMIT, DEFAULT_REPUTATION_UPPER_LIMIT


class TestReputationPolicy(TestCase):
    """test reputation signals and policy"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get("/")
        self.ip = "127.0.0.1"
        self.username = "username"
        self.password = generate_id()
        # We need a user for the one-to-one in userreputation
        self.user = User.objects.create(username=self.username)
        self.user.set_password(self.password)
        self.backends = [BACKEND_INBUILT]

    def test_ip_reputation(self):
        """test IP reputation"""
        # Trigger negative reputation
        authenticate(self.request, self.backends, username=self.username, password=self.username)
        self.assertEqual(Reputation.objects.get(ip=self.ip).score, -1)

    def test_user_reputation(self):
        """test User reputation"""
        # Trigger negative reputation
        authenticate(self.request, self.backends, username=self.username, password=self.username)
        self.assertEqual(Reputation.objects.get(identifier=self.username).score, -1)

    def test_update_reputation(self):
        """test reputation update"""
        Reputation.objects.create(identifier=self.username, ip=self.ip, score=4)
        # Trigger negative reputation
        authenticate(self.request, self.backends, username=self.username, password=self.username)
        self.assertEqual(Reputation.objects.get(identifier=self.username).score, 3)

    def test_reputation_lower_limit(self):
        """test reputation lower limit"""
        Reputation.objects.create(identifier=self.username, ip=self.ip)
        update_score(self.request, identifier=self.username, amount=-1000)
        self.assertEqual(
            Reputation.objects.get(identifier=self.username).score, DEFAULT_REPUTATION_LOWER_LIMIT
        )

    def test_reputation_upper_limit(self):
        """test reputation upper limit"""
        Reputation.objects.create(identifier=self.username, ip=self.ip)
        update_score(self.request, identifier=self.username, amount=1000)
        self.assertEqual(
            Reputation.objects.get(identifier=self.username).score, DEFAULT_REPUTATION_UPPER_LIMIT
        )

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
