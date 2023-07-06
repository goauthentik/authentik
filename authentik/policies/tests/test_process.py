"""policy process tests"""
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from django.views.debug import SafeExceptionReporterFilter
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Application, Group, User
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import Policy, PolicyBinding
from authentik.policies.process import PolicyProcess
from authentik.policies.types import CACHE_PREFIX, PolicyRequest


def clear_policy_cache():
    """Ensure no policy-related keys are still cached"""
    keys = cache.keys(f"{CACHE_PREFIX}*")
    cache.delete(keys)


class TestPolicyProcess(TestCase):
    """Policy Process tests"""

    def setUp(self):
        clear_policy_cache()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="policyuser")

    def test_group_passing(self):
        """Test binding to group"""
        group = Group.objects.create(name="test-group")
        group.users.add(self.user)
        group.save()
        binding = PolicyBinding(group=group)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, True)

    def test_group_negative(self):
        """Test binding to group"""
        group = Group.objects.create(name="test-group")
        group.save()
        binding = PolicyBinding(group=group)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)

    def test_user_passing(self):
        """Test binding to user"""
        binding = PolicyBinding(user=self.user)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, True)

    def test_user_negative(self):
        """Test binding to user"""
        binding = PolicyBinding(user=get_anonymous_user())

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)

    def test_empty(self):
        """Test binding to user"""
        binding = PolicyBinding()

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)

    def test_invalid(self):
        """Test Process with invalid arguments"""
        policy = DummyPolicy.objects.create(result=True, wait_min=0, wait_max=1)
        binding = PolicyBinding(policy=policy)
        with self.assertRaises(ValueError):
            PolicyProcess(binding, None, None)  # type: ignore

    def test_true(self):
        """Test policy execution"""
        policy = DummyPolicy.objects.create(result=True, wait_min=0, wait_max=1)
        binding = PolicyBinding(policy=policy)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, True)
        self.assertEqual(response.messages, ("dummy",))

    def test_false(self):
        """Test policy execution"""
        policy = DummyPolicy.objects.create(result=False, wait_min=0, wait_max=1)
        binding = PolicyBinding(policy=policy)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)
        self.assertEqual(response.messages, ("dummy",))

    def test_negate(self):
        """Test policy execution"""
        policy = DummyPolicy.objects.create(result=False, wait_min=0, wait_max=1)
        binding = PolicyBinding(policy=policy, negate=True)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, True)
        self.assertEqual(response.messages, ("dummy",))

    def test_exception(self):
        """Test policy execution"""
        policy = Policy.objects.create(name="test-execution")
        binding = PolicyBinding(policy=policy, target=Application.objects.create(name="test"))

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)

    def test_execution_logging(self):
        """Test policy execution creates event"""
        policy = DummyPolicy.objects.create(
            name="test-execution-logging",
            result=False,
            wait_min=0,
            wait_max=1,
            execution_logging=True,
        )
        binding = PolicyBinding(policy=policy, target=Application.objects.create(name="test"))

        http_request = self.factory.get(reverse("authentik_api:user-impersonate-end"))
        http_request.user = self.user
        http_request.resolver_match = resolve(reverse("authentik_api:user-impersonate-end"))

        request = PolicyRequest(self.user)
        request.set_http_request(http_request)
        request.context = {
            "complex": {
                "dict": {"foo": "bar"},
                "list": ["foo", "bar"],
                "tuple": ("foo", "bar"),
                "set": {"foo", "bar"},
                "password": generate_id(),
            }
        }
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)
        self.assertEqual(response.messages, ("dummy",))

        events = Event.objects.filter(
            action=EventAction.POLICY_EXECUTION,
            context__policy_uuid=policy.policy_uuid.hex,
        )
        self.assertTrue(events.exists())
        self.assertEqual(len(events), 1)
        event = events.first()
        self.assertEqual(event.user["username"], self.user.username)
        self.assertEqual(event.context["result"]["passing"], False)
        self.assertEqual(event.context["result"]["messages"], ["dummy"])
        self.assertEqual(event.client_ip, "127.0.0.1")
        # Python sets don't preserve order when converted to list,
        # so ensure we sort the converted set
        event.context["request"]["context"]["complex"]["set"].sort()
        self.assertEqual(
            event.context["request"]["context"],
            {
                "complex": {
                    "set": [
                        "bar",
                        "foo",
                    ],
                    "dict": {"foo": "bar"},
                    "list": ["foo", "bar"],
                    "tuple": ["foo", "bar"],
                    "password": SafeExceptionReporterFilter.cleansed_substitute,
                }
            },
        )

    def test_execution_logging_anonymous(self):
        """Test policy execution creates event with anonymous user"""
        policy = DummyPolicy.objects.create(
            name="test-execution-logging-anon",
            result=False,
            wait_min=0,
            wait_max=1,
            execution_logging=True,
        )
        binding = PolicyBinding(policy=policy, target=Application.objects.create(name="test"))

        user = AnonymousUser()

        http_request = self.factory.get("/")
        http_request.user = user

        request = PolicyRequest(user)
        request.set_http_request(http_request)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)
        self.assertEqual(response.messages, ("dummy",))

        events = Event.objects.filter(
            action=EventAction.POLICY_EXECUTION,
            context__policy_uuid=policy.policy_uuid.hex,
        )
        self.assertTrue(events.exists())
        self.assertEqual(len(events), 1)
        event = events.first()
        self.assertEqual(event.user["username"], "AnonymousUser")
        self.assertEqual(event.context["result"]["passing"], False)
        self.assertEqual(event.context["result"]["messages"], ["dummy"])
        self.assertEqual(event.client_ip, "127.0.0.1")

    def test_raises(self):
        """Test policy that raises error"""
        policy_raises = ExpressionPolicy.objects.create(name="raises", expression="{{ 0/0 }}")
        binding = PolicyBinding(
            policy=policy_raises, target=Application.objects.create(name="test")
        )

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)
        self.assertEqual(response.messages, ("division by zero",))

        events = Event.objects.filter(
            action=EventAction.POLICY_EXCEPTION,
            context__policy_uuid=policy_raises.policy_uuid.hex,
        )
        self.assertTrue(events.exists())
        self.assertEqual(len(events), 1)
        event = events.first()
        self.assertEqual(event.user["username"], self.user.username)
        self.assertIn("division by zero", event.context["message"])
