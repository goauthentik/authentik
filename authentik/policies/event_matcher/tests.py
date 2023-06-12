"""event_matcher tests"""
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.events.models import Event, EventAction
from authentik.policies.event_matcher.models import EventMatcherPolicy
from authentik.policies.types import PolicyRequest


class TestEventMatcherPolicy(TestCase):
    """EventMatcherPolicy tests"""

    def test_match_action(self):
        """Test match action"""
        event = Event.new(EventAction.LOGIN)
        request = PolicyRequest(get_anonymous_user())
        request.context["event"] = event
        policy: EventMatcherPolicy = EventMatcherPolicy.objects.create(action=EventAction.LOGIN)
        response = policy.passes(request)
        self.assertTrue(response.passing)
        self.assertTupleEqual(response.messages, ("Action matched.",))

    def test_match_client_ip(self):
        """Test match client_ip"""
        event = Event.new(EventAction.LOGIN)
        event.client_ip = "1.2.3.4"
        request = PolicyRequest(get_anonymous_user())
        request.context["event"] = event
        policy: EventMatcherPolicy = EventMatcherPolicy.objects.create(client_ip="1.2.3.4")
        response = policy.passes(request)
        self.assertTrue(response.passing)
        self.assertTupleEqual(response.messages, ("Client IP matched.",))

    def test_match_app(self):
        """Test match app"""
        event = Event.new(EventAction.LOGIN)
        event.app = "foo"
        request = PolicyRequest(get_anonymous_user())
        request.context["event"] = event
        policy: EventMatcherPolicy = EventMatcherPolicy.objects.create(app="foo")
        response = policy.passes(request)
        self.assertTrue(response.passing)
        self.assertTupleEqual(response.messages, ("App matched.",))

    def test_match_model(self):
        """Test match model"""
        event = Event.new(EventAction.LOGIN)
        event.context = {
            "model": {
                "app": "foo",
                "model_name": "bar",
            }
        }
        request = PolicyRequest(get_anonymous_user())
        request.context["event"] = event
        policy: EventMatcherPolicy = EventMatcherPolicy.objects.create(model="foo.bar")
        response = policy.passes(request)
        self.assertTrue(response.passing)
        self.assertTupleEqual(response.messages, ("Model matched.",))

    def test_drop(self):
        """Test drop event"""
        event = Event.new(EventAction.LOGIN)
        event.client_ip = "1.2.3.4"
        request = PolicyRequest(get_anonymous_user())
        request.context["event"] = event
        policy: EventMatcherPolicy = EventMatcherPolicy.objects.create(client_ip="1.2.3.5")
        response = policy.passes(request)
        self.assertFalse(response.passing)

    def test_drop_multiple(self):
        """Test drop event"""
        event = Event.new(EventAction.LOGIN)
        event.app = "foo"
        event.client_ip = "1.2.3.4"
        request = PolicyRequest(get_anonymous_user())
        request.context["event"] = event
        policy: EventMatcherPolicy = EventMatcherPolicy.objects.create(
            client_ip="1.2.3.5", app="bar"
        )
        response = policy.passes(request)
        self.assertFalse(response.passing)

    def test_invalid(self):
        """Test passing event"""
        request = PolicyRequest(get_anonymous_user())
        policy: EventMatcherPolicy = EventMatcherPolicy.objects.create(client_ip="1.2.3.4")
        response = policy.passes(request)
        self.assertFalse(response.passing)
