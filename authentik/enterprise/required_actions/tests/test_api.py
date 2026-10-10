"""Required action user API tests"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.enterprise.required_actions import USER_ATTRIBUTE_REQUIRED_ACTIONS
from authentik.flows.models import FlowAuthenticationRequirement, FlowDesignation


class TestRequiredActionsAPI(APITestCase):
    def setUp(self):
        self.client.force_login(create_test_admin_user())
        self.user = create_test_user()
        self.url = reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk})

    def patch_attributes(self, attributes: dict):
        return self.client.patch(self.url, {"attributes": attributes}, format="json")

    def test_set(self):
        """A flow slug or a list of flow slugs is accepted"""
        flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        for value in [flow.slug, [flow.slug]]:
            with self.subTest(value=value):
                response = self.patch_attributes({USER_ATTRIBUTE_REQUIRED_ACTIONS: value})
                self.assertEqual(response.status_code, 200)
                self.user.refresh_from_db()
                self.assertEqual(self.user.attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS], value)

    def test_set_invalid(self):
        """Flows that are missing or cannot run, and values that aren't slugs, are rejected"""
        authentication = create_test_flow(FlowDesignation.AUTHENTICATION)
        invalidation = create_test_flow(FlowDesignation.INVALIDATION)
        recovery = create_test_flow(
            FlowDesignation.RECOVERY,
            authentication=FlowAuthenticationRequirement.REQUIRE_UNAUTHENTICATED,
        )
        for value in [
            "does-not-exist",
            [authentication.slug],
            [invalidation.slug],
            [recovery.slug],
            [42],
            None,
        ]:
            with self.subTest(value=value):
                response = self.patch_attributes({USER_ATTRIBUTE_REQUIRED_ACTIONS: value})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json(),
                    {
                        "attributes": [
                            "Required actions must reference existing flows that a logged-in "
                            "user can run, other than authentication or invalidation flows."
                        ]
                    },
                )

    def test_unchanged_invalid_actions_allow_other_edits(self):
        """Deleting a required flow doesn't block unrelated edits to the user"""
        flow = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.patch_attributes({USER_ATTRIBUTE_REQUIRED_ACTIONS: [flow.slug]})
        flow.delete()
        response = self.patch_attributes(
            {USER_ATTRIBUTE_REQUIRED_ACTIONS: [flow.slug], "department": "Support"}
        )
        self.assertEqual(response.status_code, 200)
