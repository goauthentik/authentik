from unittest.mock import PropertyMock, patch

from django.apps import apps
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.crypto.generators import generate_id
from authentik.events.models import Event, EventAction
from authentik.events.utils import sanitize_item


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
                "password": {"new_value": "********************", "previous_value": None},
                "password_change_date": {
                    "new_value": sanitize_item(user.password_change_date),
                    "previous_value": None,
                },
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
