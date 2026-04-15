"""Enterprise task tests"""

from django.test import TestCase

from authentik.core.models import (
    USER_ATTRIBUTE_AGENT_OWNER_PK,
    USER_PATH_AGENT,
    User,
    UserTypes,
)
from authentik.lib.generators import generate_id


class TestDeactivateAgentUsers(TestCase):
    """Tests for _deactivate_agent_users enterprise task"""

    def _create_agent(self, owner):
        agent = User.objects.create(
            username=generate_id(),
            type=UserTypes.AGENT,
            attributes={USER_ATTRIBUTE_AGENT_OWNER_PK: str(owner.pk)},
            path=USER_PATH_AGENT,
            is_active=True,
        )
        agent.set_unusable_password()
        agent.save()
        return agent

    def test_deactivates_all_active_agents(self):
        """_deactivate_agent_users marks all active agent users inactive"""
        from authentik.enterprise.tasks import _deactivate_agent_users

        owner = User.objects.create(username=generate_id())
        agent1 = self._create_agent(owner)
        agent2 = self._create_agent(owner)

        _deactivate_agent_users()

        agent1.refresh_from_db()
        agent2.refresh_from_db()
        self.assertFalse(agent1.is_active)
        self.assertFalse(agent2.is_active)

    def test_does_not_deactivate_non_agents(self):
        """_deactivate_agent_users does not affect non-agent service accounts"""
        from authentik.enterprise.tasks import _deactivate_agent_users

        sa = User.objects.create(
            username=generate_id(),
            type=UserTypes.SERVICE_ACCOUNT,
            is_active=True,
        )
        internal = User.objects.create(
            username=generate_id(),
            type=UserTypes.INTERNAL,
            is_active=True,
        )

        _deactivate_agent_users()

        sa.refresh_from_db()
        internal.refresh_from_db()
        self.assertTrue(sa.is_active)
        self.assertTrue(internal.is_active)
