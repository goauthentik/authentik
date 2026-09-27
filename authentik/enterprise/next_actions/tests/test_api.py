"""Required-action user API tests."""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.enterprise.next_actions import USER_ATTRIBUTE_NEXT_ACTIONS
from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowDesignation


class TestNextActionsAPI(APITestCase):
    def setUp(self):
        self.admin = create_test_admin_user()
        self.user = create_test_user()

    def test_set_next_actions(self):
        """Test setting next action flows on a user"""
        self.client.force_login(self.admin)
        flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        for value in [flow.slug, [flow.slug]]:
            response = self.client.patch(
                reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
                data={"attributes": {USER_ATTRIBUTE_NEXT_ACTIONS: value}},
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.user.refresh_from_db()
            self.assertEqual(self.user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS], value)
        # Only the first patch changes the set of actions
        self.assertEqual(
            Event.objects.filter(
                action=EventAction.NEXT_ACTION_SET, context__flow_slug=flow.slug
            ).count(),
            1,
        )

        response = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            data={"attributes": {}},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Event.objects.filter(
                action=EventAction.NEXT_ACTION_REMOVED, context__flow_slug=flow.slug
            ).count(),
            1,
        )
        # Next-action-only updates don't additionally log a model update
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.MODEL_UPDATED,
                context__model__pk=self.user.pk,
            ).exists()
        )

    def test_next_actions_require_change_user_permission(self):
        """A delegated editor can change actions only for their assigned user."""
        actor = create_test_user()
        actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(actor)
        flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        data = {"attributes": {USER_ATTRIBUTE_NEXT_ACTIONS: [flow.slug]}}
        target = reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk})
        self.assertEqual(self.client.patch(target, data, format="json").status_code, 403)
        actor.assign_perms_to_managed_role("authentik_core.change_user", self.user)
        self.assertEqual(self.client.patch(target, data, format="json").status_code, 200)
        own = reverse("authentik_api:user-detail", kwargs={"pk": actor.pk})
        self.assertEqual(self.client.patch(own, data, format="json").status_code, 403)
        self.assertEqual(
            self.client.patch(target, {"attributes": {}}, format="json").status_code, 200
        )

    def test_set_next_actions_invalid(self):
        """Test that unknown flows and disallowed designations are rejected"""
        self.client.force_login(self.admin)
        authentication_flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        for value in ["does-not-exist", [authentication_flow.slug], [42]]:
            response = self.client.patch(
                reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
                data={"attributes": {USER_ATTRIBUTE_NEXT_ACTIONS: value}},
                format="json",
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json(),
                {
                    "attributes": [
                        "Next actions must reference existing flows other than "
                        "authentication or invalidation flows."
                    ]
                },
            )
