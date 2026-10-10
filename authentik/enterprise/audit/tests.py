from unittest.mock import Mock, PropertyMock, patch

from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_init
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.admin.flags import patch_flag
from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.enterprise.audit.apps import AuditIncludeExpandedDiff
from authentik.enterprise.audit.middleware import EnterpriseAuditMiddleware
from authentik.events.middleware import _CTX_REQUEST
from authentik.events.models import Event, EventAction
from authentik.events.utils import sanitize_item
from authentik.lib.generators import generate_id


class TestEnterpriseAudit(APITestCase):
    """Test audit middleware"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()

    def test_import(self):
        """Ensure middleware is imported when app.ready is called"""
        # Revert import swap
        orig_import = "authentik.events.middleware.AuditMiddleware"
        new_import = "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware"
        settings.MIDDLEWARE = [orig_import if x == new_import else x for x in settings.MIDDLEWARE]
        # Re-call ready()
        apps.get_app_config("authentik_enterprise_audit").ready()
        self.assertIn(
            "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware", settings.MIDDLEWARE
        )

    @patch(
        "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
        PropertyMock(return_value=True),
    )
    def test_create(self):
        """Test create audit log"""
        self.client.force_login(self.user)
        username = generate_id()
        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": username, "groups": [], "path": "foo"},
        )
        user = User.objects.get(username=username)
        self.assertEqual(response.status_code, 201)
        events = Event.objects.filter(
            action=EventAction.MODEL_CREATED,
            context__model__model_name="user",
            context__model__app="authentik_core",
            context__model__pk=user.pk,
        )
        event = events.first()
        self.assertIsNotNone(event)
        self.assertIsNotNone(event.context["diff"])
        diff = event.context["diff"]
        diff.pop("last_updated")
        self.assertEqual(
            diff,
            {
                "name": {
                    "new_value": user.name,
                    "previous_value": None,
                },
                "path": {"new_value": "foo", "previous_value": None},
                "type": {"new_value": "internal", "previous_value": None},
                "uuid": {
                    "new_value": user.uuid.hex,
                    "previous_value": None,
                },
                "email": {"new_value": "", "previous_value": None},
                "username": {
                    "new_value": user.username,
                    "previous_value": None,
                },
                "is_active": {"new_value": True, "previous_value": None},
                "attributes": {"new_value": {}, "previous_value": None},
                "date_joined": {
                    "new_value": sanitize_item(user.date_joined),
                    "previous_value": None,
                },
                "first_name": {"new_value": "", "previous_value": None},
                "id": {"new_value": user.pk, "previous_value": None},
                "last_name": {"new_value": "", "previous_value": None},
            },
        )

    @patch(
        "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
        PropertyMock(return_value=True),
    )
    def test_update(self):
        """Test update audit log"""
        self.client.force_login(self.user)
        user = create_test_admin_user()
        current_name = user.name
        new_name = generate_id()
        response = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": user.id}),
            data={"name": new_name},
        )
        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        events = Event.objects.filter(
            action=EventAction.MODEL_UPDATED,
            context__model__model_name="user",
            context__model__app="authentik_core",
            context__model__pk=user.pk,
        )
        event = events.first()
        self.assertIsNotNone(event)
        self.assertIsNotNone(event.context["diff"])
        diff = event.context["diff"]
        diff.pop("last_updated")
        self.assertEqual(
            diff,
            {
                "name": {
                    "new_value": new_name,
                    "previous_value": current_name,
                },
            },
        )

    @patch(
        "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
        PropertyMock(return_value=True),
    )
    def test_delete(self):
        """Test delete audit log"""
        self.client.force_login(self.user)
        user = create_test_admin_user()
        response = self.client.delete(
            reverse("authentik_api:user-detail", kwargs={"pk": user.id}),
        )
        self.assertEqual(response.status_code, 204)
        events = Event.objects.filter(
            action=EventAction.MODEL_DELETED,
            context__model__model_name="user",
            context__model__app="authentik_core",
            context__model__pk=user.pk,
        )
        event = events.first()
        self.assertIsNotNone(event)
        self.assertNotIn("diff", event.context)

    @patch(
        "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
        PropertyMock(return_value=True),
    )
    def test_m2m_add(self):
        """Test m2m add audit log"""
        self.client.force_login(self.user)
        user = create_test_admin_user()
        group = Group.objects.create(name=generate_id())
        response = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.group_uuid}),
            data={
                "pk": user.pk,
            },
        )
        self.assertEqual(response.status_code, 204)
        events = Event.objects.filter(
            action=EventAction.MODEL_UPDATED,
            context__model__model_name="group",
            context__model__app="authentik_core",
            context__model__pk=group.pk.hex,
        )
        event = events.first()
        self.assertIsNotNone(event)
        self.assertIsNotNone(event.context["diff"])
        diff = event.context["diff"]
        self.assertEqual(
            diff,
            {"users": {"add": [user.pk]}},
        )

    @patch(
        "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
        PropertyMock(return_value=True),
    )
    @patch_flag(AuditIncludeExpandedDiff, True)
    def test_m2m_add_expanded(self):
        """Test m2m add audit log"""
        user = create_test_admin_user()
        group = Group.objects.create(name=generate_id())
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.group_uuid}),
            data={
                "pk": user.pk,
            },
        )
        self.assertEqual(response.status_code, 204)
        events = Event.objects.filter(
            action=EventAction.MODEL_UPDATED,
            context__model__model_name="group",
            context__model__app="authentik_core",
            context__model__pk=group.pk.hex,
        )
        event = events.first()
        self.assertIsNotNone(event)
        self.assertIsNotNone(event.context["diff"])
        diff = event.context["diff"]
        self.assertEqual(
            diff,
            {
                "users": {
                    "add": [
                        {
                            "attributes": {},
                            "date_joined": sanitize_item(user.date_joined),
                            "email": user.email,
                            "first_name": "",
                            "id": user.pk,
                            "is_active": True,
                            "last_login": None,
                            "last_name": "",
                            "last_updated": sanitize_item(user.last_updated),
                            "name": user.name,
                            "path": "users",
                            "type": "internal",
                            "username": user.username,
                            "uuid": user.uuid.hex,
                        }
                    ]
                }
            },
        )

    @patch(
        "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
        PropertyMock(return_value=True),
    )
    def test_m2m_remove(self):
        """Test m2m remove audit log"""
        self.client.force_login(self.user)
        user = create_test_admin_user()
        group = Group.objects.create(name=generate_id())
        response = self.client.post(
            reverse("authentik_api:group-remove-user", kwargs={"pk": group.group_uuid}),
            data={
                "pk": user.pk,
            },
        )
        self.assertEqual(response.status_code, 204)
        events = Event.objects.filter(
            action=EventAction.MODEL_UPDATED,
            context__model__model_name="group",
            context__model__app="authentik_core",
            context__model__pk=group.pk.hex,
        )
        event = events.first()
        self.assertIsNotNone(event)
        self.assertIsNotNone(event.context["diff"])
        diff = event.context["diff"]
        self.assertEqual(
            diff,
            {"users": {"remove": [user.pk]}},
        )

    @patch(
        "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
        PropertyMock(return_value=True),
    )
    def test_diff_update_fields(self):
        """Test update audit log"""
        self.client.force_login(self.user)
        diff = EnterpriseAuditMiddleware(None).diff(
            {
                "foo": "bar",
                "is_active": False,
            },
            {
                "foo": "baz",
                "is_active": True,
            },
            update_fields=["is_active"],
        )
        self.assertEqual(diff, {"is_active": {"new_value": True, "previous_value": False}})


class TestEnterpriseAuditLifecycle(SimpleTestCase):
    """Enterprise audit callbacks stay scoped to their request."""

    def test_disconnect_without_license_lookup(self):
        """Disconnect even if licensing is unavailable after connecting."""
        request = RequestFactory().get("/")
        request.request_id = generate_id()
        middleware = EnterpriseAuditMiddleware(Mock())
        baseline = len(post_init.receivers)
        with patch.object(
            EnterpriseAuditMiddleware, "enabled", new_callable=PropertyMock, return_value=True
        ) as enabled:
            middleware.connect(request)
            self.assertEqual(len(post_init.receivers), baseline + 1)
            try:
                enabled.side_effect = AssertionError("cleanup must not query licensing")
                middleware.disconnect(request)
                self.assertEqual(len(post_init.receivers), baseline)
            finally:
                enabled.side_effect = None
                middleware.disconnect(request)

    def test_foreign_request_handlers(self):
        """Another request's callbacks must not query licensing or serialize models."""
        middleware = EnterpriseAuditMiddleware(Mock())
        request = RequestFactory().get("/")
        request.request_id = generate_id()
        other = RequestFactory().get("/")
        other.request_id = generate_id()
        for current in (None, other):
            with self.subTest(current=current):
                token = _CTX_REQUEST.set(current)
                try:
                    with (
                        patch.object(
                            EnterpriseAuditMiddleware,
                            "enabled",
                            new_callable=PropertyMock,
                            return_value=False,
                        ) as enabled,
                        patch.object(middleware, "serialize_simple") as serialize,
                    ):
                        instance = Mock(spec=User)
                        middleware.post_init_handler(request, User, instance)
                        middleware.post_save_handler(request, User, instance, created=False)
                        middleware.m2m_changed_handler(request, User, instance, "pre_add", set())
                        enabled.assert_not_called()
                        serialize.assert_not_called()
                finally:
                    _CTX_REQUEST.reset(token)
