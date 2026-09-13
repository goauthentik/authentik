from django.test import TestCase

from authentik.core.models import User, UserTypes
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.agents.models import Agent
from authentik.events.utils import get_user
from authentik.lib.generators import generate_id


class AgentAttributionTests(TestCase):
    """Agent actions are audited on behalf of the owning human."""

    def test_agent_event_user_records_owner(self):
        owner = create_test_user()
        agent = Agent.create_for_user(owner, name="support-bot")
        data = get_user(agent)
        self.assertTrue(data["is_agent"])
        self.assertEqual(data["on_behalf_of"]["pk"], owner.pk)

    def test_normal_user_has_no_attribution(self):
        data = get_user(create_test_user())
        self.assertNotIn("on_behalf_of", data)
        self.assertNotIn("is_agent", data)

    def test_plain_service_account_has_no_attribution(self):
        """A service account that is not an agent is not attributed to an owner."""
        service_account = User.objects.create(
            username=generate_id(), type=UserTypes.SERVICE_ACCOUNT
        )
        data = get_user(service_account)
        self.assertNotIn("on_behalf_of", data)
        self.assertNotIn("is_agent", data)
