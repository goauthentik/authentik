"""event tests"""

from urllib.parse import urlencode

from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.views.debug import SafeExceptionReporterFilter
from guardian.shortcuts import get_anonymous_user

from authentik.brands.models import Brand
from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views.executor import QS_QUERY, SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy


class TestEvents(TestCase):
    """Test Event"""

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_new_with_model(self):
        """Create a new Event passing a model as kwarg"""
        test_model = Group.objects.create(name="test")
        event = Event.new("unittest", test={"model": test_model})
        event.save()  # We save to ensure nothing is un-saveable
        model_content_type = ContentType.objects.get_for_model(test_model)
        self.assertEqual(
            event.context.get("test").get("model").get("app"),
            model_content_type.app_label,
        )

    def test_new_with_user(self):
        """Create a new Event passing a user as kwarg"""
        event = Event.new("unittest", test={"model": get_anonymous_user()})
        event.save()  # We save to ensure nothing is un-saveable
        self.assertEqual(
            event.context.get("test").get("model").get("username"),
            get_anonymous_user().username,
        )

    def test_new_with_uuid_model(self):
        """Create a new Event passing a model (with UUID PK) as kwarg"""
        temp_model = DummyPolicy.objects.create(name="test", result=True)
        event = Event.new("unittest", model=temp_model)
        event.save()  # We save to ensure nothing is un-saveable
        model_content_type = ContentType.objects.get_for_model(temp_model)
        self.assertEqual(event.context.get("model").get("app"), model_content_type.app_label)
        self.assertEqual(event.context.get("model").get("pk"), temp_model.pk.hex)

    def test_from_http_basic(self):
        """Test plain from_http"""
        event = Event.new("unittest").from_http(self.factory.get("/"))
        self.assertEqual(
            event.context,
            {
                "http_request": {
                    "args": {},
                    "method": "GET",
                    "path": "/",
                    "user_agent": "",
                }
            },
        )

    def test_from_http_clean_querystring(self):
        """Test cleansing query string"""
        token = generate_id()
        request = self.factory.get(f"/?token={token}")
        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.context,
            {
                "http_request": {
                    "args": {"token": SafeExceptionReporterFilter.cleansed_substitute},
                    "method": "GET",
                    "path": "/",
                    "user_agent": "",
                }
            },
        )

    def test_from_http_clean_querystring_flow(self):
        """Test cleansing query string (nested query string like flow executor)"""
        token = generate_id()
        nested_qs = {"token": token}
        request = self.factory.get(f"/?{QS_QUERY}={urlencode(nested_qs)}")
        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.context,
            {
                "http_request": {
                    "args": {"token": SafeExceptionReporterFilter.cleansed_substitute},
                    "method": "GET",
                    "path": "/",
                    "user_agent": "",
                }
            },
        )

    def test_from_http_brand(self):
        """Test from_http brand"""
        # Test brand
        request = self.factory.get("/")
        brand = Brand(domain="test-brand")
        request.brand = brand
        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.brand,
            {
                "app": "authentik_brands",
                "model_name": "brand",
                "name": "Brand test-brand",
                "pk": brand.pk.hex,
            },
        )

    def test_from_http_flow_pending_user(self):
        """Test request from flow request with a pending user"""
        user = create_test_user()

        session = self.client.session
        plan = FlowPlan(generate_id())
        plan.context[PLAN_CONTEXT_PENDING_USER] = user
        session[SESSION_KEY_PLAN] = plan
        session.save()

        request = self.factory.get("/")
        request.session = session
        request.user = user

        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.user,
            {
                "email": user.email,
                "pk": user.pk,
                "username": user.username,
            },
        )

    def test_from_http_flow_pending_user_anon(self):
        """Test request from flow request with a pending user"""
        user = create_test_user()
        anon = get_anonymous_user()

        session = self.client.session
        plan = FlowPlan(generate_id())
        plan.context[PLAN_CONTEXT_PENDING_USER] = user
        session[SESSION_KEY_PLAN] = plan
        session.save()

        request = self.factory.get("/")
        request.session = session
        request.user = anon

        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.user,
            {
                "authenticated_as": {
                    "pk": anon.pk,
                    "is_anonymous": True,
                    "username": "AnonymousUser",
                    "email": "",
                },
                "email": user.email,
                "pk": user.pk,
                "username": user.username,
            },
        )

    def test_from_http_flow_pending_user_fake(self):
        """Test request from flow request with a pending user"""
        user = User(
            username=generate_id(),
            email=generate_id(),
        )
        anon = get_anonymous_user()

        session = self.client.session
        plan = FlowPlan(generate_id())
        plan.context[PLAN_CONTEXT_PENDING_USER] = user
        session[SESSION_KEY_PLAN] = plan
        session.save()

        request = self.factory.get("/")
        request.session = session
        request.user = anon

        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.user,
            {
                "authenticated_as": {
                    "pk": anon.pk,
                    "is_anonymous": True,
                    "username": "AnonymousUser",
                    "email": "",
                },
                "email": user.email,
                "pk": user.pk,
                "username": user.username,
            },
        )

    def test_password_set_signal_on_set_password_from_hash(self):
        """Changing password from hash should still emit an audit event."""
        user = create_test_user()
        old_count = Event.objects.filter(action=EventAction.PASSWORD_SET, user__pk=user.pk).count()

        user.set_password_from_hash(make_password(generate_id()))
        user.save()

        new_count = Event.objects.filter(action=EventAction.PASSWORD_SET, user__pk=user.pk).count()
        self.assertEqual(new_count, old_count + 1)
