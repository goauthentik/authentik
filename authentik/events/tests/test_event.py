"""event tests"""
from urllib.parse import urlencode

from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.views.debug import SafeExceptionReporterFilter
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Group
from authentik.events.models import Event
from authentik.flows.views.executor import QS_QUERY
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.tenants.models import Tenant


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
            event.context, {"http_request": {"args": {}, "method": "GET", "path": "/"}}
        )

    def test_from_http_clean_querystring(self):
        """Test cleansing query string"""
        request = self.factory.get(f"/?token={generate_id()}")
        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.context,
            {
                "http_request": {
                    "args": {"token": SafeExceptionReporterFilter.cleansed_substitute},
                    "method": "GET",
                    "path": "/",
                }
            },
        )

    def test_from_http_clean_querystring_flow(self):
        """Test cleansing query string (nested query string like flow executor)"""
        nested_qs = {"token": generate_id()}
        request = self.factory.get(f"/?{QS_QUERY}={urlencode(nested_qs)}")
        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.context,
            {
                "http_request": {
                    "args": {"token": SafeExceptionReporterFilter.cleansed_substitute},
                    "method": "GET",
                    "path": "/",
                }
            },
        )

    def test_from_http_tenant(self):
        """Test from_http tenant"""
        # Test tenant
        request = self.factory.get("/")
        tenant = Tenant(domain="test-tenant")
        setattr(request, "tenant", tenant)
        event = Event.new("unittest").from_http(request)
        self.assertEqual(
            event.tenant,
            {
                "app": "authentik_tenants",
                "model_name": "tenant",
                "name": "Tenant test-tenant",
                "pk": tenant.pk.hex,
            },
        )
