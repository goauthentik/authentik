from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.enterprise.agents.models import Agent


class AgentTests(APITestCase):

    def _grant_create_perm(self, user):
        user.assign_perms_to_managed_role("authentik_agents.add_agent")

    def test_create_requires_permission(self):
        """Ordinary users cannot create agents -- admin-provisioned, not
        self-service"""
        user = create_test_user()
        other_user = create_test_user()
        self.client.force_login(user)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            data={"parent": other_user.pk},
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_creates_agent_for_user(self):
        """An admin with add_agent can create an agent for any user"""
        admin = create_test_user()
        self._grant_create_perm(admin)
        other_user = create_test_user()
        self.client.force_login(admin)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            data={"parent": other_user.pk, "label": "support-bot"},
        )
        self.assertEqual(res.status_code, 201, res.content)
        agent = Agent.objects.get(owner=other_user)
        self.assertTrue(agent.username.startswith("agent-"))
        self.assertEqual(agent.name, "support-bot")

    def test_agent_defaults_to_non_expiring(self):
        """An agent created without an explicit expiry is a standing identity"""
        admin = create_test_user()
        self._grant_create_perm(admin)
        other_user = create_test_user()
        self.client.force_login(admin)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            data={"parent": other_user.pk},
        )
        self.assertEqual(res.status_code, 201, res.content)
        agent = Agent.objects.get(owner=other_user)
        self.assertFalse(agent.expiring)
        self.assertIsNone(agent.expires)

    def test_list_only_shows_own_agents(self):
        """A user only sees agents they have object-level permission on
        (granted automatically to the parent at creation time)"""
        admin = create_test_user()
        self._grant_create_perm(admin)
        user = create_test_user()
        other_user = create_test_user()
        self.client.force_login(admin)

        self.client.post(
            reverse("authentik_api:agent-list"),
            data={"parent": other_user.pk},
        )
        res = self.client.post(
            reverse("authentik_api:agent-list"),
            data={"parent": user.pk},
        )
        self.assertEqual(res.status_code, 201, res.content)

        self.client.force_login(user)
        res = self.client.get(reverse("authentik_api:agent-list"))
        content = res.json()
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(content["results"][0]["parent"]["pk"], user.pk)

    def test_destroy_own_agent(self):
        user = create_test_user()
        self.client.force_login(user)
        agent = Agent.create_for_user(user)
        user.assign_perms_to_managed_role(
            ["authentik_agents.view_agent", "authentik_agents.delete_agent"], agent
        )

        res = self.client.delete(reverse("authentik_api:agent-detail", kwargs={"pk": agent.pk}))
        self.assertEqual(res.status_code, 204, res.content)
        self.assertFalse(Agent.objects.filter(pk=agent.pk).exists())

    def test_deleting_parent_cascades_to_agent(self):
        """Deleting the parent user deletes their agents along with it"""
        user = create_test_user()
        agent = Agent.create_for_user(user)
        agent_pk = agent.pk

        user.delete()
        self.assertFalse(Agent.objects.filter(pk=agent_pk).exists())
