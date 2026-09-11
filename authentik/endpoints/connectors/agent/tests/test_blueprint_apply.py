from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group, User, UserTypes
from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.connectors.agent.blueprint import AGENT_APPLY_IDENTITY_USERNAME
from authentik.endpoints.connectors.agent.models import AgentConnector
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role

APPLY_PERMS = [
    "authentik_core.add_application",
    "authentik_core.change_application",
    "authentik_providers_oauth2.add_oauth2provider",
    "authentik_providers_oauth2.change_oauth2provider",
    "authentik_providers_saml.add_samlprovider",
    "authentik_providers_saml.change_samlprovider",
]


class TestAgentBlueprintApply(APITestCase):
    """The bounded server-side apply path for Agent-proposed Blueprints."""

    def setUp(self):
        self.connector = AgentConnector.objects.create(name=generate_id())
        # The caller is a superuser, to prove the boundary comes from the apply
        # identity, not from the operator's own (here unlimited) privileges.
        self.client.force_login(create_test_admin_user())

    def _provision_identity(self) -> User:
        role = Role.objects.create(name=generate_id())
        role.assign_perms(APPLY_PERMS)
        group = Group.objects.create(name=generate_id())
        group.roles.add(role)
        identity = User.objects.create(
            username=AGENT_APPLY_IDENTITY_USERNAME,
            type=UserTypes.INTERNAL_SERVICE_ACCOUNT,
        )
        group.users.add(identity)
        return identity

    def _apply(self, content: str):
        return self.client.post(
            reverse(
                "authentik_api:agentconnector-apply-blueprint",
                kwargs={"pk": self.connector.pk},
            ),
            data={"content": content},
        )

    def test_apply_allowed_model(self):
        """A curated model (Application) applies successfully."""
        self._provision_identity()
        slug = generate_id()
        res = self._apply(
            f"version: 1\nentries:\n  - model: authentik_core.application\n"
            f"    identifiers: {{slug: {slug}}}\n    attrs: {{name: {slug}}}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertTrue(Application.objects.filter(slug=slug).exists())

    def test_apply_denied_model_even_as_superuser(self):
        """A superuser group (Finding B) is refused: the apply identity lacks
        add_group, and the superuser caller does not lend it their privileges."""
        self._provision_identity()
        name = generate_id()
        res = self._apply(
            f"version: 1\nentries:\n  - model: authentik_core.group\n"
            f"    identifiers: {{name: {name}}}\n    attrs: {{is_superuser: true}}"
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(Group.objects.filter(name=name).exists())

    def test_apply_destructive_denied(self):
        """An absent (delete) entry needs delete_application, which the bounded
        identity does not hold, so destructive applies are refused server-side."""
        self._provision_identity()
        app = Application.objects.create(slug=generate_id(), name=generate_id())
        res = self._apply(
            f"version: 1\nentries:\n  - model: authentik_core.application\n"
            f"    state: absent\n    identifiers: {{slug: {app.slug}}}"
        )
        self.assertEqual(res.status_code, 403)
        self.assertTrue(Application.objects.filter(pk=app.pk).exists())

    def test_apply_identity_not_provisioned(self):
        """Without the provisioned identity the endpoint refuses rather than
        falling back to the caller."""
        res = self._apply(
            "version: 1\nentries:\n  - model: authentik_core.application\n"
            "    identifiers: {slug: x}\n    attrs: {name: x}"
        )
        self.assertEqual(res.status_code, 400)

    def test_apply_invalid_yaml(self):
        """Malformed content is a validation error, not a 500."""
        self._provision_identity()
        res = self._apply("this: is: not: a: blueprint")
        self.assertEqual(res.status_code, 400)
