from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from authentik.core.models import Token, TokenIntents, UserTypes
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.agents.apps import AllowAnyAgentCreate
from authentik.enterprise.agents.models import Agent
from authentik.tenants.flags import patch_flag


class AgentTests(APITestCase):

    def _grant_create_perm(self, user):
        user.assign_perms_to_managed_role("authentik_agents.add_agent")

    def test_create_requires_permission(self):
        """Without the add_agent permission and with self-service disabled, a user
        cannot create an agent -- neither for someone else nor for themselves"""
        user = create_test_user()
        other_user = create_test_user()
        self.client.force_login(user)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            data={"parent": other_user.pk},
        )
        self.assertEqual(res.status_code, 403)

        res = self.client.post(reverse("authentik_api:agent-list"), data={})
        self.assertEqual(res.status_code, 403)

    @patch_flag(AllowAnyAgentCreate, True)
    def test_self_service_create_for_self(self):
        """Self-service creation returns a usable API token, creates a service-account
        machine identity, and the token authenticates as the agent"""
        user = create_test_user()
        self.client.force_login(user)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            data={"label": "my-agent"},
        )
        self.assertEqual(res.status_code, 201, res.content)
        body = res.json()

        agent = Agent.objects.get(owner=user)
        self.assertEqual(agent.name, "my-agent")
        # Agents are machine identities, not login users
        self.assertEqual(agent.type, UserTypes.SERVICE_ACCOUNT)
        self.assertFalse(agent.has_usable_password())

        # A single-use API token is returned and bound to the agent
        self.assertTrue(body["token"])
        token = Token.objects.get(user=agent)
        self.assertEqual(token.intent, TokenIntents.INTENT_API)
        self.assertEqual(token.key, body["token"])

        # The token authenticates API requests as the agent
        bearer = APIClient()
        bearer.credentials(HTTP_AUTHORIZATION=f"Bearer {body['token']}")
        me = bearer.get(reverse("authentik_api:user-me"))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["username"], agent.username)

        # owner_field lets the creator see and delete their own agent
        res = self.client.get(reverse("authentik_api:agent-list"))
        content = res.json()
        self.assertEqual(content["pagination"]["count"], 1)
        self.assertEqual(content["results"][0]["parent"]["pk"], user.pk)
        self.assertEqual(content["results"][0]["token_identifier"], token.identifier)

        res = self.client.delete(reverse("authentik_api:agent-detail", kwargs={"pk": agent.pk}))
        self.assertEqual(res.status_code, 204, res.content)
        # Deleting the agent cascades to its token
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())

    @patch_flag(AllowAnyAgentCreate, True)
    def test_self_service_always_expires(self):
        """Self-service agents are always expiring; the caller cannot opt out"""
        user = create_test_user()
        self.client.force_login(user)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            # Attempt to create a standing, never-expiring identity
            data={"expiring": False, "expires": "2099-01-01T00:00:00Z"},
        )
        self.assertEqual(res.status_code, 201, res.content)
        agent = Agent.objects.get(owner=user)
        self.assertTrue(agent.expiring)
        self.assertIsNotNone(agent.expires)
        # The forced expiry is bounded (near the token duration), not the caller's 2099
        self.assertLess(agent.expires.year, 2099)

    def test_admin_creating_for_self_always_expires(self):
        """A privileged user (add_agent) creating an agent for THEMSELVES is still
        self-service, so it must expire -- ownership decides, not the permission"""
        admin = create_test_user()
        self._grant_create_perm(admin)
        self.client.force_login(admin)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            # No parent -> owned by the requester; try to opt out of expiry
            data={"expiring": False, "expires": "2099-01-01T00:00:00Z"},
        )
        self.assertEqual(res.status_code, 201, res.content)
        agent = Agent.objects.get(owner=admin)
        self.assertTrue(agent.expiring)
        self.assertIsNotNone(agent.expires)
        self.assertLess(agent.expires.year, 2099)

    @patch_flag(AllowAnyAgentCreate, True)
    def test_self_service_cannot_create_for_other(self):
        """Self-service only lets a user create agents for themselves, never for
        another user"""
        user = create_test_user()
        other_user = create_test_user()
        self.client.force_login(user)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            data={"parent": other_user.pk},
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(Agent.objects.filter(owner=other_user).exists())

    @patch_flag(AllowAnyAgentCreate, True)
    def test_admin_creates_for_other_with_self_service_enabled(self):
        """An admin with add_agent can still provision for any parent, regardless of
        the self-service flag"""
        admin = create_test_user()
        self._grant_create_perm(admin)
        other_user = create_test_user()
        self.client.force_login(admin)

        res = self.client.post(
            reverse("authentik_api:agent-list"),
            data={"parent": other_user.pk},
        )
        self.assertEqual(res.status_code, 201, res.content)
        agent = Agent.objects.filter(owner=other_user).first()
        self.assertIsNotNone(agent)
        # Admins still get a token issued for the provisioned agent
        self.assertTrue(res.json()["token"])
        self.assertTrue(Token.objects.filter(user=agent, intent=TokenIntents.INTENT_API).exists())

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

    def test_admin_agent_honors_non_expiring(self):
        """An admin-provisioned agent may be a standing (non-expiring) identity"""
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
