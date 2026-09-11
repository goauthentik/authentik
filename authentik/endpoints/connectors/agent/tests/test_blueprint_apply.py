from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group, User, UserTypes
from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.connectors.agent.blueprint import (
    AGENT_APPLY_IDENTITY_USERNAME,
    TOKEN_MAX_SECONDS,
    check_agent_apply_content,
)
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
        self.assertEqual(res.status_code, 400)
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
        self.assertEqual(res.status_code, 400)
        self.assertTrue(Application.objects.filter(pk=app.pk).exists())

    def test_apply_rejects_permissions_and_unsafe_tags(self):
        """Content policy cannot be bypassed by a modified Agent binary."""
        self._provision_identity()
        res = self._apply(
            "version: 1\nentries:\n  - model: authentik_core.application\n"
            "    identifiers: {slug: x}\n    attrs: {name: !Env SECRET}\n"
            "    permissions: [{permission: authentik_core.change_application}]"
        )
        self.assertEqual(res.status_code, 400)

    def test_apply_rejects_api_scope(self):
        """OAuth API scopes must never be attachable through Agent apply."""
        self._provision_identity()
        res = self._apply(
            "version: 1\nentries:\n  - model: authentik_providers_oauth2.oauth2provider\n"
            "    identifiers: {name: x}\n    attrs:\n      name: x\n"
            "      include_claims_in_id_token: false\n"
            "      property_mappings:\n"
            "        - !Find [authentik_providers_oauth2.scopemapping, [managed, "
            "goauthentik.io/providers/oauth2/scope-authentik_api]]"
        )
        self.assertEqual(res.status_code, 400)

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


class TestAgentApplyContentPolicy(TestCase):
    """The server-side content policy, unit-tested independently of apply."""

    def _provider(self, extra_attrs: str = "") -> str:
        return (
            "version: 1\nentries:\n"
            "  - model: authentik_providers_oauth2.oauth2provider\n"
            "    attrs:\n"
            "      name: x\n" + extra_attrs
        )

    def test_forced_fields_optional_when_absent(self):
        """Forced fields (sub_mode/issuer_mode/include_claims) are enforced only
        when present — a provider that omits them is accepted, matching the
        Agent's client-side validator so the propose→apply loop doesn't break."""
        self.assertEqual(check_agent_apply_content(self._provider()), [])

    def test_forced_fields_enforced_when_present(self):
        self.assertTrue(
            check_agent_apply_content(self._provider("      include_claims_in_id_token: true\n"))
        )
        self.assertTrue(check_agent_apply_content(self._provider("      sub_mode: user_id\n")))
        self.assertEqual(
            check_agent_apply_content(self._provider("      include_claims_in_id_token: false\n")),
            [],
        )

    def test_token_validity_within_cap_accepted(self):
        for value in ("3600", "hours=1", f"seconds={TOKEN_MAX_SECONDS}", "0"):
            self.assertEqual(
                check_agent_apply_content(
                    self._provider(f"      access_token_validity: {value}\n")
                ),
                [],
                value,
            )

    def test_token_validity_over_cap_or_unparseable_rejected(self):
        for value in ("weeks=9999", "days=2", "-5", "forever", "hours=abc"):
            self.assertTrue(
                check_agent_apply_content(self._provider(f"      access_code_validity: {value}\n")),
                value,
            )
