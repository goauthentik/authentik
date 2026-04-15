"""user tests"""

from django.test.testcases import TestCase

from authentik.core.models import (
    USER_ATTRIBUTE_AGENT_OWNER_PK,
    USER_PATH_AGENT,
    AuthenticatedSession,
    Session,
    User,
    UserTypes,
)
from authentik.events.models import Event
from authentik.lib.generators import generate_id


class TestUsers(TestCase):
    """Test user"""

    def test_user_managed_role(self):
        """Test user managed role"""
        perm = "authentik_core.view_user"
        user = User.objects.create(username=generate_id())
        user.assign_perms_to_managed_role(perm)
        self.assertEqual(user.roles.count(), 1)
        self.assertTrue(user.has_perm(perm))
        user.remove_perms_from_managed_role(perm)
        self.assertFalse(user.has_perm(perm))

    def test_user_ak_groups(self):
        """Test user.ak_groups is a proxy for user.groups"""
        user = User.objects.create(username=generate_id())
        self.assertEqual(user.ak_groups, user.groups)

    def test_user_ak_groups_event(self):
        """Test user.ak_groups creates exactly one event"""
        user = User.objects.create(username=generate_id())
        self.assertEqual(Event.objects.count(), 0)
        user.ak_groups.all()
        self.assertEqual(Event.objects.count(), 1)
        user.ak_groups.all()
        self.assertEqual(Event.objects.count(), 1)


class TestAgentUserSignals(TestCase):
    """Test signals related to agent user lifecycle"""

    def _create_owner(self):
        owner = User.objects.create(username=generate_id())
        owner.set_unusable_password()
        owner.save()
        return owner

    def _create_agent(self, owner):
        agent = User.objects.create(
            username=generate_id(),
            type=UserTypes.AGENT,
            attributes={USER_ATTRIBUTE_AGENT_OWNER_PK: str(owner.pk)},
            path=USER_PATH_AGENT,
        )
        agent.set_unusable_password()
        agent.save()
        return agent

    def test_delete_owner_cascades_to_agents(self):
        """Deleting an owner also deletes all their agent users"""
        owner = self._create_owner()
        agent1 = self._create_agent(owner)
        agent2 = self._create_agent(owner)
        other_owner = self._create_owner()
        other_agent = self._create_agent(other_owner)

        owner.delete()

        self.assertFalse(User.objects.filter(pk=agent1.pk).exists())
        self.assertFalse(User.objects.filter(pk=agent2.pk).exists())
        self.assertTrue(User.objects.filter(pk=other_agent.pk).exists())

    def test_deactivate_owner_deactivates_agents(self):
        """Setting an owner inactive also marks all their agents inactive"""
        owner = self._create_owner()
        agent = self._create_agent(owner)

        owner.is_active = False
        owner.save(update_fields=["is_active"])

        agent.refresh_from_db()
        self.assertFalse(agent.is_active)

    def test_reactivate_owner_reactivates_agents(self):
        """Setting an owner active again also re-activates their agents"""
        owner = self._create_owner()
        owner.is_active = False
        owner.save(update_fields=["is_active"])
        agent = self._create_agent(owner)
        agent.is_active = False
        agent.save(update_fields=["is_active"])

        owner.is_active = True
        owner.save(update_fields=["is_active"])

        agent.refresh_from_db()
        self.assertTrue(agent.is_active)

    def test_unrelated_owner_save_does_not_affect_agents(self):
        """Saving an owner without changing is_active does not touch agents"""
        owner = self._create_owner()
        agent = self._create_agent(owner)
        agent.is_active = False
        agent.save(update_fields=["is_active"])

        owner.name = generate_id()
        owner.save(update_fields=["name"])

        agent.refresh_from_db()
        self.assertFalse(agent.is_active)

    def test_deactivate_owner_clears_agent_sessions(self):
        """Deactivating an owner removes authenticated sessions for their agents"""
        owner = self._create_owner()
        agent = self._create_agent(owner)
        session = Session.objects.create(
            session_key=generate_id(),
            last_ip="255.255.255.255",
            last_user_agent="",
        )
        AuthenticatedSession.objects.create(user=agent, session=session)

        owner.is_active = False
        owner.save(update_fields=["is_active"])

        self.assertFalse(Session.objects.filter(pk=session.pk).exists())
