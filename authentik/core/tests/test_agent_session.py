"""Test agent token-to-session exchange"""

from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import (
    USER_ATTRIBUTE_AGENT_OWNER_PK,
    Token,
    TokenIntents,
    User,
    UserTypes,
)
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id


class TestAgentSession(APITestCase):
    """Test agent token-to-session exchange"""

    def _create_agent_with_token(self):
        owner = create_test_user()
        agent = User.objects.create(
            username=generate_id(),
            type=UserTypes.INTERNAL,
            attributes={USER_ATTRIBUTE_AGENT_OWNER_PK: str(owner.pk)},
        )
        agent.set_unusable_password()
        agent.save()
        token = Token.objects.create(
            identifier=generate_id(),
            intent=TokenIntents.INTENT_API,
            user=agent,
            expiring=True,
        )
        return owner, agent, token

    def test_session_exchange_success(self):
        """Valid agent token creates a session"""
        _owner, _agent, token = self._create_agent_with_token()
        response = self.client.post(
            reverse("authentik_api:agent-session"),
            data={"key": token.key},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 204)

    def test_session_exchange_invalid_token(self):
        """Invalid token key is rejected"""
        response = self.client.post(
            reverse("authentik_api:agent-session"),
            data={"key": "nonexistent-key"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_session_exchange_non_agent(self):
        """Token belonging to a non-agent user is rejected"""
        user = create_test_user()
        token = Token.objects.create(
            identifier=generate_id(),
            intent=TokenIntents.INTENT_API,
            user=user,
            expiring=True,
        )
        response = self.client.post(
            reverse("authentik_api:agent-session"),
            data={"key": token.key},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_session_exchange_inactive_agent(self):
        """Inactive agent is rejected"""
        _owner, agent, token = self._create_agent_with_token()
        agent.is_active = False
        agent.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("authentik_api:agent-session"),
            data={"key": token.key},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
