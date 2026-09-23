"""Event Middleware tests"""

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group, Token, TokenIntents
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.middleware import audit_ignore, audit_overwrite_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id


@override_settings(
    MIDDLEWARE=[
        (
            "authentik.events.middleware.AuditMiddleware"
            if middleware == "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware"
            else middleware
        )
        for middleware in settings.MIDDLEWARE
    ]
)
class TestEventsMiddleware(APITestCase):
    """Test Event Middleware"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        Event.objects.all().delete()

    def test_create(self):
        """Test model creation event"""
        uid = generate_id()
        self.client.post(
            reverse("authentik_api:application-list"),
            data={"name": uid, "slug": uid},
        )
        self.assertTrue(Application.objects.filter(name=uid).exists())
        event = Event.objects.filter(
            action=EventAction.MODEL_CREATED,
            context__model__model_name="application",
            context__model__app="authentik_core",
            context__model__name=uid,
        ).first()
        self.assertIsNotNone(event)

    def test_delete(self):
        """Test model creation event"""
        uid = generate_id()
        Application.objects.create(name=uid, slug=uid)
        self.client.delete(reverse("authentik_api:application-detail", kwargs={"slug": uid}))
        self.assertFalse(Application.objects.filter(name="test").exists())
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_DELETED,
                context__model__model_name="application",
                context__model__app="authentik_core",
                context__model__name=uid,
            ).exists()
        )

    def test_m2m_membership_changes(self):
        """Group membership changes must succeed and produce an audit event without enterprise."""
        group = Group.objects.create(name=generate_id())
        for action in ("add", "remove"):
            with self.subTest(action=action):
                Event.objects.all().delete()
                response = self.client.post(
                    reverse(f"authentik_api:group-{action}-user", kwargs={"pk": group.pk}),
                    data={"pk": self.user.pk},
                )
                self.assertEqual(response.status_code, 204)
                self.assertEqual(group.users.filter(pk=self.user.pk).exists(), action == "add")
                event = Event.objects.get(
                    action=EventAction.MODEL_UPDATED,
                    context__model__model_name="group",
                    context__model__pk=group.pk.hex,
                )
                self.assertEqual(event.user["pk"], self.user.pk)

    def test_audit_ignore(self):
        """Test audit_ignore context manager"""
        uid = generate_id()
        with audit_ignore():
            self.client.post(
                reverse("authentik_api:application-list"),
                data={"name": uid, "slug": uid},
            )
        self.assertTrue(Application.objects.filter(name=uid).exists())
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.MODEL_CREATED,
                context__model__model_name="application",
                context__model__app="authentik_core",
                context__model__name=uid,
            ).exists()
        )

    def test_audit_overwrite_user(self):
        """Test audit_overwrite_user context manager"""
        uid = generate_id()
        new_user = create_test_admin_user()
        with audit_overwrite_user(new_user):
            self.client.post(
                reverse("authentik_api:application-list"),
                data={"name": uid, "slug": uid},
            )
        self.assertTrue(Application.objects.filter(name=uid).exists())
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.MODEL_CREATED,
                context__model__model_name="application",
                context__model__app="authentik_core",
                context__model__name=uid,
                user__username=new_user.username,
            ).exists()
        )

    def test_create_with_api(self):
        """Test model creation event (with API token auth)"""
        self.client.logout()
        token = Token.objects.create(user=self.user, intent=TokenIntents.INTENT_API, expiring=False)
        uid = generate_id()
        self.client.post(
            reverse("authentik_api:application-list"),
            data={"name": uid, "slug": uid},
            HTTP_AUTHORIZATION=f"Bearer {token.key}",
        )
        self.assertTrue(Application.objects.filter(name=uid).exists())
        event = Event.objects.filter(
            action=EventAction.MODEL_CREATED,
            context__model__model_name="application",
            context__model__app="authentik_core",
            context__model__name=uid,
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(
            event.user,
            {
                "pk": self.user.pk,
                "email": self.user.email,
                "username": self.user.username,
            },
        )
