"""event tests"""

from textwrap import dedent
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.debug import SafeExceptionReporterFilter
from guardian.shortcuts import get_anonymous_user

from authentik.blueprints.v1.importer import Importer
from authentik.brands.models import Brand
from authentik.core.models import Group, Source, User
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.events.middleware import event_origin
from authentik.events.models import Event, EventAction
from authentik.events.tasks import gdpr_cleanup
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views.executor import QS_QUERY, SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.tenants.utils import get_current_tenant


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

    def test_invalid_string(self):
        """Test creating an event with invalid unicode string data"""
        event = Event.new("unittest", foo="foo bar \u0000 baz")
        event.save()
        self.assertEqual(event.context["foo"], "foo bar  baz")

    def test_password_set_signal_on_set_password_from_hash(self):
        """Changing password from hash should still emit an audit event."""
        user = create_test_user()
        old_count = Event.objects.filter(action=EventAction.PASSWORD_SET, user__pk=user.pk).count()

        user.set_password_from_hash(make_password(generate_id()))
        user.save()

        new_count = Event.objects.filter(action=EventAction.PASSWORD_SET, user__pk=user.pk).count()
        self.assertEqual(new_count, old_count + 1)

    def test_password_set_event(self):
        """Password changes should carry subject_uuid and synced_from_source"""
        user = create_test_user()

        user.set_password(generate_id())
        user.save()

        event = (
            Event.objects.filter(action=EventAction.PASSWORD_SET, user__pk=user.pk)
            .order_by("-created")
            .first()
        )
        self.assertFalse(event.context["synced_from_source"])
        self.assertEqual(event.context["subject_uuid"], user.uuid.hex)

    def test_password_set_synced_from_source(self):
        """Passwords cached from a source login should be flagged as synced_from_source"""
        user = create_test_user()

        source = Source.objects.create(name=generate_id(), slug=generate_id())
        user.set_password(generate_id(), sender=source)
        user.save()

        event = (
            Event.objects.filter(action=EventAction.PASSWORD_SET, user__pk=user.pk)
            .order_by("-created")
            .first()
        )
        self.assertTrue(event.context["synced_from_source"])

    def test_user_created_event(self):
        """Creating a user in a request context should emit a user_created event"""
        admin = create_test_admin_user()
        self.client.force_login(admin)
        username = generate_id()

        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"username": username, "name": username},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(username=username)
        event = Event.objects.filter(
            action=EventAction.USER_CREATED, context__subject_uuid=user.uuid.hex
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["username"], username)
        self.assertEqual(event.context["user_type"], "internal")
        self.assertEqual(event.context["origin"], "http")
        self.assertEqual(event.user["pk"], admin.pk)

    def test_user_created_event_no_request(self):
        """Creating a user outside a request context should emit user_created
        with an unknown origin"""
        user = create_test_user()
        event = Event.objects.filter(
            action=EventAction.USER_CREATED, context__subject_uuid=user.uuid.hex
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["origin"], "unknown")

    def test_user_created_event_origin_stamp(self):
        """Users created inside an event_origin block should carry that origin"""
        with event_origin("source_sync"):
            user = create_test_user()
        event = Event.objects.filter(
            action=EventAction.USER_CREATED, context__subject_uuid=user.uuid.hex
        ).first()
        self.assertEqual(event.context["origin"], "source_sync")

    def test_user_created_event_origin_blueprint(self):
        """Users created by a blueprint apply should carry origin "blueprint" """
        username = generate_id()
        importer = Importer.from_string(dedent(f"""
                version: 1
                entries:
                  - model: authentik_core.user
                    identifiers:
                      username: {username}
                    attrs:
                      name: {username}
                """))
        self.assertTrue(importer.apply())
        user = User.objects.get(username=username)
        event = Event.objects.filter(
            action=EventAction.USER_CREATED, context__subject_uuid=user.uuid.hex
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["origin"], "blueprint")

    def test_gdpr_cleanup_subject_events(self):
        """GDPR cleanup should remove events about the user, not only events by them"""
        admin = create_test_admin_user()
        user = create_test_user()
        actored_by_user = Event.new("some_action").set_user(user)
        actored_by_user.save()
        about_user = Event.new(EventAction.USER_CREATED, subject_uuid=user.uuid).set_user(admin)
        about_user.save()
        unrelated = Event.new("some_action").set_user(admin)
        unrelated.save()

        gdpr_cleanup(user.pk, user.uuid.hex)

        self.assertFalse(Event.objects.filter(pk=actored_by_user.pk).exists())
        self.assertFalse(Event.objects.filter(pk=about_user.pk).exists())
        self.assertTrue(Event.objects.filter(pk=unrelated.pk).exists())

    def test_gdpr_cleanup_dispatched_with_uuid(self):
        """Deleting a user with gdpr_compliance should dispatch cleanup with pk and uuid"""
        user = create_test_user()
        user_pk = user.pk
        user_uuid = user.uuid.hex
        tenant = get_current_tenant()
        tenant.gdpr_compliance = True
        tenant.save()
        try:
            with patch("authentik.events.tasks.gdpr_cleanup.send") as send_mock:
                user.delete()
            send_mock.assert_called_once_with(user_pk, user_uuid)
        finally:
            tenant.gdpr_compliance = False
            tenant.save()

    def test_log_deprecation(self):
        """Test Event.log_deprecation"""
        Event.log_deprecation(self.__module__, "Test deprecation")
        Event.log_deprecation(self.__module__, "Test deprecation")
        Event.log_deprecation(self.__module__, "Test deprecation")
        Event.log_deprecation(self.__module__, "Test deprecation", cause=create_test_user())
        logs = Event.objects.filter(
            action=EventAction.CONFIGURATION_WARNING, context__deprecation=self.__module__
        )
        self.assertEqual(logs.count(), 2)
