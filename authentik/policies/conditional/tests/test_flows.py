"""Default flows using conditional policies"""

from django.test import TestCase
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.tests.utils import create_test_user


class TestConditionalPolicyFlows(TestCase):
    """Default flows using conditional policies"""

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_authentication_requires_password(self):
        """The password stage is only skipped when the user is already authenticated, and
        not when the policy fails to run"""
        user = create_test_user()
        url = reverse(
            "authentik_api:flow-executor", kwargs={"flow_slug": "default-authentication-flow"}
        )
        self.client.get(url)
        response = self.client.post(
            url,
            {"component": "ak-stage-identification", "uid_field": user.username},
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(response.json()["component"], "ak-stage-password")
